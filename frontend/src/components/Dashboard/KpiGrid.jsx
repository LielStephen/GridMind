import React from 'react';
import {
  Thermometer,
  ThermometerSun,
  DollarSign,
  Zap,
  Battery,
  Activity,
} from 'lucide-react';
import KpiCard from './KpiCard';

export default function KpiGrid({ current, deltas }) {
  const cards = [
    {
      icon: Thermometer,
      label: 'Indoor Temp',
      value: current.indoor_temp?.toFixed(1),
      unit: '°C',
      delta: deltas.indoor_temp,
      accentColor: 'var(--chart-indoor)',
      iconColor: 'var(--chart-indoor)',
    },
    {
      icon: ThermometerSun,
      label: 'Outdoor Temp',
      value: current.outdoor_temp?.toFixed(1),
      unit: '°C',
      delta: deltas.outdoor_temp,
      accentColor: 'var(--chart-outdoor)',
      iconColor: 'var(--chart-outdoor)',
    },
    {
      icon: DollarSign,
      label: 'Step Cost',
      value: `$${current.energy_cost?.toFixed(3)}`,
      unit: null,
      delta: null,
      accentColor: 'var(--color-success)',
      iconColor: 'var(--color-success)',
    },
    {
      icon: Zap,
      label: 'Net Load',
      value: current.net_consumption?.toFixed(0),
      unit: 'W',
      delta: null,
      accentColor: 'var(--chart-net)',
      iconColor: 'var(--chart-net)',
    },
    {
      icon: Battery,
      label: 'Battery SOC',
      value: (current.battery_soc * 100)?.toFixed(1),
      unit: '%',
      delta: deltas.battery_soc ? deltas.battery_soc * 100 : null,
      accentColor:
        current.battery_soc < 0.2
          ? 'var(--color-danger)'
          : current.battery_soc < 0.5
            ? 'var(--color-warning)'
            : 'var(--color-success)',
      iconColor:
        current.battery_soc < 0.2
          ? 'var(--color-danger)'
          : current.battery_soc < 0.5
            ? 'var(--color-warning)'
            : 'var(--color-success)',
    },
    {
      icon: Activity,
      label: 'Step Reward',
      value: current.reward?.toFixed(3),
      unit: null,
      delta: null,
      accentColor: current.reward >= 0 ? 'var(--chart-reward-pos)' : 'var(--chart-reward-neg)',
      iconColor: current.reward >= 0 ? 'var(--chart-reward-pos)' : 'var(--chart-reward-neg)',
    },
  ];

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
        gap: 'var(--space-4)',
      }}
    >
      {cards.map((card) => (
        <KpiCard key={card.label} {...card} />
      ))}
    </div>
  );
}
