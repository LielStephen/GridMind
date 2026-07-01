"""
Physics-Informed Neural Network (PINN) for Thermal Dynamics.

Incorporates thermal conservation laws directly into neural network loss function:
Loss_total = Loss_data + lambda * Loss_physics
where Loss_physics = || dT/dt - (1/RC)*(T_out - T) + Q_hvac/C ||^2
"""

from __future__ import annotations

from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class ThermalPINN(nn.Module):
    """Neural surrogate model enforced by thermal physics ODEs."""

    def __init__(self, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, hidden_dim), # Inputs: [T_indoor, T_outdoor, Solar, HVAC_power]
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, 1),  # Output: dT_indoor/dt rate of change
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.net(inputs)

    def compute_physics_loss(
        self,
        t_in: torch.Tensor,
        t_out: torch.Tensor,
        solar: torch.Tensor,
        q_hvac: torch.Tensor,
        c_air: float = 1.5e6,
        r_win: float = 0.45,
    ) -> torch.Tensor:
        """Compute residual violation of heat conservation law."""
        inputs = torch.cat([t_in, t_out, solar, q_hvac], dim=-1)
        dt_predicted = self.forward(inputs)

        # Theoretical heat balance dT/dt = ((T_out - T_in)/R + Q_solar - Q_hvac) / C
        q_solar = solar * 800.0 * 0.65 * 12.0
        dt_physics = ((t_out - t_in) / r_win + q_solar - q_hvac * 3500.0) / (c_air / 3600.0)

        physics_residual = F.mse_loss(dt_predicted, dt_physics)
        return physics_residual


class PINNPredictor:
    """Interface for PINN surrogate thermal predictions."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = ThermalPINN().to(self.device)

    def predict_next_temp(
        self,
        t_in: float,
        t_out: float,
        solar_pu: float,
        hvac_power_ratio: float,
        dt_minutes: float = 15.0,
    ) -> float:
        inputs_t = torch.FloatTensor([[t_in, t_out, solar_pu, hvac_power_ratio]]).to(self.device)
        with torch.no_grad():
            dT_dt = self.model(inputs_t).item()

        next_temp = t_in + dT_dt * (dt_minutes / 60.0)
        return float(next_temp)
