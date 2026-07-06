export function fmtDelay(minutes) {
  if (minutes == null) return '—';
  if (minutes < 0) return `${Math.abs(minutes)}m early`;
  return `${minutes.toFixed(1)}m`;
}

export function fmtPct(value) {
  if (value == null) return '—';
  return `${value.toFixed(1)}%`;
}

export function fmtNumber(n) {
  if (n == null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export function statusColor(delay) {
  if (delay == null) return 'text-muted';
  if (delay <= 5) return 'text-success';
  if (delay <= 15) return 'text-warning';
  return 'text-destructive';
}

export function routeStatusColor(delay) {
  if (delay == null) return 'bg-muted';
  if (delay <= 5) return 'bg-success';
  if (delay <= 15) return 'bg-warning';
  return 'bg-destructive';
}

export function scoreColor(score) {
  if (score == null) return 'text-muted';
  if (score < 3) return 'text-success';
  if (score < 6) return 'text-warning';
  return 'text-destructive';
}
