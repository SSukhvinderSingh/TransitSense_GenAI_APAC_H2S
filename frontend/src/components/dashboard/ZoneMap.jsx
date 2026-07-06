import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { ChartSkeleton } from '../shared/LoadingSkeleton';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export default function ZoneMap({ zones }) {
  const [ready, setReady] = useState(false);
  useEffect(() => { setReady(true); }, []);

  if (!ready) return <ChartSkeleton height={240} />;
  if (!zones || zones.length === 0) {
    return (
      <div className="bg-surface rounded-xl border border-border p-6 text-center text-text-dim text-sm h-[240px] flex items-center justify-center">
        Map data unavailable
      </div>
    );
  }

  const center = [17.3850, 78.4867];

  return (
    <div className="bg-surface rounded-xl border border-border overflow-hidden" style={{ height: 240 }}>
      <MapContainer center={center} zoom={11} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {zones.slice(0, 20).map((z, i) => {
          if (!z.lat || !z.lon) return null;
          return (
            <Marker key={z.name || i} position={[z.lat, z.lon]}>
              <Popup>
                <div className="text-sm">
                  <strong>{z.name}</strong><br />
                  {z.route_count} routes
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
