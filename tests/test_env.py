"""
GridMind test suite.

Covers the Gymnasium environment, simulator device models, utility helpers,
and the FastAPI HTTP layer.

Run from project root::

    python -m pytest tests/ -v
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym
import pytest
from fastapi.testclient import TestClient

from backend.rl.env import GridMindEnv
from backend.simulator.models import AirConditioner, Battery, WeatherProvider
from backend.config.settings import EnvConfig, BatteryConfig, HVACConfig
from backend.utils.helpers import obs_to_dict, step_to_clock, format_watts
from backend.api.main import app


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def env():
    """Fresh GridMindEnv for each test."""
    e = GridMindEnv()
    yield e
    e.close()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ===================================================================
# Environment — Registration & Reset
# ===================================================================

class TestEnvRegistration:
    """Verify the environment registers correctly with Gymnasium."""

    def test_make_by_id(self):
        import backend.rl  # noqa: F401 — triggers registration
        made = gym.make("GridMind/Energy-v0")
        assert isinstance(made.unwrapped, GridMindEnv)
        made.close()


class TestEnvReset:
    """Verify reset returns correct shapes and initial state."""

    def test_obs_shape(self, env):
        obs, info = env.reset()
        assert obs.shape == (7,)
        assert isinstance(info, dict)

    def test_initial_temp(self, env):
        obs, _ = env.reset()
        assert obs[1] == pytest.approx(22.0, abs=0.1)

    def test_step_counter_resets(self, env):
        env.step(0)
        env.step(0)
        env.reset()
        assert env.current_step == 0


# ===================================================================
# Environment — Step Mechanics
# ===================================================================

class TestEnvStep:
    """Verify step transitions, rewards, and termination."""

    def test_idle_step_returns_valid(self, env):
        env.reset()
        obs, reward, terminated, truncated, info = env.step(0)
        assert obs.shape == (7,)
        assert isinstance(reward, float)
        assert "cost" in info
        assert "net_w" in info

    def test_ac_cools_indoor(self, env):
        env.reset()
        env.indoor_temp = 30.0
        env.step(2)  # AC OFF
        temp_no_ac = env.indoor_temp

        env.indoor_temp = 30.0
        env.step(1)  # AC ON
        temp_with_ac = env.indoor_temp

        assert temp_with_ac < temp_no_ac

    def test_battery_charges(self, env):
        env.reset()
        initial_soc = env.battery.soc
        for _ in range(5):
            env.step(3)  # Charge
        assert env.battery.soc > initial_soc
        assert env.battery.soc <= 1.0

    def test_battery_discharges(self, env):
        env.reset()
        # Charge first to have something to discharge
        for _ in range(3):
            env.step(3)
        charged_soc = env.battery.soc
        env.step(4)  # Discharge
        assert env.battery.soc < charged_soc

    def test_episode_terminates_at_96(self, env):
        env.reset()
        terminated = False
        for i in range(100):
            _, _, terminated, _, _ = env.step(0)
            if terminated:
                break
        assert terminated
        assert env.current_step > 96


# ===================================================================
# Simulator Models
# ===================================================================

class TestAirConditioner:
    """Verify AC power consumption logic."""

    def test_on_draws_rated_power(self):
        ac = AirConditioner("TestAC")
        ac.is_on = True
        power = ac.step()
        assert power == 2000.0

    def test_off_draws_standby(self):
        ac = AirConditioner("TestAC")
        ac.is_on = False
        power = ac.step()
        assert power == 0.5

    def test_repr_contains_name(self):
        ac = AirConditioner("LivingRoom")
        assert "LivingRoom" in repr(ac)


class TestBattery:
    """Verify battery charge/discharge and SOC tracking."""

    def test_initial_soc_is_half(self):
        batt = Battery()
        assert batt.soc == pytest.approx(0.5, abs=0.01)

    def test_charge_increases_soc(self):
        batt = Battery()
        initial = batt.soc
        batt.charge(2000, 900)
        assert batt.soc > initial

    def test_discharge_returns_negative(self):
        batt = Battery()
        result = batt.discharge(2000, 900)
        assert result < 0

    def test_soc_never_exceeds_one(self):
        batt = Battery()
        for _ in range(100):
            batt.charge(5000, 900)
        assert batt.soc <= 1.0

    def test_empty_battery_returns_zero(self):
        cfg = BatteryConfig(initial_soc=0.0)
        batt = Battery(config=cfg)
        result = batt.discharge(2000, 900)
        assert result == 0.0


class TestWeatherProvider:
    """Verify synthetic weather signals are sane."""

    def test_returns_four_values(self):
        wp = WeatherProvider()
        result = wp.get_state(0)
        assert len(result) == 4

    def test_solar_zero_at_night(self):
        wp = WeatherProvider()
        _, solar, _, _ = wp.get_state(0)  # step 0 = midnight
        assert solar == 0.0

    def test_solar_positive_at_noon(self):
        wp = WeatherProvider()
        _, solar, _, _ = wp.get_state(48)  # step 48 = noon
        assert solar > 0.0

    def test_peak_pricing(self):
        wp = WeatherProvider()
        _, _, price, _ = wp.get_state(68)  # step 68 = 17:00
        assert price == pytest.approx(0.45)


# ===================================================================
# Utility Helpers
# ===================================================================

class TestHelpers:
    """Verify formatting and conversion utilities."""

    def test_obs_to_dict_keys(self):
        obs = np.array([12, 22.5, 30.0, 0.8, 0.6, 0.15, 1.0], dtype=np.float32)
        d = obs_to_dict(obs)
        assert set(d.keys()) == {"hour", "indoor_temp", "outdoor_temp", "solar_gen", "battery_soc", "price", "occupancy"}

    def test_obs_to_dict_bad_length(self):
        with pytest.raises(ValueError):
            obs_to_dict(np.array([1, 2, 3]))

    def test_step_to_clock_midnight(self):
        assert step_to_clock(0) == "00:00"

    def test_step_to_clock_noon(self):
        assert step_to_clock(48) == "12:00"

    def test_format_watts_small(self):
        assert format_watts(450) == "450 W"

    def test_format_watts_large(self):
        assert format_watts(2500) == "2.5 kW"


# ===================================================================
# API Layer
# ===================================================================

class TestAPI:
    """Verify HTTP endpoints via FastAPI TestClient."""

    def test_health_check(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "GridMind Operational" in r.json()["status"]

    def test_reset_returns_state(self, client):
        r = client.post("/simulation/reset")
        assert r.status_code == 200
        body = r.json()
        assert "initial_state" in body
        assert len(body["initial_state"]) == 7

    def test_step_returns_full_obs(self, client):
        client.post("/simulation/reset")
        r = client.post("/simulation/step?action=0")
        assert r.status_code == 200
        body = r.json()
        for key in ("indoor_temp", "outdoor_temp", "solar_gen", "battery_soc",
                     "price", "occupancy", "energy_cost", "reward", "terminated"):
            assert key in body, f"Missing key: {key}"

    def test_step_invalid_action_rejected(self, client):
        client.post("/simulation/reset")
        r = client.post("/simulation/step?action=9")
        assert r.status_code == 422  # FastAPI validation error

    def test_get_state_endpoint(self, client):
        client.post("/simulation/reset")
        r = client.get("/simulation/state")
        assert r.status_code == 200
        assert "battery_soc" in r.json()
