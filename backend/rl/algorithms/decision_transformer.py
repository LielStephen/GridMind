"""
Offline Decision Transformer for Building Energy Management.

Casts reinforcement learning as a sequence modeling problem.
Conditions future HVAC & battery action tokens on target return-to-go, past states, and past actions.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class DecisionTransformer(nn.Module):
    """Decision Transformer model using PyTorch MultiheadAttention."""

    def __init__(
        self,
        state_dim: int = 7,
        action_dim: int = 2,
        max_length: int = 24,
        hidden_dim: int = 128,
        num_heads: int = 4,
    ):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim

        # Embeddings
        self.embed_return = nn.Linear(1, hidden_dim)
        self.embed_state = nn.Linear(state_dim, hidden_dim)
        self.embed_action = nn.Linear(action_dim, hidden_dim)

        self.embed_ln = nn.LayerNorm(hidden_dim)

        # Transformer Encoder Layer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, nhead=num_heads, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=3)

        # Output Action Head
        self.predict_action = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
            nn.Tanh(),
        )

    def forward(
        self,
        states: torch.Tensor,       # (batch, seq_len, state_dim)
        actions: torch.Tensor,      # (batch, seq_len, action_dim)
        returns_to_go: torch.Tensor,# (batch, seq_len, 1)
    ) -> torch.Tensor:
        batch_size, seq_len, _ = states.shape

        state_embeddings = self.embed_state(states)
        action_embeddings = self.embed_action(actions)
        returns_embeddings = self.embed_return(returns_to_go)

        # Interleave tokens: (R_1, s_1, a_1, R_2, s_2, a_2, ...)
        stacked_inputs = (
            torch.stack([returns_embeddings, state_embeddings, action_embeddings], dim=2)
            .permute(0, 1, 2, 3)
            .reshape(batch_size, 3 * seq_len, self.hidden_dim)
        )
        stacked_inputs = self.embed_ln(stacked_inputs)

        # Causal mask for autoregressive prediction
        causal_mask = torch.triu(
            torch.ones((3 * seq_len, 3 * seq_len), device=states.device) * float("-inf"),
            diagonal=1,
        )

        transformer_outputs = self.transformer(stacked_inputs, mask=causal_mask)

        # Extract predictions corresponding to state tokens (offset 1 in triplet)
        state_rep = transformer_outputs[:, 1::3, :]
        action_preds = self.predict_action(state_rep)
        return action_preds
