import { test } from 'node:test'
import assert from 'node:assert/strict'
import { ossBlock, brokenLinksNote } from './health.js'

const github = (id, extra = {}) => ({ key: `github:${id.toLowerCase()}`, platform: 'github', id, status: 'measured', ...extra })

const entry = (oss, extra = {}) => ({
  availability: 'available', checked_at: '2026-10-09', context: 'recently_updated', link_count: 3,
  broken_links: [], hosts: { github: 2, website: 1 }, oss, ...extra,
})

// ui_80 as measured on 9 Oct 2026: the approved mockup.
const ui80 = {
  status: 'measured', measured_at: '2026-10-09', window: { start: '2025-10-10', end: '2026-10-09' },
  scope: { github: 1, huggingface: 0, zenodo: 0, unreadable: 1, failed: 0 },
  last_change: { at: '2026-08-02', platform: 'github', archived: false },
  people: { github: { total: 5, active: 2, absence_factor: 2, assets: 1, fork_history: false } },
  releases: { github: { in_window: 0, total: 0, latest_at: null } },
  reuse: { github: { forks: 1, stars: 1 } },
  license: { github: [{ status: 'none', spdx: null, raw: null, assets: 1 }] },
  first_response: null, change_requests: null,
  gaps: [{ metric: 'first_response', reason: 'too_few_items', count: 0 },
    { metric: 'change_request_closure', reason: 'too_few_items', count: 0 }],
  assets: [github('Marconi-Lab/SolarIrradiation'),
    { key: 'github:marconi-lab/irradiation_portal', platform: 'github', id: 'Marconi-Lab/Irradiation_Portal', status: 'unavailable' }],
}

test('the approved mockup project reads exactly as agreed', () => {
  assert.deepEqual(ossBlock(entry(ui80)), {
    dateLabel: 'measured', date: '9 Oct 2026', scope: 'from 1 GitHub repository',
    note: '1 more linked repository could not be read',
    rows: [
      { key: 'last_change', label: 'Last change', chaoss: 'Activity Dates and Times', lines: ['2 Aug 2026'] },
      { key: 'contributors', label: 'Contributors', chaoss: 'Contributors', lines: ['5 people, 2 active in the last 12 months'] },
      { key: 'absence_factor', label: 'Absence factor', chaoss: 'Contributor Absence Factor', lines: ['half the commits came from 2 people'] },
      { key: 'releases', label: 'Releases', chaoss: 'Release Frequency', lines: ['none in the last 12 months'] },
      { key: 'reuse', label: 'Reuse', chaoss: 'Technical Fork, Project Popularity, Number of Downloads', lines: ['1 fork, 1 star'] },
      { key: 'license', label: 'License at source', chaoss: 'Licenses Declared', lines: ['none detected'] },
    ],
    gapsLabel: 'Not measurable',
    gaps: 'response time, pull request closure (too few outside issues or pull requests)',
  })
})

test('a Hugging Face project names its downloads window and what the platform cannot show', () => {
  const hfAsset = (id, kind) => ({ key: `huggingface:${kind}/${id}`, platform: 'huggingface', kind, id, status: 'measured' })
  const block = ossBlock(entry({
    status: 'measured', measured_at: '2026-10-09', window: {},
    scope: { github: 0, huggingface: 2, zenodo: 0, unreadable: 0, failed: 0 },
    last_change: { at: '2023-10-02', platform: 'huggingface', archived: false },
    people: { huggingface: { total: 4, active: 0, absence_factor: 1, assets: 2, fork_history: false } },
    releases: {},
    reuse: { huggingface: { downloads_30d: 440, downloads_all_time: 28186, likes: 7 } },
    license: { huggingface: [{ status: 'detected', spdx: 'CC-BY-4.0', raw: 'cc-by-4.0', assets: 1 },
      { status: 'detected', spdx: 'CC-BY-2.0', raw: 'cc-by-2.0', assets: 1 }] },
    first_response: null, change_requests: null,
    gaps: [{ metric: 'first_response', reason: 'github_only' }, { metric: 'change_request_closure', reason: 'github_only' },
      { metric: 'releases', reason: 'no_releases_on_platform' }],
    assets: [hfAsset('o/ds', 'datasets'), hfAsset('o/model', 'models')],
  }))
  assert.equal(block.scope, 'from 1 Hugging Face dataset and 1 Hugging Face model')
  assert.deepEqual(block.rows.map(r => [r.label, r.lines]), [
    ['Last change', ['2 Oct 2023']],
    ['Contributors', ['4 people, none active in the last 12 months']],
    ['Absence factor', ['half the commits came from 1 person']],
    ['Reuse', ['Hugging Face: 28,186 downloads (440 in the last 30 days), 7 likes']],
    ['License at source', ['CC-BY-4.0, CC-BY-2.0']],
  ])
  assert.equal(block.gaps, 'response time, pull request closure (measured on GitHub only); releases (Hugging Face has no releases)')
})

test('a Zenodo record shows versions and reuse, and names the people gap', () => {
  const block = ossBlock(entry({
    status: 'measured', measured_at: '2026-10-09', window: {},
    scope: { github: 0, huggingface: 0, zenodo: 1, unreadable: 0, failed: 0 },
    last_change: { at: '2025-07-29', platform: 'zenodo', archived: false },
    people: {}, releases: { zenodo: { in_window: 0, total: 2, latest_at: '2025-07-29' } },
    reuse: { zenodo: { downloads: 390, views: 2366 } },
    license: { zenodo: [{ status: 'detected', spdx: 'CC-BY-4.0', raw: 'cc-by-4.0', assets: 1 }] },
    first_response: null, change_requests: null,
    gaps: [{ metric: 'first_response', reason: 'github_only' }, { metric: 'change_request_closure', reason: 'github_only' },
      { metric: 'contributors', reason: 'archive_record' }, { metric: 'absence_factor', reason: 'archive_record' }],
    assets: [{ key: 'zenodo:15778396', platform: 'zenodo', id: '15778396', status: 'measured' }],
  }))
  assert.equal(block.scope, 'from 1 Zenodo record')
  assert.deepEqual(block.rows.map(r => r.lines[0]), ['29 Jul 2025', '2 versions on Zenodo, latest 29 Jul 2025',
    'Zenodo: 390 downloads, 2,366 views', 'CC-BY-4.0'])
  assert.equal(block.gaps, 'response time, pull request closure (measured on GitHub only); ' +
    'contributors, absence factor (a Zenodo record has no commit history)')
})

test('several platforms are named line by line, and a fork says so', () => {
  const block = ossBlock(entry({
    ...ui80,
    scope: { github: 1, huggingface: 1, zenodo: 0, unreadable: 0, failed: 0 },
    last_change: { at: '2025-10-14', platform: 'github', archived: false },
    people: { github: { total: 5, active: 1, absence_factor: 1, assets: 1, fork_history: true },
      huggingface: { total: 1, active: 0, absence_factor: 1, assets: 1, fork_history: false } },
    releases: { github: { in_window: 0, total: 1, latest_at: '2022-04-19' } },
    reuse: { github: { forks: 30, stars: 43 }, huggingface: { downloads_30d: 148, downloads_all_time: 7687, likes: 6 } },
    license: { github: [{ status: 'detected', spdx: 'CC-BY-4.0', raw: 'CC-BY-4.0', assets: 1 }],
      huggingface: [{ status: 'none', spdx: null, raw: null, assets: 1 }] },
    assets: [github('hausanlp/NaijaSenti'),
      { key: 'huggingface:models/d/m', platform: 'huggingface', kind: 'models', id: 'd/m', status: 'measured' }],
  }))
  const rows = Object.fromEntries(block.rows.map(r => [r.key, r.lines]))
  assert.deepEqual(rows.last_change, ['14 Oct 2025 on GitHub'])
  assert.deepEqual(rows.contributors, [
    "GitHub: 5 people, 1 active in the last 12 months (fork, includes the original repository's history)",
    'Hugging Face: 1 person, not active in the last 12 months'])
  assert.deepEqual(rows.absence_factor, ['GitHub: half the commits came from 1 person', 'Hugging Face: 1 person made all the commits'])
  assert.deepEqual(rows.releases, ['none in the last 12 months, latest 19 Apr 2022'])
  assert.deepEqual(rows.reuse, ['GitHub: 30 forks, 43 stars', 'Hugging Face: 7,687 downloads (148 in the last 30 days), 6 likes'])
  assert.deepEqual(rows.license, ['CC-BY-4.0 (GitHub)'])
})

test('an archived repository and a measurable response time read plainly', () => {
  const block = ossBlock(entry({
    ...ui80,
    last_change: { at: '2024-10-14', platform: 'github', archived: true },
    reuse: { github: { forks: 0, stars: 0 } },
    first_response: { items: 12, answered: 10, median_hours: 52.5, median_is_lower_bound: false },
    change_requests: { opened: 6, closed: 4 },
    gaps: [],
  }))
  const rows = Object.fromEntries(block.rows.map(r => [r.key, r.lines]))
  assert.deepEqual(rows.last_change, ['14 Oct 2024, repository archived'])
  assert.deepEqual(rows.reuse, ['no forks or stars'])
  assert.deepEqual(rows.first_response, ['median 2 days (12 outside issues and pull requests)'])
  assert.deepEqual(rows.change_request_closure, ['4 of 6 outside pull requests closed'])
  assert.equal(block.gaps, null)
})

test('a lower-bound median says more than', () => {
  const block = ossBlock(entry({ ...ui80, first_response: { items: 5, answered: 1, median_hours: 760, median_is_lower_bound: true } }))
  assert.deepEqual(block.rows.find(r => r.key === 'first_response').lines, ['median more than 32 days (5 outside issues and pull requests)'])
})

test('a carried-forward block shows the date it was measured', () => {
  assert.equal(ossBlock(entry({ ...ui80, status: 'carried_forward', measured_at: '2026-10-02' })).date, '2 Oct 2026')
})

test('a project whose links are not on a measured platform says so', () => {
  assert.deepEqual(ossBlock(entry(null, { hosts: { website: 2, kaggle: 1 } })), {
    dateLabel: 'checked', date: '9 Oct 2026', scope: null, note: null, rows: [],
    gapsLabel: 'Not measured',
    gaps: 'none of these links is a repository, model or record on GitHub, Hugging Face or Zenodo',
  })
})

test('a project whose only asset could not be read or reached says so', () => {
  const unreadable = ossBlock(entry({ status: 'unreadable', measured_at: '2026-10-09', people: {}, gaps: [],
    assets: [{ key: 'huggingface:spaces/giz/audit_assistant', platform: 'huggingface', id: 'GIZ/audit_assistant', status: 'unavailable' }] }))
  assert.equal(unreadable.gaps, 'the linked Hugging Face space could not be read')
  const failed = ossBlock(entry({ status: 'partial', measured_at: '2026-10-09', people: {}, gaps: [],
    scope: { github: 0, huggingface: 0, zenodo: 0, unreadable: 0, failed: 1 },
    assets: [{ key: 'zenodo:15778396', platform: 'zenodo', id: '15778396', status: 'failed' }] }))
  assert.equal(failed.gaps, 'the linked Zenodo record could not be reached this week')
})

test('no block for opted-out projects, older data or projects without links', () => {
  assert.equal(ossBlock(entry({ status: 'opted_out' })), null)
  assert.equal(ossBlock({ availability: 'available', checked_at: '2026-10-05', github: { pushed_at: '2025-01-01' } }), null)
  assert.equal(ossBlock(undefined), null)
})

test('broken links are counted against all links', () => {
  assert.equal(brokenLinksNote(entry(ui80, { broken_links: ['a'], link_count: 3 })), '1 of 3 links did not respond at the last check')
  assert.equal(brokenLinksNote(entry(ui80, { broken_links: ['a'], link_count: 1 })), 'The link did not respond at the last check')
  assert.equal(brokenLinksNote(entry(ui80)), null)
})

test('dates read the same in every time zone', () => {
  const previous = process.env.TZ
  process.env.TZ = 'America/Los_Angeles'
  try {
    assert.equal(ossBlock(entry(ui80)).date, '9 Oct 2026')
  } finally {
    process.env.TZ = previous
  }
})

test('no output uses an em dash', () => {
  const text = JSON.stringify([ossBlock(entry(ui80)), ossBlock(entry(null, { hosts: { website: 1 } })), brokenLinksNote(entry(ui80, { broken_links: ['a'] }))])
  assert.ok(!text.includes('—'))
})
