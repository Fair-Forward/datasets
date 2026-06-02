// Helpers for rendering the per-entry health / sustainability signal (data/health.json).
// The signal has two parts: availability (always present) and an optional context tag.
// Vocabulary is intentionally neutral -- see docs/health-thresholds.md.

const AVAILABILITY_LABELS = {
  available: 'Available',
  unavailable: 'Link unavailable',
}

const CONTEXT_LABELS = {
  recently_updated: 'Recently updated',
  stable_archive: 'Stable archive',
  no_recent_updates: 'No recent updates',
}

// True when there is a meaningful availability signal worth showing.
export const hasHealthSignal = (health) =>
  Boolean(health) && (health.availability === 'available' || health.availability === 'unavailable')

export const availabilityLabel = (availability) => AVAILABILITY_LABELS[availability] || null

export const contextLabel = (context) => CONTEXT_LABELS[context] || null

// Status filter vocabulary: availability + context as one list, in display order.
export const STATUS_OPTIONS = [
  { value: 'available', label: AVAILABILITY_LABELS.available },
  { value: 'unavailable', label: AVAILABILITY_LABELS.unavailable },
  { value: 'recently_updated', label: CONTEXT_LABELS.recently_updated },
  { value: 'stable_archive', label: CONTEXT_LABELS.stable_archive },
  { value: 'no_recent_updates', label: CONTEXT_LABELS.no_recent_updates },
]

// The status keys an entry matches (its availability plus any context tag).
export const entryStatusValues = (health) => {
  if (!health) return []
  const values = []
  if (health.availability) values.push(health.availability)
  if (health.context) values.push(health.context)
  return values
}

// Filter predicate: an empty status matches everything.
export const matchesStatus = (health, status) =>
  !status || entryStatusValues(health).includes(status)

const fmtDate = (iso) => {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

const fmtMonthYear = (iso) => {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })
}

// Build the muted supporting-detail lines shown in the detail panel Status section.
export const healthDetailLines = (health) => {
  if (!health) return []
  const lines = []

  const checked = fmtDate(health.checked_at)
  if (checked) lines.push(`Checked ${checked}`)

  if (health.github) {
    if (health.github.archived) {
      lines.push('GitHub repository archived')
    } else {
      const updated = fmtMonthYear(health.github.pushed_at)
      if (updated) lines.push(`Last commit ${updated}`)
    }
    if (typeof health.github.stars === 'number' && health.github.stars > 0) {
      lines.push(`${health.github.stars.toLocaleString('en-GB')} stars on GitHub`)
    }
  }

  if (health.hf && typeof health.hf.downloads === 'number') {
    const downloads = health.hf.downloads.toLocaleString('en-GB')
    lines.push(`${downloads} downloads on Hugging Face`)
  }

  return lines
}
