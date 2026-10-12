// CHAOSS metrics by SDG, for the Insights page. Projects are counted, never named: CHAOSS
// advises against comparing projects, so this compares goals, and prints a goal's upkeep figures
// only when it has at least `min_group` measured projects (health.json `method`). The yes/no facts
// per project are decided once in scripts/health_check.py (`compare`), so this page and the private
// report count the same way.
import { parseSdgList } from './sdgColors.js'

const NO_FLAGS = { open_asset: false, measured: false, changed_12m: null, several_contributors: null }

const summarise = (group, entries, minGroup) => {
  let open = 0
  let measured = 0
  const changed = { yes: 0, of: 0 }
  const several = { yes: 0, of: 0 }
  for (const project of group) {
    const flags = entries[project.id]?.compare || NO_FLAGS
    if (flags.open_asset) open += 1
    if (!flags.measured) continue
    measured += 1
    // null means the fact does not apply: an archive record does not "change", a record has no committers.
    if (flags.changed_12m != null) {
      changed.of += 1
      if (flags.changed_12m) changed.yes += 1
    }
    if (flags.several_contributors != null) {
      several.of += 1
      if (flags.several_contributors) several.yes += 1
    }
  }
  // Below the minimum a share is noise and points at single projects, so the fact is not shown.
  return {
    projects: group.length,
    open,
    measured,
    none: group.length - open,
    changed: changed.of < minGroup ? null : changed,
    several: several.of < minGroup ? null : several,
  }
}

export const summariseBySdg = (projects, health) => {
  if (!health || !(health.schema_version >= 2)) return null
  const entries = health.entries || {}
  const minGroup = health.method?.min_group ?? 5

  const bySdg = new Map()
  for (const project of projects) {
    for (const sdg of parseSdgList(project.sdgs)) {
      if (!bySdg.has(sdg.num)) bySdg.set(sdg.num, { sdg, members: [] })
      bySdg.get(sdg.num).members.push(project)
    }
  }
  const rows = [...bySdg.values()]
    .map(({ sdg, members }) => ({
      key: sdg.label, number: sdg.num, label: sdg.label, name: sdg.name, color: sdg.color,
      ...summarise(members, entries, minGroup),
    }))
    .sort((a, b) => b.projects - a.projects || a.number - b.number)

  const absentSdgs = []
  for (let n = 1; n <= 17; n += 1) if (!bySdg.has(n)) absentSdgs.push(n)

  return {
    measuredAt: health.generated_at,
    minGroup,
    all: { key: 'all', label: 'All projects', ...summarise(projects, entries, minGroup) },
    rows,
    absentSdgs,
  }
}

// How many dots a row prints in each state for a view: inked for the fact, ringed for its
// absence, faint where it does not apply. Null when the row shows coverage only.
export const dotStates = (row, view) => {
  if (view === 'open') return { inked: row.measured, ringed: row.open - row.measured, faint: row.none }
  const fact = view === 'changed' ? row.changed : row.several
  if (!fact) return null
  return { inked: fact.yes, ringed: fact.of - fact.yes, faint: row.projects - fact.of }
}
