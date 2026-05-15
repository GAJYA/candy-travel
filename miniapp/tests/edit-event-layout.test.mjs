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

test('map coordinate removal is hidden behind row swipe actions', () => {
  assert.match(
    source,
    /class="map-route-row-action"/,
    'coordinate removal should be attached to the route row action area',
  )
  assert.match(
    source,
    /@touchstart="onMapRouteTouchStart/,
    'route rows should support horizontal swipe gestures',
  )
  assert.doesNotMatch(
    source,
    /class="map-coordinate-action"/,
    'selected map summary should not show a persistent coordinate removal button',
  )
})

test('revealed swipe row removes the foreground right corner seam', () => {
  const revealedRow = styleBlock('.map-route-swipe-row--revealed .map-route-row')

  assert.match(
    revealedRow,
    /border-top-right-radius:\s*0\s*;/,
    'revealed foreground row should not keep a rounded right edge before the action button',
  )
  assert.match(
    revealedRow,
    /border-bottom-right-radius:\s*0\s*;/,
    'revealed foreground row should not show a rounded bottom-right seam',
  )
})

test('selecting a map route remounts the native map viewport', () => {
  assert.match(
    source,
    /:key="tripMapViewportKey"/,
    'native map should have a reactive key so first selection applies the new center immediately',
  )
  assert.match(
    source,
    /tripMapViewportKey\s*=\s*ref\(0\)/,
    'map viewport key should be reactive state',
  )
  assert.match(
    source,
    /tripMapViewportKey\.value\s*\+=\s*1/,
    'selecting a route should refresh the map viewport',
  )
})
