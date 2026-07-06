export default function ProvenanceBadge({ text }) {
  if (!text) return null;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-warning/15 text-warning border border-warning/30">
      <span className="w-1.5 h-1.5 rounded-full bg-warning animate-pulse" style={{ animationDuration: '2s' }} />
      {text}
    </span>
  );
}
