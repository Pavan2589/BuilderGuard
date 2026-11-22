import { CheckCircle2, XCircle, CircleDashed, Wrench } from 'lucide-react'
import { toolStatusStyle } from '../../utils/severity'

function StatusIcon({ status }) {
  const normalized = String(status).toLowerCase()
  if (normalized === 'success') return <CheckCircle2 className="h-4 w-4 text-green-600" />
  if (normalized === 'failure' || normalized === 'error') {
    return <XCircle className="h-4 w-4 text-red-600" />
  }
  return <CircleDashed className="h-4 w-4 text-neutral-400" />
}

export default function ToolTimeline({ toolCalls = [], title = 'Tool execution trace' }) {
  if (!toolCalls.length) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-white p-4 text-sm text-neutral-500">
        No tool calls were recorded.
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-neutral-200 bg-white">
      <div className="flex items-center gap-2 border-b border-neutral-200 px-4 py-3">
        <Wrench className="h-4 w-4 text-neutral-500" />
        <h3 className="text-sm font-semibold text-neutral-800">{title}</h3>
      </div>
      <ol className="divide-y divide-neutral-100">
        {toolCalls.map((call, idx) => (
          <li key={`${call.tool}-${idx}`} className="flex items-center gap-3 px-4 py-2.5">
            <span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-neutral-100 text-xs font-medium text-neutral-500">
              {idx + 1}
            </span>
            <code className="flex-1 truncate text-sm text-neutral-800">{call.tool}</code>
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${toolStatusStyle(
                call.status
              )}`}
            >
              <StatusIcon status={call.status} />
              {call.status}
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}
