import { Syringe } from 'lucide-react'

export default function PayloadViewer({ payload }) {
  if (!payload) return null
  return (
    <div>
      <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-neutral-500">
        <Syringe className="h-3.5 w-3.5" />
        Attack payload
      </div>
      <pre className="overflow-x-auto rounded-md bg-neutral-900 px-3 py-2.5 text-xs text-neutral-100">
        <code>{payload}</code>
      </pre>
    </div>
  )
}
