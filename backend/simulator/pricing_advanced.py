"""
Advanced Dynamic Pricing & Grid Tariff Simulator.

Models complex power tariffs:
1. Time-of-Use (TOU) & Locational Marginal Spot Pricing (LMP).
2. Peak Demand Charge ($/kW peak over monthly billing cycle).
3. Solar Feed-in Tariff (FiT) for power exports.
4. Carbon Intensity Index (gCO2/kWh) for emissions tracking.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class TariffConfig:
    tou_off_peak_price: float = 0.12     # Off-peak $/kWh (00:00 - 07:00, 22:00 - 24:00)
    tou_mid_peak_price: float = 0.24     # Mid-peak $/kWh (07:00 - 14:00, 19:00 - 22:00)
    tou_on_peak_price: float = 0.48      # On-peak $/kWh  (14:00 - 19:00)

    feed_in_tariff: float = 0.08         # FiT credit $/kWh exported to grid
    demand_charge_per_kw: float = 12.50   # Monthly peak demand penalty ($/kW)
    carbon_intensity_base: float = 350.0 # Base grid carbon (gCO2/kWh)


class AdvancedTariffManager:
    """Calculates real-time electricity costs, demand charges, and emissions."""

    def __init__(self, config: TariffConfig | None = None) -> None:
        self.cfg = config or TariffConfig()
        self.peak_demand_kw: float = 0.0

    def reset() -> None:
        """Reset monthly peak tracker."""
        self.peak_demand_kw = 0.0

    def get_spot_price(self, hour: float, stochastic_noise: float = 0.0) -> float:
        """Calculate dynamic spot price ($/kWh) based on hour of day."""
        h = hour % 24.0
        if 0.0 <= h < 7.0 or 22.0 <= h <= 24.0:
            base = self.cfg.tou_off_peak_price
        elif 14.0 <= h < 19.0:
            base = self.cfg.tou_on_peak_price
        else:
            base = self.cfg.tou_mid_peak_price

        # Add price volatility spike on peak hours
        if 16.0 <= h <= 18.0:
            base += 0.05 * math.sin((h - 16.0) * math.pi / 2.0)

        price = max(0.02, base + stochastic_noise)
        return price

    def get_carbon_intensity(self, hour: float) -> float:
        """Calculate grid carbon intensity (gCO2/kWh). Peak solar hours are cleaner."""
        h = hour % 24.0
        solar_factor = max(0.0, math.sin(math.pi * max(0.0, h - 6.0) / 12.0))
        # Renewable energy lowers grid carbon during mid-day
        intensity = self.cfg.carbon_intensity_base * (1.0 - 0.5 * solar_factor)
        return intensity

    def compute_step_cost(
        self,
        grid_imported_w: float,
        grid_exported_w: float,
        hour: float,
        dt_seconds: float = 900.0,
    ) -> Tuple[float, float, float]:
        """Compute net energy cost, carbon footprint, and demand charge penalty.

        Returns
        -------
        Tuple[float, float, float]
            (net_cost_dollars, carbon_g, demand_charge_increment)
        """
        dt_hours = dt_seconds / 3600.0
        spot_price = self.get_spot_price(hour)
        carbon_rate = self.get_carbon_intensity(hour)

        import_kwh = (grid_imported_w / 1000.0) * dt_hours
        export_kwh = (grid_exported_w / 1000.0) * dt_hours

        cost_import = import_kwh * spot_price
        credit_export = export_kwh * self.cfg.feed_in_tariff
        net_cost = cost_import - credit_export

        carbon_g = import_kwh * carbon_rate

        # Peak demand tracking
        power_kw = grid_imported_w / 1000.0
        demand_penalty = 0.0
        if power_kw > self.peak_demand_kw:
            incremental_kw = power_kw - self.peak_demand_kw
            demand_penalty = incremental_kw * self.cfg.demand_charge_per_kw
            self.peak_demand_kw = power_kw

        return net_cost, carbon_g, demand_penalty
