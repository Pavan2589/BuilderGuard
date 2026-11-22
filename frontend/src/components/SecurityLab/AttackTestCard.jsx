import { ChevronRight, ShieldCheck, ShieldX, ShieldQuestion } from 'lucide-react'
import { formatCategory } from './CategorySelector'

function VerdictIcon({ verdict }) {
  if (verdict === 'defended') return <ShieldCheck className="h-4 w-4 text-green-600" />
  if (verdict === 'compromised') return <ShieldX className="h-4 w-4 text-red-600" />
  if (verdict === 'inconclusive') return <ShieldQuestion className="h-4 w-4 text-amber-600" />
  return null
}

export default function AttackTestCard({ test, selected, lastVerdict, onSelect }) {
  return (
    <button
      onClick={() => onSelect(test.id)}
      className={`w-full rounded-lg border p-3 text-left transition ${
        selected
          ? 'border-neutral-900 bg-neutral-900/[0.03] ring-1 ring-neutral-900'
          : 'border-neutral-200 bg-white hover:border-neutral-300'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-neutral-900">{test.name}</p>
          <p className="mt-0.5 text-xs text-neutral-400">{formatCategory(test.category)}</p>
        </div>
        <div className="flex flex-none items-center gap-1.5">
          {lastVerdict && <VerdictIcon verdict={lastVerdict} />}
          <ChevronRight className="h-4 w-4 text-neutral-300" />
        </div>
      </div>
      <p className="mt-2 line-clamp-2 text-xs text-neutral-500">{test.description}</p>
    </button>
  )
}
