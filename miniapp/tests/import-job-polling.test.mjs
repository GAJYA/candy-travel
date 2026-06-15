import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const importPageSource = readFileSync(new URL('../src/pages/import/index.vue', import.meta.url), 'utf8')
const inspirationServiceSource = readFileSync(new URL('../src/services/inspiration.ts', import.meta.url), 'utf8')

test('inspiration service creates and polls share import jobs', () => {
  assert.match(
    inspirationServiceSource,
    /export interface InspirationImportJob/,
    'service should expose the import job response shape',
  )
  assert.match(
    inspirationServiceSource,
    /createShareImportJob:\s*\(payload:[\s\S]*\/import-jobs\/from-share/,
    'service should create a backend import job instead of waiting for extraction',
  )
  assert.match(
    inspirationServiceSource,
    /getImportJob:\s*\(id:\s*string\)[\s\S]*\/import-jobs\/\$\{id\}/,
    'service should fetch a job by id for polling',
  )
})

test('import page polls job status with a hard stop and clears timers', () => {
  assert.match(
    importPageSource,
    /const\s+IMPORT_JOB_POLL_INTERVAL_MS\s*=\s*2500/,
    'page should poll every 2.5 seconds',
  )
  assert.match(
    importPageSource,
    /const\s+IMPORT_JOB_MAX_POLLS\s*=\s*72/,
    'page should stop polling after 3 minutes of attempts',
  )
  assert.match(
    importPageSource,
    /inspirationApi\.createShareImportJob/,
    'page should submit a job and receive a job id immediately',
  )
  assert.match(
    importPageSource,
    /const\s+pollImportJob\s*=\s*async/,
    'page should have an explicit polling function',
  )
  assert.match(
    importPageSource,
    /pollCount\.value\s*>=\s*IMPORT_JOB_MAX_POLLS/,
    'polling should stop if the backend never reaches a terminal state',
  )
  assert.match(
    importPageSource,
    /clearImportJobPolling\(\)/,
    'page should clear the active polling timer',
  )
  assert.match(
    importPageSource,
    /onUnmounted\(clearImportJobPolling\)/,
    'page should clear polling when leaving the page',
  )
  assert.doesNotMatch(
    importPageSource,
    /inspirationApi\.extractFromShare/,
    'page should not use the old long request path',
  )
})
