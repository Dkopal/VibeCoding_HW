import { useEffect, useRef } from 'react'
import type { SSEEvent } from '../hooks/useSSE'

const TYPE_COLORS: Record<string, string> = {
  'supervisor:plan_ready': 'text-purple-400',
  'research:started': 'text-blue-400',
  'research:done': 'text-green-400',
  'research:skipped': 'text-yellow-400',
  'writer:draft_ready': 'text-cyan-400',
  'editor:approved': 'text-emerald-400',
  'output:ready': 'text-pink-400',
  error: 'text-red-400',
}

function colorFor(type: string): string {
  if (type.startsWith('editor:iteration')) return 'text-orange-400'
  return TYPE_COLORS[type] ?? 'text-slate-400'
}

function summarize(event: SSEEvent): string {
  const p = event.payload as Record<string, unknown>
  switch (event.type) {
    case 'supervisor:plan_ready':
      return `Planned ${(p.tasks as unknown[]).length} research tasks`
    case 'research:started':
      return `Researching: ${p.topic}`
    case 'research:done':
      return `Done: ${p.topic} — found: ${p.found}`
    case 'research:skipped':
      return `Skipped (no results): ${p.topic}`
    case 'writer:draft_ready':
      return `Draft ready (${p.length} chars)`
    case 'editor:approved':
      return `Approved after ${p.iterations} iteration(s)${p.forced ? ' (max reached)' : ''}`
    case 'output:ready':
      return 'Newsletter HTML ready'
    case 'error':
      return `Error: ${p.message}`
    default:
      if (event.type.startsWith('editor:iteration'))
        return `Editor pass ${(event.type.split(':')[2])}`
      return event.type
  }
}

interface Props {
  events: SSEEvent[]
}

export function AgentLog({ events }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  if (events.length === 0) return null

  return (
    <div className="bg-slate-900 rounded-2xl p-4 font-mono text-sm space-y-1 max-h-72 overflow-y-auto border border-slate-700">
      <p className="text-slate-500 text-xs mb-2">Agent activity</p>
      {events.map((e, i) => (
        <div key={i} className="flex gap-2">
          <span className="text-slate-600 select-none">{String(i + 1).padStart(2, '0')}</span>
          <span className={`${colorFor(e.type)} font-medium min-w-[220px]`}>{e.type}</span>
          <span className="text-slate-300">{summarize(e)}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
