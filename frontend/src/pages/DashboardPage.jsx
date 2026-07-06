import { useState } from 'react';
import { useDashboard } from '../hooks/useDashboard';
import KPIStrip from '../components/dashboard/KPIStrip';
import RouteList from '../components/dashboard/RouteList';
import PriorityChart from '../components/dashboard/PriorityChart';
import ForecastChart from '../components/dashboard/ForecastChart';
import AnomalyFeed from '../components/dashboard/AnomalyFeed';
import ZoneMap from '../components/dashboard/ZoneMap';
import QuickStats from '../components/dashboard/QuickStats';
import { CardSkeleton, ChartSkeleton, ListSkeleton } from '../components/shared/LoadingSkeleton';

export default function DashboardPage() {
  const { summary, routes, zones, anomalies, loading, error } = useDashboard();
  const [selectedRoute, setSelectedRoute] = useState(null);

  if (error) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="text-center">
          <p className="text-destructive text-sm mb-2">{error}</p>
          <p className="text-text-dim text-xs">Make sure the backend is running</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-4 space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-1"><ListSkeleton rows={8} /></div>
          <div className="lg:col-span-3 space-y-4">
            <ChartSkeleton height={200} />
            <ChartSkeleton height={200} />
          </div>
        </div>
      </div>
    );
  }

  const activeRoute = selectedRoute || routes?.[0]?.route_id || '219';

  return (
    <div className="p-4 space-y-4">
      <KPIStrip summary={summary} />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-1 space-y-4">
          <RouteList
            routes={routes}
            onSelect={setSelectedRoute}
            selectedId={activeRoute}
          />
          <QuickStats summary={summary} />
        </div>

        <div className="lg:col-span-3 space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <PriorityChart routes={routes} />
            <ForecastChart routeId={activeRoute} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ZoneMap zones={zones} />
            <AnomalyFeed anomalies={anomalies} />
          </div>
        </div>
      </div>
    </div>
  );
}
