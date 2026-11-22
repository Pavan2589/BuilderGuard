export const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low']

export const SEVERITY_STYLES = {
  critical: {
    label: 'Critical',
    badge: 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200',
    dot: 'bg-red-600',
  },
  high: {
    label: 'High',
    badge: 'bg-orange-50 text-orange-700 ring-1 ring-inset ring-orange-200',
    dot: 'bg-orange-500',
  },
  medium: {
    label: 'Medium',
    badge: 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200',
    dot: 'bg-amber-500',
  },
  low: {
    label: 'Low',
    badge: 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200',
    dot: 'bg-blue-500',
  },
}

export function severityStyle(severity) {
  return (
    SEVERITY_STYLES[String(severity).toLowerCase()] ?? {
      label: severity ?? 'Unknown',
      badge: 'bg-neutral-100 text-neutral-700 ring-1 ring-inset ring-neutral-200',
      dot: 'bg-neutral-400',
    }
  )
}

export function groupFindingsBySeverity(findings = []) {
  const groups = new Map()
  for (const finding of findings) {
    const key = String(finding.severity ?? 'unknown').toLowerCase()
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(finding)
  }
  const ordered = []
  for (const key of SEVERITY_ORDER) {
    if (groups.has(key)) {
      ordered.push([key, groups.get(key)])
      groups.delete(key)
    }
  }
  for (const [key, items] of groups) {
    ordered.push([key, items])
  }
  return ordered
}

export const VERDICT_STYLES = {
  defended: {
    label: 'Defended',
    badge: 'bg-green-50 text-green-700 ring-1 ring-inset ring-green-200',
  },
  compromised: {
    label: 'Compromised',
    badge: 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200',
  },
  inconclusive: {
    label: 'Inconclusive',
    badge: 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200',
  },
}

export function verdictStyle(verdict) {
  return (
    VERDICT_STYLES[String(verdict).toLowerCase()] ?? {
      label: verdict ?? 'Unknown',
      badge: 'bg-neutral-100 text-neutral-700 ring-1 ring-inset ring-neutral-200',
    }
  )
}

export function toolStatusStyle(status) {
  const normalized = String(status).toLowerCase()
  if (normalized === 'success') {
    return 'bg-green-50 text-green-700 ring-1 ring-inset ring-green-200'
  }
  if (normalized === 'failure' || normalized === 'error') {
    return 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200'
  }
  return 'bg-neutral-100 text-neutral-700 ring-1 ring-inset ring-neutral-200'
}
