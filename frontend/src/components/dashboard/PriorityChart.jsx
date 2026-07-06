import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts';

const barColors = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#22c55e'];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  if (!d) return null;
  return (
    <div className="bg-surface border border-border rounded-lg px-3 py-2 text-sm shadow-lg">
      <p className="font-medium">{d.route_id}</p>
      <p className="text-text-dim">Score: <span className="font-mono text-text">{d.score?.toFixed(2) ?? '—'}</span></p>
      <p className="text-text-dim">Delay: <span className="font-mono text-text">{d.contributing_factors?.avg_delay_min?.toFixed(1) ?? '—'}m</span></p>
      <p className="text-text-dim">On-Time: <span className="font-mono text-text">{d.contributing_factors?.on_time_pct?.toFixed(1) ?? '—'}%</span></p>
    </div>
  );
}

export default function PriorityChart({ routes }) {
  if (!routes || routes.length === 0) return null;

  const data = [...routes]
    .sort((a, b) => b.score - a.score)
    .slice(0, 10)
    .map(r => ({
      ...r,
      shortId: r.route_id.length > 8 ? r.route_id.slice(0, 8) + '…' : r.route_id,
    }));

  return (
    <div className="bg-surface rounded-xl border border-border p-4">
      <h3 className="text-sm font-medium text-text mb-4">Priority Ranking</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 8, top: 0, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="shortId" width={70} tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
          <Bar dataKey="score" radius={[0, 4, 4, 0]} maxBarSize={20}>
            {data.map((_, i) => (
              <Cell key={i} fill={barColors[i % barColors.length]} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
