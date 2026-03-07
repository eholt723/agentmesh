function ScoreRing({ score, label, color }) {
  const radius = 28
  const circumference = 2 * Math.PI * radius
  const filled = (score / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative w-16 h-16">
        <svg className="w-16 h-16 -rotate-90" viewBox="0 0 72 72">
          <circle cx="36" cy="36" r={radius} fill="none" stroke="#1f2937" strokeWidth="6" />
          <circle
            cx="36"
            cy="36"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeDasharray={`${filled} ${circumference}`}
            strokeLinecap="round"
            className="transition-all duration-700"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-200">
          {score}
        </span>
      </div>
      <span className="text-xs text-gray-400 text-center">{label}</span>
    </div>
  )
}

const DECISION_STYLES = {
  pass: {
    bg: 'bg-green-900/30 border-green-700',
    text: 'text-green-300',
    label: 'PASS',
  },
  fail: {
    bg: 'bg-red-900/30 border-red-700',
    text: 'text-red-300',
    label: 'FAIL',
  },
  retry: {
    bg: 'bg-orange-900/30 border-orange-700',
    text: 'text-orange-300',
    label: 'RETRY',
  },
}

export function EvaluatorPanel({ data, isRetrying }) {
  if (!data) return null

  const {
    correctness,
    completeness,
    code_quality,
    overall_score,
    decision,
    feedback,
  } = data.evaluator_output || data

  const style = DECISION_STYLES[decision] || DECISION_STYLES.fail

  return (
    <div className="space-y-4">
      <h2 className="text-base font-semibold text-gray-200">Evaluator</h2>

      <div className="flex items-center gap-6 bg-gray-900 border border-gray-800 rounded-lg p-4">
        <div className="flex gap-5">
          <ScoreRing score={correctness.score} label="Correctness" color="#6366f1" />
          <ScoreRing score={completeness.score} label="Completeness" color="#8b5cf6" />
          <ScoreRing score={code_quality.score} label="Code Quality" color="#a78bfa" />
        </div>

        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold text-gray-100">{overall_score}</span>
            <span className="text-gray-500 text-sm">/100</span>
            <span
              className={`ml-2 px-3 py-1 rounded border text-xs font-bold tracking-widest ${style.bg} ${style.text}`}
            >
              {style.label}
            </span>
          </div>

          {isRetrying && (
            <div className="flex items-center gap-2 text-orange-400 text-sm">
              <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
              <span>Sending back to Fixer...</span>
            </div>
          )}
        </div>
      </div>

      {feedback && (
        <div className="text-sm text-gray-400 bg-gray-900 border border-gray-800 rounded-lg p-3 italic">
          {feedback}
        </div>
      )}

      <div className="grid grid-cols-3 gap-3 text-xs">
        {[
          { label: 'Correctness', data: correctness },
          { label: 'Completeness', data: completeness },
          { label: 'Code Quality', data: code_quality },
        ].map(({ label, data: dim }) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded p-2.5 space-y-1">
            <span className="text-gray-500 font-medium">{label}</span>
            <p className="text-gray-400 leading-relaxed">{dim.notes}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
