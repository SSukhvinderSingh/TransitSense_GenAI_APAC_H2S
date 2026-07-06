import { AlertTriangle } from 'lucide-react';

export default function AnomalyFeed({ anomalies }) {
  if (!anomalies || anomalies.length === 0) return null;

  const displayed = anomalies.slice(0, 20);

  return (
    <div className="bg-surface rounded-xl border border-border p-4">
      <h3 className="text-sm font-medium text-text mb-3">Recent Anomalies</h3>
      <div className="flex items-center gap-2 px-2 pb-1.5 text-[10px] uppercase tracking-wider text-text-dim font-medium border-b border-border/50 mb-1.5">
        <span className="w-3" />
        <span className="min-w-[48px]">Trip</span>
        <span className="w-[40px]">Delay</span>
        <span className="flex-1">Reason</span>
        <span className="w-8" />
      </div>
      <div className="space-y-1.5">
        {displayed.map((a, i) => (
          <div key={i} className="flex items-center gap-2 py-1.5 px-2 rounded-lg hover:bg-bg/50 transition-colors">
            <AlertTriangle size={12} className={
              a.delay_min > 20 ? 'text-destructive' : a.delay_min > 10 ? 'text-warning' : 'text-text-dim'
            } />
            <span className="text-xs font-mono text-text-dim min-w-[48px]">{a.trip_id?.slice(0, 6) || ''}</span>
            <span className={`text-xs font-mono font-medium ${
              a.delay_min > 20 ? 'text-destructive' : a.delay_min > 10 ? 'text-warning' : 'text-text-dim'
            }`}>
              {a.delay_min > 0 ? `+${a.delay_min.toFixed(0)}m` : `${a.delay_min.toFixed(0)}m`}
            </span>
            <span className="text-xs text-text-dim flex-1 truncate">{a.reason || ''}</span>
            {a.source === 'synthetic' && (
              <span className="text-[10px] text-warning/70 px-1.5 py-0.5 rounded bg-warning/10">sim</span>
            )}
          </div>
        ))}
      </div>
      {anomalies.length > 20 && (
        <p className="text-xs text-text-dim text-center mt-3">+{anomalies.length - 20} more</p>
      )}
    </div>
  );
}
