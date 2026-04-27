import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import Map from '../components/Map.jsx';
import StatCard from '../components/StatCard.jsx';
import { businessesApi, scrapingApi, statsApi } from '../services/api.js';
import { formatDate, jobStatusBadge, jobStatusLabel } from '../utils/format.js';

const BUCKET_COLORS = {
  '80-100': '#dc2626',
  '60-79': '#f97316',
  '40-59': '#facc15',
  '20-39': '#22c55e',
  '0-19': '#0ea5e9',
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [mapBusinesses, setMapBusinesses] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  const reload = async () => {
    setLoading(true);
    try {
      const [statsData, mapData, jobsData] = await Promise.all([
        statsApi.get(),
        businessesApi.forMap({ limit: 500 }),
        scrapingApi.listJobs(),
      ]);
      setStats(statsData);
      setMapBusinesses(mapData);
      setRecentJobs(jobsData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
    const id = setInterval(reload, 15000);
    return () => clearInterval(id);
  }, []);

  if (loading && !stats) {
    return <div className="text-slate-500">Cargando dashboard...</div>;
  }

  const empty = stats?.total_businesses === 0;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500">Visión general de tus oportunidades comerciales</p>
        </div>
        <Link to="/scrape" className="btn-primary">+ Nuevo scraping</Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard label="Negocios" value={stats?.total_businesses ?? 0} accent="brand" />
        <StatCard label="Oportunidades altas" value={stats?.high_opportunity_count ?? 0} accent="red" hint="Score ≥ 70" />
        <StatCard label="Sin sitio web" value={stats?.no_website_count ?? 0} accent="amber" />
        <StatCard label="Score promedio" value={stats?.avg_opportunity_score ?? 0} accent="green" />
        <StatCard label="Mis prospectos" value={stats?.total_leads ?? 0} accent="slate" />
      </div>

      {empty && (
        <div className="card text-center py-10">
          <h2 className="text-xl font-semibold mb-2">¡Todavía no scrapeaste ninguna zona!</h2>
          <p className="text-slate-500 mb-4">Pegá una URL de Google Maps y arrancá a generar prospectos.</p>
          <Link to="/scrape" className="btn-primary">Lanzar primer scraping</Link>
        </div>
      )}

      {!empty && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-2">
              <h2 className="text-lg font-semibold">Mapa de oportunidades</h2>
              <Map businesses={mapBusinesses} height={460} />
            </div>
            <div className="space-y-6">
              <div className="card">
                <h3 className="font-semibold text-slate-900 mb-3">Distribución por score</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      dataKey="count"
                      nameKey="bucket"
                      data={stats?.by_score_bucket || []}
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                    >
                      {(stats?.by_score_bucket || []).map((entry) => (
                        <Cell key={entry.bucket} fill={BUCKET_COLORS[entry.bucket] || '#94a3b8'} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="card">
                <h3 className="font-semibold text-slate-900 mb-3">Top categorías</h3>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={stats?.by_category || []} layout="vertical" margin={{ left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" allowDecimals={false} />
                    <YAxis type="category" dataKey="category" width={120} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#6366f1" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold">Jobs recientes</h2>
              <Link to="/results" className="text-sm text-brand-700 hover:underline">Ver resultados →</Link>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase text-slate-500 border-b border-slate-200">
                    <th className="py-2 pr-3">#</th>
                    <th className="py-2 pr-3">Keyword</th>
                    <th className="py-2 pr-3">Radio</th>
                    <th className="py-2 pr-3">Estado</th>
                    <th className="py-2 pr-3">Encontrados</th>
                    <th className="py-2 pr-3">Lanzado</th>
                  </tr>
                </thead>
                <tbody>
                  {recentJobs.slice(0, 8).map((job) => (
                    <tr key={job.id} className="border-b border-slate-100">
                      <td className="py-2 pr-3 font-mono">{job.id}</td>
                      <td className="py-2 pr-3">{job.keyword || '-'}</td>
                      <td className="py-2 pr-3">{job.radius_km} km</td>
                      <td className="py-2 pr-3">
                        <span className={jobStatusBadge(job.status)}>{jobStatusLabel(job.status)}</span>
                        {job.status === 'running' && (
                          <span className="ml-2 text-xs text-slate-500">{job.progress}%</span>
                        )}
                      </td>
                      <td className="py-2 pr-3">{job.total_found}</td>
                      <td className="py-2 pr-3 text-slate-500">{formatDate(job.created_at)}</td>
                    </tr>
                  ))}
                  {recentJobs.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-3 text-slate-500 text-center">
                        Aún no hay jobs.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
