"""
3-Node Lumped Thermal RC Model for Building Thermodynamics.

Models thermal energy balances across:
1. Indoor Air & Fast Dynamics Node (C_air)
2. Building Envelope & Heavy Mass Node (C_wall)
3. Roof & Attic Node (C_attic)

Governed by system of coupled ODEs:
  C_air * dT_air/dt   = (T_wall - T_air)/R_wall + (T_attic - T_air)/R_attic + (T_out - T_air)/R_win + Q_int + Q_solar_win - Q_hvac
  C_wall * dT_wall/dt = (T_air - T_wall)/R_wall + (T_out - T_wall)/R_ext_wall + Q_solar_wall
  C_attic * dT_attic/dt = (T_air - T_attic)/R_attic + (T_out - T_attic)/R_roof + Q_solar_roof
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class RCModelConfig:
    """Thermal capacities (J/K) and resistances (K/W)."""
    c_air: float = 1.5e6      # ~500 kg air + light furnishings (J/K)
    c_wall: float = 1.2e7     # Heavy masonry/concrete wall mass (J/K)
    c_attic: float = 3.0e6    # Attic and roof mass (J/K)

    r_wall: float = 0.08      # Indoor air to wall resistance (K/W)
    r_attic: float = 0.12     # Indoor air to attic resistance (K/W)
    r_win: float = 0.45       # Direct window envelope loss (K/W)
    r_ext_wall: float = 0.35  # Wall to outdoor ambient (K/W)
    r_roof: float = 0.25      # Attic to outdoor ambient (K/W)

    window_area_m2: float = 12.0   # Total glazing area (m^2)
    shgc: float = 0.65             # Solar Heat Gain Coefficient
    wall_absorptivity: float = 0.7 # Exterior wall solar absorption
    internal_gains_w: float = 300.0# Base internal heat (occupants + plug load)


class LumpedRCBuildingModel:
    """Precise physics simulator for 3-node thermal dynamics."""

    def __init__(self, config: RCModelConfig | None = None) -> None:
        self.cfg = config or RCModelConfig()
        self.t_air: float = 22.0
        self.t_wall: float = 21.5
        self.t_attic: float = 22.5

    def reset(self, initial_temp: float = 22.0) -> Tuple[float, float, float]:
        """Reset nodes to initial thermal equilibrium."""
        self.t_air = initial_temp
        self.t_wall = initial_temp
        self.t_attic = initial_temp
        return self.t_air, self.t_wall, self.t_attic

    def step(
        self,
        t_out: float,
        solar_irradiance_w_m2: float,
        hvac_cooling_power_w: float,
        dt_seconds: float = 900.0,  # 15 minutes
        occupancy: bool = True,
    ) -> Tuple[float, float, float]:
        """Advance thermal states using sub-step Runge-Kutta 4th order (RK4) numerical integration.

        Parameters
        ----------
        t_out : float
            Outdoor ambient temperature (°C).
        solar_irradiance_w_m2 : float
            Global horizontal solar irradiance (W/m^2).
        hvac_cooling_power_w : float
            Thermal cooling power removed by HVAC (W).
        dt_seconds : float
            Time step duration in seconds.
        occupancy : bool
            Occupancy flag for heat gain scaling.

        Returns
        -------
        Tuple[float, float, float]
            Updated (T_air, T_wall, T_attic) in °C.
        """
        # Internal heat gains from occupants & equipment
        q_int = self.cfg.internal_gains_w if occupancy else 100.0

        # Solar gains through windows and opaque surfaces
        q_solar_win = solar_irradiance_w_m2 * self.cfg.window_area_m2 * self.cfg.shgc
        q_solar_wall = solar_irradiance_w_m2 * self.cfg.wall_absorptivity * 0.3
        q_solar_roof = solar_irradiance_w_m2 * self.cfg.wall_absorptivity * 0.7

        # RK4 sub-stepping for numerical stability
        substeps = 10
        sub_dt = dt_seconds / substeps

        def derivatives(ta: float, tw: float, tr: float) -> Tuple[float, float, float]:
            # dT_air/dt
            d_ta = (
                (tw - ta) / self.cfg.r_wall
                + (tr - ta) / self.cfg.r_attic
                + (t_out - ta) / self.cfg.r_win
                + q_int
                + q_solar_win
                - hvac_cooling_power_w
            ) / self.cfg.c_air

            # dT_wall/dt
            d_tw = (
                (ta - tw) / self.cfg.r_wall
                + (t_out - tw) / self.cfg.r_ext_wall
                + q_solar_wall
            ) / self.cfg.c_wall

            # dT_attic/dt
            d_tr = (
                (ta - tr) / self.cfg.r_attic
                + (t_out - tr) / self.cfg.r_roof
                + q_solar_roof
            ) / self.cfg.c_attic

            return d_ta, d_tw, d_tr

        ta, tw, tr = self.t_air, self.t_wall, self.t_attic
        for _ in range(substeps):
            k1_ta, k1_tw, k1_tr = derivatives(ta, tw, tr)
            k2_ta, k2_tw, k2_tr = derivatives(
                ta + 0.5 * sub_dt * k1_ta,
                tw + 0.5 * sub_dt * k1_tw,
                tr + 0.5 * sub_dt * k1_tr,
            )
            k3_ta, k3_tw, k3_tr = derivatives(
                ta + 0.5 * sub_dt * k2_ta,
                tw + 0.5 * sub_dt * k2_tw,
                tr + 0.5 * sub_dt * k2_tr,
            )
            k4_ta, k4_tw, k4_tr = derivatives(
                ta + sub_dt * k3_ta,
                tw + sub_dt * k3_tw,
                tr + sub_dt * k3_tr,
            )

            ta += (sub_dt / 6.0) * (k1_ta + 2 * k2_ta + 2 * k3_ta + k4_ta)
            tw += (sub_dt / 6.0) * (k1_tw + 2 * k2_tw + 2 * k3_tw + k4_tw)
            tr += (sub_dt / 6.0) * (k1_tr + 2 * k2_tr + 2 * k3_tr + k4_tr)

        self.t_air = float(clamp(ta, -10.0, 60.0))
        self.t_wall = float(clamp(tw, -10.0, 60.0))
        self.t_attic = float(clamp(tr, -10.0, 60.0))

        return self.t_air, self.t_wall, self.t_attic


def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(val, max_val))
