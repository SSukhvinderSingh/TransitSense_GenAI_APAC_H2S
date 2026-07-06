import { Clock, Target, Route, AlertTriangle } from 'lucide-react';
import MetricCard from '../shared/MetricCard';

export default function KPIStrip({ summary }) {
  if (!summary) return null;
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <MetricCard
        label="Avg Delay"
        value={`${summary.avg_delay_min?.toFixed(1) || '—'}m`}
        sub="across all routes"
        icon={Clock}
        color={summary.avg_delay_min > 10 ? 'destructive' : summary.avg_delay_min > 5 ? 'warning' : 'success'}
      />
      <MetricCard
        label="On-Time Rate"
        value={`${summary.on_time_pct?.toFixed(1) || '—'}%`}
        sub="arrivals within 5min"
        icon={Target}
        color={summary.on_time_pct < 60 ? 'destructive' : summary.on_time_pct < 80 ? 'warning' : 'success'}
      />
      <MetricCard
        label="Routes"
        value={summary.total_routes || '—'}
        sub="being monitored"
        icon={Route}
        color="primary"
      />
      <MetricCard
        label="Anomalies"
        value={summary.total_anomalies || '—'}
        sub="in last 24h"
        icon={AlertTriangle}
        color={summary.total_anomalies > 100 ? 'destructive' : 'warning'}
      />
    </div>
  );
}
