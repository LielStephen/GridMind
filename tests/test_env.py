import unittest
import numpy as np
import gymnasium as gym
from backend.rl.env import GridMindEnv
from fastapi.testclient import TestClient
from backend.api.main import app

class TestGridMindEnv(unittest.TestCase):
    def test_registration(self):
        """Test that the environment is registered correctly with gymnasium."""
        import backend.rl  # Trigger registration
        env = gym.make("GridMind/Energy-v0")
        self.assertIsInstance(env.unwrapped, GridMindEnv)
        env.close()

    def test_reset(self):
        """Test the environment reset returns correct state shapes."""
        env = GridMindEnv()
        obs, info = env.reset()
        self.assertEqual(obs.shape, (7,))
        self.assertIsInstance(info, dict)
        env.close()

    def test_step_idle(self):
        """Test taking an idle step."""
        env = GridMindEnv()
        env.reset()
        obs, reward, terminated, truncated, info = env.step(0)  # 0 is Idle
        self.assertEqual(obs.shape, (7,))
        self.assertIn("cost", info)
        self.assertIn("net_w", info)
        env.close()

    def test_battery_bounds(self):
        """Test that battery charge remains within bounds when charging."""
        env = GridMindEnv()
        env.reset()
        initial_soc = env.battery.soc
        
        # Charge battery for several steps
        for _ in range(5):
            env.step(3)  # Action 3: Charge Batt
            
        self.assertGreater(env.battery.soc, initial_soc)
        self.assertLessEqual(env.battery.soc, 1.0)
        env.close()

    def test_ac_cooling(self):
        """Test that the AC reduces indoor temperature."""
        env = GridMindEnv()
        env.reset()
        env.indoor_temp = 30.0  # Set it high
        
        # AC OFF
        env.step(2)
        temp_without_ac = env.indoor_temp
        
        # AC ON
        env.indoor_temp = 30.0
        env.step(1)
        temp_with_ac = env.indoor_temp
        
        self.assertLess(temp_with_ac, temp_without_ac)
        env.close()

class TestGridMindAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("GridMind Operational", response.json()["status"])

    def test_reset_sim(self):
        response = self.client.post("/simulation/reset")
        self.assertEqual(response.status_code, 200)
        self.assertIn("initial_state", response.json())
        self.assertEqual(len(response.json()["initial_state"]), 7)

    def test_take_step(self):
        self.client.post("/simulation/reset")
        response = self.client.post("/simulation/step?action=0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("indoor_temp", data)
        self.assertIn("reward", data)

if __name__ == "__main__":
    unittest.main()
