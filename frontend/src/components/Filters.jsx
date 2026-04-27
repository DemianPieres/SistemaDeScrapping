export default function Filters({ filters, onChange, onReset, jobs = [] }) {
  const update = (patch) => onChange({ ...filters, ...patch });
  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-900">Filtros</h3>
        <button onClick={onReset} className="text-xs text-slate-500 hover:text-brand-700">
          Limpiar
        </button>
      </div>

      <div>
        <label className="label">Buscar</label>
        <input
          type="text"
          className="input"
          placeholder="Nombre, dirección, categoría..."
          value={filters.search || ''}
          onChange={(e) => update({ search: e.target.value })}
        />
      </div>

      {jobs.length > 0 && (
        <div>
          <label className="label">Sesión de scraping</label>
          <select
            className="input"
            value={filters.job_id ?? ''}
            onChange={(e) => update({ job_id: e.target.value || undefined })}
          >
            <option value="">Todas</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                #{j.id} · {j.keyword || 'sin keyword'} ({j.total_found || 0})
              </option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label className="label">Categoría</label>
        <input
          className="input"
          placeholder="restaurante, gimnasio..."
          value={filters.category || ''}
          onChange={(e) => update({ category: e.target.value })}
        />
      </div>

      <div>
        <label className="label">Ciudad</label>
        <input
          className="input"
          placeholder="Mendoza, Buenos Aires..."
          value={filters.city || ''}
          onChange={(e) => update({ city: e.target.value })}
        />
      </div>

      <div>
        <label className="label">Sitio web</label>
        <select
          className="input"
          value={filters.has_website ?? ''}
          onChange={(e) => update({
            has_website: e.target.value === '' ? undefined : e.target.value === 'true',
          })}
        >
          <option value="">Indistinto</option>
          <option value="false">Sin sitio web</option>
          <option value="true">Con sitio web</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label">Score mín.</label>
          <input
            type="number"
            min={0}
            max={100}
            className="input"
            value={filters.min_score ?? ''}
            onChange={(e) =>
              update({ min_score: e.target.value === '' ? undefined : Number(e.target.value) })
            }
          />
        </div>
        <div>
          <label className="label">Score máx.</label>
          <input
            type="number"
            min={0}
            max={100}
            className="input"
            value={filters.max_score ?? ''}
            onChange={(e) =>
              update({ max_score: e.target.value === '' ? undefined : Number(e.target.value) })
            }
          />
        </div>
      </div>

      <div>
        <label className="label">Rating mínimo</label>
        <input
          type="number"
          step="0.1"
          min={0}
          max={5}
          className="input"
          value={filters.min_rating ?? ''}
          onChange={(e) =>
            update({ min_rating: e.target.value === '' ? undefined : Number(e.target.value) })
          }
        />
      </div>

      <div>
        <label className="label">Tamaño estimado</label>
        <select
          className="input"
          value={filters.size_tier ?? ''}
          onChange={(e) => update({ size_tier: e.target.value || undefined })}
        >
          <option value="">Todos</option>
          <option value="muy_pequeño">Muy pequeño</option>
          <option value="pequeño">Pequeño</option>
          <option value="mediano">Mediano</option>
          <option value="grande">Grande</option>
          <option value="muy_grande">Muy grande</option>
        </select>
      </div>
    </div>
  );
}
