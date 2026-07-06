export default function MetricCard({ label, value, sub, icon: Icon, color = 'primary' }) {
  const borderColors = {
    primary: 'border-primary',
    success: 'border-success',
    warning: 'border-warning',
    destructive: 'border-destructive',
    forecast: 'border-forecast',
  };
  return (
    <div className={`bg-surface border-l-4 ${borderColors[color] || borderColors.primary} rounded-lg p-4`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-text-dim font-medium uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-semibold mt-1 font-mono">{value}</p>
          {sub && <p className="text-xs text-text-dim mt-1">{sub}</p>}
        </div>
        {Icon && <Icon size={20} className="text-muted mt-1" />}
      </div>
    </div>
  );
}
