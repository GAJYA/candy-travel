import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const homePageSource = readFileSync(new URL('../src/pages/index/index.vue', import.meta.url), 'utf8')

test('home page allows browsing before login', () => {
  assert.doesNotMatch(
    homePageSource,
    /v-if="!auth\.isAuthenticated"[\s\S]{0,120}login-card/,
    'home page should not show a blocking login card as the first unauthenticated experience',
  )
  assert.doesNotMatch(
    homePageSource,
    /开启你的P人旅行计划|微信登录后开始整理下一段旅程/,
    'home page should not ask for login before users browse the service',
  )
  assert.match(
    homePageSource,
    /guest-preview/,
    'home page should render a guest preview area before login',
  )
  assert.match(
    homePageSource,
    /const visibleTrips = computed/,
    'home page should have a unified trip list source for guest and logged-in states',
  )
  assert.match(
    homePageSource,
    /const onCreate = async \(\) => \{[\s\S]*if \(!auth\.isAuthenticated\)[\s\S]*await login\(\)/,
    'creating a trip may request login after the user initiates the action',
  )
})
