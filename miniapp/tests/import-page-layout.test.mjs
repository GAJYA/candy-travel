import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const pagesConfig = JSON.parse(readFileSync(new URL('../src/pages.json', import.meta.url), 'utf8'))
const bottomNavSource = readFileSync(new URL('../src/components/CandyBottomNav.vue', import.meta.url), 'utf8')
const importPageSource = readFileSync(new URL('../src/pages/import/index.vue', import.meta.url), 'utf8')

test('import page is registered and reachable from bottom navigation', () => {
  assert.ok(
    pagesConfig.pages.some((page) => page.path === 'pages/import/index'),
    'import page should be registered in pages.json',
  )
  assert.match(
    bottomNavSource,
    /\{\s*key:\s*'import'[\s\S]*url:\s*'\/pages\/import\/index'/,
    'import bottom nav item should navigate to the import page',
  )
  assert.doesNotMatch(
    bottomNavSource,
    /\{\s*key:\s*'import'[\s\S]*disabled:\s*true/,
    'import bottom nav item should be enabled',
  )
})

test('import page collects share text and user-selected dates', () => {
  assert.match(
    importPageSource,
    /v-model="shareText"/,
    'import page should bind a share text textarea',
  )
  assert.match(
    importPageSource,
    /placeholder="粘贴旅行分享链接或分享文案"/,
    'share text input should describe generic travel shares',
  )
  assert.match(
    importPageSource,
    /mode="date"[\s\S]*@change="onStartDateChange"/,
    'import page should let users choose a start date',
  )
  assert.match(
    importPageSource,
    /mode="date"[\s\S]*@change="onEndDateChange"/,
    'import page should let users choose an end date',
  )
  assert.match(
    importPageSource,
    /inspirationApi\.createShareImportJob/,
    'import page should submit a backend import job instead of holding a long request',
  )
  assert.match(
    importPageSource,
    /tripApi\.create/,
    'import page should create a trip after extraction',
  )
  assert.match(
    importPageSource,
    /quickImportApi\.importTripEvents/,
    'import page should import extracted places as editable trip events',
  )
  assert.match(
    importPageSource,
    /normalizeShareEventCandidates/,
    'import page should fill missing event dates from the user-selected date range before importing',
  )
})
