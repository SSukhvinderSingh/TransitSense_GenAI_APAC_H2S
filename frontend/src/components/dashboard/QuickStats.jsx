import { Clock, Target, Users, Bus } from 'lucide-react';

export default function QuickStats({ summary }) {
  if (!summary) return null;

  const stats = [
    { label: 'Avg Delay', value: `${summary.avg_delay_min?.toFixed(1) || '—'}m`, icon: Clock, color: 'text-warning' },
    { label: 'On-Time', value: `${summary.on_time_pct?.toFixed(0) || '—'}%`, icon: Target, color: 'text-success' },
    { label: 'Ridership', value: summary.total_ridership ? `${(summary.total_ridership / 1000).toFixed(0)}K` : '—', icon: Users, color: 'text-primary' },
    { label: 'Routes', value: summary.total_routes || '—', icon: Bus, color: 'text-secondary' },
  ];

  return (
    <div className="grid grid-cols-2 gap-2">
      {stats.map(s => (
        <div key={s.label} className="bg-surface rounded-lg border border-border p-3 flex items-center gap-3">
          <div className={`${s.color} bg-${s.color}/10 p-2 rounded-lg`}>
            <s.icon size={16} />
          </div>
          <div>
            <p className="text-xs text-text-dim">{s.label}</p>
            <p className="text-sm font-semibold font-mono">{s.value}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
