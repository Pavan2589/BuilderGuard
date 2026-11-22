import { FileText } from 'lucide-react'
import SampleDataBadge from '../common/SampleDataBadge'

export default function ReviewSummary({ review }) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-neutral-500" />
          <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
            Review summary
          </h2>
        </div>
        {review._mock && <SampleDataBadge />}
      </div>
      <p className="mt-3 text-sm leading-relaxed text-neutral-800">{review.summary}</p>
      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-xs text-neutral-400">
        <span>Review ID: {review.id}</span>
        <span>Status: {review.status}</span>
      </div>
    </div>
  )
}
