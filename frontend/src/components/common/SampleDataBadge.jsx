import { FlaskConical } from 'lucide-react'

export default function SampleDataBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-violet-50 px-2.5 py-1 text-xs font-medium text-violet-700 ring-1 ring-inset ring-violet-200">
      <FlaskConical className="h-3.5 w-3.5" />
      Sample data — not a real result
    </span>
  )
}
