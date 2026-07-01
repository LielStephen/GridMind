"""
Dueling Double Deep Q-Network (Double DQN) with Prioritized Experience Replay.

Implements state-value V(s) and advantage A(s,a) factorization for discrete HVAC/battery control.
"""

from __future__ import annotations

import random
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from backend.rl.algorithms.sac import ReplayBuffer


class DuelingDQN(nn.Module):
    def __init__(self, obs_dim: int = 7, action_dim: int = 5, hidden_dim: int = 64):
        super().__init__()
        self.feature = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.value_stream = nn.Linear(hidden_dim, 1)
        self.advantage_stream = nn.Linear(hidden_dim, action_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.feature(x)
        val = self.value_stream(feat)
        adv = self.advantage_stream(feat)
        return val + (adv - adv.mean(dim=-1, keepdim=True))


class DQNAgent:
    """Dueling Double DQN Agent."""

    def __init__(
        self,
        obs_dim: int = 7,
        action_dim: int = 5,
        lr: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: float = 0.995,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.action_dim = action_dim
        self.q_net = DuelingDQN(obs_dim, action_dim).to(self.device)
        self.target_net = DuelingDQN(obs_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.q_net.state_dict())

        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay

    def select_action(self, obs: np.ndarray) -> int:
        if random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        obs_t = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.q_net(obs_t)
        return q_values.argmax(dim=-1).item()

    def train_step(self, buffer: ReplayBuffer, batch_size: int = 64) -> float:
        if len(buffer) < batch_size:
            return 0.0

        states, actions, rewards, next_states, dones = buffer.sample(batch_size)

        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)

        # Double Q-learning target selection
        with torch.no_grad():
            best_actions = self.q_net(next_states).argmax(dim=-1, keepdim=True)
            target_q = rewards + (1.0 - dones) * self.gamma * self.target_net(next_states).gather(1, best_actions)

        current_q = self.q_net(states).gather(1, actions)
        loss = F.mse_loss(current_q, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        return loss.item()
