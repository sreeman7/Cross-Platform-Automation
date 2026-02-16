import VideoCard from './VideoCard'

function VideoQueue({ videos, jobsByVideo, onLoadJobs, jobsLoadingByVideo }) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-slate-800">Processing Queue</h2>
      <div className="grid gap-3">
        {videos.length === 0 ? (
          <p className="text-sm text-slate-500">No videos submitted yet.</p>
        ) : (
          videos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              jobs={jobsByVideo[video.id] || []}
              onLoadJobs={onLoadJobs}
              jobsLoading={Boolean(jobsLoadingByVideo[video.id])}
            />
          ))
        )}
      </div>
    </section>
  )
}

export default VideoQueue
