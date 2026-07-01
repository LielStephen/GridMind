"""
GridMind API server.

Exposes the Gymnasium environment over HTTP so the React dashboard can
drive the simulation via REST calls.  All endpoints are stateless from
the client's perspective — the server holds a single environment instance.

Endpoints
---------
GET  /                    → health check
GET  /simulation/state    → current observation without stepping
POST /simulation/reset    → reset to a fresh episode
POST /simulation/step     → advance one timestep with a given action
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config.settings import APIConfig, EnvConfig
from backend.rl.env import GridMindEnv

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-24s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gridmind.api")

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

_api_cfg = APIConfig()

app = FastAPI(
    title=_api_cfg.title,
    version=_api_cfg.version,
    description="RL-powered smart energy management simulation API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_api_cfg.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single environment instance (stateful between requests)
env = GridMindEnv()

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SimulationStepResponse(BaseModel):
    """Full observation + reward after a simulation step."""
    step: int = Field(..., description="Current simulation step index")
    hour: int = Field(..., description="Hour of day (0-23)")
    indoor_temp: float = Field(..., description="Indoor temperature in °C")
    outdoor_temp: float = Field(..., description="Outdoor temperature in °C")
    solar_gen: float = Field(..., description="Solar generation (0-1 per-unit)")
    battery_soc: float = Field(..., description="Battery state-of-charge (0-1)")
    price: float = Field(..., description="Current electricity price $/kWh")
    occupancy: bool = Field(..., description="Whether the building is occupied")
    energy_cost: float = Field(..., description="Energy cost incurred this step ($)")
    net_consumption: float = Field(..., description="Net power consumption (W)")
    reward: float = Field(..., description="RL reward signal for this step")
    terminated: bool = Field(..., description="Whether the episode has ended")


class SimulationStateResponse(BaseModel):
    """Current observation without stepping."""
    step: int
    hour: int
    indoor_temp: float
    outdoor_temp: float
    solar_gen: float
    battery_soc: float
    price: float
    occupancy: bool


class ResetResponse(BaseModel):
    """Response after resetting the environment."""
    message: str
    initial_state: List[float]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _obs_to_dict(obs, step: int) -> dict:
    """Map the raw 7-element observation array to a labelled dictionary."""
    return {
        "step": step,
        "hour": int(obs[0]),
        "indoor_temp": float(obs[1]),
        "outdoor_temp": float(obs[2]),
        "solar_gen": float(obs[3]),
        "battery_soc": float(obs[4]),
        "price": float(obs[5]),
        "occupancy": bool(obs[6]),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/", tags=["health"])
async def root():
    """Health-check endpoint."""
    return {"status": "GridMind Operational", "engine": "Gymnasium-v26"}


@app.get(
    "/simulation/state",
    response_model=SimulationStateResponse,
    tags=["simulation"],
)
async def get_state():
    """Return the current environment observation without advancing time."""
    obs = env._get_obs()
    return SimulationStateResponse(**_obs_to_dict(obs, env.current_step))


@app.post(
    "/simulation/reset",
    response_model=ResetResponse,
    tags=["simulation"],
)
async def reset_sim():
    """Reset the environment to a new 24-hour episode."""
    obs, _ = env.reset()
    logger.info("Simulation reset — initial indoor temp %.1f°C", float(obs[1]))
    return ResetResponse(message="Environment Reset", initial_state=obs.tolist())


@app.post(
    "/simulation/step",
    response_model=SimulationStepResponse,
    tags=["simulation"],
)
async def take_step(
    action: int = Query(..., ge=0, le=4, description="Action index (0-4)"),
):
    """Advance the simulation by one timestep with the given action.

    Actions: 0=Idle, 1=AC On, 2=AC Off, 3=Charge Battery, 4=Discharge Battery
    """
    obs, reward, terminated, _, info = env.step(action)

    state = _obs_to_dict(obs, env.current_step)
    response = SimulationStepResponse(
        **state,
        energy_cost=info["cost"],
        net_consumption=info["net_w"],
        reward=float(reward),
        terminated=terminated,
    )

    if terminated:
        logger.info("Episode terminated at step %d", env.current_step)

    return response


# ---------------------------------------------------------------------------
# Advanced RL & ML Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/algorithms/compare", tags=["benchmarking"])
async def compare_algorithms():
    """Run head-to-head evaluation across SAC, TD3, PPO, MPC, Rule-Based, A2C, and DQN."""
    from backend.rl.benchmark_suite import BenchmarkSuite
    suite = BenchmarkSuite()
    return suite.run_all_benchmarks()


@app.get("/api/forecast/weather", tags=["forecasting"])
async def forecast_weather(start_hour: float = Query(0.0, ge=0.0, le=24.0)):
    """Return 24-hour ahead XGBoost/LSTM forecast for temperature and solar irradiance."""
    from backend.ml.forecast import GridEnergyForecaster
    forecaster = GridEnergyForecaster()
    return forecaster.predict_24h(start_hour)


@app.post("/api/anomalies/detect", tags=["ml"])
async def detect_anomalies(telemetry: List[dict]):
    """Detect building power and thermal anomalies using Isolation Forest."""
    from backend.ml.anomaly_detector import GridAnomalyDetector
    detector = GridAnomalyDetector()
    return detector.detect_anomalies(telemetry)


@app.post("/api/pinn/predict", tags=["ml"])
async def pinn_predict(t_in: float, t_out: float, solar_pu: float, hvac_ratio: float):
    """Predict next-step indoor temperature using Physics-Informed Neural Network (PINN)."""
    from backend.ml.pinn_model import PINNPredictor
    pinn = PINNPredictor()
    next_temp = pinn.predict_next_temp(t_in, t_out, solar_pu, hvac_ratio)
    return {"predicted_indoor_temp": next_temp}


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=_api_cfg.host,
        port=_api_cfg.port,
    )

