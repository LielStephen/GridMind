"""
GridMind — PPO agent training script.

Trains a Proximal Policy Optimisation agent on the GridMind/Energy-v0
environment using Stable-Baselines3.  Configuration is pulled from
``backend.config.settings.TrainingConfig``.

Usage
-----
From the project root::

    python -m backend.training.train

Or with custom timesteps::

    python -m backend.training.train --timesteps 100000
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path when running as a script
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

from backend.config.settings import TrainingConfig
from backend.rl.env import GridMindEnv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-20s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gridmind.training")


def train_agent(cfg: TrainingConfig | None = None) -> Path:
    """Train a PPO agent and save the model.

    Parameters
    ----------
    cfg : TrainingConfig, optional
        Training hyperparameters.  Falls back to defaults if omitted.

    Returns
    -------
    Path
        Absolute path to the saved model file.
    """
    cfg = cfg or TrainingConfig()

    logger.info("=" * 60)
    logger.info("GridMind PPO Training")
    logger.info("=" * 60)
    logger.info("  Algorithm      : %s", cfg.algorithm)
    logger.info("  Policy         : %s", cfg.policy)
    logger.info("  Timesteps      : %s", f"{cfg.total_timesteps:,}")
    logger.info("  Parallel envs  : %d", cfg.n_envs)
    logger.info("  TensorBoard    : %s", cfg.tensorboard_log_dir)
    logger.info("=" * 60)

    # Vectorised environment
    env = make_vec_env(GridMindEnv, n_envs=cfg.n_envs)

    # Initialise model
    model = PPO(
        cfg.policy,
        env,
        verbose=cfg.verbose,
        tensorboard_log=cfg.tensorboard_log_dir,
    )
    logger.info("Model initialised — starting training...")

    # Train
    model.learn(total_timesteps=cfg.total_timesteps)

    # Save
    save_dir = Path(cfg.model_save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    model_path = save_dir / cfg.model_name
    model.save(str(model_path))

    logger.info("Training complete — model saved to %s.zip", model_path)
    return model_path.with_suffix(".zip")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a PPO agent on the GridMind environment.",
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=None,
        help="Override total training timesteps (default: from TrainingConfig)",
    )
    parser.add_argument(
        "--envs",
        type=int,
        default=None,
        help="Number of parallel environments (default: from TrainingConfig)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    config = TrainingConfig()
    if args.timesteps:
        config = TrainingConfig(total_timesteps=args.timesteps)
    if args.envs:
        config = TrainingConfig(
            total_timesteps=config.total_timesteps,
            n_envs=args.envs,
        )

    train_agent(config)
