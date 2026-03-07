import { useEffect, useRef } from 'react'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import java from 'highlight.js/lib/languages/java'
import csharp from 'highlight.js/lib/languages/csharp'
import go from 'highlight.js/lib/languages/go'
import xml from 'highlight.js/lib/languages/xml'
import 'highlight.js/styles/github-dark.css'

hljs.registerLanguage('python', python)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('java', java)
hljs.registerLanguage('csharp', csharp)
hljs.registerLanguage('go', go)
hljs.registerLanguage('xml', xml)

function CodeBlock({ code, language }) {
  const ref = useRef(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.removeAttribute('data-highlighted')
      hljs.highlightElement(ref.current)
    }
  }, [code, language])

  return (
    <div className="bg-gray-950 border border-gray-800 rounded-lg overflow-auto">
      <pre className="p-4 text-sm leading-relaxed overflow-x-auto">
        <code ref={ref} className={language ? `language-${language}` : ''}>
          {code}
        </code>
      </pre>
    </div>
  )
}

export function FixerPanel({ data, language, isRetry }) {
  if (!data) return null

  const { fixed_code, changelog = [] } = data.fixer_output || data

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h2 className="text-base font-semibold text-gray-200">Fixer</h2>
        {isRetry && (
          <span className="text-xs px-2 py-0.5 bg-orange-900/50 text-orange-300 border border-orange-700 rounded">
            retry pass
          </span>
        )}
      </div>

      <CodeBlock code={fixed_code} language={language} />

      {changelog.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-400">Changelog</h3>
          {changelog.map((entry, i) => (
            <div key={i} className="flex gap-3 text-sm bg-gray-900 border border-gray-800 rounded-lg p-3">
              <span className="text-green-400 mt-0.5 shrink-0">+</span>
              <div>
                <p className="text-gray-300">{entry.change_made}</p>
                <p className="text-gray-600 text-xs mt-0.5">resolves: {entry.issue_ref}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
