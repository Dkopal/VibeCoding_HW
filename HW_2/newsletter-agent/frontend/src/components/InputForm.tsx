import { KeyboardEvent, useState } from 'react'

interface Props {
  onGenerate: (topics: string[], style: string, language: string) => void
  onCancel: () => void
  loading: boolean
}

export function InputForm({ onGenerate, onCancel, loading }: Props) {
  const [input, setInput] = useState('')
  const [topics, setTopics] = useState<string[]>([])
  const [style, setStyle] = useState('casual')
  const [language, setLanguage] = useState('EN')

  const addTopic = () => {
    const trimmed = input.trim()
    if (trimmed && !topics.includes(trimmed) && topics.length < 10) {
      setTopics(prev => [...prev, trimmed])
      setInput('')
    }
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTopic()
    } else if (e.key === 'Backspace' && !input && topics.length > 0) {
      setTopics(prev => prev.slice(0, -1))
    }
  }

  return (
    <div className="bg-slate-800 rounded-2xl p-6 space-y-4">
      <h2 className="text-xl font-semibold text-white">Newsletter Generator</h2>

      <div>
        <label className="text-sm text-slate-400 mb-1 block">Topics (press Enter to add)</label>
        <div className="flex flex-wrap gap-2 p-2 bg-slate-900 rounded-lg border border-slate-600 min-h-[44px]">
          {topics.map(t => (
            <span
              key={t}
              className="bg-indigo-600 text-white text-sm px-2 py-1 rounded-md flex items-center gap-1"
            >
              {t}
              <button
                onClick={() => setTopics(prev => prev.filter(x => x !== t))}
                className="hover:text-red-300 ml-1"
              >
                ×
              </button>
            </span>
          ))}
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            onBlur={addTopic}
            placeholder={topics.length === 0 ? 'e.g. AI, Space, Climate...' : ''}
            className="flex-1 min-w-[120px] bg-transparent outline-none text-white text-sm placeholder-slate-500"
          />
        </div>
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <label className="text-sm text-slate-400 mb-1 block">Style</label>
          <select
            value={style}
            onChange={e => setStyle(e.target.value)}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
          >
            <option value="casual">Casual</option>
            <option value="formal">Formal</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="text-sm text-slate-400 mb-1 block">Language</label>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
          >
            <option value="EN">English</option>
            <option value="CZ">Czech</option>
          </select>
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => topics.length > 0 && onGenerate(topics, style, language)}
          disabled={loading || topics.length === 0}
          className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium py-2 rounded-lg transition-colors"
        >
          {loading ? 'Generating...' : 'Generate Newsletter'}
        </button>
        {loading && (
          <button
            onClick={onCancel}
            className="px-4 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}
