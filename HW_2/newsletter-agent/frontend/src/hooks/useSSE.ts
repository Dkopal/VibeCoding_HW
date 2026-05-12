import { useCallback, useRef, useState } from 'react'

export interface SSEEvent {
  type: string
  payload: unknown
}

export interface SSEState {
  events: SSEEvent[]
  html: string | null
  loading: boolean
  error: string | null
}

export function useSSE() {
  const [state, setState] = useState<SSEState>({
    events: [],
    html: null,
    loading: false,
    error: null,
  })
  const abortRef = useRef<AbortController | null>(null)

  const generate = useCallback(
    async (topics: string[], style: string, language: string) => {
      abortRef.current?.abort()
      const ctrl = new AbortController()
      abortRef.current = ctrl

      setState({ events: [], html: null, loading: true, error: null })

      try {
        const res = await fetch('/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topics, style, language }),
          signal: ctrl.signal,
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        if (!res.body) throw new Error('No response body')

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed.startsWith('data: ')) continue
            try {
              const event: SSEEvent = JSON.parse(trimmed.slice(6))
              if (event.type === 'output:ready') {
                setState(s => ({
                  ...s,
                  html: (event.payload as { html: string }).html,
                }))
              } else if (event.type === 'error') {
                setState(s => ({
                  ...s,
                  error: (event.payload as { message: string }).message,
                }))
              }
              setState(s => ({ ...s, events: [...s.events, event] }))
            } catch {
              // skip malformed line
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setState(s => ({ ...s, error: String(err) }))
        }
      } finally {
        setState(s => ({ ...s, loading: false }))
      }
    },
    [],
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setState(s => ({ ...s, loading: false }))
  }, [])

  return { ...state, generate, cancel }
}
