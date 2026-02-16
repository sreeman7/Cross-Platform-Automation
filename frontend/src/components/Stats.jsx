function Stats({ stats }) {
  const cards = [
    { label: 'Total', value: stats.total_videos ?? 0 },
    { label: 'Pending', value: stats.pending ?? 0 },
    { label: 'Processing', value: (stats.downloading ?? 0) + (stats.processing ?? 0) + (stats.uploading ?? 0) },
    { label: 'Completed', value: stats.completed ?? 0 },
    { label: 'Failed', value: stats.failed ?? 0 },
  ]

  return (
    <section className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {cards.map((card) => (
        <div key={card.label} className="bg-white rounded-lg shadow p-4">
          <p className="text-xs text-slate-500">{card.label}</p>
          <p className="text-2xl font-semibold text-slate-900">{card.value}</p>
        </div>
      ))}
    </section>
  )
}

export default Stats
