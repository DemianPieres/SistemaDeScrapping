import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import BusinessDetail from './pages/BusinessDetail.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Leads from './pages/Leads.jsx';
import NotFound from './pages/NotFound.jsx';
import Results from './pages/Results.jsx';
import Scrape from './pages/Scrape.jsx';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/scrape" element={<Scrape />} />
        <Route path="/results" element={<Results />} />
        <Route path="/leads" element={<Leads />} />
        <Route path="/businesses/:id" element={<BusinessDetail />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
