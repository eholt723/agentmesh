import { useCallback, useRef, useState } from 'react'

export function useSSEStream({ onEvent, onDone, onError }) {
  const [streaming, setStreaming] = useState(false)
  const readerRef = useRef(null)

  const start = useCallback(async ({ code, language, file }) => {
    setStreaming(true)

    let body, headers

    if (file) {
      const form = new FormData()
      form.append('file', file)
      form.append('language', language)
      body = form
    } else {
      body = JSON.stringify({ code, language })
      headers = { 'Content-Type': 'application/json' }
    }

    try {
      const response = await fetch('/review/stream', {
        method: 'POST',
        headers,
        body,
      })

      if (!response.ok) {
        throw new Error(`HTTP_${response.status}`)
      }

      const reader = response.body.getReader()
      readerRef.current = reader
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // keep incomplete last line

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.slice(6))
              onEvent(parsed)
              if (parsed.type === 'complete' || parsed.type === 'error') {
                setStreaming(false)
                if (parsed.type === 'complete') onDone?.()
                if (parsed.type === 'error') onError?.(parsed.message)
              }
            } catch {
              // malformed SSE line — skip
            }
          }
        }
      }
    } catch (err) {
      onError?.(err.message)
    } finally {
      setStreaming(false)
    }
  }, [onEvent, onDone, onError])

  const stop = useCallback(() => {
    readerRef.current?.cancel()
    setStreaming(false)
  }, [])

  return { streaming, start, stop }
}
