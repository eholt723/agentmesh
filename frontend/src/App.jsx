import { useCallback, useEffect, useRef, useState } from 'react'
import { ActivityLog } from './components/ActivityLog'
import { CodeInput } from './components/CodeInput'
import { EvaluatorPanel } from './components/EvaluatorPanel'
import { FixerPanel } from './components/FixerPanel'
import { ReviewerPanel } from './components/ReviewerPanel'
import { useSSEStream } from './hooks/useSSEStream'

// ------------------------------
// Icons
// ------------------------------

function SunIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/>
      <line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/>
      <line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  )
}

// ------------------------------
// Panel components
// ------------------------------

function Panel({ children }) {
  return (
    <div className="bg-white dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-xl p-5">
      {children}
    </div>
  )
}

function CollapsiblePanel({ label, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="bg-white dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/40 transition-colors"
      >
        <span className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
          {label}
        </span>
        <svg
          className={`w-2.5 h-2.5 text-gray-400 transition-transform duration-200 ${open ? 'rotate-90' : ''}`}
          fill="currentColor"
          viewBox="0 0 6 10"
        >
          <path d="M0 0l6 5-6 5V0z" />
        </svg>
      </button>
      {open && <div className="px-5 pb-5">{children}</div>}
    </div>
  )
}

// ------------------------------
// Main app
// ------------------------------

export default function App() {
  const [darkMode, setDarkMode] = useState(true)
  const streamStartRef = useRef(null)
  const [reviewerData, setReviewerData] = useState(null)
  const [fixerData, setFixerData] = useState(null)
  const [evaluatorData, setEvaluatorData] = useState(null)
  const [activityLog, setActivityLog] = useState([])
  const [detectedLanguage, setDetectedLanguage] = useState('')
  const [isRetrying, setIsRetrying] = useState(false)
  const [fixPassCount, setFixPassCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState('')

  // Apply/remove dark class on <html>
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  function reset() {
    setReviewerData(null)
    setFixerData(null)
    setEvaluatorData(null)
    setActivityLog([])
    setDetectedLanguage('')
    setIsRetrying(false)
    setFixPassCount(0)
    setErrorMessage('')
  }

  function addLogEntry(type) {
    const elapsed = streamStartRef.current
      ? ((Date.now() - streamStartRef.current) / 1000).toFixed(1) + 's'
      : null
    setActivityLog((prev) => [...prev, { type, elapsed }])
  }

  const handleEvent = useCallback((event) => {
    const { type, data } = event

    switch (type) {
      case 'reviewing':
        addLogEntry('reviewing')
        setReviewerData(data)
        if (data.language) setDetectedLanguage(data.language)
        break

      case 'fixing':
        addLogEntry('fixing')
        setFixerData(data)
        setFixPassCount((n) => n + 1)
        setIsRetrying(false)
        break

      case 'evaluating':
        addLogEntry('evaluating')
        setEvaluatorData(data)
        if (data.evaluator_output?.decision === 'retry') {
          setIsRetrying(true)
          addLogEntry('retry')
        }
        break

      case 'complete':
        addLogEntry('complete')
        setIsRetrying(false)
        break

      case 'error':
        addLogEntry('error')
        setIsRetrying(false)
        break
    }
  }, [])

  function handleError(msg) {
    const isRateLimit = msg?.includes('HTTP_429') || msg?.toLowerCase().includes('rate limit')
    setErrorMessage(
      isRateLimit
        ? 'Rate limit reached. Try a smaller file or wait a moment before resubmitting.'
        : 'Something went wrong. Check the activity log for details.'
    )
  }

  const { streaming, start } = useSSEStream({
    onEvent: handleEvent,
    onDone: () => {},
    onError: handleError,
  })

  function handleSubmit(params) {
    streamStartRef.current = Date.now()
    reset()
    start(params)
  }

  const hasResults = reviewerData || fixerData || evaluatorData

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">

        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 tracking-tight">
              AgentMesh
              <span className="font-normal text-gray-400 dark:text-gray-500">
                {' '}— Multi-Agent Code Review System
              </span>
            </h1>
            <p className="text-sm text-gray-500">
              Reviewer · Fixer · Evaluator
              <span className="text-gray-400 dark:text-gray-600"> · llama-3.3-70b · Groq</span>
            </p>
          </div>

          {/* Light/dark toggle */}
          <button
            type="button"
            onClick={() => setDarkMode((d) => !d)}
            className="p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors"
            aria-label="Toggle light/dark mode"
          >
            {darkMode ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed -mt-4">
          Submit code for review. Three agents collaborate in sequence: the Reviewer identifies
          issues, the Fixer corrects them, and the Evaluator scores the fix for correctness —
          triggering a second pass if the score falls short.
        </p>

        {/* Input */}
        <Panel>
          <CodeInput onSubmit={handleSubmit} streaming={streaming} />
        </Panel>

        {/* Activity log */}
        {activityLog.length > 0 && (
          <ActivityLog entries={activityLog} streaming={streaming} />
        )}

        {/* Detected language badge */}
        {detectedLanguage && (
          <div className="flex items-center gap-2 -mt-4">
            <span className="text-xs text-gray-400 dark:text-gray-500">Detected language:</span>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-cyan-100 dark:bg-cyan-900/40 text-cyan-600 dark:text-cyan-400 capitalize">
              {detectedLanguage}
            </span>
          </div>
        )}

        {/* Error banner */}
        {errorMessage && (
          <div className="flex items-center justify-between gap-3 px-4 py-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-600 dark:text-red-400">
            <span>{errorMessage}</span>
            <button
              type="button"
              onClick={() => setErrorMessage('')}
              className="shrink-0 text-red-400 hover:text-red-600 dark:hover:text-red-300"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        )}

        {/* Results */}
        {hasResults && (
          <div className="space-y-6">
            {reviewerData && (
              <CollapsiblePanel label="Reviewer">
                <ReviewerPanel data={reviewerData} />
              </CollapsiblePanel>
            )}

            {fixerData && (
              <CollapsiblePanel label="Fixer">
                <FixerPanel
                  data={fixerData}
                  language={detectedLanguage}
                  isRetry={fixPassCount > 1}
                />
              </CollapsiblePanel>
            )}

            {evaluatorData && (
              <Panel>
                <EvaluatorPanel data={evaluatorData} isRetrying={isRetrying} />
              </Panel>
            )}
          </div>
        )}
      </div>

      {/* Footer attribution */}
      <div className="fixed bottom-4 right-4 text-right select-none leading-tight">
        <p className="text-xs text-gray-400 dark:text-gray-700">Created by</p>
        <p className="text-xs font-medium text-gray-400 dark:text-gray-500">Eric Holt</p>
      </div>
    </div>
  )
}
