import React from 'react';

export default function StatusDot({ status = 'default', size = 8, pulse = false }) {
  const colors = {
    success: 'var(--color-success)',
    warning: 'var(--color-warning)',
    danger: 'var(--color-danger)',
    info: 'var(--accent)',
    default: 'var(--text-muted)',
  };

  const color = colors[status] || colors.default;

  return (
    <span
      style={{
        display: 'inline-block',
        width: size,
        height: size,
        borderRadius: '50%',
        backgroundColor: color,
        boxShadow: pulse ? `0 0 0 3px ${color}33` : 'none',
        animation: pulse ? 'pulse-subtle 2s ease-in-out infinite' : 'none',
        flexShrink: 0,
      }}
    />
  );
}
