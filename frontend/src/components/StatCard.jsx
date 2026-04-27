export default function StatCard({ label, value, hint, accent = 'brand' }) {
  const accents = {
    brand: 'from-brand-500 to-brand-700',
    green: 'from-emerald-500 to-emerald-700',
    amber: 'from-amber-500 to-amber-700',
    red: 'from-red-500 to-red-700',
    slate: 'from-slate-500 to-slate-700',
  };
  return (
    <div className="rounded-xl bg-white shadow-sm ring-1 ring-slate-200 overflow-hidden">
      <div className={`h-1 bg-gradient-to-r ${accents[accent]}`} />
      <div className="p-5">
        <div className="text-xs uppercase tracking-wide text-slate-500 font-medium">{label}</div>
        <div className="mt-2 text-3xl font-bold text-slate-900">{value}</div>
        {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
      </div>
    </div>
  );
}
