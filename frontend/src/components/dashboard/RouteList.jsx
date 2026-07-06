import { useState } from 'react';
import { Search } from 'lucide-react';
import StatusDot from '../shared/StatusDot';
import { fmtDelay } from '../../utils/format';

function delayStatus(delay) {
  if (delay == null) return 'muted';
  if (delay <= 5) return 'success';
  if (delay <= 15) return 'warning';
  return 'destructive';
}

export default function RouteList({ routes, onSelect, selectedId }) {
  const [filter, setFilter] = useState('');

  const filtered = routes.filter(r =>
    r.route_id?.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="bg-surface rounded-xl border border-border overflow-hidden">
      <div className="p-3 border-b border-border">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Find route..."
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-bg border border-border text-text text-sm placeholder-text-dim focus:outline-none focus:border-primary transition-colors"
          />
        </div>
      </div>
      <div className="overflow-y-auto" style={{ maxHeight: 'calc(100vh - 320px)' }}>
        {filtered.map(r => (
          <button
            key={r.route_id}
            onClick={() => onSelect?.(r.route_id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-surface-alt transition-colors border-b border-border/50 last:border-0 cursor-pointer ${
              selectedId === r.route_id ? 'bg-surface-alt' : ''
            }`}
          >
            <StatusDot status={delayStatus(r.avg_delay_min)} size={8} />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-text truncate">{r.route_id}</div>
              <div className="text-xs text-text-dim">{r.ridership > 0 ? `${(r.ridership / 1000).toFixed(0)}K riders` : '—'}</div>
            </div>
            <div className={`text-sm font-mono font-medium text-right ${delayStatus(r.avg_delay_min) === 'success' ? 'text-success' : delayStatus(r.avg_delay_min) === 'warning' ? 'text-warning' : 'text-destructive'}`}>
              {fmtDelay(r.avg_delay_min)}
            </div>
          </button>
        ))}
        {filtered.length === 0 && (
          <div className="p-6 text-center text-text-dim text-sm">No routes match "{filter}"</div>
        )}
      </div>
    </div>
  );
}
