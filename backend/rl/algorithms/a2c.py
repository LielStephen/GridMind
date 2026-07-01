"""
Advantage Actor-Critic (A2C) Algorithm in PyTorch.

Synchronous Actor-Critic algorithm with entropy regularization.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


class ActorCriticNetwork(nn.Module):
    def __init__(self, obs_dim: int = 7, action_dim: int = 5, hidden_dim: int = 64):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.actor = nn.Linear(hidden_dim, action_dim)
        self.critic = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = F.relu(self.fc1(x))
        h = F.relu(self.fc2(h))
        policy_logits = self.actor(h)
        value = self.critic(h)
        return policy_logits, value


class A2CAgent:
    """A2C Agent for discrete energy environment."""

    def __init__(self, obs_dim: int = 7, action_dim: int = 5, lr: float = 7e-4, gamma: float = 0.99):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.net = ActorCriticNetwork(obs_dim, action_dim).to(self.device)
        self.optimizer = optim.Adam(self.net.parameters(), lr=lr)
        self.gamma = gamma

    def select_action(self, obs: np.ndarray) -> Tuple[int, torch.Tensor, torch.Tensor]:
        obs_t = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        logits, value = self.net(obs_t)
        probs = F.softmax(logits, dim=-1)
        dist = torch.distributions.Categorical(probs)
        action = dist.sample()
        return action.item(), dist.log_prob(action), value.squeeze(0)

    def train_step(self, log_prob: torch.Tensor, value: torch.Tensor, reward: float, next_obs: np.ndarray, done: bool) -> float:
        next_obs_t = torch.FloatTensor(next_obs).unsqueeze(0).to(self.device)
        _, next_value = self.net(next_obs_t)

        target = reward + (0.0 if done else self.gamma * next_value.item())
        advantage = target - value.item()

        actor_loss = -log_prob * advantage
        critic_loss = F.mse_loss(value, torch.tensor([target], device=self.device))
        loss = actor_loss + critic_loss

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return loss.item()
