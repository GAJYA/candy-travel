import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import test from 'node:test'
import vm from 'node:vm'
import { readFileSync } from 'node:fs'

const require = createRequire(import.meta.url)
const ts = require('../node_modules/typescript')

const source = readFileSync(new URL('../src/utils/trip-map.ts', import.meta.url), 'utf8')
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

const { buildTripMapData } = module.exports

function tripEvent(id, title, latitude, longitude, sortOrder) {
  return {
    id,
    title,
    locationName: title,
    latitude,
    longitude,
    startAt: `2026-05-16T${String(8 + sortOrder).padStart(2, '0')}:00:00+08:00`,
    endAt: null,
    sortOrder,
    eventType: 'activity',
  }
}

test('destination focus hides both long-distance arrival and return endpoints', () => {
  const data = buildTripMapData([
    tripEvent('shanghai-start', '上海虹桥站', 31.19458, 121.32699, 0),
    tripEvent('yangzhou-1', '张阿姨炸串', 32.38262, 119.42051, 1),
    tripEvent('yangzhou-2', '瘦西湖', 32.41599, 119.42771, 2),
    tripEvent('yangzhou-3', '扬州东站', 32.39824, 119.51513, 3),
    tripEvent('shanghai-end', '上海虹桥站', 31.19458, 121.32699, 4),
  ], { focusMode: 'destination' })

  assert.deepEqual(
    Array.from(data.mappableEvents, (event) => event.id),
    ['yangzhou-1', 'yangzhou-2', 'yangzhou-3'],
  )
  assert.equal(data.hasDestinationFocus, true)
})

test('selected map event becomes the viewport center', () => {
  const data = buildTripMapData([
    tripEvent('yangzhou-1', '张阿姨炸串', 32.38262, 119.42051, 1),
    tripEvent('yangzhou-2', '瘦西湖', 32.41599, 119.42771, 2),
    tripEvent('yangzhou-3', '扬州东站', 32.39824, 119.51513, 3),
  ], { selectedEventId: 'yangzhou-2' })

  assert.equal(data.center.latitude, 32.41599)
  assert.equal(data.center.longitude, 119.42771)
  assert.deepEqual(
    Array.from(data.includePoints, (point) => [point.latitude, point.longitude]),
    [[32.41599, 119.42771]],
  )
  assert.equal(data.scale, 15)
  assert.equal(data.markers[1].iconPath, '/static/logo.png')
})
