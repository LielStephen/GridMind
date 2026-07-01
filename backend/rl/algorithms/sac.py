"""
Soft Actor-Critic (SAC) Algorithm in PyTorch.

Off-policy maximum entropy deep RL for continuous control.
Features twin Q-networks, target Q networks with soft update tau, and automated entropy temperature alpha optimization.
"""

from __future__ import annotations

import random
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


class ReplayBuffer:
    def __init__(self, capacity: int = 100000):
        self.capacity = capacity
        self.buffer = []
        self.position = 0

    def push(self, state, action, reward, next_state, done):
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.position] = (state, action, reward, next_state, done)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        state, action, reward, next_state, done = map(np.stack, zip(*batch))
        return state, action, reward, next_state, done

    def __len__(self):
        return len(self.buffer)


class GaussianPolicy(nn.Module):
    def __init__(self, num_inputs: int, num_actions: int, hidden_dim: int = 128):
        super().__init__()
        self.fc1 = nn.Linear(num_inputs, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.mean_linear = nn.Linear(hidden_dim, num_actions)
        self.log_std_linear = nn.Linear(hidden_dim, num_actions)

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        mean = self.mean_linear(x)
        log_std = self.log_std_linear(x)
        log_std = torch.clamp(log_std, min=-20, max=2)
        return mean, log_std

    def sample(self, state: torch.Tensor, epsilon: float = 1e-6) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mean, log_std = self.forward(state)
        std = log_std.exp()
        normal = torch.distributions.Normal(mean, std)
        x_t = normal.rsample()
        action = torch.tanh(x_t)

        log_prob = normal.log_prob(x_t)
        # Enforcing Action Bound penalty
        log_prob -= torch.log(1 - action.pow(2) + epsilon)
        log_prob = log_prob.sum(1, keepdim=True)
        mean_action = torch.tanh(mean)
        return action, log_prob, mean_action


class QNetwork(nn.Module):
    def __init__(self, num_inputs: int, num_actions: int, hidden_dim: int = 128):
        super().__init__()
        # Q1 architecture
        self.q1_fc1 = nn.Linear(num_inputs + num_actions, hidden_dim)
        self.q1_fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.q1_out = nn.Linear(hidden_dim, 1)

        # Q2 architecture
        self.q2_fc1 = nn.Linear(num_inputs + num_actions, hidden_dim)
        self.q2_fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.q2_out = nn.Linear(hidden_dim, 1)

    def forward(self, state: torch.Tensor, action: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        xu = torch.cat([state, action], 1)

        x1 = F.relu(self.q1_fc1(xu))
        x1 = F.relu(self.q1_fc2(x1))
        q1 = self.q1_out(x1)

        x2 = F.relu(self.q2_fc1(xu))
        x2 = F.relu(self.q2_fc2(x2))
        q2 = self.q2_out(x2)

        return q1, q2


class SACAgent:
    """Soft Actor-Critic Agent for continuous energy optimization."""

    def __init__(
        self,
        num_inputs: int = 7,
        num_actions: int = 2,
        lr: float = 3e-4,
        gamma: float = 0.99,
        tau: float = 0.005,
        alpha: float = 0.2,
        hidden_dim: int = 128,
    ):
        self.gamma = gamma
        self.tau = tau
        self.alpha = alpha

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.critic = QNetwork(num_inputs, num_actions, hidden_dim).to(self.device)
        self.critic_optim = optim.Adam(self.critic.parameters(), lr=lr)

        self.critic_target = QNetwork(num_inputs, num_actions, hidden_dim).to(self.device)
        self.critic_target.load_state_dict(self.critic.state_dict())

        self.policy = GaussianPolicy(num_inputs, num_actions, hidden_dim).to(self.device)
        self.policy_optim = optim.Adam(self.policy.parameters(), lr=lr)

        self.target_entropy = -float(num_actions)
        self.log_alpha = torch.zeros(1, requires_grad=True, device=self.device)
        self.alpha_optim = optim.Adam([self.log_alpha], lr=lr)

    def select_action(self, state: np.ndarray, evaluate: bool = False) -> np.ndarray:
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        if not evaluate:
            action, _, _ = self.policy.sample(state_t)
        else:
            _, _, action = self.policy.sample(state_t)
        return action.detach().cpu().numpy()[0]

    def update_parameters(self, memory: ReplayBuffer, batch_size: int = 64) -> Tuple[float, float]:
        if len(memory) < batch_size:
            return 0.0, 0.0

        state_batch, action_batch, reward_batch, next_state_batch, mask_batch = memory.sample(batch_size)

        state_batch = torch.FloatTensor(state_batch).to(self.device)
        next_state_batch = torch.FloatTensor(next_state_batch).to(self.device)
        action_batch = torch.FloatTensor(action_batch).to(self.device)
        reward_batch = torch.FloatTensor(reward_batch).unsqueeze(1).to(self.device)
        mask_batch = torch.FloatTensor(1.0 - mask_batch).unsqueeze(1).to(self.device)

        with torch.no_grad():
            next_state_action, next_state_log_pi, _ = self.policy.sample(next_state_batch)
            q1_next_target, q2_next_target = self.critic_target(next_state_batch, next_state_action)
            min_q_next_target = torch.min(q1_next_target, q2_next_target) - self.alpha * next_state_log_pi
            next_q_value = reward_batch + mask_batch * self.gamma * min_q_next_target

        q1, q2 = self.critic(state_batch, action_batch)
        q1_loss = F.mse_loss(q1, next_q_value)
        q2_loss = F.mse_loss(q2, next_q_value)
        critic_loss = q1_loss + q2_loss

        self.critic_optim.zero_grad()
        critic_loss.backward()
        self.critic_optim.step()

        pi, log_pi, _ = self.policy.sample(state_batch)
        q1_pi, q2_pi = self.critic(state_batch, pi)
        min_q_pi = torch.min(q1_pi, q2_pi)
        policy_loss = ((self.alpha * log_pi) - min_q_pi).mean()

        self.policy_optim.zero_grad()
        policy_loss.backward()
        self.policy_optim.step()

        alpha_loss = -(self.log_alpha * (log_pi + self.target_entropy).detach()).mean()
        self.alpha_optim.zero_grad()
        alpha_loss.backward()
        self.alpha_optim.step()

        self.alpha = self.log_alpha.exp().item()

        # Soft update target critics
        for target_param, param in zip(self.critic_target.parameters(), self.critic.parameters()):
            target_param.data.copy_(target_param.data * (1.0 - self.tau) + param.data * self.tau)

        return critic_loss.item(), policy_loss.item()
