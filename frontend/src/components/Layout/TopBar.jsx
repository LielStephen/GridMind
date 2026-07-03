import React from 'react';
import { Clock, Hash, AlertCircle } from 'lucide-react';

export default function TopBar({ step, clockDisplay, terminated, occupancy, price }) {
  const progress = Math.min((step / 96) * 100, 100);

  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 'var(--space-3) var(--space-6)',
        background: 'var(--surface-0)',
        borderBottom: '1px solid var(--border-subtle)',
        height: 52,
        gap: 'var(--space-4)',
      }}
    >
      {/* Left: clock + step */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-5)' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            fontFamily: 'var(--font-mono)',
            fontSize: '1.125rem',
            fontWeight: 500,
            color: 'var(--text-primary)',
            letterSpacing: '-0.01em',
          }}
        >
          <Clock size={15} style={{ color: 'var(--text-muted)' }} />
          {clockDisplay}
        </div>

        <div className="badge">
          <Hash size={10} />
          Step {step} / 96
        </div>

        {terminated && (
          <div
            className="badge"
            style={{
              background: 'var(--color-warning-muted)',
              borderColor: 'var(--color-warning)',
              color: 'var(--color-warning)',
            }}
          >
            <AlertCircle size={10} />
            Episode Complete
          </div>
        )}
      </div>

      {/* Center: progress bar */}
      <div
        style={{
          flex: 1,
          maxWidth: 360,
          height: 4,
          background: 'var(--surface-2)',
          borderRadius: 2,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progress}%`,
            background: terminated
              ? 'var(--color-warning)'
              : 'linear-gradient(90deg, var(--accent-strong), var(--accent))',
            borderRadius: 2,
            transition: 'width var(--duration-normal) var(--ease-out)',
          }}
        />
      </div>

      {/* Right: context badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <div
          className="badge"
          style={
            occupancy
              ? {
                  background: 'var(--color-success-muted)',
                  borderColor: 'var(--color-success)',
                  color: 'var(--color-success)',
                }
              : {}
          }
        >
          {occupancy ? '● Occupied' : '○ Vacant'}
        </div>

        <div className="badge" style={{ fontFamily: 'var(--font-mono)' }}>
          ${price?.toFixed(2)}/kWh
        </div>
      </div>
    </header>
  );
}
