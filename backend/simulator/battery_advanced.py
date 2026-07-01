"""
Advanced Non-Linear Battery System with Degradation Dynamics.

Models Lithium-ion battery physics including:
1. SoC-dependent charging/discharging internal resistance.
2. Peukert's capacity effect under high C-rates.
3. Thermal Arrhenius cell degradation.
4. Depth of Discharge (DoD) cycle aging & State-of-Health (SoH) tracking.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class AdvancedBatteryConfig:
    capacity_wh: float = 10000.0        # 10 kWh nominal capacity
    max_charge_power_w: float = 3500.0   # 3.5 kW max charge rate
    max_discharge_power_w: float = 3500.0# 3.5 kW max discharge rate
    nominal_efficiency: float = 0.95    # Round-trip base efficiency sqrt(0.95) per direction
    initial_soc: float = 0.5            # 50% initial charge
    initial_soh: float = 1.0            # 100% initial health
    peukert_exponent: float = 1.05      # Peukert discharge loss exponent
    ambient_temp_c: float = 25.0        # Cell ambient temperature


class AdvancedBatterySystem:
    """Non-linear battery simulator with cycle degradation."""

    def __init__(self, config: AdvancedBatteryConfig | None = None) -> None:
        self.cfg = config or AdvancedBatteryConfig()
        self.current_charge_wh: float = self.cfg.capacity_wh * self.cfg.initial_soc
        self.soh: float = self.cfg.initial_soh
        self.cell_temp_c: float = self.cfg.ambient_temp_c
        self.total_throughput_wh: float = 0.0
        self.equivalent_full_cycles: float = 0.0

    @property
    def max_usable_capacity_wh(self) -> float:
        """Effective capacity scaled by State-of-Health."""
        return self.cfg.capacity_wh * self.soh

    @property
    def soc(self) -> float:
        """State of Charge ratio [0.0, 1.0]."""
        if self.max_usable_capacity_wh <= 0:
            return 0.0
        return self.current_charge_wh / self.max_usable_capacity_wh

    def reset(self, initial_soc: float | None = None) -> float:
        """Reset charge to target SoC."""
        soc = self.cfg.initial_soc if initial_soc is None else initial_soc
        self.current_charge_wh = self.max_usable_capacity_wh * soc
        return self.soc

    def _get_soc_efficiency(self, is_charging: bool) -> float:
        """Non-linear efficiency penalty at SoC extremes (<10% or >90%)."""
        s = self.soc
        base_eta = math.sqrt(self.cfg.nominal_efficiency)
        if is_charging:
            # Charging slows down near 100% (CV stage)
            penalty = 1.0 - max(0.0, (s - 0.85) * 2.0) ** 2 * 0.3
        else:
            # Discharge efficiency drops at very low SoC
            penalty = 1.0 - max(0.0, (0.15 - s) * 3.0) ** 2 * 0.3
        return base_eta * max(0.5, penalty)

    def charge(self, requested_power_w: float, dt_seconds: float) -> Tuple[float, float]:
        """Attempt to charge battery.

        Returns
        -------
        Tuple[float, float]
            (actual_grid_power_w, energy_stored_wh)
        """
        p_req = min(requested_power_w, self.cfg.max_charge_power_w)
        if p_req <= 0 or self.soc >= 0.999:
            return 0.0, 0.0

        eta = self._get_soc_efficiency(is_charging=True)
        dt_hours = dt_seconds / 3600.0

        # Maximum energy space remaining
        headroom_wh = self.max_usable_capacity_wh - self.current_charge_wh
        max_grid_energy_wh = headroom_wh / eta
        actual_grid_energy_wh = min(p_req * dt_hours, max_grid_energy_wh)
        energy_stored_wh = actual_grid_energy_wh * eta

        self.current_charge_wh += energy_stored_wh
        self.total_throughput_wh += energy_stored_wh
        self._update_degradation(energy_stored_wh, dt_seconds, is_charge=True)

        grid_power_w = actual_grid_energy_wh / dt_hours
        return grid_power_w, energy_stored_wh

    def discharge(self, requested_power_w: float, dt_seconds: float) -> Tuple[float, float]:
        """Attempt to discharge battery.

        Returns
        -------
        Tuple[float, float]
            (actual_output_power_w, energy_extracted_wh)
        """
        p_req = min(requested_power_w, self.cfg.max_discharge_power_w)
        if p_req <= 0 or self.soc <= 0.001:
            return 0.0, 0.0

        eta = self._get_soc_efficiency(is_charging=False)
        dt_hours = dt_seconds / 3600.0

        # Peukert effect increases effective discharge draw at high C-rate
        c_rate = p_req / self.cfg.capacity_wh
        peukert_factor = c_rate ** (self.cfg.peukert_exponent - 1.0) if c_rate > 1.0 else 1.0

        available_energy_wh = self.current_charge_wh * eta
        requested_drawn_wh = p_req * dt_hours * peukert_factor

        actual_output_wh = min(p_req * dt_hours, available_energy_wh)
        internal_drawn_wh = actual_output_wh / eta * peukert_factor

        self.current_charge_wh = max(0.0, self.current_charge_wh - internal_drawn_wh)
        self.total_throughput_wh += actual_output_wh
        self._update_degradation(actual_output_wh, dt_seconds, is_charge=False)

        output_power_w = actual_output_wh / dt_hours
        return output_power_w, actual_output_wh

    def _update_degradation(self, energy_wh: float, dt_seconds: float, is_charge: bool) -> None:
        """Update cell thermal rise & State-of-Health degradation."""
        # Thermal heating proportional to I^2 R loss
        heat_gen_w = energy_wh / (dt_seconds / 3600.0) * (1.0 - self.cfg.nominal_efficiency)
        dT = (heat_gen_w * 0.001 - 0.05 * (self.cell_temp_c - self.cfg.ambient_temp_c)) * (dt_seconds / 60.0)
        self.cell_temp_c += dT

        # Cycle degradation: ~3000 equivalent full cycles to 80% SoH
        self.equivalent_full_cycles += (energy_wh / self.cfg.capacity_wh) / 2.0
        dod_factor = 1.0 + (1.0 - self.soc) * 0.5  # Deeper discharge accelerates degradation
        temp_arrhenius = math.exp((self.cell_temp_c - 25.0) / 40.0)

        soh_loss_per_cycle = 0.20 / 3000.0
        cycle_delta = (energy_wh / self.cfg.capacity_wh) * soh_loss_per_cycle * dod_factor * temp_arrhenius
        self.soh = max(0.5, self.soh - cycle_delta)
