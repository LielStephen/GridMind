import React, { useMemo } from 'react';
import {
  Thermometer,
  DollarSign,
  Activity,
  Sun,
  ShieldAlert,
  BatteryCharging,
  Unplug,
  CircleDot,
  Snowflake,
  PowerOff,
  TrendingUp,
  Coins,
} from 'lucide-react';

const ACTIONS = [
  {
    id: 0,
    label: 'Idle',
    icon: CircleDot,
    desc: 'No control action is active.',
    details: 'The HVAC unit remains in standby (0.5 W draw). The battery state-of-charge remains constant.',
    color: 'var(--text-muted)',
    accent: 'rgba(136, 130, 172, 0.25)',
  },
  {
    id: 1,
    label: 'AC On',
    icon: Snowflake,
    desc: 'Active HVAC cooling is enabled.',
    details: 'Draws 2,000 W from solar or grid. Lowers the indoor temperature by 0.5°C per 15-minute step.',
    color: 'var(--chart-indoor)',
    accent: 'rgba(0, 229, 255, 0.25)',
  },
  {
    id: 2,
    label: 'AC Off',
    icon: PowerOff,
    desc: 'HVAC cooling is disabled.',
    details: 'HVAC unit draws standby power (0.5 W). Building temperature naturally rises/falls towards outdoor ambient temp based on building leakage rate.',
    color: 'var(--text-secondary)',
    accent: 'rgba(0, 255, 204, 0.25)',
  },
  {
    id: 3,
    label: 'Charge',
    icon: BatteryCharging,
    desc: 'Store energy in the battery.',
    details: 'Charges home battery from local solar or the grid (up to 5 kW rate). Helps store cheap off-peak power. 94% charging efficiency.',
    color: 'var(--color-success)',
    accent: 'rgba(57, 255, 20, 0.25)',
  },
  {
    id: 4,
    label: 'Discharge',
    icon: Unplug,
    desc: 'Discharge battery to power local loads.',
    details: 'Releases battery energy (up to 5 kW rate) to offset building AC loads. Essential for avoiding peak grid tariffs ($0.45/kWh).',
    color: 'var(--color-warning)',
    accent: 'rgba(255, 183, 0, 0.25)',
  },
];

export default function AnalyticsView({ history, cumulativeReward, cumulativeCost }) {
  // 1. Calculations
  const stats = useMemo(() => {
    // Comfort Compliance
    const occupiedSteps = history.filter((h) => h.occupancy);
    const comfortSteps = occupiedSteps.filter(
      (h) => h.indoor_temp >= 20.0 && h.indoor_temp <= 24.0
    );
    const comfortCompliance = occupiedSteps.length > 0
      ? (comfortSteps.length / occupiedSteps.length) * 100
      : 100.0;
    const comfortViolations = occupiedSteps.length - comfortSteps.length;

    // Solar Utilization
    let totalSolarGen = 0;
    let totalSolarUtilized = 0;
    history.forEach((h) => {
      const solarW = (h.solar_gen || 0) * 5000;
      const netW = h.net_consumption || 0;
      const excessSolarW = netW < 0 ? Math.abs(netW) : 0;
      const utilizedSolarW = Math.max(0, solarW - excessSolarW);
      totalSolarGen += solarW * 0.25; // Wh
      totalSolarUtilized += utilizedSolarW * 0.25; // Wh
    });
    const solarUtilizationRate = totalSolarGen > 0
      ? (totalSolarUtilized / totalSolarGen) * 100
      : 100.0;

    // Peak vs Off-Peak Costs
    let peakCost = 0;
    let offPeakCost = 0;
    history.forEach((h) => {
      if (h.hour >= 16 && h.hour < 21) {
        peakCost += h.energy_cost || 0;
      } else {
        offPeakCost += h.energy_cost || 0;
      }
    });

    // Action distribution counts
    const actionCounts = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 };
    let validActionSteps = 0;
    history.forEach((h) => {
      if (h.action !== undefined && h.action !== null) {
        actionCounts[h.action] = (actionCounts[h.action] || 0) + 1;
        validActionSteps++;
      }
    });

    return {
      comfortCompliance,
      comfortViolations,
      solarUtilizationRate,
      totalSolarGenKwh: totalSolarGen / 1000,
      totalSolarUtilizedKwh: totalSolarUtilized / 1000,
      peakCost,
      offPeakCost,
      actionCounts,
      validActionSteps,
    };
  }, [history]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-6)',
        animation: 'fadeIn var(--duration-slow) var(--ease-out)',
      }}
    >
      {/* View Header */}
      <div>
        <h1
          style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            color: 'var(--accent)',
            fontFamily: 'var(--font-mono)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Simulation Analytics & Report
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: 'var(--space-1)' }}>
          Detailed performance breakdown of building comfort compliance, solar PV optimization, grid tariff costs, and action frequencies.
        </p>
      </div>

      {/* KPI Cards Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        {/* Comfort Compliance */}
        <div className="card" style={{ borderTop: '2px solid var(--chart-indoor)' }}>
          <div className="card-inner" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyStyle: 'space-between', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Comfort Score
              </span>
              <Thermometer size={16} style={{ color: 'var(--chart-indoor)' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)' }}>
              <span className="data-value" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {stats.comfortCompliance.toFixed(1)}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>%</span>
            </div>
            <span style={{ fontSize: '0.7rem', color: stats.comfortViolations > 0 ? 'var(--color-danger)' : 'var(--color-success)', fontFamily: 'var(--font-mono)' }}>
              {stats.comfortViolations} out-of-band occupied steps
            </span>
          </div>
        </div>

        {/* Solar Utilization Rate */}
        <div className="card" style={{ borderTop: '2px solid var(--chart-solar)' }}>
          <div className="card-inner" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Solar Utilization
              </span>
              <Sun size={16} style={{ color: 'var(--chart-solar)' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)' }}>
              <span className="data-value" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {stats.solarUtilizationRate.toFixed(1)}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>%</span>
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Used {stats.totalSolarUtilizedKwh.toFixed(2)} / {stats.totalSolarGenKwh.toFixed(2)} kWh
            </span>
          </div>
        </div>

        {/* Peak Pricing Cost */}
        <div className="card" style={{ borderTop: '2px solid var(--accent-strong)' }}>
          <div className="card-inner" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Peak Cost (4pm-9pm)
              </span>
              <TrendingUp size={16} style={{ color: 'var(--accent-strong)' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)' }}>
              <span className="data-value" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                ${stats.peakCost.toFixed(3)}
              </span>
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Rate: $0.45/kWh (Peak Tariff)
            </span>
          </div>
        </div>

        {/* Off-Peak Pricing Cost */}
        <div className="card" style={{ borderTop: '2px solid var(--color-success)' }}>
          <div className="card-inner" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Off-Peak Cost
              </span>
              <Coins size={16} style={{ color: 'var(--color-success)' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)' }}>
              <span className="data-value" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                ${stats.offPeakCost.toFixed(3)}
              </span>
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Rate: $0.15/kWh (Off-Peak Tariff)
            </span>
          </div>
        </div>
      </div>

      {/* Analytics Grid: Left (Action Distributions) & Right (Actions Description Reference) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--space-5)',
          alignItems: 'start',
        }}
      >
        {/* Action Distributions Card */}
        <div className="card">
          <div className="card-inner">
            <h2
              style={{
                fontSize: '0.875rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: 'var(--space-4)',
                fontFamily: 'var(--font-mono)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                borderBottom: '1px solid var(--border-subtle)',
                paddingBottom: 'var(--space-2)',
              }}
            >
              Action Distribution Breakdown
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {ACTIONS.map((act) => {
                const count = stats.actionCounts[act.id] || 0;
                const percentage = stats.validActionSteps > 0
                  ? (count / stats.validActionSteps) * 100
                  : 0;
                const ActIcon = act.icon;

                return (
                  <div key={act.id} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: act.color }}>
                        <ActIcon size={14} />
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{act.label}</span>
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {count} steps ({percentage.toFixed(0)}%)
                      </div>
                    </div>
                    {/* Retro Progress Bar */}
                    <div
                      style={{
                        height: 10,
                        background: 'var(--surface-2)',
                        borderRadius: 'var(--radius-sm)',
                        overflow: 'hidden',
                        border: '1px solid var(--border-subtle)',
                        position: 'relative',
                      }}
                    >
                      <div
                        style={{
                          height: '100%',
                          width: `${percentage}%`,
                          background: `linear-gradient(90deg, ${act.color}cc, ${act.color})`,
                          transition: 'width 0.5s ease-out',
                          boxShadow: `0 0 8px ${act.color}`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div
              style={{
                marginTop: 'var(--space-4)',
                fontSize: '0.7rem',
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-mono)',
                textAlign: 'center',
              }}
            >
              Total Steps Logged: {stats.validActionSteps} / 96
            </div>
          </div>
        </div>

        {/* Action Reference Guide Card */}
        <div className="card">
          <div className="card-inner">
            <h2
              style={{
                fontSize: '0.875rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: 'var(--space-4)',
                fontFamily: 'var(--font-mono)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                borderBottom: '1px solid var(--border-subtle)',
                paddingBottom: 'var(--space-2)',
              }}
            >
              System Actions Reference Guide
            </h2>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-4)',
                maxHeight: 400,
                overflowY: 'auto',
                paddingRight: 'var(--space-2)',
              }}
            >
              {ACTIONS.map((act) => {
                const ActIcon = act.icon;
                return (
                  <div
                    key={act.id}
                    style={{
                      padding: 'var(--space-3)',
                      background: 'var(--surface-2)',
                      border: `1px solid var(--border-subtle)`,
                      borderLeft: `3px solid ${act.color}`,
                      borderRadius: 'var(--radius-sm)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-2)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: act.color }}>
                      <ActIcon size={15} />
                      <h3 style={{ fontSize: '0.8rem', fontWeight: 700, fontFamily: 'var(--font-mono)', margin: 0, textTransform: 'uppercase' }}>
                        Action {act.id}: {act.label}
                      </h3>
                    </div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-primary)', margin: 0, fontWeight: 500 }}>
                      {act.desc}
                    </p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', margin: 0 }}>
                      {act.details}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
