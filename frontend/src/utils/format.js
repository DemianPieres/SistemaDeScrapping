export function scoreBadge(score) {
  if (score == null) return 'badge-gray';
  if (score >= 80) return 'badge-red';
  if (score >= 60) return 'badge-yellow';
  if (score >= 40) return 'badge-indigo';
  if (score >= 20) return 'badge-green';
  return 'badge-gray';
}

export function formatDate(value) {
  if (!value) return '–';
  const d = new Date(value);
  return d.toLocaleString('es-AR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function jobStatusLabel(status) {
  return (
    {
      pending: 'En cola',
      running: 'En ejecución',
      completed: 'Completado',
      failed: 'Falló',
      cancelled: 'Cancelado',
    }[status] || status
  );
}

export function jobStatusBadge(status) {
  return (
    {
      pending: 'badge-gray',
      running: 'badge-indigo',
      completed: 'badge-green',
      failed: 'badge-red',
      cancelled: 'badge-yellow',
    }[status] || 'badge-gray'
  );
}
