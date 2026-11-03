import { test } from 'node:test'
import assert from 'node:assert/strict'
import { requestJson } from './api.js'

test('API response handling', async (t) => {
  const original = globalThis.fetch
  t.after(() => { globalThis.fetch = original })
  for (const [name, body, status, expected] of [
    ['empty proxy failure', '', 500, /HTTP 500.*Empty response/],
    ['empty success', '', 200, /Empty response/],
    ['invalid JSON', '<html>Error</html>', 502, /HTTP 502.*Invalid JSON/],
    ['API error', '{"detail":"Try again"}', 503, /HTTP 503.*Try again/],
    ['validation error', '{"detail":[]}', 422, /HTTP 422.*Check your input/],
    ['null response', 'null', 200, /invalid response object/],
  ]) {
    await t.test(name, async () => {
      globalThis.fetch = async () => new Response(body, { status })
      await assert.rejects(requestJson('/api/analyze'), expected)
    })
  }
  await t.test('network failure', async () => {
    globalThis.fetch = async () => { throw new TypeError('Failed to fetch') }
    await assert.rejects(requestJson('/api/analyze'), /Cannot reach the API/)
  })
  await t.test('valid JSON and request forwarding', async () => {
    const options = { method: 'POST', body: '{"scenario":"port-conflict"}' }
    globalThis.fetch = async (url, received) => {
      assert.equal(url, '/api/verify-fix')
      assert.equal(received, options)
      return new Response('{"status":"passed"}')
    }
    assert.deepEqual(await requestJson('/api/verify-fix', options), { status: 'passed' })
  })
})
