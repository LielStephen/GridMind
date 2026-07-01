"""
Recurrent PPO (PPO + LSTM) Algorithm.

Maintains an internal LSTM hidden state memory to resolve partial observability
such as unobserved occupancy schedules, weather fronts, and latent battery state dynamics.
"""

from __future__ import annotations

from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


class RecurrentActorCritic(nn.Module):
    def __init__(self, obs_dim: int = 7, num_actions: int = 5, hidden_dim: int = 64):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.fc1 = nn.Linear(obs_dim, hidden_dim)
        self.lstm = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.actor_head = nn.Linear(hidden_dim, num_actions)
        self.critic_head = nn.Linear(hidden_dim, 1)

    def forward(
        self,
        obs: torch.Tensor,
        hidden: Tuple[torch.Tensor, torch.Tensor] | None = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        # obs shape: (batch, seq_len, obs_dim)
        x = F.relu(self.fc1(obs))
        lstm_out, hidden_next = self.lstm(x, hidden)

        logits = self.actor_head(lstm_out)
        values = self.critic_head(lstm_out)
        return logits, values.squeeze(-1), hidden_next


class RecurrentPPOAgent:
    """Recurrent PPO agent for sequential energy optimization."""

    def __init__(
        self,
        obs_dim: int = 7,
        num_actions: int = 5,
        lr: float = 3e-4,
        gamma: float = 0.99,
        clip_ratio: float = 0.2,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ac = RecurrentActorCritic(obs_dim, num_actions).to(self.device)
        self.optimizer = optim.Adam(self.ac.parameters(), lr=lr)
        self.gamma = gamma
        self.clip_ratio = clip_ratio

    def get_action(
        self,
        obs: torch.Tensor,
        hidden: Tuple[torch.Tensor, torch.Tensor] | None = None,
    ) -> Tuple[int, float, Tuple[torch.Tensor, torch.Tensor]]:
        # Single step inference
        obs_t = obs.unsqueeze(0).unsqueeze(0).to(self.device)  # (1, 1, obs_dim)
        logits, value, hidden_next = self.ac(obs_t, hidden)

        dist = torch.distributions.Categorical(logits=logits[:, -1, :])
        action = dist.sample()
        log_prob = dist.log_prob(action)

        return action.item(), log_prob.item(), hidden_next
