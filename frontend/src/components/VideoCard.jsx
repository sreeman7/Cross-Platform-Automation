import { useEffect, useState } from 'react'

import JobTimeline from './JobTimeline'

function VideoCard({ video, jobs, onLoadJobs, onApprove, jobsLoading }) {
  const [showJobs, setShowJobs] = useState(false)
  const serverTags = (video.hashtags || []).join(' ')
  const [caption, setCaption] = useState(video.caption || '')
  const [tags, setTags] = useState(serverTags)
  const [approving, setApproving] = useState(false)

  useEffect(() => setCaption(video.caption || ''), [video.caption])
  useEffect(() => setTags(serverTags), [serverTags])

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
      {video.status === 'ready_for_review' && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 space-y-3">
          <h3 className="font-semibold text-emerald-950">Review before publishing</h3>
          {video.storage_url && (
            <video controls className="w-full max-w-sm rounded bg-black" src={video.storage_url}>
              Your browser cannot preview this video.
            </video>
          )}
          <label className="block text-sm text-slate-800" htmlFor={`caption-${video.id}`}>Caption</label>
          <textarea id={`caption-${video.id}`} value={caption} onChange={(event) => setCaption(event.target.value)}
            maxLength={2200} rows={3} className="w-full rounded border border-slate-300 p-2" />
          <label className="block text-sm text-slate-800" htmlFor={`tags-${video.id}`}>Hashtags</label>
          <input id={`tags-${video.id}`} value={tags} onChange={(event) => setTags(event.target.value)}
            className="w-full rounded border border-slate-300 p-2" />
          <p className="text-xs text-slate-600">The connected TikTok account will receive this clip as a private post.</p>
          <button type="button" disabled={approving || !caption.trim()}
            onClick={async () => {
              setApproving(true)
              try { await onApprove(video.id, caption.trim(), tags.split(/\s+/).filter(Boolean)) }
              finally { setApproving(false) }
            }}
            className="rounded bg-emerald-700 px-4 py-2 text-white disabled:opacity-50">
            {approving ? 'Queuing...' : 'Approve and publish privately'}
          </button>
        </div>
      )}
      {video.error_message && <p className="text-sm text-rose-700">{video.error_message}</p>}
      {['publishing', 'publishing_in_progress'].includes(video.status) && (
        <p className="text-sm text-amber-700">Uploaded to TikTok; waiting for publication confirmation.</p>
      )}
      {video.status === 'demo_completed' && (
        <p className="text-sm text-slate-600">Demo processing completed. No TikTok post was created.</p>
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
