import L from 'leaflet';
import { useEffect } from 'react';
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet';
import { Link } from 'react-router-dom';

// Fix para iconos por defecto de Leaflet con bundlers (Vite no resuelve los assets internos).
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function colorForScore(score) {
  if (score == null) return '#94a3b8';
  if (score >= 80) return '#dc2626';
  if (score >= 60) return '#f97316';
  if (score >= 40) return '#facc15';
  if (score >= 20) return '#22c55e';
  return '#0ea5e9';
}

function FitBounds({ businesses }) {
  const map = useMap();
  useEffect(() => {
    const points = businesses
      .filter((b) => b.latitude && b.longitude)
      .map((b) => [b.latitude, b.longitude]);
    if (points.length === 0) return;
    const bounds = L.latLngBounds(points);
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
  }, [businesses, map]);
  return null;
}

export default function Map({ businesses, height = 480, center }) {
  const fallbackCenter = center || [-32.8908, -68.8272];
  return (
    <div className="rounded-xl overflow-hidden ring-1 ring-slate-200 shadow-sm" style={{ height }}>
      <MapContainer center={fallbackCenter} zoom={12} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {businesses
          .filter((b) => b.latitude && b.longitude)
          .map((b) => (
            <CircleMarker
              key={b.id}
              center={[b.latitude, b.longitude]}
              radius={Math.max(6, Math.min(14, (b.opportunity_score || 30) / 8))}
              pathOptions={{
                color: colorForScore(b.opportunity_score),
                weight: 1.5,
                fillColor: colorForScore(b.opportunity_score),
                fillOpacity: 0.65,
              }}
            >
              <Popup>
                <div className="space-y-1">
                  <div className="font-semibold">{b.name}</div>
                  {b.category && <div className="text-xs text-slate-600">{b.category}</div>}
                  {b.address && <div className="text-xs">{b.address}</div>}
                  <div className="text-xs">
                    <span className="font-semibold">Oportunidad:</span> {b.opportunity_score ?? '–'}
                  </div>
                  <Link
                    to={`/businesses/${b.id}`}
                    className="text-brand-700 text-xs font-semibold hover:underline"
                  >
                    Ver detalle →
                  </Link>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        <FitBounds businesses={businesses} />
      </MapContainer>
    </div>
  );
}
