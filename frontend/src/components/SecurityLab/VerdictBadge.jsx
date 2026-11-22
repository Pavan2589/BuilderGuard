import { ShieldCheck, ShieldX, ShieldQuestion } from 'lucide-react'
import { verdictStyle } from '../../utils/severity'

const ICONS = {
  defended: ShieldCheck,
  compromised: ShieldX,
  inconclusive: ShieldQuestion,
}

export default function VerdictBadge({ verdict }) {
  const style = verdictStyle(verdict)
  const Icon = ICONS[String(verdict).toLowerCase()] ?? ShieldQuestion
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${style.badge}`}>
      <Icon className="h-4 w-4" />
      {style.label}
    </span>
  )
}
