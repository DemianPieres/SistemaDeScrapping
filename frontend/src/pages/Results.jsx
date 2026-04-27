import { useEffect, useMemo, useState } from 'react';
import BusinessCard from '../components/BusinessCard.jsx';
import Filters from '../components/Filters.jsx';
import Map from '../components/Map.jsx';
import { businessesApi, leadsApi, scrapingApi } from '../services/api.js';

const PAGE_SIZE = 12;

export default function Results() {
  const [filters, setFilters] = useState({});
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0 });
  const [mapData, setMapData] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('list');
  const [orderBy, setOrderBy] = useState('opportunity_score');
  const [orderDir, setOrderDir] = useState('desc');
  const [savedLeadBusinessIds, setSavedLeadBusinessIds] = useState(new Set());
  const [feedback, setFeedback] = useState(null);

  const queryParams = useMemo(
    () => ({ ...filters, page, size: PAGE_SIZE, order_by: orderBy, order_dir: orderDir }),
    [filters, page, orderBy, orderDir],
  );

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [list, leads, jobsRes, mapRes] = await Promise.all([
        businessesApi.list(queryParams),
        leadsApi.list(),
        scrapingApi.listJobs(),
        businessesApi.forMap({ ...filters, limit: 500 }),
      ]);
      setData(list);
      setSavedLeadBusinessIds(new Set(leads.map((l) => l.business.id)));
      setJobs(jobsRes);
      setMapData(mapRes);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, [queryParams]);

  const handleAddLead = async (business) => {
    try {
      await leadsApi.create({ business_id: business.id });
      setSavedLeadBusinessIds(new Set([...savedLeadBusinessIds, business.id]));
      setFeedback({ type: 'ok', message: `${business.name} guardado como prospecto.` });
    } catch (e) {
      setFeedback({
        type: 'error',
        message: e.response?.data?.detail || 'No se pudo guardar el prospecto',
      });
    }
    setTimeout(() => setFeedback(null), 4000);
  };

  const totalPages = Math.max(1, Math.ceil((data.total || 0) / PAGE_SIZE));

  const handleExport = () => {
    const url = businessesApi.exportCsvUrl(filters);
    fetch(url)
      .then((r) => r.blob())
      .then((blob) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'leadscraper_export.csv';
        a.click();
      });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <aside className="lg:col-span-1">
        <Filters
          filters={filters}
          onChange={(f) => {
            setFilters(f);
            setPage(1);
          }}
          onReset={() => {
            setFilters({});
            setPage(1);
          }}
          jobs={jobs}
        />
      </aside>

      <section className="lg:col-span-3 space-y-4">
        <div className="card flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold">Resultados</h1>
            <p className="text-sm text-slate-500">
              {data.total} negocios coinciden con tu búsqueda
            </p>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <select
              className="input w-auto"
              value={`${orderBy}:${orderDir}`}
              onChange={(e) => {
                const [field, dir] = e.target.value.split(':');
                setOrderBy(field);
                setOrderDir(dir);
              }}
            >
              <option value="opportunity_score:desc">Mejor oportunidad</option>
              <option value="opportunity_score:asc">Menor oportunidad</option>
              <option value="rating:desc">Mejor rating</option>
              <option value="reviews_count:desc">Más reseñas</option>
              <option value="name:asc">Nombre (A-Z)</option>
              <option value="created_at:desc">Más recientes</option>
            </select>
            <div className="inline-flex rounded-lg overflow-hidden ring-1 ring-slate-300">
              <button
                onClick={() => setView('list')}
                className={`px-3 py-1.5 text-sm ${view === 'list' ? 'bg-brand-600 text-white' : 'bg-white'}`}
              >
                Lista
              </button>
              <button
                onClick={() => setView('map')}
                className={`px-3 py-1.5 text-sm ${view === 'map' ? 'bg-brand-600 text-white' : 'bg-white'}`}
              >
                Mapa
              </button>
            </div>
            <button onClick={handleExport} className="btn-secondary">Exportar CSV</button>
          </div>
        </div>

        {feedback && (
          <div
            className={`rounded-md border p-3 text-sm ${
              feedback.type === 'ok'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-red-50 border-red-200 text-red-800'
            }`}
          >
            {feedback.message}
          </div>
        )}

        {view === 'map' ? (
          <Map businesses={mapData} height={600} />
        ) : loading ? (
          <div className="text-slate-500">Cargando...</div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {data.items.map((b) => (
                <BusinessCard
                  key={b.id}
                  business={b}
                  isLead={savedLeadBusinessIds.has(b.id)}
                  onAddLead={handleAddLead}
                />
              ))}
            </div>
            {data.items.length === 0 && (
              <div className="card text-center text-slate-500 py-10">
                No hay negocios que cumplan los filtros.
              </div>
            )}

            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">
                Página {page} de {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  className="btn-secondary"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  Anterior
                </button>
                <button
                  className="btn-secondary"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                >
                  Siguiente
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
