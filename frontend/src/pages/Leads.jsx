import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { leadsApi } from '../services/api.js';
import { formatDate, scoreBadge } from '../utils/format.js';

const STATUS_OPTIONS = [
  { value: 'nuevo', label: 'Nuevo' },
  { value: 'contactado', label: 'Contactado' },
  { value: 'interesado', label: 'Interesado' },
  { value: 'negociando', label: 'Negociando' },
  { value: 'cerrado', label: 'Cerrado' },
  { value: 'descartado', label: 'Descartado' },
];

export default function Leads() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [openInteractionFor, setOpenInteractionFor] = useState(null);
  const [interactionForm, setInteractionForm] = useState({ channel: 'email', summary: '' });

  const reload = async () => {
    setLoading(true);
    try {
      const data = await leadsApi.list(filterStatus ? { status_filter: filterStatus } : undefined);
      setLeads(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
  }, [filterStatus]);

  const updateLead = async (lead, patch) => {
    const updated = await leadsApi.update(lead.id, patch);
    setLeads((prev) => prev.map((l) => (l.id === lead.id ? updated : l)));
  };

  const deleteLead = async (lead) => {
    if (!confirm(`¿Eliminar a ${lead.business.name} de tus prospectos?`)) return;
    await leadsApi.remove(lead.id);
    setLeads((prev) => prev.filter((l) => l.id !== lead.id));
  };

  const submitInteraction = async (lead) => {
    if (!interactionForm.summary.trim()) return;
    await leadsApi.addInteraction(lead.id, interactionForm);
    setInteractionForm({ channel: 'email', summary: '' });
    setOpenInteractionFor(null);
    reload();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Mis prospectos</h1>
          <p className="text-sm text-slate-500">Negocios que estás trabajando comercialmente.</p>
        </div>
        <select
          className="input w-auto"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="">Todos los estados</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-slate-500">Cargando...</div>
      ) : leads.length === 0 ? (
        <div className="card text-center py-10">
          <p className="text-slate-500">Todavía no guardaste prospectos.</p>
          <Link to="/results" className="btn-primary mt-3 inline-flex">Ir a resultados</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {leads.map((lead) => (
            <div key={lead.id} className="card">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/businesses/${lead.business.id}`}
                      className="text-lg font-semibold hover:text-brand-700"
                    >
                      {lead.business.name}
                    </Link>
                    <span className={scoreBadge(lead.business.opportunity_score)}>
                      {lead.business.opportunity_score ?? '–'}/100
                    </span>
                  </div>
                  {lead.business.category && (
                    <div className="text-sm text-slate-500">{lead.business.category}</div>
                  )}
                  <div className="text-xs text-slate-500 mt-1">
                    Agregado el {formatDate(lead.created_at)}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 items-center">
                  <select
                    className="input w-auto"
                    value={lead.status}
                    onChange={(e) => updateLead(lead, { status: e.target.value })}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                  <select
                    className="input w-auto"
                    value={lead.priority || ''}
                    onChange={(e) =>
                      updateLead(lead, { priority: e.target.value || undefined })
                    }
                  >
                    <option value="">Prioridad</option>
                    <option value="baja">Baja</option>
                    <option value="media">Media</option>
                    <option value="alta">Alta</option>
                  </select>
                  <button onClick={() => deleteLead(lead)} className="btn-danger text-xs">
                    Eliminar
                  </button>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                {lead.business.phone && (
                  <a href={`tel:${lead.business.phone}`} className="card !p-3 flex items-center gap-2">
                    📞 {lead.business.phone}
                  </a>
                )}
                {lead.business.website && (
                  <a
                    href={lead.business.website}
                    target="_blank"
                    rel="noreferrer"
                    className="card !p-3 flex items-center gap-2 truncate"
                  >
                    🌐 <span className="truncate">{lead.business.website}</span>
                  </a>
                )}
                {lead.business.address && (
                  <div className="card !p-3 flex items-center gap-2 truncate">
                    📍 <span className="truncate">{lead.business.address}</span>
                  </div>
                )}
              </div>

              <div className="mt-3">
                <label className="label">Notas</label>
                <textarea
                  className="input min-h-[60px]"
                  defaultValue={lead.notes || ''}
                  onBlur={(e) => {
                    if (e.target.value !== (lead.notes || '')) {
                      updateLead(lead, { notes: e.target.value });
                    }
                  }}
                  placeholder="Tomá notas sobre este prospecto..."
                />
              </div>

              <div className="mt-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-sm">
                    Historial ({lead.interactions?.length || 0})
                  </h4>
                  <button
                    onClick={() =>
                      setOpenInteractionFor(openInteractionFor === lead.id ? null : lead.id)
                    }
                    className="text-sm text-brand-700 hover:underline"
                  >
                    + Registrar contacto
                  </button>
                </div>

                {openInteractionFor === lead.id && (
                  <div className="mt-2 rounded-lg border border-slate-200 p-3 bg-slate-50">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <select
                        className="input"
                        value={interactionForm.channel}
                        onChange={(e) =>
                          setInteractionForm({ ...interactionForm, channel: e.target.value })
                        }
                      >
                        <option value="email">Email</option>
                        <option value="whatsapp">WhatsApp</option>
                        <option value="llamada">Llamada</option>
                        <option value="reunion">Reunión</option>
                        <option value="visita">Visita</option>
                      </select>
                      <input
                        className="input sm:col-span-2"
                        placeholder="Resumen del contacto"
                        value={interactionForm.summary}
                        onChange={(e) =>
                          setInteractionForm({ ...interactionForm, summary: e.target.value })
                        }
                      />
                    </div>
                    <div className="mt-2 flex justify-end">
                      <button
                        className="btn-primary text-xs"
                        onClick={() => submitInteraction(lead)}
                      >
                        Guardar
                      </button>
                    </div>
                  </div>
                )}

                {lead.interactions?.length > 0 && (
                  <ul className="mt-2 divide-y divide-slate-100 text-sm">
                    {lead.interactions.map((it) => (
                      <li key={it.id} className="py-2 flex items-start justify-between gap-3">
                        <div>
                          <div className="font-medium capitalize">{it.channel}</div>
                          <div className="text-slate-600">{it.summary}</div>
                        </div>
                        <span className="text-xs text-slate-500 shrink-0">
                          {formatDate(it.occurred_at)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
