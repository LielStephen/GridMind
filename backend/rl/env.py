import gymnasium as gym
from gymnasium import spaces
import numpy as np
from backend.simulator.models import AirConditioner, Battery, WeatherProvider

class GridMindEnv(gym.Env):
    """
    State Space: [Hour, IndoorTemp, OutdoorTemp, SolarGen, BatterySOC, Price, Occupancy]
    Action Space: Discrete(5) -> [Do Nothing, AC On, AC Off, Charge Batt, Discharge Batt]
    """
    def __init__(self):
        super().__init__()
        self.weather = WeatherProvider()
        self.ac = AirConditioner("MainAC")
        self.battery = Battery()
        
        # Define Action Space: 0: Idle, 1: AC ON, 2: AC OFF, 3: Charge, 4: Discharge
        self.action_space = spaces.Discrete(5)
        
        # Observation Space: Low/High bounds for normalized state
        self.observation_space = spaces.Box(
            low=np.array([0, 10, 0, 0, 0, 0, 0]), 
            high=np.array([23, 35, 45, 1, 1, 1, 1]), 
            dtype=np.float32
        )
        
        self.current_step = 0
        self.indoor_temp = 22.0
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.indoor_temp = 22.0
        return self._get_obs(), {}

    def _get_obs(self):
        ext_temp, solar, price, occ = self.weather.get_state(self.current_step)
        return np.array([
            (self.current_step // 4) % 24,
            self.indoor_temp,
            ext_temp,
            solar,
            self.battery.soc,
            price,
            float(occ)
        ], dtype=np.float32)

    def step(self, action):
        dt = 900 # 15 minute steps (seconds)
        ext_temp, solar, price, occupied = self.weather.get_state(self.current_step)
        
        # 1. Apply Actions
        if action == 1: self.ac.is_on = True
        elif action == 2: self.ac.is_on = False
        
        batt_load = 0
        if action == 3: batt_load = self.battery.charge(2000, dt)
        elif action == 4: batt_load = self.battery.discharge(2000, dt)

        # 2. Update Physics
        # Thermal Leakage
        self.indoor_temp += (ext_temp - self.indoor_temp) * 0.02
        if self.ac.is_on:
            self.indoor_temp -= self.ac.cooling_rate
        
        # Energy Calculation
        solar_w = solar * 5000
        net_w = self.ac.step() + batt_load - solar_w
        cost = (max(0, net_w) / 1000) * (dt/3600) * price

        # 3. Calculate Reward
        # Penalty for discomfort (Target 22°C)
        comfort_penalty = 0
        if occupied and (self.indoor_temp < 20 or self.indoor_temp > 24):
            comfort_penalty = abs(self.indoor_temp - 22) * 2.0
        
        reward = -(cost + comfort_penalty)

        self.current_step += 1
        terminated = self.current_step > 96 # 24 hours
        
        return self._get_obs(), reward, terminated, False, {"cost": cost, "net_w": net_w}
