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

// Dates in health.json are calendar dates measured in UTC; format them in UTC so a reader west of
// Greenwich does not see the day before.
const fmtDate = (iso) => {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
}

const fmtMonthYear = (iso) => {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric', timeZone: 'UTC' })
}

const count = (n, one, many) => `${n.toLocaleString('en-GB')} ${n === 1 ? one : many}`

const starsLine = (stars) =>
  typeof stars === 'number' && stars > 0 ? `${count(stars, 'star', 'stars')} on GitHub` : null

const downloadsLine = (downloads) =>
  typeof downloads === 'number'
    ? `${count(downloads, 'download', 'downloads')} on Hugging Face in the last 30 days`
    : null

// Build the muted supporting-detail lines shown in the detail panel Status section.
// schema_version 2 entries carry an `oss` block (open-source health facts); older entries carry
// `github` / `hf`, whose pushed_at is the last push to any branch, not the last commit.
export const healthDetailLines = (health) => {
  if (!health) return []
  const lines = []

  const checked = fmtDate(health.checked_at)
  if (checked) lines.push(`Checked ${checked}`)

  if (health.oss) {
    const change = health.oss.last_change
    if (change?.archived) {
      lines.push('GitHub repository archived')
    } else {
      const changed = fmtMonthYear(change?.at)
      if (changed) lines.push(`Last change ${changed}`)
    }
    const reuse = health.oss.reuse || {}
    const stars = starsLine(reuse.github?.stars)
    if (stars) lines.push(stars)
    const downloads = downloadsLine(reuse.huggingface?.downloads_30d)
    if (downloads) lines.push(downloads)
    return lines
  }

  if (health.github) {
    if (health.github.archived) {
      lines.push('GitHub repository archived')
    } else {
      const pushed = fmtMonthYear(health.github.pushed_at)
      if (pushed) lines.push(`Last push ${pushed}`)
    }
    const stars = starsLine(health.github.stars)
    if (stars) lines.push(stars)
  }
  const downloads = downloadsLine(health.hf?.downloads)
  if (downloads) lines.push(downloads)

  return lines
}
