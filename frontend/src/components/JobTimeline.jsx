const statusColor = {
  pending: 'bg-slate-100 text-slate-700',
  started: 'bg-amber-100 text-amber-700',
  completed: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-rose-100 text-rose-700',
}

function JobTimeline({ jobs }) {
  if (!jobs?.length) {
    return <p className="text-xs text-slate-500">No job records yet.</p>
  }

  return (
    <ul className="space-y-2">
      {jobs.map((job) => (
        <li key={job.id} className="rounded border border-slate-200 p-2">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-medium text-slate-700">{job.task_type}</p>
            <span className={`text-[11px] px-2 py-0.5 rounded ${statusColor[job.status] || statusColor.pending}`}>
              {job.status}
            </span>
          </div>
          {job.error_message && <p className="text-xs text-rose-600 mt-1">{job.error_message}</p>}
        </li>
      ))}
    </ul>
  )
}

export default JobTimeline
