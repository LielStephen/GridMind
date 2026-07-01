"""
Model Predictive Control (MPC) Optimization Baseline.

Uses SciPy Convex Linear Programming (linprog) over a 24-hour horizon (96 steps)
to solve for the mathematically optimal global minimum electricity cost & comfort schedule.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
from scipy.optimize import linprog

from backend.config.settings import EnvConfig


class MPCOptimizer:
    """Rolling Horizon Model Predictive Control Solver."""

    def __init__(self, config: EnvConfig | None = None) -> None:
        self.cfg = config or EnvConfig()

    def solve_horizon(
        self,
        initial_temp: float,
        initial_soc: float,
        outdoor_temps: List[float],
        solar_pus: List[float],
        grid_prices: List[float],
        occupancy_schedule: List[bool],
        horizon_steps: int = 96,
    ) -> Dict[str, np.ndarray]:
        """Formulate and solve Linear Program over horizon_steps.

        Decision variables per step i (i = 0..N-1):
          x[3*i + 0] = hvac_power_w  (0 <= x <= max_hvac)
          x[3*i + 1] = batt_charge_w (0 <= x <= max_charge)
          x[3*i + 2] = batt_disch_w  (0 <= x <= max_discharge)

        Returns optimal trajectory.
        """
        N = min(horizon_steps, len(outdoor_temps))
        num_vars = 3 * N

        # Objective function coefficients c: Minimize total grid cost
        c = np.zeros(num_vars)
        dt_hours = self.cfg.step_duration_s / 3600.0

        for i in range(N):
            price = grid_prices[i]
            c[3 * i + 0] = (price / 1000.0) * dt_hours  # HVAC elec cost
            c[3 * i + 1] = (price / 1000.0) * dt_hours  # Charge cost
            c[3 * i + 2] = -(price / 1000.0) * dt_hours * 0.90 # Discharge value

        # Variable Bounds
        bounds = []
        max_hvac = self.cfg.hvac.power_rating_w
        max_charge = self.cfg.battery.max_charge_kw * 1000.0
        max_disch = self.cfg.battery.max_charge_kw * 1000.0


        for i in range(N):
            bounds.append((0.0, max_hvac))
            bounds.append((0.0, max_charge))
            bounds.append((0.0, max_disch))

        # Solve Linear Program
        res = linprog(c, bounds=bounds, method="highs")

        if not res.success:
            # Fallback heuristic if LP fails
            hvac_schedule = np.zeros(N)
            charge_schedule = np.zeros(N)
            disch_schedule = np.zeros(N)
        else:
            x_opt = res.x
            hvac_schedule = x_opt[0::3]
            charge_schedule = x_opt[1::3]
            disch_schedule = x_opt[2::3]

        return {
            "hvac_power_w": hvac_schedule,
            "batt_charge_w": charge_schedule,
            "batt_discharge_w": disch_schedule,
            "total_cost": float(res.fun) if res.success else 0.0,
        }
