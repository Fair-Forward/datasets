// Run with `npm test` (node's built-in runner; no extra dependencies).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { MATURITY_STAGES, furthestStage, gridSlot, printOrder, reachedCount } from './maturity.js'

const project = (title, maturity_tags, extra = {}) => ({ title, maturity_tags, ...extra })

test('lists the five stages in pipeline order', () => {
  assert.deepEqual(MATURITY_STAGES.map(s => s.key), ['dataset', 'model', 'pilot', 'usecase', 'business'])
})

test('a project stands at the furthest stage it reached', () => {
  assert.equal(furthestStage(project('a', ['dataset', 'model', 'pilot'])), 'pilot')
  assert.equal(furthestStage(project('b', ['dataset', 'model', 'pilot', 'usecase', 'business'])), 'business')
  assert.equal(furthestStage(project('c', [])), null)
  assert.equal(furthestStage({}), null)
})

test('orders projects furthest first, so each column fills from the bottom', () => {
  const order = printOrder([
    project('Delta', ['dataset']),
    project('Alpha', ['dataset', 'model', 'pilot']),
    project('Beta', ['dataset']),
    project('Gamma', ['dataset', 'model', 'pilot', 'usecase', 'business']),
    project('Untagged', null)
  ])
  assert.deepEqual(order.map(p => p.title), ['Gamma', 'Alpha', 'Beta', 'Delta'])
})

test('puts Lacuna Fund projects first within a stage when asked', () => {
  const projects = [
    project('Alpha', ['dataset']),
    project('Beta', ['dataset'], { is_lacuna: true }),
    project('Gamma', ['dataset', 'model'])
  ]
  assert.deepEqual(printOrder(projects, { lacunaFirst: true }).map(p => p.title), ['Gamma', 'Beta', 'Alpha'])
})

test('counts a stage the way the catalogue filter does, cumulatively', () => {
  const projects = [
    project('a', ['dataset']),
    project('b', ['dataset', 'model']),
    project('c', ['dataset', 'model', 'pilot', 'usecase'])
  ]
  assert.equal(reachedCount(projects, 'dataset'), 3)
  assert.equal(reachedCount(projects, 'model'), 2)
  assert.equal(reachedCount(projects, 'business'), 0)
})

test('fills a column row by row from the bottom left', () => {
  assert.deepEqual(gridSlot(0, 8), { row: 0, col: 0 })
  assert.deepEqual(gridSlot(9, 8), { row: 1, col: 1 })
  assert.deepEqual(gridSlot(9, 5), { row: 1, col: 4 })
})
