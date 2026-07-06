import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceArea, CartesianGrid } from 'recharts';
import { fetchForecast } from '../../utils/api';
import { ChartSkeleton } from '../shared/LoadingSkeleton';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface border border-border rounded-lg px-3 py-2 text-sm shadow-lg">
      <p className="text-text-dim text-xs">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="font-mono text-xs" style={{ color: p.color }}>
          {p.name}: {p.value != null ? p.value.toFixed(2) : '—'}
        </p>
      ))}
    </div>
  );
}

export default function ForecastChart({ routeId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!routeId) return;
    setLoading(true);
    fetchForecast(routeId)
      .then(d => setData(d))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [routeId]);

  if (loading) return <ChartSkeleton height={240} />;
  if (error) return (
    <div className="bg-surface rounded-xl border border-border p-6 text-center text-text-dim text-sm">
      Forecast unavailable: {error}
    </div>
  );
  if (!data || data.low_confidence) return (
    <div className="bg-surface rounded-xl border border-border p-6 text-center text-text-dim text-sm">
      Insufficient data for forecast
    </div>
  );

  const chartData = (data.forecast || [])
    .filter(f => f.value != null)
    .map(f => ({
      date: f.date?.slice(5) || '',
      forecast: f.value,
      upper: f.value + (f.value * 0.15),
      lower: Math.max(0, f.value - (f.value * 0.15)),
    }));

  return (
    <div className="bg-surface rounded-xl border border-border p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-text">
          Forecast — Route {routeId}
        </h3>
        <span className="text-[10px] text-text-dim font-mono">{data.model_version}</span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceArea y1="lower" y2="upper" fill="#8b5cf6" fillOpacity={0.08} />
          <Line type="monotone" dataKey="forecast" stroke="#8b5cf6" strokeWidth={2} dot={false} strokeDasharray="4 3" name="Forecast" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
