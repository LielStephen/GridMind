"""
GridMind utilities — shared helpers and formatting tools.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Observation helpers
# ---------------------------------------------------------------------------

OBS_KEYS = ("hour", "indoor_temp", "outdoor_temp", "solar_gen", "battery_soc", "price", "occupancy")


def obs_to_dict(obs: np.ndarray) -> Dict[str, Any]:
    """Convert a raw observation array to a labelled dictionary.

    Parameters
    ----------
    obs : np.ndarray
        7-element observation vector from ``GridMindEnv``.

    Returns
    -------
    dict
        Keys: ``hour``, ``indoor_temp``, ``outdoor_temp``, ``solar_gen``,
        ``battery_soc``, ``price``, ``occupancy``.
    """
    if len(obs) != len(OBS_KEYS):
        raise ValueError(f"Expected {len(OBS_KEYS)}-element obs, got {len(obs)}")

    return {
        "hour": int(obs[0]),
        "indoor_temp": float(obs[1]),
        "outdoor_temp": float(obs[2]),
        "solar_gen": float(obs[3]),
        "battery_soc": float(obs[4]),
        "price": float(obs[5]),
        "occupancy": bool(obs[6]),
    }


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def step_to_clock(step: int, step_duration_min: int = 15) -> str:
    """Convert a step index to a ``HH:MM`` clock string.

    Parameters
    ----------
    step : int
        Simulation step index (0-based).
    step_duration_min : int
        Duration of each step in minutes.

    Returns
    -------
    str
        Formatted time string, e.g. ``"14:30"``.
    """
    total_minutes = step * step_duration_min
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def format_watts(watts: float) -> str:
    """Format a power value to a human-readable string.

    Parameters
    ----------
    watts : float
        Power in watts.

    Returns
    -------
    str
        Formatted string, e.g. ``"2.5 kW"`` or ``"450 W"``.
    """
    if abs(watts) >= 1_000:
        return f"{watts / 1_000:.1f} kW"
    return f"{watts:.0f} W"


def format_energy_cost(cost: float) -> str:
    """Format energy cost to dollars with 3 decimal places.

    Parameters
    ----------
    cost : float
        Cost in dollars.

    Returns
    -------
    str
        Formatted string, e.g. ``"$0.045"``.
    """
    return f"${cost:.3f}"
