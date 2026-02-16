import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 15000,
})

export const createVideo = (instagram_url) => api.post('/api/videos/', { instagram_url })
export const getVideos = () => api.get('/api/videos/')
export const getStats = () => api.get('/api/stats/summary')

export default api
