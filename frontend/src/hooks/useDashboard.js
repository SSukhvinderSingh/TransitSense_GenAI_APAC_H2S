import { useState, useEffect } from 'react';
import { fetchStatsSummary, fetchRoutes, fetchZones, fetchAnomalies } from '../utils/api';

export function useDashboard() {
  const [summary, setSummary] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [zones, setZones] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [s, r, z, a] = await Promise.all([
          fetchStatsSummary(),
          fetchRoutes(),
          fetchZones(),
          fetchAnomalies(),
        ]);
        if (cancelled) return;
        setSummary(s);
        setRoutes(r);
        setZones(z);
        setAnomalies(a);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const selectedRoute = routes.find(r => r.selected) || routes[0];

  return { summary, routes, zones, anomalies, loading, error, selectedRoute };
}
