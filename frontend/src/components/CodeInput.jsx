import { useRef, useState } from 'react'

// ------------------------------
// Constants
// ------------------------------

const LANGUAGES = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'java', label: 'Java' },
  { value: 'csharp', label: 'C#' },
  { value: 'go', label: 'Go' },
  { value: 'other', label: 'Other' },
]

// ------------------------------
// Component
// ------------------------------

export function CodeInput({ onSubmit, streaming }) {
  const [mode, setMode] = useState('text') // 'text' | 'file'
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('auto')
  const [file, setFile] = useState(null)
  const fileRef = useRef(null)

  function handleSubmit(e) {
    e.preventDefault()
    if (mode === 'text' && !code.trim()) return
    if (mode === 'file' && !file) return
    onSubmit({ code, language, file: mode === 'file' ? file : null })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <div className="flex rounded-lg overflow-hidden border border-gray-300 dark:border-gray-700">
          <button
            type="button"
            onClick={() => setMode('text')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              mode === 'text'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
          >
            Paste Code
          </button>
          <button
            type="button"
            onClick={() => setMode('file')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              mode === 'file'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
          >
            Upload File
          </button>
        </div>

        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-200 text-sm rounded-lg px-3 py-2 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
        >
          {LANGUAGES.map((l) => (
            <option key={l.value} value={l.value}>
              {l.label}
            </option>
          ))}
        </select>
      </div>

      {mode === 'text' ? (
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Paste your code here..."
          rows={14}
          className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg p-4 font-mono text-sm text-gray-800 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-600 focus:ring-1 focus:ring-indigo-500 focus:outline-none resize-y"
        />
      ) : (
        <div
          onClick={() => fileRef.current?.click()}
          className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg cursor-pointer hover:border-indigo-500 transition-colors bg-gray-50 dark:bg-gray-900"
        >
          <input
            ref={fileRef}
            type="file"
            accept=".py,.js,.ts,.jsx,.tsx,.java,.cs,.go,.rb,.rs,.cpp,.c,.h,.php,.swift,.kt"
            className="hidden"
            onChange={(e) => setFile(e.target.files[0] || null)}
          />
          {file ? (
            <div className="text-center">
              <p className="text-indigo-500 dark:text-indigo-400 font-medium">{file.name}</p>
              <p className="text-gray-400 text-sm mt-1">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-gray-400 text-sm">Click to upload a code file</p>
              <p className="text-gray-400 dark:text-gray-600 text-xs mt-1">or drag and drop</p>
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between gap-4">
        <p className="text-xs text-gray-400 dark:text-gray-600">
          Best results under 300 lines. Larger files may hit free-tier rate limits.
        </p>
        <button
          type="submit"
          disabled={streaming || (mode === 'text' ? !code.trim() : !file)}
          className="shrink-0 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-200 dark:disabled:bg-gray-700 disabled:text-gray-400 dark:disabled:text-gray-500 text-white font-medium rounded-lg transition-colors"
        >
          {streaming ? 'Reviewing...' : 'Review Code'}
        </button>
      </div>
    </form>
  )
}
