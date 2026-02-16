function TikTokConnectCard({ account, onConnect, connecting, callbackState }) {
  return (
    <section className="bg-white rounded-lg shadow p-4 space-y-3">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">TikTok Account</h2>
          <p className="text-sm text-slate-600">
            {account.connected
              ? `Connected${account.open_id ? ` (${account.open_id})` : ''}`
              : 'Not connected yet'}
          </p>
        </div>
        <button
          type="button"
          onClick={onConnect}
          disabled={connecting}
          className="rounded bg-emerald-600 text-white px-4 py-2 text-sm font-medium disabled:opacity-60"
        >
          {connecting ? 'Redirecting...' : account.connected ? 'Reconnect' : 'Connect TikTok'}
        </button>
      </div>

      {account.scope && <p className="text-xs text-slate-500">Scopes: {account.scope}</p>}
      {account.expires_at && <p className="text-xs text-slate-500">Token expires: {account.expires_at}</p>}

      {callbackState.message && (
        <p className={`text-sm ${callbackState.error ? 'text-rose-600' : 'text-emerald-700'}`}>
          {callbackState.message}
        </p>
      )}
    </section>
  )
}

export default TikTokConnectCard
