"""
GridMind Gymnasium environment — smart energy management.

A single-building, single-day energy simulation where an RL agent controls
HVAC and battery storage to minimise electricity cost while maintaining
occupant comfort.

Observation Space (7-dim, continuous)
    ┌────┬───────────────┬──────┬──────┐
    │ Idx│ Feature       │  Low │ High │
    ├────┼───────────────┼──────┼──────┤
    │  0 │ Hour of day   │    0 │   23 │
    │  1 │ Indoor temp   │   10 │   35 │
    │  2 │ Outdoor temp  │    0 │   45 │
    │  3 │ Solar gen (pu)│    0 │    1 │
    │  4 │ Battery SOC   │    0 │    1 │
    │  5 │ Grid price    │    0 │    1 │
    │  6 │ Occupancy     │    0 │    1 │
    └────┴───────────────┴──────┴──────┘

Action Space: Discrete(5)
    0 — Do nothing (idle)
    1 — Turn AC on
    2 — Turn AC off
    3 — Charge battery from grid
    4 — Discharge battery to load
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from backend.config.settings import EnvConfig
from backend.simulator.models import AirConditioner, Battery, WeatherProvider

logger = logging.getLogger(__name__)


class GridMindEnv(gym.Env):
    """Gymnasium environment for building energy management.

    Parameters
    ----------
    config : EnvConfig, optional
        Environment configuration.  Uses sensible defaults when omitted.
    render_mode : str | None
        Gymnasium render mode (unused — headless sim).
    """

    metadata = {"render_modes": []}

    # Action constants for readability
    ACTION_IDLE = 0
    ACTION_AC_ON = 1
    ACTION_AC_OFF = 2
    ACTION_CHARGE = 3
    ACTION_DISCHARGE = 4

    def __init__(
        self,
        config: EnvConfig | None = None,
        render_mode: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.cfg = config or EnvConfig()

        # Subsystems — inject config down
        self.weather = WeatherProvider(pricing=self.cfg.pricing)
        self.ac = AirConditioner("MainAC", config=self.cfg.hvac)
        self.battery = Battery(config=self.cfg.battery)

        # Gymnasium spaces
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(
            low=np.array([0, 10, 0, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([23, 35, 45, 1, 1, 1, 1], dtype=np.float32),
        )

        # Internal state
        self.current_step: int = 0
        self.indoor_temp: float = self.cfg.building.initial_indoor_temp

        # Perform initial reset (sets obs cache)
        self.reset()

    # ------------------------------------------------------------------
    # Gymnasium API
    # ------------------------------------------------------------------

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, dict]:
        """Reset the environment to the start of a new 24-hour episode."""
        super().reset(seed=seed)

        self.current_step = 0
        self.indoor_temp = self.cfg.building.initial_indoor_temp
        self.ac.is_on = False
        self.battery.current_charge = (
            self.cfg.battery.capacity_wh * self.cfg.battery.initial_soc
        )

        logger.debug("Environment reset — step=%d, indoor=%.1f°C", 0, self.indoor_temp)
        return self._get_obs(), {}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """Execute one simulation timestep.

        Parameters
        ----------
        action : int
            Agent action from ``{0, 1, 2, 3, 4}``.

        Returns
        -------
        obs : np.ndarray
            Updated observation vector (7,).
        reward : float
            Scalar reward (negative of cost + comfort penalty).
        terminated : bool
            ``True`` when the episode completes after 96 steps (24 h).
        truncated : bool
            Always ``False`` (no early truncation).
        info : dict
            ``{"cost": float, "net_w": float}`` — step cost and net load.
        """
        dt = self.cfg.step_duration_s
        bldg = self.cfg.building
        ext_temp, solar, price, occupied = self.weather.get_state(self.current_step)

        # 1. Apply discrete actions -----------------------------------------
        if action == self.ACTION_AC_ON:
            self.ac.is_on = True
        elif action == self.ACTION_AC_OFF:
            self.ac.is_on = False

        batt_load = 0.0
        if action == self.ACTION_CHARGE:
            batt_load = self.battery.charge(self.ac.power_rating, dt)
        elif action == self.ACTION_DISCHARGE:
            batt_load = self.battery.discharge(self.ac.power_rating, dt)

        # 2. Update building physics ----------------------------------------
        # Thermal leakage from outdoor
        self.indoor_temp += (ext_temp - self.indoor_temp) * bldg.thermal_leakage_coeff

        # Active cooling
        if self.ac.is_on:
            self.indoor_temp -= self.ac.cooling_rate

        # 3. Energy balance --------------------------------------------------
        solar_w = solar * self.cfg.solar.peak_output_w
        net_w = self.ac.step() + batt_load - solar_w
        cost = (max(0.0, net_w) / 1_000) * (dt / 3_600) * price

        # 4. Reward signal ---------------------------------------------------
        comfort_penalty = 0.0
        if occupied and (self.indoor_temp < bldg.comfort_low or self.indoor_temp > bldg.comfort_high):
            comfort_penalty = abs(self.indoor_temp - bldg.comfort_target) * bldg.comfort_penalty_weight

        reward = -(cost + comfort_penalty)

        # 5. Advance time ----------------------------------------------------
        self.current_step += 1
        terminated = self.current_step > self.cfg.steps_per_episode

        logger.debug(
            "step=%d  action=%d  indoor=%.1f°C  cost=%.4f  reward=%.4f  term=%s",
            self.current_step, action, self.indoor_temp, cost, reward, terminated,
        )

        return self._get_obs(), reward, terminated, False, {"cost": cost, "net_w": net_w}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_obs(self) -> np.ndarray:
        """Build the observation vector from current simulator state."""
        ext_temp, solar, price, occ = self.weather.get_state(self.current_step)
        return np.array(
            [
                (self.current_step // 4) % 24,   # hour of day
                self.indoor_temp,                 # indoor temperature
                ext_temp,                         # outdoor temperature
                solar,                            # solar generation (pu)
                self.battery.soc,                 # battery state-of-charge
                price,                            # grid price
                float(occ),                       # occupancy flag
            ],
            dtype=np.float32,
        )
