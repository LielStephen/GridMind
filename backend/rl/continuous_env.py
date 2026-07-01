"""
Continuous Action Gymnasium Environment for Building Energy Management.

Continuous Action Space: Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
    Action[0]: HVAC continuous cooling power [-1.0, 1.0] -> mapped to [0.0, 1.0] fraction of rated capacity.
    Action[1]: Battery rate [-1.0, 1.0] -> [-1.0, 0.0) discharge, (0.0, 1.0] charge fraction of max power.

Observation Space: Box(7-dim continuous)
    [Hour/24, T_indoor, T_outdoor, Solar_pu, Battery_SoC, Grid_Price, Occupancy]
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from backend.config.settings import EnvConfig
from backend.simulator.battery_advanced import AdvancedBatterySystem
from backend.simulator.pricing_advanced import AdvancedTariffManager
from backend.simulator.rc_model import LumpedRCBuildingModel

logger = logging.getLogger(__name__)


class GridMindContinuousEnv(gym.Env):
    """Continuous control Gymnasium environment suited for SAC, TD3, and DDPG."""

    metadata = {"render_modes": []}

    def __init__(self, config: EnvConfig | None = None) -> None:
        super().__init__()
        self.cfg = config or EnvConfig()

        self.rc_model = LumpedRCBuildingModel()
        self.battery = AdvancedBatterySystem()
        self.tariff_mgr = AdvancedTariffManager()

        # Continuous action space: [hvac_power_ratio, battery_ratio]
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(2,), dtype=np.float32
        )

        # Observation space: 7 continuous features
        self.observation_space = spaces.Box(
            low=np.array([0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([24.0, 35.0, 45.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32),
        )

        self.current_step: int = 0
        self.reset()

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, dict]:
        super().reset(seed=seed)

        self.current_step = 0
        self.rc_model.reset(self.cfg.building.initial_indoor_temp)
        self.battery.reset(self.cfg.battery.initial_soc)

        return self._get_obs(), {}

    def _get_obs(self) -> np.ndarray:
        hour = (self.current_step * self.cfg.step_duration_s / 3600.0) % 24.0
        # Synthetic weather curve
        solar_pu = max(0.0, np.sin(np.pi * max(0.0, hour - 6.0) / 12.0))
        ext_temp = 20.0 + 8.0 * np.sin(np.pi * (hour - 8.0) / 12.0)
        grid_price = self.tariff_mgr.get_spot_price(hour)
        occupied = 1.0 if (7.0 <= hour <= 23.0) else 0.0

        obs = np.array(
            [
                hour,
                self.rc_model.t_air,
                ext_temp,
                solar_pu,
                self.battery.soc,
                grid_price,
                occupied,
            ],
            dtype=np.float32,
        )
        return obs

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, dict]:
        action = np.clip(action, -1.0, 1.0)
        hvac_raw, batt_raw = float(action[0]), float(action[1])

        # Map HVAC [-1, 1] -> [0, 1] fraction of rated cooling (e.g. 3500 W)
        hvac_fraction = max(0.0, (hvac_raw + 1.0) / 2.0)
        hvac_thermal_power_w = hvac_fraction * self.cfg.hvac.power_rating_w * 1.75
        hvac_elec_power_w = hvac_fraction * self.cfg.hvac.power_rating_w

        dt = float(self.cfg.step_duration_s)
        obs = self._get_obs()
        hour, _, ext_temp, solar_pu, _, grid_price, occupied = obs

        # 1. Update battery
        batt_grid_import_w = 0.0
        batt_elec_output_w = 0.0
        if batt_raw > 0.05:
            # Charge battery from grid
            req_charge_w = batt_raw * self.battery.cfg.max_charge_power_w
            batt_grid_import_w, _ = self.battery.charge(req_charge_w, dt)
        elif batt_raw < -0.05:
            # Discharge battery to building load
            req_discharge_w = abs(batt_raw) * self.battery.cfg.max_discharge_power_w
            batt_elec_output_w, _ = self.battery.discharge(req_discharge_w, dt)

        # 2. Update thermal physics
        solar_w_m2 = solar_pu * 800.0
        t_air, t_wall, t_attic = self.rc_model.step(
            t_out=ext_temp,
            solar_irradiance_w_m2=solar_w_m2,
            hvac_cooling_power_w=hvac_thermal_power_w,
            dt_seconds=dt,
            occupancy=bool(occupied),
        )

        # 3. Calculate energy balance & net grid draw
        base_load_w = 400.0 + (300.0 if occupied else 0.0)
        net_load_w = base_load_w + hvac_elec_power_w + batt_grid_import_w - batt_elec_output_w

        grid_imported_w = max(0.0, net_load_w)
        grid_exported_w = max(0.0, -net_load_w)

        net_cost, carbon_g, demand_penalty = self.tariff_mgr.compute_step_cost(
            grid_imported_w, grid_exported_w, hour, dt
        )

        # 4. Thermal Comfort Penalty
        t_min, t_max = self.cfg.building.comfort_low, self.cfg.building.comfort_high
        comfort_penalty = 0.0
        if occupied:

            if t_air < t_min:
                comfort_penalty = (t_min - t_air) ** 2 * 0.25
            elif t_air > t_max:
                comfort_penalty = (t_air - t_max) ** 2 * 0.25

        reward = -(net_cost + comfort_penalty + 0.001 * demand_penalty)

        self.current_step += 1
        terminated = self.current_step >= self.cfg.steps_per_episode
        next_obs = self._get_obs()


        info = {
            "step_cost": net_cost,
            "indoor_temp": t_air,
            "comfort_penalty": comfort_penalty,
            "battery_soc": self.battery.soc,
            "grid_imported_w": grid_imported_w,
            "carbon_g": carbon_g,
        }

        return next_obs, float(reward), terminated, False, info
