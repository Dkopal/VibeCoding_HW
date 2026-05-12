import { AgentLog } from './components/AgentLog'
import { InputForm } from './components/InputForm'
import { Newsletter } from './components/Newsletter'
import { useSSE } from './hooks/useSSE'

export default function App() {
  const { events, html, loading, error, generate, cancel } = useSSE()

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white">AI Newsletter Generator</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Multi-agent: Supervisor → Parallel Research → Conditional Gate → Writer → Editor Loop
          </p>
        </div>

        <InputForm onGenerate={generate} onCancel={cancel} loading={loading} />

        {error && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-xl p-4 text-sm">
            {error}
          </div>
        )}

        <AgentLog events={events} />

        {html && <Newsletter html={html} />}
      </div>
    </div>
  )
}
