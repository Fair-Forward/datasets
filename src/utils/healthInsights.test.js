import { test } from 'node:test'
import assert from 'node:assert/strict'
import { summariseBySdg, dotStates } from './healthInsights.js'

const project = (id, sdgs) => ({ id, sdgs })
const flags = (open, measured, changed = null, several = null) =>
  ({ compare: { open_asset: open, measured, changed_12m: changed, several_contributors: several } })

const health = (entries, minGroup = 2) => ({
  schema_version: 2, generated_at: '2026-10-09', method: { min_group: minGroup, window_days: 365 }, entries,
})

const PROJECTS = [
  project('a', ['SDG 2', 'SDG 13']),
  project('b', ['SDG 2']),
  project('c', ['SDG 2']),
  project('d', ['SDG 13']),
  project('e', ['SDG 5']),
]
const ENTRIES = {
  a: flags(true, true, true, true),
  b: flags(true, true, false, false),
  c: flags(true, true, null, null), // measured only through an archive record
  d: flags(true, false),            // open, on a host we do not measure yet
  // e has no health entry: no in-scope links
}

test('a project counts under every SDG it addresses, and the rows follow project counts', () => {
  const summary = summariseBySdg(PROJECTS, health(ENTRIES))
  assert.deepEqual(summary.rows.map(r => [r.label, r.projects]), [['SDG 2', 3], ['SDG 13', 2], ['SDG 5', 1]])
  assert.equal(summary.all.projects, 5)
  assert.equal(summary.measuredAt, '2026-10-09')
})

test('counts open, measured and the facts that apply', () => {
  const sdg2 = summariseBySdg(PROJECTS, health(ENTRIES)).rows[0]
  assert.equal(sdg2.name, 'Zero Hunger')
  assert.deepEqual([sdg2.open, sdg2.measured, sdg2.none], [3, 3, 0])
  assert.deepEqual(sdg2.changed, { yes: 1, of: 2 }) // the archive-only project is left out
  assert.deepEqual(sdg2.several, { yes: 1, of: 2 })
})

test('groups below the minimum show coverage only', () => {
  const sdg13 = summariseBySdg(PROJECTS, health(ENTRIES)).rows[1]
  assert.equal(sdg13.measured, 1)
  assert.equal(sdg13.changed, null)
  assert.equal(sdg13.several, null)
  assert.deepEqual([sdg13.open, sdg13.measured], [2, 1])
})

test('the minimum applies to the projects a view counts, not only to the measured ones', () => {
  // SDG 2 has three measured projects, but the archive-only one has no "changed" or "contributors" fact.
  const sdg2 = summariseBySdg(PROJECTS, health(ENTRIES, 3)).rows[0]
  assert.equal(sdg2.measured, 3)
  assert.equal(sdg2.changed, null)
  assert.equal(sdg2.several, null)
  assert.equal(dotStates(sdg2, 'changed'), null)
  assert.deepEqual(dotStates(sdg2, 'open'), { inked: 3, ringed: 0, faint: 0 })
})

test('names the goals no project addresses', () => {
  assert.deepEqual(summariseBySdg(PROJECTS, health(ENTRIES)).absentSdgs,
    [1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17])
})

test('dots per view: the fact, its absence, and where it does not apply', () => {
  const summary = summariseBySdg(PROJECTS, health(ENTRIES))
  assert.deepEqual(dotStates(summary.all, 'open'), { inked: 3, ringed: 1, faint: 1 })
  assert.deepEqual(dotStates(summary.rows[0], 'changed'), { inked: 1, ringed: 1, faint: 1 })
  assert.deepEqual(dotStates(summary.rows[0], 'several'), { inked: 1, ringed: 1, faint: 1 })
  assert.equal(dotStates(summary.rows[1], 'changed'), null)
})

test('nothing to show for an older health.json', () => {
  assert.equal(summariseBySdg(PROJECTS, { generated_at: '2026-10-05', entries: {} }), null)
  assert.equal(summariseBySdg(PROJECTS, null), null)
})
