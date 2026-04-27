import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <div className="text-6xl font-bold text-brand-600">404</div>
        <p className="mt-2 text-slate-600">Página no encontrada</p>
        <Link to="/" className="btn-primary mt-4">Volver al inicio</Link>
      </div>
    </div>
  );
}
