import uuid
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class SimulationState:
    timestamp: int
    outdoor_temp: float
    indoor_temp: float
    is_occupied: bool
    solar_gen: float
    battery_soc: float
    grid_price: float
    net_consumption: float

class BaseDevice(ABC):
    def __init__(self, name: str, power_rating: float):
        self.id = str(uuid.uuid4())
        self.name = name
        self.power_rating = power_rating # Watts
        self.is_on = False
        self.consumption = 0.0

    @abstractmethod
    def step(self) -> float:
        pass

class AirConditioner(BaseDevice):
    def __init__(self, name: str, power_rating: float = 2000.0, cooling_rate: float = 0.5):
        super().__init__(name, power_rating)
        self.cooling_rate = cooling_rate 

    def step(self) -> float:
        self.consumption = self.power_rating if self.is_on else 0.5 # Standby
        return self.consumption

class Battery:
    def __init__(self, capacity_wh: float = 13500.0, max_kw: float = 5.0):
        self.capacity = capacity_wh
        self.current_charge = capacity_wh * 0.5 # Start at 50%
        self.max_rate = max_kw * 1000.0
        self.efficiency = 0.94

    def charge(self, power_w: float, dt: float) -> float:
        actual_power = min(power_w, self.max_rate)
        energy = actual_power * (dt / 3600) * self.efficiency
        self.current_charge = min(self.capacity, self.current_charge + energy)
        return actual_power

    def discharge(self, power_w: float, dt: float) -> float:
        actual_power = min(power_w, self.max_rate)
        energy = (actual_power / self.efficiency) * (dt / 3600)
        if self.current_charge >= energy:
            self.current_charge -= energy
            return -actual_power
        return 0.0

    @property
    def soc(self) -> float:
        return self.current_charge / self.capacity

class WeatherProvider:
    def get_state(self, step_idx: int):
        hour = (step_idx // 4) % 24
        # Synthetic diurnal cycles
        temp = 20 + 10 * np.sin(np.pi * (hour - 9) / 12)
        solar = max(0, np.sin(np.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0
        price = 0.15 if not (16 <= hour <= 21) else 0.45
        occupancy = 1.0 if (hour < 8 or hour > 18) else 0.0
        return temp, solar, price, bool(occupancy)
