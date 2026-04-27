import { Link } from 'react-router-dom';
import { scoreBadge } from '../utils/format.js';

export default function BusinessCard({ business, onAddLead, isLead }) {
  const score = business.opportunity_score ?? 0;
  return (
    <div className="card flex flex-col gap-3 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div>
          <Link to={`/businesses/${business.id}`} className="text-lg font-semibold text-slate-900 hover:text-brand-700">
            {business.name}
          </Link>
          {business.category && (
            <div className="text-sm text-slate-500">{business.category}</div>
          )}
        </div>
        <span className={scoreBadge(score)}>
          {score}/100
        </span>
      </div>

      <div className="text-sm text-slate-600 space-y-1">
        {business.address && <div>📍 {business.address}</div>}
        {business.phone && <div>📞 {business.phone}</div>}
        {business.website ? (
          <div className="truncate">
            🌐{' '}
            <a href={business.website} target="_blank" rel="noreferrer" className="text-brand-700 hover:underline">
              {business.website}
            </a>
          </div>
        ) : (
          <div className="text-amber-700 font-medium">⚠ Sin sitio web</div>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {business.has_website ? (
          <span className={business.is_responsive ? 'badge-green' : 'badge-yellow'}>
            {business.is_responsive ? 'Responsivo' : 'No responsivo'}
          </span>
        ) : (
          <span className="badge-red">Sin web</span>
        )}
        {business.size_tier && (
          <span className="badge-indigo capitalize">{business.size_tier.replace('_', ' ')}</span>
        )}
        {business.rating != null && business.reviews_count != null && (
          <span className="badge-gray">
            ⭐ {business.rating.toFixed(1)} · {business.reviews_count} reseñas
          </span>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
        <Link to={`/businesses/${business.id}`} className="btn-secondary text-xs">
          Ver detalle
        </Link>
        {onAddLead && !isLead && (
          <button onClick={() => onAddLead(business)} className="btn-primary text-xs">
            Guardar como prospecto
          </button>
        )}
        {isLead && <span className="badge-green">En tus prospectos</span>}
      </div>
    </div>
  );
}
