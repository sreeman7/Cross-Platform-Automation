import { useState } from 'react'

function UploadForm({ onSubmit, loading }) {
  const [instagramUrl, setInstagramUrl] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    await onSubmit(instagramUrl)
    setInstagramUrl('')
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-4 space-y-3">
      <h2 className="text-lg font-semibold text-slate-800">Submit Instagram Reel</h2>
      <input
        type="url"
        required
        placeholder="https://www.instagram.com/reel/ABC123/"
        value={instagramUrl}
        onChange={(event) => setInstagramUrl(event.target.value)}
        className="w-full rounded border border-slate-300 px-3 py-2"
      />
      <button
        type="submit"
        disabled={loading}
        className="rounded bg-slate-900 text-white px-4 py-2 disabled:opacity-60"
      >
        {loading ? 'Submitting...' : 'Queue Video'}
      </button>
    </form>
  )
}

export default UploadForm
