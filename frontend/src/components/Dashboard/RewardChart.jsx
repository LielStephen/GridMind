import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

function MiniTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const val = payload[0].value;
  return (
    <div
      style={{
        background: 'var(--surface-2)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-sm)',
        padding: '4px 8px',
        fontSize: '0.6875rem',
        fontFamily: 'var(--font-mono)',
        color: 'var(--text-primary)',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
      }}
    >
      {Number(val).toFixed(2)}
    </div>
  );
}

export default function RewardChart({ history, cumulativeReward }) {
  const data = useMemo(() => {
    let cumulative = 0;
    return history.map((h) => {
      cumulative += h.reward || 0;
      return { step: h.step, cumReward: cumulative };
    });
  }, [history]);

  const trending = cumulativeReward >= 0;
  const strokeColor = trending ? 'var(--chart-reward-pos)' : 'var(--chart-reward-neg)';
  const gradId = 'rewardGrad';

  return (
    <div className="card">
      <div className="card-inner">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 'var(--space-3)',
          }}
        >
          <h2 style={{ fontSize: '0.875rem', fontWeight: 600 }}>
            Cumulative Reward
          </h2>
          <span
            className="data-value"
            style={{
              fontSize: '1.25rem',
              fontWeight: 700,
              color: strokeColor,
            }}
          >
            {cumulativeReward.toFixed(2)}
          </span>
        </div>

        <div style={{ width: '100%', height: 100 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={strokeColor} stopOpacity={0.25} />
                  <stop offset="100%" stopColor={strokeColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <Tooltip content={<MiniTooltip />} />
              <Area
                type="monotone"
                dataKey="cumReward"
                stroke={strokeColor}
                fill={`url(#${gradId})`}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 3, strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
