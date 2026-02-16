import { useCallback, useEffect, useMemo, useState } from 'react'

import Dashboard from './components/Dashboard'
import {
  completeTikTokAuth,
  createVideo,
  getStats,
  getTikTokAccount,
  getTikTokAuthUrl,
  getVideoJobs,
  getVideos,
} from './services/api'

function App() {
  const [videos, setVideos] = useState([])
  const [stats, setStats] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [globalError, setGlobalError] = useState('')

  const [account, setAccount] = useState({ connected: false, open_id: null, scope: null, expires_at: null })
  const [connectingTikTok, setConnectingTikTok] = useState(false)
  const [callbackState, setCallbackState] = useState({ message: '', error: false })

  const [jobsByVideo, setJobsByVideo] = useState({})
  const [jobsLoadingByVideo, setJobsLoadingByVideo] = useState({})

  const fetchJobsForVideo = useCallback(async (videoId) => {
    setJobsLoadingByVideo((prev) => ({ ...prev, [videoId]: true }))
    try {
      const jobsRes = await getVideoJobs(videoId)
      setJobsByVideo((prev) => ({ ...prev, [videoId]: jobsRes.data }))
    } finally {
      setJobsLoadingByVideo((prev) => ({ ...prev, [videoId]: false }))
    }
  }, [])

  const loadData = useCallback(async () => {
    try {
      setGlobalError('')
      const [videosRes, statsRes, accountRes] = await Promise.all([getVideos(), getStats(), getTikTokAccount()])
      setVideos(videosRes.data)
      setStats(statsRes.data)
      setAccount(accountRes.data)

      const recentVideos = videosRes.data.slice(0, 5)
      await Promise.all(recentVideos.map((video) => fetchJobsForVideo(video.id)))
    } catch (error) {
      const message = error?.response?.data?.detail || 'Failed to load dashboard data.'
      setGlobalError(String(message))
    }
  }, [fetchJobsForVideo])

  const handleSubmit = async (instagramUrl) => {
    setSubmitting(true)
    try {
      await createVideo(instagramUrl)
      await loadData()
    } catch (error) {
      const message = error?.response?.data?.detail || 'Failed to submit video.'
      setGlobalError(String(message))
    } finally {
      setSubmitting(false)
    }
  }

  const handleConnectTikTok = async () => {
    setConnectingTikTok(true)
    setCallbackState({ message: '', error: false })
    try {
      const response = await getTikTokAuthUrl()
      window.location.href = response.data.authorization_url
    } catch (error) {
      const message = error?.response?.data?.detail || 'Failed to start TikTok OAuth flow.'
      setCallbackState({ message: String(message), error: true })
      setConnectingTikTok(false)
    }
  }

  useEffect(() => {
    const processCallback = async () => {
      const params = new URLSearchParams(window.location.search)
      const code = params.get('code')
      const state = params.get('state')
      if (!code || !state) {
        return
      }

      try {
        await completeTikTokAuth(code, state)
        setCallbackState({ message: 'TikTok connected successfully.', error: false })
      } catch (error) {
        const message = error?.response?.data?.detail || 'TikTok callback failed.'
        setCallbackState({ message: String(message), error: true })
      } finally {
        window.history.replaceState({}, '', window.location.pathname)
      }
    }

    processCallback()
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 5000)
    return () => clearInterval(interval)
  }, [loadData])

  const dashboardProps = useMemo(
    () => ({
      videos,
      stats,
      onSubmit: handleSubmit,
      submitting,
      account,
      onConnectTikTok: handleConnectTikTok,
      connectingTikTok,
      callbackState,
      jobsByVideo,
      onLoadJobs: fetchJobsForVideo,
      jobsLoadingByVideo,
      globalError,
    }),
    [
      videos,
      stats,
      submitting,
      account,
      connectingTikTok,
      callbackState,
      jobsByVideo,
      fetchJobsForVideo,
      jobsLoadingByVideo,
      globalError,
    ],
  )

  return <Dashboard {...dashboardProps} />
}

export default App
