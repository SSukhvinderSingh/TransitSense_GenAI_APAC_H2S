export function CardSkeleton({ lines = 2 }) {
  return (
    <div className="bg-surface rounded-lg p-4 animate-pulse">
      <div className="h-3 bg-surface-alt rounded w-1/3 mb-3" />
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-4 bg-surface-alt rounded w-full mb-2 last:mb-0" style={{ width: `${70 + i * 15}%` }} />
      ))}
    </div>
  );
}

export function ChartSkeleton({ height = 200 }) {
  return (
    <div className="bg-surface rounded-lg p-4 animate-pulse" style={{ height }}>
      <div className="h-3 bg-surface-alt rounded w-1/4 mb-4" />
      <div className="h-full bg-surface-alt rounded" style={{ height: 'calc(100% - 24px)' }} />
    </div>
  );
}

export function ListSkeleton({ rows = 5 }) {
  return (
    <div className="space-y-2 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 bg-surface rounded-lg">
          <div className="w-2 h-2 bg-surface-alt rounded-full" />
          <div className="h-4 bg-surface-alt rounded flex-1" />
          <div className="h-4 bg-surface-alt rounded w-16" />
        </div>
      ))}
    </div>
  );
}
