import { Info } from 'lucide-react'

export default function Limitations({ limitations = [] }) {
  if (!limitations.length) return null

  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4">
      <div className="mb-2 flex items-center gap-2">
        <Info className="h-4 w-4 text-neutral-500" />
        <h3 className="text-sm font-semibold text-neutral-700">Review limitations</h3>
      </div>
      <ul className="list-inside list-disc space-y-1 text-sm text-neutral-600">
        {limitations.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ul>
    </div>
  )
}
