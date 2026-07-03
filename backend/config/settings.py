"""
GridMind simulation configuration.

Centralises all physical constants, environment parameters, and training
hyperparameters so nothing is hard-coded across the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Physical / device defaults
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HVACConfig:
    """Air-conditioning unit parameters."""
    power_rating_w: float = 2_000.0       # Nominal draw in watts
    cooling_rate_degc: float = 0.5         # °C removed per 15-min step when on
    standby_power_w: float = 0.5           # Idle/standby draw in watts


@dataclass(frozen=True)
class BatteryConfig:
    """Home battery storage parameters (Tesla Powerwall-class)."""
    capacity_wh: float = 13_500.0          # Total usable capacity
    max_charge_kw: float = 5.0             # Max charge/discharge rate
    round_trip_efficiency: float = 0.94    # One-way efficiency (charge path)
    initial_soc: float = 0.50              # Starting state-of-charge (0-1)


@dataclass(frozen=True)
class SolarConfig:
    """Rooftop PV array parameters."""
    peak_output_w: float = 5_000.0         # Nameplate peak generation


@dataclass(frozen=True)
class BuildingConfig:
    """Building thermal envelope."""
    thermal_leakage_coeff: float = 0.02    # Heat transfer coefficient per step
    initial_indoor_temp: float = 22.0      # Starting indoor temp (°C)
    comfort_low: float = 20.0              # Lower comfort bound (°C)
    comfort_high: float = 24.0             # Upper comfort bound (°C)
    comfort_target: float = 22.0           # Ideal setpoint (°C)
    comfort_penalty_weight: float = 2.0    # Multiplier for out-of-band penalty


@dataclass(frozen=True)
class PricingConfig:
    """Time-of-use electricity pricing."""
    off_peak_rate: float = 0.15            # $/kWh during off-peak
    on_peak_rate: float = 0.45             # $/kWh during peak (16:00–21:00)
    peak_start_hour: int = 16
    peak_end_hour: int = 21


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EnvConfig:
    """Top-level Gymnasium environment configuration."""
    step_duration_s: int = 900             # 15 minutes in seconds
    steps_per_episode: int = 96            # 24 h × (60/15) = 96 steps
    hvac: HVACConfig = field(default_factory=HVACConfig)
    battery: BatteryConfig = field(default_factory=BatteryConfig)
    solar: SolarConfig = field(default_factory=SolarConfig)
    building: BuildingConfig = field(default_factory=BuildingConfig)
    pricing: PricingConfig = field(default_factory=PricingConfig)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrainingConfig:
    """PPO training hyperparameters."""
    algorithm: str = "PPO"
    policy: str = "MlpPolicy"
    total_timesteps: int = 50_000
    n_envs: int = 1
    tensorboard_log_dir: str = "./ppo_gridmind_tensorboard/"
    model_save_dir: str = "backend/models"
    model_name: str = "ppo_gridmind"
    verbose: int = 1


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class APIConfig:
    """FastAPI server defaults."""
    host: str = "0.0.0.0"
    port: int = 8_000
    reload: bool = True
    title: str = "GridMind API"
    version: str = "1.0.0"
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
