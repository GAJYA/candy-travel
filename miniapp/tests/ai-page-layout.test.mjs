import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const pagesConfig = JSON.parse(readFileSync(new URL('../src/pages.json', import.meta.url), 'utf8'))
const bottomNavSource = readFileSync(new URL('../src/components/CandyBottomNav.vue', import.meta.url), 'utf8')
const aiPageSource = readFileSync(new URL('../src/pages/ai/index.vue', import.meta.url), 'utf8')

test('ai page is registered and reachable from bottom navigation', () => {
  assert.ok(
    pagesConfig.pages.some((page) => page.path === 'pages/ai/index'),
    'AI page should be registered in pages.json',
  )
  assert.match(
    bottomNavSource,
    /\{\s*key:\s*'ai'[\s\S]*url:\s*'\/pages\/ai\/index'/,
    'AI bottom nav item should navigate to the AI page',
  )
  assert.doesNotMatch(
    bottomNavSource,
    /\{\s*key:\s*'ai'[\s\S]*disabled:\s*true/,
    'AI bottom nav item should be enabled',
  )
})

test('ai page collects xiaohongshu share text and user-selected dates', () => {
  assert.match(
    aiPageSource,
    /v-model="shareText"/,
    'AI page should bind a share text textarea',
  )
  assert.match(
    aiPageSource,
    /placeholder="粘贴小红书分享链接或分享文案"/,
    'share text input should be specific to Xiaohongshu shares',
  )
  assert.match(
    aiPageSource,
    /mode="date"[\s\S]*@change="onStartDateChange"/,
    'AI page should let users choose a start date',
  )
  assert.match(
    aiPageSource,
    /mode="date"[\s\S]*@change="onEndDateChange"/,
    'AI page should let users choose an end date',
  )
  assert.match(
    aiPageSource,
    /inspirationApi\.extractFromShare/,
    'AI page should read a Xiaohongshu draft through the backend without saving an inspiration',
  )
  assert.match(
    aiPageSource,
    /tripApi\.create/,
    'AI page should create a trip after AI extraction',
  )
  assert.match(
    aiPageSource,
    /aiImportApi\.importTripEvents/,
    'AI page should import extracted Xiaohongshu places as editable trip events',
  )
  assert.match(
    aiPageSource,
    /normalizeShareEventCandidates/,
    'AI page should fill missing event dates from the user-selected date range before importing',
  )
})
