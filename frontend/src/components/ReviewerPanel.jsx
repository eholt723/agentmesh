// ------------------------------
// Severity styles
// ------------------------------

const SEVERITY_STYLES = {
  critical: 'bg-red-100 text-red-700 border border-red-300 dark:bg-red-900/50 dark:text-red-300 dark:border-red-700',
  warning: 'bg-yellow-100 text-yellow-700 border border-yellow-300 dark:bg-yellow-900/50 dark:text-yellow-300 dark:border-yellow-700',
  suggestion: 'bg-blue-100 text-blue-700 border border-blue-300 dark:bg-blue-900/50 dark:text-blue-300 dark:border-blue-700',
}

function IssueBadge({ severity }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide ${SEVERITY_STYLES[severity]}`}>
      {severity}
    </span>
  )
}

// ------------------------------
// Component
// ------------------------------

export function ReviewerPanel({ data }) {
  if (!data) return null

  const { language, issues = [], summary } = data.reviewer_output || data

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-800 dark:text-gray-200">Reviewer</h2>
        {language && (
          <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 rounded font-mono">
            {language}
          </span>
        )}
      </div>

      {summary && (
        <p className="text-sm text-gray-500 dark:text-gray-400 italic border-l-2 border-gray-300 dark:border-gray-700 pl-3">
          {summary}
        </p>
      )}

      <div className="flex gap-3 text-xs text-gray-500">
        <span>
          <span className="text-red-500 dark:text-red-400 font-medium">
            {issues.filter((i) => i.severity === 'critical').length}
          </span>{' '}
          critical
        </span>
        <span>
          <span className="text-yellow-500 dark:text-yellow-400 font-medium">
            {issues.filter((i) => i.severity === 'warning').length}
          </span>{' '}
          warnings
        </span>
        <span>
          <span className="text-blue-500 dark:text-blue-400 font-medium">
            {issues.filter((i) => i.severity === 'suggestion').length}
          </span>{' '}
          suggestions
        </span>
      </div>

      <div className="space-y-2">
        {issues.map((issue, i) => (
          <div key={i} className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-3 space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <IssueBadge severity={issue.severity} />
              <code className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">
                {issue.line_ref}
              </code>
              <span className="text-xs text-gray-400 dark:text-gray-500">{issue.issue_type}</span>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300">{issue.explanation}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
