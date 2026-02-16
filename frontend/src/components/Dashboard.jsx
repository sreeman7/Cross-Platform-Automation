import UploadForm from './UploadForm'
import Stats from './Stats'
import VideoQueue from './VideoQueue'

function Dashboard({ videos, stats, onSubmit, submitting }) {
  return (
    <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-slate-900">Social Media Automation Dashboard</h1>
        <p className="text-slate-600">Submit Instagram Reels and monitor TikTok publishing pipeline.</p>
      </header>
      <Stats stats={stats} />
      <UploadForm onSubmit={onSubmit} loading={submitting} />
      <VideoQueue videos={videos} />
    </main>
  )
}

export default Dashboard
