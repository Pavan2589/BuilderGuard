import { Check, X } from 'lucide-react'

export default function AssertionList({ assertions = [] }) {
  if (!assertions.length) {
    return <p className="text-sm text-neutral-400">No assertions were recorded for this run.</p>
  }

  return (
    <ul className="divide-y divide-neutral-100 rounded-lg border border-neutral-200 bg-white">
      {assertions.map((assertion, idx) => (
        <li key={idx} className="flex items-center gap-2.5 px-3 py-2.5">
          {assertion.passed ? (
            <Check className="h-4 w-4 flex-none text-green-600" />
          ) : (
            <X className="h-4 w-4 flex-none text-red-600" />
          )}
          <span className={`text-sm ${assertion.passed ? 'text-neutral-700' : 'text-red-700'}`}>
            {assertion.name}
          </span>
        </li>
      ))}
    </ul>
  )
}
