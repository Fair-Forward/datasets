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
const fmtDay = (iso) => {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
}

export const formatDay = fmtDay

const count = (n, one, many) => `${n.toLocaleString('en-GB')} ${n === 1 ? one : many}`

const listOf = (items) =>
  items.length > 1 ? `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}` : items[0]

const PLATFORM_NAMES = { github: 'GitHub', huggingface: 'Hugging Face', zenodo: 'Zenodo' }
const PLATFORM_ORDER = ['github', 'huggingface', 'zenodo']

// What a linked asset is: "GitHub repository", "Hugging Face dataset", "Zenodo record".
const assetNoun = (asset) => {
  if (asset.platform === 'github') return ['GitHub repository', 'GitHub repositories']
  if (asset.platform === 'zenodo') return ['Zenodo record', 'Zenodo records']
  const kind = asset.kind || (asset.key || '').split(':')[1]?.split('/')[0]
  const one = { datasets: 'dataset', models: 'model', spaces: 'space' }[kind]
  return one ? [`Hugging Face ${one}`, `Hugging Face ${one}s`] : ['Hugging Face repository', 'Hugging Face repositories']
}

// In "1 more linked repository could not be read" GitHub needs no name.
const shortNoun = (asset) => (asset.platform === 'github' ? ['repository', 'repositories'] : assetNoun(asset))

const describeMissing = (assets, verb, { more }) => {
  if (!assets.length) return null
  const nouns = assets.map(more ? shortNoun : assetNoun)
  const same = nouns.every(noun => noun[0] === nouns[0][0])
  if (more) {
    return same
      ? `${assets.length} more linked ${assets.length === 1 ? nouns[0][0] : nouns[0][1]} ${verb}`
      : `${assets.length} more links ${verb}`
  }
  if (assets.length === 1) return `the linked ${nouns[0][0]} ${verb}`
  return same ? `the ${assets.length} linked ${nouns[0][1]} ${verb}` : `${assets.length} links ${verb}`
}

const missingText = (assets, options) => [
  describeMissing(assets.filter(a => a.status === 'unavailable'), 'could not be read', options),
  describeMissing(assets.filter(a => a.status === 'failed'), 'could not be reached this week', options),
].filter(Boolean).join('; ') || null

// "from 1 GitHub repository and 2 Hugging Face datasets": the measured assets, by kind.
const scopeText = (oss, measured) => {
  const groups = new Map()
  for (const asset of measured) {
    const [one, many] = assetNoun(asset)
    const group = groups.get(one) || { one, many, n: 0 }
    group.n += 1
    groups.set(one, group)
  }
  // Two versions of one Zenodo record are one record (the collector counts them in scope.zenodo).
  const zenodo = groups.get('Zenodo record')
  if (zenodo && typeof oss.scope?.zenodo === 'number') zenodo.n = oss.scope.zenodo
  return groups.size ? `from ${listOf([...groups.values()].map(g => count(g.n, g.one, g.many)))}` : null
}

const peopleText = (p) => {
  let active
  if (!p.active) active = p.total === 1 ? 'not active in the last 12 months' : 'none active in the last 12 months'
  else active = p.total === 1 ? 'active in the last 12 months' : `${p.active} active in the last 12 months`
  const text = `${count(p.total, 'person', 'people')}, ${active}`
  return p.fork_history ? `${text} (fork, includes the original repository's history)` : text
}

const absenceText = (p) =>
  p.total === 1 ? '1 person made all the commits' : `half the commits came from ${count(p.absence_factor, 'person', 'people')}`

const releaseLines = (releases = {}) => {
  const lines = []
  const github = releases.github
  if (github) {
    const recent = github.in_window ? `${github.in_window} in the last 12 months` : 'none in the last 12 months'
    lines.push(github.latest_at ? `${recent}, latest ${fmtDay(github.latest_at)}` : recent)
  }
  const zenodo = releases.zenodo
  if (zenodo) {
    const latest = zenodo.latest_at ? `, latest ${fmtDay(zenodo.latest_at)}` : ''
    lines.push(`${count(zenodo.total, 'version', 'versions')} on Zenodo${latest}`)
  }
  if (github && zenodo) lines[0] = `GitHub: ${lines[0]}`
  return lines
}

const reuseLines = (reuse = {}) => {
  const lines = []
  const github = reuse.github
  if (github) {
    const forks = github.forks || 0
    const stars = github.stars || 0
    lines.push(forks || stars ? `${count(forks, 'fork', 'forks')}, ${count(stars, 'star', 'stars')}` : 'no forks or stars')
  }
  const hf = reuse.huggingface
  if (hf) {
    const parts = []
    if (typeof hf.downloads_all_time === 'number') {
      const recent = typeof hf.downloads_30d === 'number' ? ` (${hf.downloads_30d.toLocaleString('en-GB')} in the last 30 days)` : ''
      parts.push(`${count(hf.downloads_all_time, 'download', 'downloads')}${recent}`)
    } else if (typeof hf.downloads_30d === 'number') {
      parts.push(`${count(hf.downloads_30d, 'download', 'downloads')} in the last 30 days`)
    }
    if (hf.likes) parts.push(count(hf.likes, 'like', 'likes'))
    if (parts.length) lines.push(`Hugging Face: ${parts.join(', ')}`)
  }
  const zenodo = reuse.zenodo
  if (zenodo) {
    const parts = []
    if (typeof zenodo.downloads === 'number') parts.push(count(zenodo.downloads, 'download', 'downloads'))
    if (typeof zenodo.views === 'number') parts.push(count(zenodo.views, 'view', 'views'))
    if (parts.length) lines.push(`Zenodo: ${parts.join(', ')}`)
  }
  if (github && lines.length > 1) lines[0] = `GitHub: ${lines[0]}`
  return lines
}

const LICENSE_LABELS = {
  detected: (item) => item.spdx,
  unrecognised: () => 'a license file GitHub does not recognise',
  other: (item) => item.raw,
}

const licenseText = (license = {}) => {
  const platforms = PLATFORM_ORDER.filter(p => license[p]?.length)
  if (!platforms.length) return null
  const named = platforms.map(p => {
    const labels = []
    for (const item of license[p]) {
      const label = LICENSE_LABELS[item.status]?.(item)
      if (label && !labels.includes(label)) labels.push(label)
    }
    return [p, labels]
  }).filter(([, labels]) => labels.length)
  if (!named.length) return 'none detected'
  if (platforms.length === 1) return named[0][1].join(', ')
  return named.map(([p, labels]) => `${labels.join(', ')} (${PLATFORM_NAMES[p]})`).join(', ')
}

const duration = (hours) =>
  hours < 48 ? count(Math.max(1, Math.round(hours)), 'hour', 'hours') : count(Math.round(hours / 24), 'day', 'days')

const GAP_METRICS = {
  last_change: 'last change',
  releases: 'releases',
  contributors: 'contributors',
  absence_factor: 'absence factor',
  first_response: 'response time',
  change_request_closure: 'pull request closure',
}

const GAP_REASONS = {
  too_few_items: 'too few outside issues or pull requests',
  github_only: 'measured on GitHub only',
  no_releases_on_platform: 'Hugging Face has no releases',
  archive_record: 'a Zenodo record has no commit history',
  gated: 'gated dataset',
  unreadable: 'commit history could not be read',
  empty_repository: 'empty repository',
  no_human_commits: 'no commits by people',
}

// "response time, pull request closure (too few outside issues or pull requests)": gaps grouped by reason.
const gapsText = (gaps = []) => {
  const groups = new Map()
  for (const gap of gaps) {
    const metric = GAP_METRICS[gap.metric]
    const reason = GAP_REASONS[gap.reason]
    if (!metric || !reason) continue
    const metrics = groups.get(reason) || []
    if (!metrics.includes(metric)) metrics.push(metric)
    groups.set(reason, metrics)
  }
  return groups.size ? [...groups].map(([reason, metrics]) => `${metrics.join(', ')} (${reason})`).join('; ') : null
}

const NOT_ON_A_MEASURED_PLATFORM = 'none of these links is a repository, model or record on GitHub, Hugging Face or Zenodo'

// The detail panel's "Open-source health" block (see docs/health-thresholds.md, Part 4): rows of
// facts measured with CHAOSS metric definitions, and the gaps named in one line. Null when there is
// nothing to show: no health entry, an older health.json, or a project left out at its maintainers' request.
export const ossBlock = (health) => {
  if (!health || (!health.oss && !health.hosts)) return null
  const oss = health.oss
  if (!oss) {
    return { dateLabel: 'checked', date: fmtDay(health.checked_at), scope: null, note: null, rows: [],
      gapsLabel: 'Not measured', gaps: NOT_ON_A_MEASURED_PLATFORM }
  }
  if (oss.status === 'opted_out') return null
  const assets = oss.assets || []
  const measured = assets.filter(a => a.status === 'measured')
  if (!measured.length) {
    return { dateLabel: 'checked', date: fmtDay(oss.measured_at || health.checked_at), scope: null, note: null,
      rows: [], gapsLabel: 'Not measured', gaps: missingText(assets, { more: false }) }
  }

  const rows = []
  const add = (key, label, lines) => { if (lines.length) rows.push({ key, label, lines }) }

  const change = oss.last_change
  if (change?.at) {
    const platforms = new Set(measured.map(a => a.platform))
    let text = fmtDay(change.at)
    if (change.archived) text += ', repository archived'
    else if (platforms.size > 1) text += ` on ${PLATFORM_NAMES[change.platform]}`
    add('last_change', 'Last change', [text])
  }

  const withPeople = PLATFORM_ORDER.filter(p => oss.people?.[p]?.total)
  const named = (p, text) => (withPeople.length > 1 ? `${PLATFORM_NAMES[p]}: ${text}` : text)
  add('contributors', 'Contributors', withPeople.map(p => named(p, peopleText(oss.people[p]))))
  add('absence_factor', 'Absence factor', withPeople
    .filter(p => oss.people[p].absence_factor != null)
    .map(p => named(p, absenceText(oss.people[p]))))

  add('releases', 'Releases', releaseLines(oss.releases))
  add('reuse', 'Reuse', reuseLines(oss.reuse))
  const license = licenseText(oss.license)
  if (license) add('license', 'License at source', [license])

  const response = oss.first_response
  if (response) {
    const median = `median ${response.median_is_lower_bound ? 'more than ' : ''}${duration(response.median_hours)}`
    add('first_response', 'Response time',
      [`${median} (${count(response.items, 'outside issue or pull request', 'outside issues and pull requests')})`])
  }
  const requests = oss.change_requests
  if (requests) {
    add('change_request_closure', 'Pull request closure',
      [`${requests.closed} of ${count(requests.opened, 'outside pull request', 'outside pull requests')} closed`])
  }

  return {
    dateLabel: 'measured',
    date: fmtDay(oss.measured_at),
    scope: scopeText(oss, measured),
    note: missingText(assets, { more: true }),
    rows,
    gapsLabel: 'Not measurable',
    gaps: gapsText(oss.gaps),
  }
}

// "1 of 3 links did not respond at the last check", shown under the Status row.
export const brokenLinksNote = (health) => {
  const broken = health?.broken_links?.length || 0
  if (!broken) return null
  const total = health.link_count || broken
  if (total === 1) return 'The link did not respond at the last check'
  return `${broken} of ${total} links did not respond at the last check`
}
