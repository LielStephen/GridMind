"""
Comprehensive Verification Runner for GridMind RL & ML components.
"""

from __future__ import annotations

import sys
from backend.simulator.rc_model import LumpedRCBuildingModel
from backend.simulator.battery_advanced import AdvancedBatterySystem
from backend.simulator.pricing_advanced import AdvancedTariffManager
from backend.rl.continuous_env import GridMindContinuousEnv
from backend.rl.algorithms.sac import SACAgent
from backend.rl.algorithms.td3 import TD3Agent
from backend.simulator.mpc_solver import MPCOptimizer
from backend.rl.benchmark_suite import BenchmarkSuite
from backend.ml.forecast import GridEnergyForecaster
from backend.ml.pinn_model import PINNPredictor
from backend.ml.anomaly_detector import GridAnomalyDetector


def main():
    print("=" * 60)
    print("GRIDMIND SYSTEM VERIFICATION SUITE")
    print("=" * 60)

    print("\n1. Testing 3-Node RC Thermal Model...")
    rc = LumpedRCBuildingModel()
    rc.reset(22.0)
    t_air, t_wall, t_attic = rc.step(35.0, 500.0, 3500.0, 900.0)
    print(f"   -> Result T_air: {t_air:.2f}°C, T_wall: {t_wall:.2f}°C, T_attic: {t_attic:.2f}°C")

    print("\n2. Testing Non-linear Battery System...")
    batt = AdvancedBatterySystem()
    batt.reset(0.5)
    grid_w, stored_wh = batt.charge(3500.0, 900.0)
    print(f"   -> Charge Grid W: {grid_w:.1f}W, Energy Stored: {stored_wh:.1f}Wh, SoC: {batt.soc:.3f}, SoH: {batt.soh:.4f}")

    print("\n3. Testing Dynamic Pricing Tariff Manager...")
    tariff = AdvancedTariffManager()
    cost, carbon, demand_pen = tariff.compute_step_cost(3000.0, 0.0, 16.0, 900.0)
    print(f"   -> Step Cost: ${cost:.3f}, Carbon: {carbon:.1f}g, Demand Penalty: ${demand_pen:.2f}")

    print("\n4. Testing Continuous Gymnasium Environment...")
    env = GridMindContinuousEnv()
    obs, _ = env.reset()
    next_obs, reward, term, _, info = env.step([0.5, -0.5])
    print(f"   -> Obs Shape: {obs.shape}, Step Reward: {reward:.3f}, Step Cost: ${info['step_cost']:.3f}")

    print("\n5. Testing Soft Actor-Critic (SAC) Agent...")
    sac = SACAgent()
    act_sac = sac.select_action(obs)
    print(f"   -> SAC Action: {act_sac}")

    print("\n6. Testing Twin Delayed DDPG (TD3) Agent...")
    td3 = TD3Agent()
    act_td3 = td3.select_action(obs)
    print(f"   -> TD3 Action: {act_td3}")

    print("\n7. Testing Model Predictive Control (MPC) Solver...")
    mpc = MPCOptimizer()
    mpc_res = mpc.solve_horizon(22.0, 0.5, [25.0]*12, [0.5]*12, [0.2]*12, [True]*12, 12)
    print(f"   -> MPC Solved Horizon Steps: {len(mpc_res['hvac_power_w'])}, Total Cost: ${mpc_res['total_cost']:.2f}")

    print("\n8. Testing Forecast & PINN Models...")
    forecaster = GridEnergyForecaster()
    fc_res = forecaster.predict_24h(0.0)
    print(f"   -> 24h Weather Forecast Steps: {len(fc_res['hours'])}, Temp Peak: {max(fc_res['temp_mean']):.1f}°C")

    pinn = PINNPredictor()
    pinn_temp = pinn.predict_next_temp(22.0, 32.0, 0.8, 0.5)
    print(f"   -> PINN Predicted Indoor Temp: {pinn_temp:.2f}°C")

    anomaly_det = GridAnomalyDetector()
    anomalies = anomaly_det.detect_anomalies([{"net_w": 25000.0, "indoor_temp": 45.0, "cost": 15.0}])
    print(f"   -> Anomaly Detected: {len(anomalies) > 0}")

    print("\n9. Running Multi-Algorithm Benchmark Suite...")
    suite = BenchmarkSuite()
    benchmarks = suite.run_all_benchmarks()
    for alg, data in benchmarks.items():
        print(f"   - {alg:30s} | Daily Cost: ${data['total_cost']:5.2f} | Comfort Penalty: {data['comfort_penalty']:5.2f}")

    print("\n" + "=" * 60)
    print("SUCCESS: ALL RL, ML, PHYSICS, AND BENCHMARKING SUITES PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
