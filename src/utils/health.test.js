import { test } from 'node:test'
import assert from 'node:assert/strict'
import { healthDetailLines } from './health.js'

const v2 = (oss, extra = {}) => ({ availability: 'available', checked_at: '2026-10-05', context: null, oss, ...extra })

test('a v2 entry shows the last change on the default branch, not the last push', () => {
  const health = v2({
    last_change: { at: '2026-08-02', platform: 'github', archived: false },
    reuse: { github: { forks: 1, stars: 1 } },
  })
  assert.deepEqual(healthDetailLines(health), ['Checked 5 Oct 2026', 'Last change Aug 2026', '1 star on GitHub'])
})

test('Hugging Face downloads name their 30-day window', () => {
  const health = v2({
    last_change: { at: '2023-10-02', platform: 'huggingface', archived: false },
    reuse: { huggingface: { downloads_30d: 440, downloads_all_time: 28186, likes: 7 } },
  })
  assert.deepEqual(healthDetailLines(health), [
    'Checked 5 Oct 2026', 'Last change Oct 2023', '440 downloads on Hugging Face in the last 30 days',
  ])
})

test('an archived repository says so instead of a date', () => {
  const health = v2({ last_change: { at: '2024-10-14', platform: 'github', archived: true }, reuse: { github: { forks: 0, stars: 8 } } })
  assert.deepEqual(healthDetailLines(health), ['Checked 5 Oct 2026', 'GitHub repository archived', '8 stars on GitHub'])
})

test('a v1 entry labels pushed_at as the last push', () => {
  const health = {
    availability: 'available', checked_at: '2026-10-05',
    github: { repo: 'o/r', pushed_at: '2022-10-29T10:00:00Z', archived: false, stars: 11 },
    hf: { id: 'o/d', kind: 'datasets', downloads: 192 },
  }
  assert.deepEqual(healthDetailLines(health), [
    'Checked 5 Oct 2026', 'Last push Oct 2022', '11 stars on GitHub', '192 downloads on Hugging Face in the last 30 days',
  ])
})

test('dates read the same in every time zone', () => {
  const previous = process.env.TZ
  process.env.TZ = 'America/Los_Angeles'
  try {
    assert.equal(healthDetailLines(v2(null))[0], 'Checked 5 Oct 2026')
  } finally {
    process.env.TZ = previous
  }
})
