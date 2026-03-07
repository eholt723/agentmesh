import { useCallback, useState } from 'react'
import { ActivityLog } from './components/ActivityLog'
import { CodeInput } from './components/CodeInput'
import { EvaluatorPanel } from './components/EvaluatorPanel'
import { FixerPanel } from './components/FixerPanel'
import { ReviewerPanel } from './components/ReviewerPanel'
import { useSSEStream } from './hooks/useSSEStream'

function Panel({ title, children }) {
  return (
    <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5">
      {children}
    </div>
  )
}

export default function App() {
  const [reviewerData, setReviewerData] = useState(null)
  const [fixerData, setFixerData] = useState(null)
  const [evaluatorData, setEvaluatorData] = useState(null)
  const [activityLog, setActivityLog] = useState([])
  const [detectedLanguage, setDetectedLanguage] = useState('')
  const [isRetrying, setIsRetrying] = useState(false)
  const [fixPassCount, setFixPassCount] = useState(0)

  function reset() {
    setReviewerData(null)
    setFixerData(null)
    setEvaluatorData(null)
    setActivityLog([])
    setDetectedLanguage('')
    setIsRetrying(false)
    setFixPassCount(0)
  }

  function addLogEntry(type) {
    setActivityLog((prev) => [
      ...prev,
      { type, timestamp: new Date().toLocaleTimeString() },
    ])
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

  const { streaming, start } = useSSEStream({
    onEvent: handleEvent,
    onDone: () => {},
    onError: (msg) => console.error('Stream error:', msg),
  })

  function handleSubmit(params) {
    reset()
    start(params)
  }

  const hasResults = reviewerData || fixerData || evaluatorData

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-gray-100 tracking-tight">AgentMesh</h1>
          <p className="text-sm text-gray-500">
            Multi-agent code review — Reviewer · Fixer · Evaluator
          </p>
        </div>

        {/* Input */}
        <Panel>
          <CodeInput onSubmit={handleSubmit} streaming={streaming} />
        </Panel>

        {/* Activity log */}
        {activityLog.length > 0 && (
          <ActivityLog entries={activityLog} streaming={streaming} />
        )}

        {/* Results */}
        {hasResults && (
          <div className="space-y-6">
            {reviewerData && (
              <Panel>
                <ReviewerPanel data={reviewerData} />
              </Panel>
            )}

            {fixerData && (
              <Panel>
                <FixerPanel
                  data={fixerData}
                  language={detectedLanguage}
                  isRetry={fixPassCount > 1}
                />
              </Panel>
            )}

            {evaluatorData && (
              <Panel>
                <EvaluatorPanel data={evaluatorData} isRetrying={isRetrying} />
              </Panel>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
