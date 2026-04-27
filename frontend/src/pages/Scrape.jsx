import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { scrapingApi } from '../services/api.js';
import { formatDate, jobStatusBadge, jobStatusLabel } from '../utils/format.js';

const PRESETS = [
  {
    label: 'Mendoza Centro',
    url: 'https://www.google.com/maps/@-32.8908,-68.8272,15z',
    keyword: 'restaurantes',
  },
  {
    label: 'Buenos Aires - Palermo',
    url: 'https://www.google.com/maps/@-34.5889,-58.4302,15z',
    keyword: 'gimnasios',
  },
  {
    label: 'Mendoza - Godoy Cruz',
    url: 'https://www.google.com/maps/@-32.9255,-68.8392,15z',
    keyword: 'peluquerías',
  },
];

export default function Scrape() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    source_url: '',
    keyword: 'restaurantes',
    radius_km: 2,
    max_results: 30,
    analyze_websites: true,
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [activeJob, setActiveJob] = useState(null);
  const [recentJobs, setRecentJobs] = useState([]);

  const update = (key, value) => setForm({ ...form, [key]: value });

  const refreshJobs = async () => {
    try {
      const data = await scrapingApi.listJobs();
      setRecentJobs(data);
      if (activeJob) {
        const fresh = data.find((j) => j.id === activeJob.id);
        if (fresh) setActiveJob(fresh);
      }
    } catch (e) {
      // noop
    }
  };

  useEffect(() => {
    refreshJobs();
    const id = setInterval(refreshJobs, 4000);
    return () => clearInterval(id);
  }, [activeJob?.id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const job = await scrapingApi.createJob(form);
      setActiveJob(job);
      refreshJobs();
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo crear el job');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <div className="card">
          <h1 className="text-2xl font-bold mb-1">Nuevo scraping</h1>
          <p className="text-sm text-slate-500 mb-6">
            Pegá una URL de Google Maps centrada en la zona objetivo y elegí qué buscar.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">URL de Google Maps</label>
              <input
                className="input"
                placeholder="https://www.google.com/maps/@-32.8908,-68.8272,15z"
                required
                value={form.source_url}
                onChange={(e) => update('source_url', e.target.value)}
              />
              <p className="mt-1 text-xs text-slate-500">
                Tip: abrí Google Maps, centrá la zona y copiá la URL del navegador.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Palabra clave</label>
                <input
                  className="input"
                  required
                  value={form.keyword}
                  onChange={(e) => update('keyword', e.target.value)}
                  placeholder="restaurantes, gimnasios, peluquerías..."
                />
              </div>
              <div>
                <label className="label">Radio (km)</label>
                <select
                  className="input"
                  value={form.radius_km}
                  onChange={(e) => update('radius_km', Number(e.target.value))}
                >
                  <option value={1}>1 km</option>
                  <option value={2}>2 km</option>
                  <option value={5}>5 km</option>
                  <option value={10}>10 km</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Máximo de resultados</label>
                <input
                  type="number"
                  min={1}
                  max={120}
                  className="input"
                  value={form.max_results}
                  onChange={(e) => update('max_results', Number(e.target.value))}
                />
                <p className="mt-1 text-xs text-slate-500">
                  Tip: empezá con 10-20 para una prueba rápida (~1-2 min).
                </p>
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-slate-300"
                    checked={form.analyze_websites}
                    onChange={(e) => update('analyze_websites', e.target.checked)}
                  />
                  Analizar sitios web (SEO, responsividad, tecnologías)
                </label>
              </div>
            </div>

            {error && (
              <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="flex flex-wrap gap-2 pt-2">
              <button type="submit" disabled={submitting} className="btn-primary">
                {submitting ? 'Lanzando...' : 'Iniciar scraping'}
              </button>
              {activeJob?.status === 'completed' && (
                <button type="button" onClick={() => navigate('/results')} className="btn-secondary">
                  Ver resultados →
                </button>
              )}
            </div>
          </form>

          {activeJob && (
            <div className="mt-6 rounded-lg border border-slate-200 p-4 bg-slate-50">
              <div className="flex items-center justify-between mb-2">
                <div className="font-semibold text-slate-800">Job #{activeJob.id}</div>
                <span className={jobStatusBadge(activeJob.status)}>
                  {jobStatusLabel(activeJob.status)}
                </span>
              </div>
              <div className="w-full h-2 bg-slate-200 rounded">
                <div
                  className="h-2 bg-brand-600 rounded transition-all"
                  style={{ width: `${activeJob.progress || 0}%` }}
                />
              </div>
              <div className="mt-2 flex justify-between text-xs text-slate-600">
                <span>Negocios encontrados: {activeJob.total_found}</span>
                <span>{activeJob.progress || 0}%</span>
              </div>
              {activeJob.error_message && (
                <div className="mt-2 text-sm text-red-700">{activeJob.error_message}</div>
              )}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="font-semibold mb-3">Atajos rápidos (zonas precargadas)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => setForm({ ...form, source_url: p.url, keyword: p.keyword })}
                className="rounded-lg border border-slate-200 p-3 text-left hover:border-brand-400 hover:bg-brand-50 transition-colors"
              >
                <div className="font-medium text-sm">{p.label}</div>
                <div className="text-xs text-slate-500 mt-1">{p.keyword}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="card h-fit">
        <h2 className="font-semibold mb-3">Mis últimos jobs</h2>
        <ul className="divide-y divide-slate-100">
          {recentJobs.slice(0, 8).map((job) => (
            <li key={job.id} className="py-3">
              <div className="flex items-center justify-between">
                <div className="font-medium text-sm">#{job.id} · {job.keyword || 'sin keyword'}</div>
                <span className={jobStatusBadge(job.status)}>{jobStatusLabel(job.status)}</span>
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {job.total_found} negocios · {formatDate(job.created_at)}
              </div>
              {(job.status === 'pending' || job.status === 'running') && (
                <div className="mt-2 w-full h-1.5 bg-slate-200 rounded">
                  <div
                    className="h-1.5 bg-brand-600 rounded"
                    style={{ width: `${job.progress || 0}%` }}
                  />
                </div>
              )}
            </li>
          ))}
          {recentJobs.length === 0 && (
            <li className="py-6 text-center text-sm text-slate-500">Sin jobs aún</li>
          )}
        </ul>
      </div>
    </div>
  );
}
