import Stats from './Stats'
import TikTokConnectCard from './TikTokConnectCard'
import UploadForm from './UploadForm'
import VideoQueue from './VideoQueue'

function Dashboard({
  videos,
  stats,
  onSubmit,
  submitting,
  account,
  onConnectTikTok,
  connectingTikTok,
  callbackState,
  jobsByVideo,
  onLoadJobs,
  jobsLoadingByVideo,
  globalError,
}) {
  return (
    <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-slate-900">Social Media Automation Dashboard</h1>
        <p className="text-slate-600">Submit Instagram Reels and monitor TikTok publishing pipeline.</p>
      </header>

      {globalError && <p className="rounded bg-rose-50 text-rose-700 text-sm p-3">{globalError}</p>}

      <Stats stats={stats} />
      <TikTokConnectCard
        account={account}
        onConnect={onConnectTikTok}
        connecting={connectingTikTok}
        callbackState={callbackState}
      />
      <UploadForm onSubmit={onSubmit} loading={submitting} />
      <VideoQueue
        videos={videos}
        jobsByVideo={jobsByVideo}
        onLoadJobs={onLoadJobs}
        jobsLoadingByVideo={jobsLoadingByVideo}
      />
    </main>
  )
}

export default Dashboard
