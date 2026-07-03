import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
} from 'recharts';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  return (
    <div
      style={{
        background: 'var(--surface-2)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 14px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
      }}
    >
      <p
        style={{
          fontSize: '0.6875rem',
          color: 'var(--text-muted)',
          marginBottom: 6,
          fontWeight: 500,
        }}
      >
        Step {label}
      </p>
      {payload.map((entry) => (
        <div
          key={entry.name}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
            padding: '2px 0',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: entry.color,
                display: 'inline-block',
              }}
            />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              {entry.name}
            </span>
          </div>
          <span
            className="data-value"
            style={{
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
            }}
          >
            {Number(entry.value).toFixed(1)}°C
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ThermalChart({ history }) {
  const data = history.map((h) => ({
    step: h.step,
    indoor: h.indoor_temp,
    outdoor: h.outdoor_temp,
  }));

  return (
    <div className="card" style={{ gridColumn: 'span 2' }}>
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
            Thermal Profile
          </h2>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-4)',
              fontSize: '0.6875rem',
              color: 'var(--text-muted)',
            }}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span
                style={{
                  width: 10,
                  height: 3,
                  borderRadius: 2,
                  background: 'var(--chart-indoor)',
                  display: 'inline-block',
                }}
              />
              Indoor
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span
                style={{
                  width: 10,
                  height: 3,
                  borderRadius: 2,
                  background: 'var(--chart-outdoor)',
                  display: 'inline-block',
                }}
              />
              Outdoor
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 2,
                  background: 'var(--chart-comfort-band)',
                  border: '1px solid var(--accent-muted)',
                  display: 'inline-block',
                }}
              />
              Comfort Band
            </span>
          </div>
        </div>

        <div style={{ width: '100%', height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
              <CartesianGrid
                strokeDasharray="none"
                stroke="var(--border-subtle)"
                vertical={false}
              />
              {/* Comfort band 20-24°C */}
              <ReferenceArea
                y1={20}
                y2={24}
                fill="var(--accent)"
                fillOpacity={0.04}
                stroke="none"
              />
              <XAxis
                dataKey="step"
                stroke="var(--text-muted)"
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                axisLine={{ stroke: 'var(--border-subtle)' }}
                tickLine={false}
              />
              <YAxis
                stroke="var(--text-muted)"
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                axisLine={false}
                tickLine={false}
                domain={['auto', 'auto']}
                tickFormatter={(v) => `${v}°`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="indoor"
                stroke="var(--chart-indoor)"
                strokeWidth={2}
                dot={false}
                name="Indoor"
                activeDot={{ r: 4, strokeWidth: 0 }}
              />
              <Line
                type="monotone"
                dataKey="outdoor"
                stroke="var(--chart-outdoor)"
                strokeWidth={1.5}
                dot={false}
                name="Outdoor"
                strokeDasharray="6 3"
                activeDot={{ r: 3, strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
