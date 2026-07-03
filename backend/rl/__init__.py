"""
GridMind RL package — Gymnasium environment registration.

Importing this module registers ``GridMind/Energy-v0`` with Gymnasium's
global registry so it can be instantiated via ``gym.make()``.
"""

from gymnasium.envs.registration import register

from backend.rl.env import GridMindEnv

__all__ = ["GridMindEnv"]

register(
    id="GridMind/Energy-v0",
    entry_point="backend.rl.env:GridMindEnv",
)
