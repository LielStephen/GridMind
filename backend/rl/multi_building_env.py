"""
Multi-Building Grid Management Gymnasium Environment.

Simulates 5 smart buildings under total neighborhood transformer load limit.
Enforces cooperative peak shaving and voltage stability.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from backend.rl.continuous_env import GridMindContinuousEnv

logger = logging.getLogger(__name__)


class MultiBuildingGridEnv(gym.Env):
    """Multi-building smart community environment."""

    def __init__(self, num_buildings: int = 5, max_transformer_capacity_kw: float = 15.0) -> None:
        super().__init__()
        self.num_buildings = num_buildings
        self.max_transformer_capacity_kw = max_transformer_capacity_kw

        self.envs = [GridMindContinuousEnv() for _ in range(num_buildings)]

        # Action space: 5 buildings x 2 actions = 10 continuous controls
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(num_buildings * 2,), dtype=np.float32
        )

        # Observation space: 5 buildings x 7 obs + 1 transformer load ratio = 36 continuous features
        self.observation_space = spaces.Box(
            low=0.0, high=50.0, shape=(num_buildings * 7 + 1,), dtype=np.float32
        )

        self.reset()

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, dict]:
        super().reset(seed=seed)

        obs_list = []
        for env in self.envs:
            obs, _ = env.reset(seed=seed)
            obs_list.extend(obs.tolist())

        obs_list.append(0.0)  # Initial transformer load ratio
        return np.array(obs_list, dtype=np.float32), {}

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, dict]:
        actions_per_bldg = np.reshape(action, (self.num_buildings, 2))

        total_grid_imported_w = 0.0
        total_step_cost = 0.0
        total_comfort_penalty = 0.0

        next_obs_list = []
        all_terminated = True

        for i, env in enumerate(self.envs):
            b_act = actions_per_bldg[i]
            obs, r, term, trunc, info = env.step(b_act)
            next_obs_list.extend(obs.tolist())

            total_grid_imported_w += info["grid_imported_w"]
            total_step_cost += info["step_cost"]
            total_comfort_penalty += info["comfort_penalty"]
            if not term:
                all_terminated = False

        total_load_kw = total_grid_imported_w / 1000.0
        transformer_ratio = total_load_kw / self.max_transformer_capacity_kw

        # Transformer overload penalty
        overload_penalty = 0.0
        if total_load_kw > self.max_transformer_capacity_kw:
            overload_penalty = (total_load_kw - self.max_transformer_capacity_kw) ** 2 * 10.0

        joint_reward = -(total_step_cost + total_comfort_penalty + overload_penalty)

        next_obs_list.append(transformer_ratio)

        info = {
            "total_load_kw": total_load_kw,
            "transformer_ratio": transformer_ratio,
            "overload_penalty": overload_penalty,
            "total_step_cost": total_step_cost,
        }

        return np.array(next_obs_list, dtype=np.float32), float(joint_reward), all_terminated, False, info
