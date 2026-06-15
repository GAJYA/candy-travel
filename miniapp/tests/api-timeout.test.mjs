import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const apiSource = readFileSync(new URL('../src/services/api.ts', import.meta.url), 'utf8')
const inspirationSource = readFileSync(new URL('../src/services/inspiration.ts', import.meta.url), 'utf8')

test('request wrapper supports per-call timeout and readable timeout errors', () => {
  assert.match(
    apiSource,
    /timeoutMs\?:\s*number/,
    'request options should allow a per-call timeout',
  )
  assert.match(
    apiSource,
    /timeout:\s*options\.timeoutMs/,
    'uni.request should receive the configured timeout',
  )
  assert.match(
    apiSource,
    /请求耗时过长/,
    'timeout failures should be converted to a readable message',
  )
})

test('share extraction uses an extended timeout', () => {
  assert.match(
    inspirationSource,
    /extractFromShare:[\s\S]*timeoutMs:\s*180000/,
    'share extraction can take longer than normal CRUD requests',
  )
})
