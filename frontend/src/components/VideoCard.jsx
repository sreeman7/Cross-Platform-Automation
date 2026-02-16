function VideoCard({ video }) {
  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-2">
      <p className="text-xs text-slate-500">Video #{video.id}</p>
      <p className="text-sm break-all text-slate-700">{video.instagram_url}</p>
      <p className="text-sm">
        <span className="font-medium">Status:</span> {video.status}
      </p>
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
    </div>
  )
}

export default VideoCard
