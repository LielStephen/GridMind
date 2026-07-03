import React, { useEffect, useRef } from 'react';

export default function KpiCard({ icon: Icon, label, value, unit, delta, accentColor, iconColor }) {
  const cardRef = useRef(null);
  const prevValue = useRef(value);

  useEffect(() => {
    if (prevValue.current !== value && cardRef.current) {
      cardRef.current.classList.remove('value-updated');
      // Force reflow
      void cardRef.current.offsetWidth;
      cardRef.current.classList.add('value-updated');
    }
    prevValue.current = value;
  }, [value]);

  const deltaDisplay = delta !== undefined && delta !== null && delta !== 0;
  const deltaPositive = delta > 0;

  return (
    <div
      ref={cardRef}
      className="card"
      style={{
        borderTop: `2px solid ${accentColor || 'var(--border-subtle)'}`,
        minWidth: 0,
      }}
    >
      <div className="card-inner" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 500,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            {label}
          </span>
          {Icon && (
            <Icon
              size={16}
              style={{
                color: iconColor || accentColor || 'var(--text-muted)',
                opacity: 0.8,
              }}
            />
          )}
        </div>

        {/* Value */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)' }}>
          <span
            className="data-value"
            style={{
              fontSize: '1.625rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1,
            }}
          >
            {value}
          </span>
          {unit && (
            <span
              style={{
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
                fontWeight: 500,
              }}
            >
              {unit}
            </span>
          )}
        </div>

        {/* Delta */}
        {deltaDisplay && (
          <span
            style={{
              fontSize: '0.6875rem',
              fontWeight: 500,
              color: deltaPositive ? 'var(--color-success)' : 'var(--color-danger)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {deltaPositive ? '▲' : '▼'} {Math.abs(delta).toFixed(2)}
          </span>
        )}
      </div>
    </div>
  );
}
