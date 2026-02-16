import { useState } from 'react'

import JobTimeline from './JobTimeline'

function VideoCard({ video, jobs, onLoadJobs, jobsLoading }) {
  const [showJobs, setShowJobs] = useState(false)

  const toggleJobs = async () => {
    const next = !showJobs
    setShowJobs(next)
    if (next) {
      await onLoadJobs(video.id)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs text-slate-500">Video #{video.id}</p>
          <p className="text-sm break-all text-slate-700">{video.instagram_url}</p>
        </div>
        <span className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-700">{video.status}</span>
      </div>

      {video.caption && (
        <p className="text-sm text-slate-700">
          <span className="font-medium">Caption:</span> {video.caption}
        </p>
      )}

      {video.tiktok_url && (
        <a
          className="text-sm text-blue-600 hover:underline"
          href={video.tiktok_url}
          target="_blank"
          rel="noreferrer"
        >
          View TikTok Post
        </a>
      )}

      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">Jobs: {jobs?.length ?? 0}</p>
        <button
          type="button"
          onClick={toggleJobs}
          className="text-xs font-medium text-slate-700 hover:underline"
        >
          {showJobs ? 'Hide job timeline' : 'Show job timeline'}
        </button>
      </div>

      {showJobs && (
        <div className="rounded bg-slate-50 p-3">
          {jobsLoading ? <p className="text-xs text-slate-500">Loading jobs...</p> : <JobTimeline jobs={jobs} />}
        </div>
      )}
    </div>
  )
}

export default VideoCard
