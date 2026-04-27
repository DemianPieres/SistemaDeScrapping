import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({
  baseURL,
  timeout: 30000,
});

export const scrapingApi = {
  createJob: (payload) => api.post('/scraping/jobs', payload).then((r) => r.data),
  listJobs: () => api.get('/scraping/jobs').then((r) => r.data),
  getJob: (id) => api.get(`/scraping/jobs/${id}`).then((r) => r.data),
  cancelJob: (id) => api.post(`/scraping/jobs/${id}/cancel`).then((r) => r.data),
};

export const businessesApi = {
  list: (params) => api.get('/businesses', { params }).then((r) => r.data),
  forMap: (params) => api.get('/businesses/map', { params }).then((r) => r.data),
  detail: (id) => api.get(`/businesses/${id}`).then((r) => r.data),
  exportCsvUrl: (params) => {
    const query = new URLSearchParams(params).toString();
    return `${baseURL}/businesses/export/csv?${query}`;
  },
};

export const leadsApi = {
  list: (params) => api.get('/leads', { params }).then((r) => r.data),
  create: (payload) => api.post('/leads', payload).then((r) => r.data),
  update: (id, payload) => api.put(`/leads/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/leads/${id}`).then((r) => r.data),
  addInteraction: (id, payload) =>
    api.post(`/leads/${id}/interactions`, payload).then((r) => r.data),
};

export const statsApi = {
  get: () => api.get('/stats').then((r) => r.data),
};
