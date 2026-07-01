from gymnasium.envs.registration import register
from backend.rl.env import GridMindEnv

__all__ = ["GridMindEnv"]

register(
    id="GridMind/Energy-v0",
    entry_point="backend.rl.env:GridMindEnv",
)
