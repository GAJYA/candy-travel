import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const source = readFileSync(new URL('../src/pages/edit/index.vue', import.meta.url), 'utf8')

function styleBlock(selector) {
  const marker = `${selector} {`
  const start = source.indexOf(marker)
  assert.notEqual(start, -1, `${selector} style block should exist`)

  const open = source.indexOf('{', start)
  let depth = 0

  for (let index = open; index < source.length; index += 1) {
    const char = source[index]
    if (char === '{') depth += 1
    if (char === '}') depth -= 1
    if (depth === 0) return source.slice(open + 1, index)
  }

  throw new Error(`${selector} style block is not closed`)
}

test('event card grid item can shrink inside the timeline column', () => {
  const eventCard = styleBlock('.event-card')

  assert.match(
    eventCard,
    /min-width:\s*0\s*;/,
    'long event titles must not force the grid column wider than the event panel',
  )
})

test('map route list scrolls vertically without a horizontal stop strip', () => {
  assert.match(
    source,
    /class="map-route-list-scroll"[\s\S]*scroll-y/,
    'map route stops should live in a vertical scroll-view',
  )
  assert.doesNotMatch(
    source,
    /class="map-stop-strip"/,
    'map view should not render a separate horizontal stop strip',
  )
  assert.doesNotMatch(
    source,
    /showTripMapStops/,
    'map route list should be directly scrollable instead of hidden behind a toggle',
  )
})
