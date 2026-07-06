export default function StatusDot({ status, size = 8 }) {
  const colors = {
    success: 'bg-success',
    warning: 'bg-warning',
    destructive: 'bg-destructive',
    muted: 'bg-muted',
    forecast: 'bg-forecast',
    primary: 'bg-primary',
  };
  return (
    <span
      className={`inline-block rounded-full ${colors[status] || 'bg-muted'}`}
      style={{ width: size, height: size, minWidth: size }}
    />
  );
}
