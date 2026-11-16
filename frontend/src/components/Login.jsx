import { useState } from 'react'

function Login({ onLogin, error }) {
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    try {
      await onLogin(password)
      setPassword('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-xl bg-white p-8 shadow-lg space-y-5">
        <p className="text-xs uppercase tracking-widest text-emerald-700">Creator workspace</p>
        <h1 className="text-3xl font-semibold text-slate-900">Sign in</h1>
        <label className="block text-sm font-medium text-slate-700" htmlFor="admin-password">Admin password</label>
        <input id="admin-password" type="password" required autoComplete="current-password" value={password}
          onChange={(event) => setPassword(event.target.value)} className="w-full rounded border border-slate-300 p-3" />
        {error && <p role="alert" className="text-sm text-rose-700">{error}</p>}
        <button disabled={busy} className="w-full rounded bg-slate-900 px-4 py-3 text-white disabled:opacity-60">
          {busy ? 'Signing in...' : 'Open dashboard'}
        </button>
      </form>
    </main>
  )
}

export default Login
