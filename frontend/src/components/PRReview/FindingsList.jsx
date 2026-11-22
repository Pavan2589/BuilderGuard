import { ShieldCheck } from 'lucide-react'
import { groupFindingsBySeverity, severityStyle } from '../../utils/severity'
import FindingCard from './FindingCard'

export default function FindingsList({ findings = [] }) {
  if (!findings.length) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
        <ShieldCheck className="h-5 w-5 flex-none text-green-600" />
        <p className="text-sm text-green-800">No findings were reported for this pull request.</p>
      </div>
    )
  }

  const grouped = groupFindingsBySeverity(findings)

  return (
    <div className="space-y-6">
      {grouped.map(([severity, items]) => {
        const style = severityStyle(severity)
        return (
          <div key={severity}>
            <div className="mb-2 flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${style.dot}`} />
              <h3 className="text-sm font-semibold text-neutral-800">
                {style.label} <span className="text-neutral-400">({items.length})</span>
              </h3>
            </div>
            <div className="space-y-3">
              {items.map((finding, idx) => (
                <FindingCard key={`${finding.file}-${finding.line}-${idx}`} finding={finding} />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
