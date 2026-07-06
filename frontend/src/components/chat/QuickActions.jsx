const ACTIONS = [
  { label: 'How is Secunderabad?', query: 'how is Secunderabad doing?' },
  { label: 'Worst routes', query: 'what are the worst routes right now?' },
  { label: 'Route 219 delay', query: 'why is route 219 always late?' },
  { label: 'Forecast 49M', query: 'forecast ridership for route 49M' },
  { label: 'Route status', query: 'what is the current status' },
];

export default function QuickActions({ onSelect, visible }) {
  if (!visible) return null;
  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {ACTIONS.map((a) => (
        <button
          key={a.label}
          onClick={() => onSelect(a.query)}
          className="px-3 py-1.5 text-xs font-medium rounded-full border border-border bg-surface hover:bg-surface-alt hover:border-primary/50 text-text-dim hover:text-text transition-colors cursor-pointer"
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}
