// ------------------------------
// Step metadata
// ------------------------------

const STEP_LABELS = {
  reviewing: { label: 'Reviewer analyzing code', color: 'text-blue-500 dark:text-blue-400' },
  fixing: { label: 'Fixer applying changes', color: 'text-yellow-500 dark:text-yellow-400' },
  evaluating: { label: 'Evaluator scoring fix', color: 'text-purple-500 dark:text-purple-400' },
  retry: { label: 'Evaluator rejected fix — sending back to Fixer', color: 'text-orange-500 dark:text-orange-400' },
  complete: { label: 'Review cycle complete', color: 'text-green-500 dark:text-green-400' },
  error: { label: 'Error occurred', color: 'text-red-500 dark:text-red-400' },
}

function Spinner() {
  return (
    <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
  )
}

// ------------------------------
// Component
// ------------------------------

export function ActivityLog({ entries, streaming }) {
  if (entries.length === 0) return null

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg px-4 py-3 space-y-1.5">
      <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">Activity</p>
      {entries.map((entry, i) => {
        const meta = STEP_LABELS[entry.type] || { label: entry.type, color: 'text-gray-400' }
        const isLast = i === entries.length - 1
        const showSpinner = isLast && streaming && entry.type !== 'complete' && entry.type !== 'error'
        return (
          <div key={i} className={`flex items-center gap-2 text-sm ${meta.color}`}>
            {showSpinner ? <Spinner /> : <span className="w-3 h-3 text-xs">✓</span>}
            <span>{meta.label}</span>
            {entry.elapsed && (
              <span className="ml-auto text-gray-400 dark:text-gray-600 text-xs tabular-nums">{entry.elapsed}</span>
            )}
          </div>
        )
      })}
    </div>
  )
}
