import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 20000,
})

export const createVideo = (instagram_url) => api.post('/api/videos/', { instagram_url })
export const getVideos = () => api.get('/api/videos/')
export const getStats = () => api.get('/api/stats/summary')
export const getVideoJobs = (videoId) => api.get(`/api/videos/${videoId}/jobs`)

export const getTikTokAuthUrl = () => api.get('/api/tiktok/auth-url')
export const completeTikTokAuth = (code, state) =>
  api.get('/api/tiktok/callback', {
    params: { code, state },
  })
export const getTikTokAccount = () => api.get('/api/tiktok/account')

export default api
