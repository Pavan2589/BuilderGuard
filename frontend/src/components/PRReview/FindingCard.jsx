import { FileCode2, Lightbulb, Search } from 'lucide-react'

export default function FindingCard({ finding }) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h4 className="text-sm font-semibold text-neutral-900">{finding.title}</h4>
        {(finding.file || finding.line) && (
          <span className="inline-flex items-center gap-1.5 rounded-md bg-neutral-50 px-2 py-1 text-xs font-mono text-neutral-600 ring-1 ring-inset ring-neutral-200">
            <FileCode2 className="h-3.5 w-3.5" />
            {finding.file}
            {finding.line != null && `:${finding.line}`}
          </span>
        )}
      </div>

      {finding.explanation && (
        <p className="mt-2 text-sm leading-relaxed text-neutral-600">{finding.explanation}</p>
      )}

      {finding.evidence && (
        <div className="mt-3">
          <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-neutral-500">
            <Search className="h-3.5 w-3.5" />
            Evidence
          </div>
          <pre className="overflow-x-auto rounded-md bg-neutral-900 px-3 py-2 text-xs text-neutral-100">
            <code>{finding.evidence}</code>
          </pre>
        </div>
      )}

      {finding.suggestion && (
        <div className="mt-3 rounded-md bg-blue-50 p-3 ring-1 ring-inset ring-blue-100">
          <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-blue-700">
            <Lightbulb className="h-3.5 w-3.5" />
            Suggested fix
          </div>
          <p className="text-sm text-blue-800">{finding.suggestion}</p>
        </div>
      )}
    </div>
  )
}
