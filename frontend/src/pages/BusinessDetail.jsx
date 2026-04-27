import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { businessesApi, leadsApi } from '../services/api.js';
import { scoreBadge } from '../utils/format.js';

export default function BusinessDetail() {
  const { id } = useParams();
  const [business, setBusiness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingLead, setSavingLead] = useState(false);
  const [savedLeadId, setSavedLeadId] = useState(null);
  const [error, setError] = useState(null);

  const reload = async () => {
    setLoading(true);
    try {
      const [data, leads] = await Promise.all([businessesApi.detail(id), leadsApi.list()]);
      setBusiness(data);
      const existing = leads.find((l) => l.business.id === Number(id));
      if (existing) setSavedLeadId(existing.id);
    } catch (e) {
      setError(e.response?.data?.detail || 'No se pudo cargar el negocio');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
  }, [id]);

  const handleSaveLead = async () => {
    setSavingLead(true);
    try {
      const lead = await leadsApi.create({ business_id: Number(id) });
      setSavedLeadId(lead.id);
    } catch (e) {
      setError(e.response?.data?.detail || 'No se pudo guardar como prospecto');
    } finally {
      setSavingLead(false);
    }
  };

  if (loading) return <div className="text-slate-500">Cargando...</div>;
  if (error) return <div className="text-red-700">{error}</div>;
  if (!business) return null;

  const score = business.opportunity_score ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link to="/results" className="text-sm text-slate-500 hover:text-brand-700">← Volver a resultados</Link>
          <h1 className="text-2xl font-bold mt-1">{business.name}</h1>
          {business.category && (
            <div className="text-slate-500">{business.category}</div>
          )}
        </div>
        <div className="flex gap-2">
          {savedLeadId ? (
            <Link to="/leads" className="btn-secondary">Ver en mis prospectos</Link>
          ) : (
            <button onClick={handleSaveLead} disabled={savingLead} className="btn-primary">
              {savingLead ? 'Guardando...' : 'Guardar como prospecto'}
            </button>
          )}
          {business.google_url && (
            <a href={business.google_url} target="_blank" rel="noreferrer" className="btn-secondary">
              Abrir en Google Maps
            </a>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-3">Información de contacto</h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <Field label="Dirección" value={business.address} />
              <Field label="Ciudad" value={business.city} />
              <Field label="Teléfono" value={business.phone} />
              <Field
                label="Sitio web"
                value={
                  business.website ? (
                    <a href={business.website} target="_blank" rel="noreferrer" className="text-brand-700 hover:underline">
                      {business.website}
                    </a>
                  ) : (
                    'Sin sitio web'
                  )
                }
              />
              <Field
                label="Rating"
                value={
                  business.rating != null
                    ? `${business.rating.toFixed(1)} ⭐ (${business.reviews_count ?? 0} reseñas)`
                    : '–'
                }
              />
              <Field label="Tamaño estimado" value={business.size_tier?.replace('_', ' ')} />
            </dl>
            {business.description && (
              <p className="mt-4 text-sm text-slate-700 leading-relaxed">{business.description}</p>
            )}
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold mb-3">Análisis de presencia digital</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
              <Stat label="Estado del sitio" value={business.website_status || 'sin sitio'} />
              <Stat label="Responsivo" value={business.is_responsive == null ? '–' : business.is_responsive ? 'Sí' : 'No'} />
              <Stat
                label="Tiempo de carga"
                value={business.page_load_seconds != null ? `${business.page_load_seconds.toFixed(2)} s` : '–'}
              />
            </div>
            {business.detected_technologies?.length > 0 && (
              <div className="mt-4">
                <div className="label">Tecnologías detectadas</div>
                <div className="flex flex-wrap gap-1.5">
                  {business.detected_technologies.map((t) => (
                    <span key={t} className="badge-indigo">{t}</span>
                  ))}
                </div>
              </div>
            )}
            {business.seo_meta && (
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <Field label="Title" value={business.seo_meta.title} />
                <Field label="Meta description" value={business.seo_meta.description} />
                <Field label="HTTPS" value={business.seo_meta.has_https ? 'Sí' : 'No'} />
                <Field label="Favicon" value={business.seo_meta.has_favicon ? 'Sí' : 'No'} />
                <Field label="Imágenes sin alt" value={business.seo_meta.images_without_alt ?? '-'} />
                <Field label="H1 detectados" value={business.seo_meta.h1_count ?? '-'} />
              </div>
            )}
            {business.social_links && Object.keys(business.social_links).length > 0 && (
              <div className="mt-4">
                <div className="label">Redes sociales detectadas</div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(business.social_links).map(([net, url]) => (
                    <a
                      key={net}
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="badge-gray hover:bg-brand-100 hover:text-brand-700"
                    >
                      {net}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>

          {business.attributes?.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-3">Atributos</h2>
              <div className="flex flex-wrap gap-1.5">
                {business.attributes.map((a) => (
                  <span key={a} className="badge-gray">{a}</span>
                ))}
              </div>
            </div>
          )}

          {business.opening_hours && Object.keys(business.opening_hours).length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-3">Horarios</h2>
              <ul className="text-sm divide-y divide-slate-100">
                {Object.entries(business.opening_hours).map(([day, hours]) => (
                  <li key={day} className="py-1.5 flex justify-between">
                    <span className="font-medium">{day}</span>
                    <span className="text-slate-600">{hours}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {business.photos?.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-3">Fotos</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {business.photos.slice(0, 6).map((src, i) => (
                  <img
                    key={i}
                    src={src}
                    alt={`foto-${i}`}
                    className="rounded-lg object-cover w-full h-32"
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        <aside className="space-y-6">
          <div className="card">
            <div className="text-xs uppercase tracking-wide text-slate-500">Score de oportunidad</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-4xl font-bold">{score}</span>
              <span className="text-slate-400">/100</span>
            </div>
            <span className={`mt-2 ${scoreBadge(score)}`}>
              {score >= 70 ? 'Alta oportunidad' : score >= 40 ? 'Oportunidad media' : 'Baja oportunidad'}
            </span>
            {business.opportunity_reasons?.length > 0 && (
              <ul className="mt-4 list-disc list-inside text-sm text-slate-700 space-y-1">
                {business.opportunity_reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            )}
          </div>

          <div className="card">
            <h3 className="font-semibold mb-2">Sugerencias de venta</h3>
            <ul className="text-sm text-slate-700 space-y-2">
              {!business.has_website && (
                <li>📌 Ofrecé un sitio web vitrina con catálogo y formulario de contacto.</li>
              )}
              {business.has_website && business.is_responsive === false && (
                <li>📱 Proponé un rediseño responsive: la mayoría de las visitas vienen del celular.</li>
              )}
              {business.seo_meta && !business.seo_meta.description && (
                <li>🔍 Mejorá el SEO básico: meta descripción y títulos de cada página.</li>
              )}
              {business.page_load_seconds && business.page_load_seconds > 3 && (
                <li>⚡ Optimizá la velocidad de carga (imágenes, hosting, caché).</li>
              )}
              {(!business.social_links || Object.keys(business.social_links).length === 0) && (
                <li>📲 Integrá redes sociales y WhatsApp en el sitio.</li>
              )}
              {business.detected_technologies?.includes('WordPress') && (
                <li>🛠 Si quedó en una versión vieja de WordPress, proponé migración a algo moderno.</li>
              )}
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-0.5 text-slate-800">{value || '–'}</div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3 ring-1 ring-slate-200">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 font-semibold text-slate-800 capitalize">{value}</div>
    </div>
  );
}
