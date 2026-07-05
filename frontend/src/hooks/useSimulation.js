import { useState, useCallback, useRef, useEffect } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const INITIAL_STATE = {
  step: 0,
  hour: 0,
  indoor_temp: 22.0,
  outdoor_temp: 20.0,
  solar_gen: 0,
  battery_soc: 0.5,
  price: 0.15,
  occupancy: false,
  energy_cost: 0,
  net_consumption: 0,
  reward: 0,
  terminated: false,
};

export function useSimulation() {
  const [current, setCurrent] = useState(INITIAL_STATE);
  const [history, setHistory] = useState([]);
  const [cumulativeReward, setCumulativeReward] = useState(0);
  const [cumulativeCost, setCumulativeCost] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isAutoRunning, setIsAutoRunning] = useState(false);
  const [actionLog, setActionLog] = useState([]);
  const autoRunRef = useRef(null);
  const prevStateRef = useRef(null);

  const ACTION_LABELS = ['Idle', 'AC On', 'AC Off', 'Charge', 'Discharge'];

  const reset = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/simulation/reset`);
      const initial = res.data.initial_state;
      const state = {
        step: 0,
        hour: Math.floor(initial[0]),
        indoor_temp: initial[1],
        outdoor_temp: initial[2],
        solar_gen: initial[3],
        battery_soc: initial[4],
        price: initial[5],
        occupancy: Boolean(initial[6]),
        energy_cost: 0,
        net_consumption: 0,
        reward: 0,
        terminated: false,
        action: null,
      };
      prevStateRef.current = null;
      setCurrent(state);
      setHistory([state]);
      setCumulativeReward(0);
      setCumulativeCost(0);
      setIsConnected(true);
      setActionLog([]);
    } catch (err) {
      console.error('Reset failed:', err);
      setIsConnected(false);
    }
    setIsLoading(false);
  }, []);

  const step = useCallback(async (action) => {
    try {
      const res = await axios.post(`${API_BASE}/simulation/step?action=${action}`);
      const data = res.data;

      prevStateRef.current = { ...current };

      const nextState = {
        step: data.step,
        hour: data.hour,
        indoor_temp: data.indoor_temp,
        outdoor_temp: data.outdoor_temp,
        solar_gen: data.solar_gen,
        battery_soc: data.battery_soc,
        price: data.price,
        occupancy: data.occupancy,
        energy_cost: data.energy_cost,
        net_consumption: data.net_consumption,
        reward: data.reward,
        terminated: data.terminated,
        action,
      };

      setCurrent(nextState);
      setHistory(prev => [...prev.slice(-95), nextState]);
      setCumulativeReward(prev => prev + data.reward);
      setCumulativeCost(prev => prev + data.energy_cost);
      setIsConnected(true);

      setActionLog(prev => [
        {
          step: data.step,
          action,
          label: ACTION_LABELS[action],
          reward: data.reward,
          timestamp: Date.now(),
        },
        ...prev.slice(0, 9),
      ]);

      if (data.terminated) {
        setIsAutoRunning(false);
      }

      return nextState;
    } catch (err) {
      console.error('Step failed:', err);
      setIsConnected(false);
      return null;
    }
  }, [current]);

  // Auto-run: step with action 0 (idle) at interval
  const toggleAutoRun = useCallback(() => {
    setIsAutoRunning(prev => !prev);
  }, []);

  useEffect(() => {
    if (isAutoRunning && !current.terminated) {
      autoRunRef.current = setInterval(() => {
        step(0); // Default to idle action
      }, 400);
    } else {
      clearInterval(autoRunRef.current);
    }
    return () => clearInterval(autoRunRef.current);
  }, [isAutoRunning, step, current.terminated]);

  // Initial reset on mount
  useEffect(() => {
    reset();
  }, [reset]);

  // Compute deltas
  const deltas = {};
  if (prevStateRef.current) {
    const prev = prevStateRef.current;
    deltas.indoor_temp = current.indoor_temp - prev.indoor_temp;
    deltas.outdoor_temp = current.outdoor_temp - prev.outdoor_temp;
    deltas.battery_soc = current.battery_soc - prev.battery_soc;
    deltas.energy_cost = current.energy_cost;
    deltas.net_consumption = current.net_consumption;
    deltas.reward = current.reward;
  }

  // Simulated clock from step
  const clockHour = Math.floor((current.step * 15) / 60) % 24;
  const clockMinute = (current.step * 15) % 60;
  const clockDisplay = `${String(clockHour).padStart(2, '0')}:${String(clockMinute).padStart(2, '0')}`;

  return {
    current,
    history,
    cumulativeReward,
    cumulativeCost,
    isConnected,
    isLoading,
    isAutoRunning,
    actionLog,
    deltas,
    clockDisplay,
    reset,
    step,
    toggleAutoRun,
  };
}
