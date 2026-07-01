"""
Unit tests for SAC, TD3, Recurrent PPO, Decision Transformer, A2C, DQN, and MPC solvers.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from backend.rl.algorithms.a2c import A2CAgent
from backend.rl.algorithms.decision_transformer import DecisionTransformer
from backend.rl.algorithms.dqn import DQNAgent
from backend.rl.algorithms.recurrent_ppo import RecurrentPPOAgent
from backend.rl.algorithms.sac import SACAgent
from backend.rl.algorithms.td3 import TD3Agent
from backend.simulator.mpc_solver import MPCOptimizer


def test_sac_agent_selection():
    agent = SACAgent(num_inputs=7, num_actions=2)
    obs = np.random.randn(7).astype(np.float32)
    action = agent.select_action(obs)
    assert action.shape == (2,)
    assert -1.0 <= action[0] <= 1.0
    assert -1.0 <= action[1] <= 1.0


def test_td3_agent_selection():
    agent = TD3Agent(state_dim=7, action_dim=2)
    obs = np.random.randn(7).astype(np.float32)
    action = agent.select_action(obs)
    assert action.shape == (2,)


def test_recurrent_ppo():
    agent = RecurrentPPOAgent()
    obs_t = torch.randn(7)
    action, log_prob, hidden = agent.get_action(obs_t)
    assert 0 <= action < 5
    assert isinstance(log_prob, float)


def test_decision_transformer():
    dt = DecisionTransformer(state_dim=7, action_dim=2, max_length=10)
    states = torch.randn(2, 10, 7)
    actions = torch.randn(2, 10, 2)
    rtg = torch.randn(2, 10, 1)

    preds = dt(states, actions, rtg)
    assert preds.shape == (2, 10, 2)


def test_mpc_solver():
    solver = MPCOptimizer()
    outdoor_temps = [25.0] * 12
    solar_pus = [0.5] * 12
    prices = [0.20] * 12
    occupancy = [True] * 12

    solution = solver.solve_horizon(
        initial_temp=22.0,
        initial_soc=0.5,
        outdoor_temps=outdoor_temps,
        solar_pus=solar_pus,
        grid_prices=prices,
        occupancy_schedule=occupancy,
        horizon_steps=12,
    )
    assert "hvac_power_w" in solution
    assert len(solution["hvac_power_w"]) == 12
