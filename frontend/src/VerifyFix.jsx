import React, { useState } from 'react'

import { requestJson } from './api'

export default function VerifyFix({ onResult = () => {}, onBusy = () => {}, disabled = false }) {
  const [scenario, setScenario] = useState('port-conflict')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function verify() {
    setLoading(true)
    onBusy(true)
    setResult(null)
    setError('')
    try {
      const data = await requestJson('/api/verify-fix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario })
      })
      setResult(data)
      onResult(data)
    } catch (err) {
      setError(err.message || 'Cannot reach verification backend.')
    } finally {
      setLoading(false)
      onBusy(false)
    }
  }

  return <section className="verification" aria-label="Safe Fix Verification">
    <h4>Safe Fix Verification / Docker lab</h4>
    <label htmlFor="scenario">Approved verification scenario</label>
    <select id="scenario" disabled={loading || disabled} value={scenario} onChange={e => { setScenario(e.target.value); setResult(null) }}>
      <option value="port-conflict">Port conflict — sample port 4000 to 4001</option>
      <option value="database-connectivity">Database connectivity — simulated TCP dependency</option>
    </select>
    <p>{scenario === 'port-conflict' ? 'Test the predefined port change from 4000 to 4001.' : 'Reproduce a missing simulated TCP dependency, then start the fixed sample dependency. This is not MySQL and does not repair a real database.'} Tests run in an isolated sample, never your application. No Meta API calls.</p>
    <button className="primary" type="button" disabled={loading || disabled} onClick={verify}>{loading ? 'Running Docker test...' : 'Verify Fix'}</button>
    <div aria-live="polite" aria-busy={loading}>
      {error && <p role="alert" className="error">{error}</p>}
      {result && <>
        <h4>Test status: {result.status.toUpperCase()}</h4>
        <p>Docker ran: {result.docker_ran ? 'Yes' : 'No'} · Cleanup: {result.cleanup_succeeded === null ? 'Not required' : result.cleanup_succeeded ? 'Succeeded' : 'Failed'}</p>
        <h4>Before / controlled failure</h4>
        <pre>{Object.keys(result.before).length ? JSON.stringify(result.before, null, 2) : 'No evidence captured.'}</pre>
        <h4>After / predefined sample recovery</h4>
        <pre>{Object.keys(result.after).length ? JSON.stringify(result.after, null, 2) : 'No evidence captured.'}</pre>
        {result.logs && <details><summary>Container logs</summary><pre>{result.logs}</pre></details>}
        {result.errors.map((message, i) => <p className="error" key={i}>{message}</p>)}
        <p className="note">{result.note}</p>
      </>}
    </div>
  </section>
}
