interface Props {
  html: string
}

export function Newsletter({ html }: Props) {
  const download = () => {
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'newsletter.html'
    a.click()
    URL.revokeObjectURL(url)
  }

  const copy = () => {
    navigator.clipboard.writeText(html)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Newsletter</h3>
        <div className="flex gap-2">
          <button
            onClick={copy}
            className="text-sm bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded-lg transition-colors"
          >
            Copy HTML
          </button>
          <button
            onClick={download}
            className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg transition-colors"
          >
            Download
          </button>
        </div>
      </div>
      <iframe
        srcDoc={html}
        className="w-full rounded-xl border border-slate-700 bg-white"
        style={{ height: '600px' }}
        sandbox="allow-same-origin"
        title="Newsletter preview"
      />
    </div>
  )
}
