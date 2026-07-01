"""
Unit tests for advanced physical models: RC thermal model, battery degradation, and dynamic tariffs.
"""

from __future__ import annotations

import pytest

from backend.simulator.battery_advanced import AdvancedBatterySystem
from backend.simulator.pricing_advanced import AdvancedTariffManager
from backend.simulator.rc_model import LumpedRCBuildingModel


def test_rc_thermal_model_step():
    model = LumpedRCBuildingModel()
    t_air, t_wall, t_attic = model.reset(22.0)
    assert t_air == 22.0

    # Step with outdoor temp 35 C and AC cooling ON
    next_air, next_wall, next_attic = model.step(
        t_out=35.0,
        solar_irradiance_w_m2=500.0,
        hvac_cooling_power_w=3500.0,
        dt_seconds=900.0,
        occupancy=True,
    )
    assert isinstance(next_air, float)
    assert 10.0 <= next_air <= 40.0


def test_battery_advanced_degradation():
    batt = AdvancedBatterySystem()
    batt.reset(0.5)

    initial_soh = batt.soh
    assert initial_soh == 1.0

    # Execute multiple heavy charge/discharge cycles
    for _ in range(10):
        batt.charge(3500.0, 3600.0)
        batt.discharge(3500.0, 3600.0)

    assert batt.soh <= initial_soh
    assert batt.total_throughput_wh > 0.0


def test_pricing_tariff_manager():
    tariff = AdvancedTariffManager()
    off_peak_price = tariff.get_spot_price(3.0)
    on_peak_price = tariff.get_spot_price(16.0)

    assert on_peak_price > off_peak_price

    net_cost, carbon, demand_penalty = tariff.compute_step_cost(
        grid_imported_w=3000.0,
        grid_exported_w=0.0,
        hour=16.0,
        dt_seconds=900.0,
    )
    assert net_cost > 0.0
    assert carbon > 0.0
