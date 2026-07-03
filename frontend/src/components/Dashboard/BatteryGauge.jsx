import React from 'react';
import { BatteryCharging, BatteryFull, BatteryLow, BatteryMedium } from 'lucide-react';

export default function BatteryGauge({ soc, isCharging, isDischarging }) {
  const percent = Math.round(soc * 100);

  let barColor = 'var(--color-success)';
  let bgColor = 'var(--color-success-muted)';
  let BattIcon = BatteryFull;

  if (percent < 20) {
    barColor = 'var(--color-danger)';
    bgColor = 'var(--color-danger-muted)';
    BattIcon = BatteryLow;
  } else if (percent < 50) {
    barColor = 'var(--color-warning)';
    bgColor = 'var(--color-warning-muted)';
    BattIcon = BatteryMedium;
  }

  if (isCharging) BattIcon = BatteryCharging;

  return (
    <div className="card">
      <div className="card-inner">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 'var(--space-4)',
          }}
        >
          <h2 style={{ fontSize: '0.875rem', fontWeight: 600 }}>
            Battery Storage
          </h2>
          <BattIcon size={18} style={{ color: barColor }} />
        </div>

        {/* Large percentage display */}
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 'var(--space-1)',
            marginBottom: 'var(--space-4)',
          }}
        >
          <span
            className="data-value"
            style={{
              fontSize: '2.5rem',
              fontWeight: 700,
              color: barColor,
              lineHeight: 1,
            }}
          >
            {percent}
          </span>
          <span
            style={{
              fontSize: '1rem',
              fontWeight: 600,
              color: 'var(--text-muted)',
            }}
          >
            %
          </span>
        </div>

        {/* Bar gauge */}
        <div
          style={{
            width: '100%',
            height: 12,
            background: 'var(--surface-2)',
            borderRadius: 6,
            overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${percent}%`,
              background: `linear-gradient(90deg, ${barColor}cc, ${barColor})`,
              borderRadius: 6,
              transition: 'width var(--duration-slow) var(--ease-out)',
              boxShadow: `0 0 8px ${barColor}44`,
            }}
          />
        </div>

        {/* Status label */}
        <div
          style={{
            marginTop: 'var(--space-3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.6875rem',
            color: 'var(--text-muted)',
          }}
        >
          <span>0%</span>
          <span
            style={{
              color: isCharging
                ? 'var(--color-success)'
                : isDischarging
                  ? 'var(--color-warning)'
                  : 'var(--text-muted)',
              fontWeight: 500,
            }}
          >
            {isCharging ? '⚡ Charging' : isDischarging ? '↓ Discharging' : '— Idle'}
          </span>
          <span>100%</span>
        </div>

        {/* Capacity label */}
        <div
          style={{
            marginTop: 'var(--space-2)',
            fontSize: '0.6875rem',
            color: 'var(--text-muted)',
            textAlign: 'center',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {((soc * 13.5)).toFixed(1)} / 13.5 kWh
        </div>
      </div>
    </div>
  );
}
