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
  }

  if (health.hf && typeof health.hf.downloads === 'number') {
    const downloads = health.hf.downloads.toLocaleString('en-GB')
    lines.push(`${downloads} downloads on Hugging Face`)
  }

  return lines
}
