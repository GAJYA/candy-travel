import assert from 'node:assert/strict'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join, relative } from 'node:path'
import test from 'node:test'

const sourceRoot = fileURLToPath(new URL('../src', import.meta.url))
const forbidden = [
  { pattern: /\bAI\b/, label: 'AI uppercase label' },
  { pattern: /\bai\b/i, label: 'ai standalone label' },
  { pattern: /\bAi[A-Z]\w*/, label: 'Ai-prefixed identifier' },
  { pattern: /\baiImport\w*/i, label: 'aiImport identifier' },
  { pattern: /ai-import/i, label: 'ai-import slug' },
  { pattern: /\/ai\//i, label: '/ai/ API path' },
  { pattern: /pages\/ai/i, label: 'pages/ai route' },
  { pattern: /小红书|xiaohongshu/i, label: 'specific share platform name' },
  { pattern: /xhs_/, label: 'xhs client id prefix' },
]

function listFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    const stat = statSync(path)
    if (stat.isDirectory()) return listFiles(path)
    return [path]
  })
}

test('miniapp source avoids review-sensitive import wording', () => {
  const failures = []
  for (const file of listFiles(sourceRoot)) {
    if (!/\.(ts|vue|json)$/.test(file)) continue
    const source = readFileSync(file, 'utf8')
    for (const item of forbidden) {
      if (item.pattern.test(source)) {
        failures.push(`${relative(sourceRoot, file)} contains ${item.label}`)
      }
    }
  }

  assert.deepEqual(failures, [])
})
