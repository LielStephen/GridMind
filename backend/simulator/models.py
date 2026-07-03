"""
GridMind simulator — physical device and weather models.

This module defines the core simulation components used by the Gymnasium
environment:

- ``BaseDevice``       — abstract device with power rating and step interface
- ``AirConditioner``   — HVAC unit that consumes power and modifies indoor temp
- ``Battery``          — electrochemical storage with round-trip efficiency
- ``WeatherProvider``  — synthetic diurnal weather, solar irradiance, and pricing
- ``SimulationState``  — snapshot dataclass for logging / replay
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from backend.config.settings import (
    HVACConfig,
    BatteryConfig,
    PricingConfig,
)


# ---------------------------------------------------------------------------
# Snapshot DTO
# ---------------------------------------------------------------------------

@dataclass
class SimulationState:
    """Immutable snapshot of a single simulation timestep — useful for
    transition logging and dataset generation."""
    timestamp: int
    outdoor_temp: float
    indoor_temp: float
    is_occupied: bool
    solar_gen: float
    battery_soc: float
    grid_price: float
    net_consumption: float


# ---------------------------------------------------------------------------
# Abstract device
# ---------------------------------------------------------------------------

class BaseDevice(ABC):
    """Base class for controllable electrical devices in the building.

    Parameters
    ----------
    name : str
        Human-readable device identifier (e.g. ``"MainAC"``).
    power_rating : float
        Nameplate power draw in watts.
    """

    def __init__(self, name: str, power_rating: float) -> None:
        self.id: str = str(uuid.uuid4())
        self.name = name
        self.power_rating = power_rating  # watts
        self.is_on: bool = False
        self.consumption: float = 0.0

    @abstractmethod
    def step(self) -> float:
        """Advance the device by one simulation timestep and return the
        instantaneous power consumption in watts."""

    def __repr__(self) -> str:
        state = "ON" if self.is_on else "OFF"
        return f"<{self.__class__.__name__} '{self.name}' [{state}] {self.power_rating}W>"


# ---------------------------------------------------------------------------
# HVAC
# ---------------------------------------------------------------------------

class AirConditioner(BaseDevice):
    """Single-zone air-conditioning unit.

    When *on*, draws ``power_rating`` watts and reduces the zone temperature
    by ``cooling_rate`` °C per simulation step.  When *off*, draws a small
    standby load.

    Parameters
    ----------
    name : str
        Device identifier.
    config : HVACConfig, optional
        Physical parameters.  Falls back to defaults if omitted.
    """

    def __init__(self, name: str, config: HVACConfig | None = None) -> None:
        cfg = config or HVACConfig()
        super().__init__(name, cfg.power_rating_w)
        self.cooling_rate: float = cfg.cooling_rate_degc
        self._standby_w: float = cfg.standby_power_w

    def step(self) -> float:
        """Return instantaneous power draw (watts) for the current step."""
        self.consumption = self.power_rating if self.is_on else self._standby_w
        return self.consumption


# ---------------------------------------------------------------------------
# Battery storage
# ---------------------------------------------------------------------------

class Battery:
    """Lithium-ion home battery with Coulombic efficiency losses.

    Modelled after a Tesla Powerwall-class system: 13.5 kWh usable
    capacity, 5 kW continuous charge/discharge, 94 % round-trip
    efficiency (applied on the charge path).

    Parameters
    ----------
    config : BatteryConfig, optional
        Storage parameters.  Falls back to defaults if omitted.
    """

    def __init__(self, config: BatteryConfig | None = None) -> None:
        cfg = config or BatteryConfig()
        self.capacity: float = cfg.capacity_wh
        self.current_charge: float = cfg.capacity_wh * cfg.initial_soc
        self.max_rate: float = cfg.max_charge_kw * 1_000.0  # kW → W
        self.efficiency: float = cfg.round_trip_efficiency

    # -- actions -----------------------------------------------------------

    def charge(self, power_w: float, dt_s: float) -> float:
        """Charge the battery and return *actual grid-side power drawn* (W).

        Parameters
        ----------
        power_w : float
            Requested charging power in watts (grid-side).
        dt_s : float
            Timestep duration in seconds.

        Returns
        -------
        float
            Actual power consumed from the grid (watts).  Always ≥ 0.
        """
        actual_power = min(power_w, self.max_rate)
        energy_wh = actual_power * (dt_s / 3600) * self.efficiency
        self.current_charge = min(self.capacity, self.current_charge + energy_wh)
        return actual_power

    def discharge(self, power_w: float, dt_s: float) -> float:
        """Discharge the battery and return *power supplied* (W, negative).

        Parameters
        ----------
        power_w : float
            Requested discharge power in watts.
        dt_s : float
            Timestep duration in seconds.

        Returns
        -------
        float
            Actual power injected to the load (watts, negative sign).
            Returns ``0.0`` if insufficient stored energy.
        """
        actual_power = min(power_w, self.max_rate)
        energy_wh = (actual_power / self.efficiency) * (dt_s / 3600)
        if self.current_charge >= energy_wh:
            self.current_charge -= energy_wh
            return -actual_power
        return 0.0

    # -- state -------------------------------------------------------------

    @property
    def soc(self) -> float:
        """State of charge as a fraction in ``[0, 1]``."""
        return self.current_charge / self.capacity

    def __repr__(self) -> str:
        return f"<Battery SOC={self.soc:.1%} ({self.current_charge:.0f}/{self.capacity:.0f} Wh)>"


# ---------------------------------------------------------------------------
# Weather / pricing provider
# ---------------------------------------------------------------------------

class WeatherProvider:
    """Synthetic weather, solar irradiance, and time-of-use pricing.

    All signals are deterministic functions of the step index, producing
    smooth diurnal curves suitable for training an initial RL policy.
    Extend this class or swap it out for a stochastic provider in
    production.

    Parameters
    ----------
    pricing : PricingConfig, optional
        Time-of-use tariff parameters.
    """

    def __init__(self, pricing: PricingConfig | None = None) -> None:
        self._pricing = pricing or PricingConfig()

    def get_state(self, step_idx: int) -> Tuple[float, float, float, bool]:
        """Return environmental conditions at the given step.

        Parameters
        ----------
        step_idx : int
            Global simulation step (each step = 15 minutes).

        Returns
        -------
        tuple[float, float, float, bool]
            ``(outdoor_temp_C, solar_fraction, price_per_kWh, is_occupied)``
        """
        hour = (step_idx // 4) % 24

        # Outdoor temperature — sinusoidal peaking mid-afternoon
        temp = 20.0 + 10.0 * np.sin(np.pi * (hour - 9) / 12)

        # Solar irradiance — bell curve from 06:00 to 18:00
        if 6 <= hour <= 18:
            solar = max(0.0, np.sin(np.pi * (hour - 6) / 12))
        else:
            solar = 0.0

        # Time-of-use pricing
        p = self._pricing
        price = p.on_peak_rate if p.peak_start_hour <= hour <= p.peak_end_hour else p.off_peak_rate

        # Occupancy — residents home before 08:00 and after 18:00
        occupied = hour < 8 or hour > 18

        return temp, solar, price, occupied
