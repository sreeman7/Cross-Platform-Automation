import { useCallback, useEffect, useMemo, useState } from 'react'

import Dashboard from './components/Dashboard'
import Login from './components/Login'
import {
  completeTikTokAuth,
  checkPublication,
  approveVideo,
  createVideo,
  getStats,
  getTikTokAccount,
  getTikTokAuthUrl,
  getVideoJobs,
  getVideos,
  login,
  updateVideo,
} from './services/api'

function App() {
  const [videos, setVideos] = useState([])
  const [stats, setStats] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [globalError, setGlobalError] = useState('')
  const [loginRequired, setLoginRequired] = useState(() => !sessionStorage.getItem('dashboard_token'))
  const [loginError, setLoginError] = useState('')

  const [account, setAccount] = useState({ connected: false, mock_mode: false, open_id: null, scope: null, expires_at: null })
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

      const publishing = videosRes.data.filter((video) => video.status === 'publishing')
      const checks = await Promise.allSettled(publishing.map((video) => checkPublication(video.id)))
      const updated = new Map()
      checks.forEach((check, index) => {
        if (check.status === 'fulfilled') {
          updated.set(publishing[index].id, check.value.data)
        } else if (check.reason?.response?.status !== 409) {
          setGlobalError('Could not refresh TikTok publication status. The dashboard will retry.')
        }
      })
      if (updated.size) {
        setVideos(videosRes.data.map((video) => updated.get(video.id) || video))
      }

      const recentVideos = videosRes.data.slice(0, 5)
      await Promise.all(recentVideos.map((video) => fetchJobsForVideo(video.id)))
    } catch (error) {
      if (error?.response?.status === 401) {
        sessionStorage.removeItem('dashboard_token')
        setLoginRequired(true)
        return
      }
      const message = error?.response?.data?.detail || 'Cannot reach the API. Check that the backend is running at http://localhost:8000.'
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

  const handleApprove = async (videoId, caption, hashtags) => {
    try {
      await updateVideo(videoId, { caption, hashtags })
      await approveVideo(videoId)
      await loadData()
    } catch (error) {
      setGlobalError(error?.response?.data?.detail || 'Could not approve video.')
    }
  }

  const handleLogin = async (password) => {
    try {
      const response = await login(password)
      sessionStorage.setItem('dashboard_token', response.data.access_token)
      setLoginRequired(false)
      setLoginError('')
      return true
    } catch (error) {
      setLoginError(error?.response?.data?.detail || 'Cannot reach the API. Check http://localhost:8000/health.')
      return false
    }
  }

  const handleConnectTikTok = async () => {
    setConnectingTikTok(true)
    setCallbackState({ message: '', error: false })
    try {
      const response = await getTikTokAuthUrl()
      sessionStorage.setItem('tiktok_oauth_state', response.data.state)
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
        if (state !== sessionStorage.getItem('tiktok_oauth_state')) {
          throw new Error('TikTok connection state did not match. Please reconnect.')
        }
        await completeTikTokAuth(code, state)
        setCallbackState({ message: 'TikTok connected successfully.', error: false })
        await loadData()
      } catch (error) {
        const message = error?.response?.data?.detail || error?.message || 'TikTok callback failed.'
        setCallbackState({ message: String(message), error: true })
      } finally {
        sessionStorage.removeItem('tiktok_oauth_state')
        window.history.replaceState({}, '', window.location.pathname)
      }
    }

    processCallback()
  }, [loadData])

  useEffect(() => {
    if (loginRequired) return undefined
    loadData()
    const interval = setInterval(loadData, 5000)
    return () => clearInterval(interval)
  }, [loadData, loginRequired])

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
      onApprove: handleApprove,
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

  if (loginRequired) return <Login onLogin={handleLogin} error={loginError} />
  return <Dashboard {...dashboardProps} />
}

export default App
