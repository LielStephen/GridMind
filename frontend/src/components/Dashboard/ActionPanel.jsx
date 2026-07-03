import React, { useState } from 'react';
import {
  CircleDot,
  Snowflake,
  PowerOff,
  BatteryCharging,
  Unplug,
} from 'lucide-react';

const ACTIONS = [
  {
    id: 0,
    label: 'Idle',
    icon: CircleDot,
    desc: 'No action',
    color: 'var(--text-muted)',
    bgHover: 'var(--surface-3)',
  },
  {
    id: 1,
    label: 'AC On',
    icon: Snowflake,
    desc: 'Enable cooling',
    color: 'var(--chart-indoor)',
    bgHover: 'var(--color-info-muted)',
  },
  {
    id: 2,
    label: 'AC Off',
    icon: PowerOff,
    desc: 'Disable cooling',
    color: 'var(--text-secondary)',
    bgHover: 'var(--surface-3)',
  },
  {
    id: 3,
    label: 'Charge',
    icon: BatteryCharging,
    desc: 'Store energy',
    color: 'var(--color-success)',
    bgHover: 'var(--color-success-muted)',
  },
  {
    id: 4,
    label: 'Discharge',
    icon: Unplug,
    desc: 'Use stored',
    color: 'var(--color-warning)',
    bgHover: 'var(--color-warning-muted)',
  },
];

export default function ActionPanel({ onAction, actionLog, terminated }) {
  const [lastPressed, setLastPressed] = useState(null);

  const handleAction = (actionId) => {
    if (terminated) return;
    setLastPressed(actionId);
    onAction(actionId);
    setTimeout(() => setLastPressed(null), 300);
  };

  return (
    <div className="card">
      <div className="card-inner" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <h2 style={{ fontSize: '0.875rem', fontWeight: 600 }}>
          Manual Override
        </h2>

        {/* Action buttons */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 'var(--space-2)',
          }}
        >
          {/* Idle spans full width */}
          <button
            onClick={() => handleAction(0)}
            disabled={terminated}
            style={{
              gridColumn: 'span 2',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 'var(--space-2)',
              padding: 'var(--space-3)',
              background:
                lastPressed === 0 ? ACTIONS[0].bgHover : 'var(--surface-2)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              color: ACTIONS[0].color,
              fontSize: '0.8125rem',
              fontWeight: 500,
              fontFamily: 'var(--font-sans)',
              cursor: terminated ? 'not-allowed' : 'pointer',
              opacity: terminated ? 0.4 : 1,
              transition: 'all var(--duration-fast) var(--ease-out)',
            }}
          >
            <CircleDot size={14} />
            Idle (No Action)
          </button>

          {ACTIONS.slice(1).map((action) => {
            const Icon = action.icon;
            const isActive = lastPressed === action.id;
            return (
              <button
                key={action.id}
                onClick={() => handleAction(action.id)}
                disabled={terminated}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 'var(--space-1)',
                  padding: 'var(--space-3) var(--space-2)',
                  background: isActive ? action.bgHover : 'var(--surface-2)',
                  border: `1px solid ${isActive ? action.color : 'var(--border-default)'}`,
                  borderRadius: 'var(--radius-md)',
                  color: action.color,
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  fontFamily: 'var(--font-sans)',
                  cursor: terminated ? 'not-allowed' : 'pointer',
                  opacity: terminated ? 0.4 : 1,
                  transition: 'all var(--duration-fast) var(--ease-out)',
                  transform: isActive ? 'scale(0.96)' : 'scale(1)',
                }}
              >
                <Icon size={16} />
                {action.label}
              </button>
            );
          })}
        </div>

        {/* Action Log */}
        {actionLog.length > 0 && (
          <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: 'var(--space-3)' }}>
            <span
              style={{
                fontSize: '0.6875rem',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                display: 'block',
                marginBottom: 'var(--space-2)',
              }}
            >
              Action Log
            </span>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-1)',
                maxHeight: 140,
                overflowY: 'auto',
              }}
            >
              {actionLog.slice(0, 6).map((entry, i) => (
                <div
                  key={entry.timestamp + i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '4px var(--space-2)',
                    borderRadius: 'var(--radius-sm)',
                    background: i === 0 ? 'var(--surface-2)' : 'transparent',
                    fontSize: '0.6875rem',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  <span style={{ color: 'var(--text-muted)' }}>
                    #{entry.step}
                  </span>
                  <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                    {entry.label}
                  </span>
                  <span
                    style={{
                      color:
                        entry.reward >= 0
                          ? 'var(--color-success)'
                          : 'var(--color-danger)',
                    }}
                  >
                    {entry.reward >= 0 ? '+' : ''}{entry.reward.toFixed(3)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
