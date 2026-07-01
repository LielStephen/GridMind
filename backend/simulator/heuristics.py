"""
Rule-Based Rule Controllers & Heuristic Energy Baselines.

Implements baseline control strategies:
1. Thermostatic Bang-Bang Controller (AC threshold).
2. Time-of-Use Battery Shifting Heuristic.
"""

from __future__ import annotations

from typing import Tuple


class ThermostaticHeuristicController:
    """Bang-Bang Hysteresis thermostat controller."""

    def __init__(self, target_temp: float = 22.0, deadband: float = 1.5):
        self.target_temp = target_temp
        self.deadband = deadband
        self.ac_state = False

    def select_action(self, indoor_temp: float) -> int:
        if indoor_temp > self.target_temp + self.deadband:
            self.ac_state = True
        elif indoor_temp < self.target_temp - self.deadband:
            self.ac_state = False

        return 1 if self.ac_state else 2  # ACTION_AC_ON or ACTION_AC_OFF


class TimeOfUseHeuristicController:
    """Smart Rule-based controller charging battery on off-peak and discharging during peak prices."""

    def __init__(self, target_temp: float = 22.0):
        self.thermostat = ThermostaticHeuristicController(target_temp)

    def select_action(self, hour: float, indoor_temp: float, battery_soc: float, grid_price: float) -> int:
        # Rule 1: High temperature emergency cooling
        if indoor_temp > 24.5:
            return 1  # Turn AC on

        # Rule 2: Peak electricity price (14:00 - 19:00 or price > $0.35/kWh) -> Discharge battery
        if (14.0 <= hour <= 19.0 or grid_price > 0.35) and battery_soc > 0.15:
            return 4  # Discharge battery

        # Rule 3: Low off-peak electricity price (00:00 - 06:00 or price < $0.15/kWh) -> Charge battery
        if (0.0 <= hour <= 6.0 or grid_price < 0.15) and battery_soc < 0.90:
            return 3  # Charge battery

        # Fallback to thermostat
        return self.thermostat.select_action(indoor_temp)
