import React from 'react';
import { useSimulation } from './hooks/useSimulation';
import Sidebar from './components/Layout/Sidebar';
import TopBar from './components/Layout/TopBar';
import KpiGrid from './components/Dashboard/KpiGrid';
import ThermalChart from './components/Dashboard/ThermalChart';
import EnergyChart from './components/Dashboard/EnergyChart';
import RewardChart from './components/Dashboard/RewardChart';
import BatteryGauge from './components/Dashboard/BatteryGauge';
import ActionPanel from './components/Dashboard/ActionPanel';

function App() {
  const {
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
  } = useSimulation();

  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          background: 'var(--surface-base)',
          flexDirection: 'column',
          gap: 'var(--space-4)',
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            border: '3px solid var(--border-default)',
            borderTopColor: 'var(--accent)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <span
          style={{
            fontSize: '0.875rem',
            color: 'var(--text-muted)',
            fontWeight: 500,
          }}
        >
          Initializing GridMind...
        </span>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  // Determine battery charge/discharge state from last action
  const lastAction = actionLog.length > 0 ? actionLog[0].action : null;
  const isCharging = lastAction === 3;
  const isDischarging = lastAction === 4;

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        background: 'var(--surface-base)',
      }}
    >
      {/* Sidebar */}
      <Sidebar
        isConnected={isConnected}
        isAutoRunning={isAutoRunning}
        onReset={reset}
        onToggleAutoRun={toggleAutoRun}
        terminated={current.terminated}
      />

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top bar */}
        <TopBar
          step={current.step}
          clockDisplay={clockDisplay}
          terminated={current.terminated}
          occupancy={current.occupancy}
          price={current.price}
        />

        {/* Dashboard body */}
        <main
          style={{
            flex: 1,
            padding: 'var(--space-6)',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-5)',
          }}
        >
          {/* Summary strip */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-6)',
              padding: 'var(--space-3) var(--space-5)',
              background: 'var(--surface-1)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-lg)',
              fontSize: '0.8125rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Total Cost</span>
              <span
                className="data-value"
                style={{ fontWeight: 600, color: 'var(--color-warning)', fontFamily: 'var(--font-mono)' }}
              >
                ${cumulativeCost.toFixed(3)}
              </span>
            </div>
            <div
              style={{
                width: 1,
                height: 16,
                background: 'var(--border-subtle)',
              }}
            />
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Total Reward</span>
              <span
                className="data-value"
                style={{
                  fontWeight: 600,
                  color: cumulativeReward >= 0 ? 'var(--color-success)' : 'var(--color-danger)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {cumulativeReward.toFixed(3)}
              </span>
            </div>
            <div
              style={{
                width: 1,
                height: 16,
                background: 'var(--border-subtle)',
              }}
            />
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Solar Output</span>
              <span
                className="data-value"
                style={{
                  fontWeight: 600,
                  color: 'var(--chart-solar)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {((current.solar_gen || 0) * 5).toFixed(1)} kW
              </span>
            </div>
          </div>

          {/* KPI Cards */}
          <KpiGrid current={current} deltas={deltas} />

          {/* Charts row: Thermal (2/3) + Battery + Action (1/3) */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '2fr 1fr',
              gap: 'var(--space-5)',
              minHeight: 0,
            }}
          >
            {/* Left column: charts stacked */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
              <ThermalChart history={history} />
              <EnergyChart history={history} />
            </div>

            {/* Right column: battery + actions + reward */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
              <ActionPanel
                onAction={step}
                actionLog={actionLog}
                terminated={current.terminated}
              />
              <BatteryGauge
                soc={current.battery_soc}
                isCharging={isCharging}
                isDischarging={isDischarging}
              />
              <RewardChart
                history={history}
                cumulativeReward={cumulativeReward}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
