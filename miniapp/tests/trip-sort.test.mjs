import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import test from 'node:test'
import vm from 'node:vm'

const require = createRequire(import.meta.url)
const ts = require('../node_modules/typescript')

const source = readFileSync(new URL('../src/utils/trip-sort.ts', import.meta.url), 'utf8')
const output = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
}).outputText

const module = { exports: {} }
vm.runInNewContext(output, {
  exports: module.exports,
  module,
  require,
})

const { sortTripsForDisplay } = module.exports

function trip(id, status, startDate) {
  return {
    id,
    status,
    startDate,
  }
}

test('trip display sort keeps completed trips after incomplete trips', () => {
  const trips = [
    trip('completed-past', 'completed', '2026-01-01'),
    trip('confirmed-later', 'confirmed', '2026-06-01'),
    trip('planning-unscheduled', 'planning', null),
    trip('completed-future', 'completed', '2026-07-01'),
    trip('draft-soon', 'draft', '2026-05-10'),
  ]

  const sorted = sortTripsForDisplay(trips)

  assert.deepEqual(
    sorted.map((item) => item.id),
    [
      'draft-soon',
      'confirmed-later',
      'planning-unscheduled',
      'completed-past',
      'completed-future',
    ],
  )
  assert.deepEqual(
    trips.map((item) => item.id),
    [
      'completed-past',
      'confirmed-later',
      'planning-unscheduled',
      'completed-future',
      'draft-soon',
    ],
    'sorting should not mutate the source trip list',
  )
})
