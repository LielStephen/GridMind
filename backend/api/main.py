from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from backend.rl.env import GridMindEnv

app = FastAPI(title="GridMind API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = GridMindEnv()


class SimulationStepResponse(BaseModel):
    step: int
    hour: int
    indoor_temp: float
    outdoor_temp: float
    solar_gen: float
    battery_soc: float
    price: float
    occupancy: bool
    energy_cost: float
    net_consumption: float
    reward: float
    terminated: bool


class SimulationStateResponse(BaseModel):
    step: int
    hour: int
    indoor_temp: float
    outdoor_temp: float
    solar_gen: float
    battery_soc: float
    price: float
    occupancy: bool


def _obs_to_dict(obs, step: int) -> dict:
    """Convert raw observation array to a labeled dictionary."""
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


@app.get("/")
async def root():
    return {"status": "GridMind Operational", "engine": "Gymnasium-v26"}


@app.get("/simulation/state", response_model=SimulationStateResponse)
async def get_state():
    obs = env._get_obs()
    return SimulationStateResponse(**_obs_to_dict(obs, env.current_step))


@app.post("/simulation/reset")
async def reset_sim():
    obs, _ = env.reset()
    return {"message": "Environment Reset", "initial_state": obs.tolist()}


@app.post("/simulation/step", response_model=SimulationStepResponse)
async def take_step(action: int):
    if action not in range(5):
        raise HTTPException(status_code=400, detail="Invalid action")

    obs, reward, terminated, truncated, info = env.step(action)

    state = _obs_to_dict(obs, env.current_step)
    return SimulationStepResponse(
        **state,
        energy_cost=info["cost"],
        net_consumption=info["net_w"],
        reward=float(reward),
        terminated=terminated,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
