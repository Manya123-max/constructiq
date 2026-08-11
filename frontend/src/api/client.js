import axios from 'axios'

const API_BASE = (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.includes('constructiq'))
  ? import.meta.env.VITE_API_URL
  : 'https://constructiq-t6qw.onrender.com'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

export const api = {
  estimate: (data) => client.post('/api/estimate', data).then(r => r.data),
  getProjects: (type) => client.get('/api/projects', { params: { project_type: type } }).then(r => r.data),
  getProject: (id) => client.get(`/api/projects/${id}`).then(r => r.data),
  monitorStatus: (id) => client.get(`/api/monitor/${id}/status`).then(r => r.data),
  monitorDelays: (id) => client.get(`/api/monitor/${id}/delays`).then(r => r.data),
  monitorRootcause: (id) => client.get(`/api/monitor/${id}/rootcause`).then(r => r.data),
  monitorMaterials: (id) => client.get(`/api/monitor/${id}/materials`).then(r => r.data),
  monitorProcurement: (id) => client.get(`/api/monitor/${id}/procurement`).then(r => r.data),
  sendChat: (messages) => client.post('/api/chat', { messages }).then(r => r.data),
}
