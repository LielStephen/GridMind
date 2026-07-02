import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from backend.rl.env import GridMindEnv

def train_agent():
    # Wrap the environment
    # stable-baselines3 usually requires a vectorized environment
    env = make_vec_env(GridMindEnv, n_envs=1)
    
    print("Initializing PPO model...")
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ppo_gridmind_tensorboard/")
    
    print("Starting training for 50000 timesteps...")
    model.learn(total_timesteps=50000)
    
    # Save the model
    os.makedirs("backend/models", exist_ok=True)
    model_path = "backend/models/ppo_gridmind"
    model.save(model_path)
    print(f"Model saved to {model_path}.zip")

if __name__ == "__main__":
    train_agent()
