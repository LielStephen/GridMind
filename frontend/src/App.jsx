import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Thermometer, ThermometerSun, Battery, Zap, DollarSign, Activity, Settings2, Power } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [state, setState] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchReset = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/simulation/reset`);
      const initial = res.data.initial_state;
      // state: [Hour, IndoorTemp, OutdoorTemp, SolarGen, BatterySOC, Price, Occupancy]
      const newState = {
        step: 0,
        indoor_temp: initial[1],
        outdoor_temp: initial[2],
        battery_soc: initial[4],
        energy_cost: 0,
        net_consumption: 0,
        reward: 0
      };
      setState(newState);
      setHistory([newState]);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const takeAction = async (actionId) => {
    try {
      const res = await axios.post(`${API_BASE}/simulation/step?action=${actionId}`);
      const data = res.data;
      
      setState((prev) => {
        const nextState = {
          ...data,
          // Merge in battery soc since it's not strictly returned by step unless we parse obs
          // Actually, we should ideally fetch the full state or just track what we have
        };
        setHistory(h => [...h.slice(-20), nextState]); // Keep last 20 steps
        return nextState;
      });
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchReset();
  }, []);

  if (loading || !state) {
    return <div className="flex h-screen items-center justify-center bg-slate-900 text-white">Initializing Simulation...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-900 p-8 text-slate-200">
      <header className="mb-8 flex items-center justify-between border-b border-slate-700 pb-4">
        <div className="flex items-center gap-3">
          <Zap className="h-8 w-8 text-emerald-400" />
          <h1 className="text-3xl font-bold tracking-tight text-white">GridMind Dashboard</h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="rounded-full bg-slate-800 px-4 py-1 text-sm font-medium border border-slate-700">
            Step: <span className="text-emerald-400">{state.step}</span> / 96
          </div>
          <button onClick={fetchReset} className="flex items-center gap-2 rounded-lg bg-slate-700 px-4 py-2 hover:bg-slate-600 transition-colors">
            <Power className="h-4 w-4" /> Reset Simulator
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* KPI Cards */}
        <div className="rounded-2xl border border-slate-700 bg-slate-800/50 p-6 backdrop-blur flex flex-col items-center justify-center">
          <Thermometer className="mb-2 h-8 w-8 text-blue-400" />
          <p className="text-sm text-slate-400">Indoor Temp</p>
          <p className="text-3xl font-semibold text-white">{state.indoor_temp.toFixed(1)}°C</p>
        </div>
        
        <div className="rounded-2xl border border-slate-700 bg-slate-800/50 p-6 backdrop-blur flex flex-col items-center justify-center">
          <ThermometerSun className="mb-2 h-8 w-8 text-orange-400" />
          <p className="text-sm text-slate-400">Outdoor Temp</p>
          <p className="text-3xl font-semibold text-white">{state.outdoor_temp.toFixed(1)}°C</p>
        </div>

        <div className="rounded-2xl border border-slate-700 bg-slate-800/50 p-6 backdrop-blur flex flex-col items-center justify-center">
          <DollarSign className="mb-2 h-8 w-8 text-emerald-400" />
          <p className="text-sm text-slate-400">Energy Cost</p>
          <p className="text-3xl font-semibold text-white">${state.energy_cost.toFixed(2)}</p>
        </div>

        <div className="rounded-2xl border border-slate-700 bg-slate-800/50 p-6 backdrop-blur flex flex-col items-center justify-center">
          <Activity className="mb-2 h-8 w-8 text-purple-400" />
          <p className="text-sm text-slate-400">Reward</p>
          <p className="text-3xl font-semibold text-white">{state.reward.toFixed(2)}</p>
        </div>

        {/* Charts */}
        <div className="col-span-1 lg:col-span-3 rounded-2xl border border-slate-700 bg-slate-800/50 p-6 backdrop-blur">
          <h2 className="mb-4 text-lg font-medium flex items-center gap-2">
            <Settings2 className="h-5 w-5" /> Thermodynamic Profile
          </h2>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="step" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} />
                <Legend />
                <Line type="monotone" dataKey="indoor_temp" stroke="#60a5fa" strokeWidth={3} name="Indoor Temp (°C)" />
                <Line type="monotone" dataKey="outdoor_temp" stroke="#f97316" strokeWidth={2} name="Outdoor Temp (°C)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Controls */}
        <div className="col-span-1 rounded-2xl border border-slate-700 bg-slate-800/50 p-6 backdrop-blur flex flex-col">
          <h2 className="mb-4 text-lg font-medium flex items-center gap-2">
            <Settings2 className="h-5 w-5" /> Manual Control Override
          </h2>
          <div className="flex flex-col gap-3">
            <button onClick={() => takeAction(0)} className="rounded-lg bg-slate-700 py-3 hover:bg-slate-600 font-medium transition-colors">
              Do Nothing (Idle)
            </button>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => takeAction(1)} className="rounded-lg bg-blue-600/80 py-3 hover:bg-blue-500 font-medium transition-colors">
                AC ON
              </button>
              <button onClick={() => takeAction(2)} className="rounded-lg bg-slate-700 py-3 hover:bg-slate-600 font-medium transition-colors">
                AC OFF
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-700">
              <button onClick={() => takeAction(3)} className="rounded-lg bg-emerald-600/80 py-3 hover:bg-emerald-500 font-medium transition-colors text-sm">
                Charge Batt
              </button>
              <button onClick={() => takeAction(4)} className="rounded-lg bg-amber-600/80 py-3 hover:bg-amber-500 font-medium transition-colors text-sm">
                Discharge Batt
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
