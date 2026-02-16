import { useCallback, useEffect, useState } from 'react'

import Dashboard from './components/Dashboard'
import { createVideo, getStats, getVideos } from './services/api'

function App() {
  const [videos, setVideos] = useState([])
  const [stats, setStats] = useState({})
  const [submitting, setSubmitting] = useState(false)

  const loadData = useCallback(async () => {
    const [videosRes, statsRes] = await Promise.all([getVideos(), getStats()])
    setVideos(videosRes.data)
    setStats(statsRes.data)
  }, [])

  const handleSubmit = async (instagramUrl) => {
    setSubmitting(true)
    try {
      await createVideo(instagramUrl)
      await loadData()
    } finally {
      setSubmitting(false)
    }
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 5000)
    return () => clearInterval(interval)
  }, [loadData])

  return <Dashboard videos={videos} stats={stats} onSubmit={handleSubmit} submitting={submitting} />
}

export default App
