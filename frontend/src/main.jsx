import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'
import VerifyFix from './VerifyFix'
import { requestJson } from './api'

const samples = {
  database: '2026-10-31 11:05:30 [ERROR] Failed to connect to MySQL\nError: connect ECONNREFUSED 127.0.0.1:3306\n    at TCPConnectWrap.afterConnect (node:net:1634:16)\nServer started but database-dependent routes are failing.',
  port: 'node:events:491\nError: listen EADDRINUSE: address already in use :::4000\n    at Server.setupListenHandle (node:net:1908:16)\nNode.js v22.16.0',
  timeout: '2026-10-31T11:05:00Z POST /api/payment\nFetchError: request to upstream service timed out after 30000ms\nError code: ETIMEDOUT\nRequest failed; retries exhausted.'
}

function App() {
  const [logs, setLogs] = useState(samples.database)
  const [appName, setAppName] = useState('Node.js + MySQL service')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState(null)

  useEffect(() => {
    requestJson('/api/health').then(setStatus).catch(() => setStatus(null))
  }, [])

  async function analyze(e) {
    e.preventDefault()
    setResult(null)
    setError('')
    setLoading(true)
    try {
      const data = await requestJson('/api/analyze', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ logs, app_name: appName })
      })
      setResult(data)
    } catch (err) {
      setError(err.message || 'Cannot reach backend. Start FastAPI on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="logo"><span className="logo-icon">F</span><span>FailureForge <em>AI</em></span></div>
        <div className="status"><span className="dot"/> {status ? `${status.mode === 'demo' ? 'DEMO MODE' : 'META LIVE'} · ${status.model}` : 'Backend not connected'}</div>
      </header>
      <main className="shell">
        <div className="eyebrow">INCIDENT INTELLIGENCE / V0.1</div>
        <h1>Go from <span>error logs</span> to a clear next step.</h1>
        <p className="intro">Paste a server error, inspect the probable cause, and get safe checks to help you debug. Results are suggestions, not confirmed repairs.</p>
        <div className="layout">
          <section className="panel">
            <div className="panel-heading"><h2>01 / Incident input</h2><span className="muted">Paste logs below</span></div>
            <form onSubmit={analyze}>
              <label htmlFor="app">Application name</label>
              <input id="app" value={appName} maxLength={80} onChange={e => setAppName(e.target.value)} />
              <div className="samples-label">Try a failure scenario</div>
              <div className="sample-buttons">
                <button type="button" onClick={() => setLogs(samples.database)}>Database down</button>
                <button type="button" onClick={() => setLogs(samples.port)}>Port conflict</button>
                <button type="button" onClick={() => setLogs(samples.timeout)}>Service timeout</button>
              </div>
              <label htmlFor="logs">Application logs</label>
              <textarea id="logs" rows={13} value={logs} maxLength={12000} onChange={e => setLogs(e.target.value)} spellCheck="false" placeholder="Paste your application logs here..." />
              <div className="below-input"><small>{logs.length.toLocaleString()} / 12,000 characters</small><small>Remove secrets and personal information</small></div>
              <button className="primary" type="submit" disabled={loading || logs.trim().length < 8}>{loading ? 'Investigating…' : 'Analyze incident →'}</button>
            </form>
          </section>
          <section className="panel analysis">
            <div className="panel-heading"><h2>02 / Diagnosis</h2><span className="muted">Evidence first</span></div>
            {error && <div className="error" role="alert">{error}</div>}
            {!result && !error && <div className="empty"><div className="pulse">⌕</div><h3>Awaiting an incident</h3><p>Select a sample or paste your logs, then click Analyze.</p></div>}
            {result && <div className="result">
              <div className="pills"><span className={`pill ${result.diagnosis.severity}`}>{result.diagnosis.severity.toUpperCase()} SEVERITY</span><span className="pill">{result.diagnosis.confidence.toUpperCase()} CONFIDENCE</span><span className="pill">{result.mode === 'meta' ? 'META MODEL' : 'OFFLINE RULES'}</span></div>
              <h3>{result.diagnosis.failure_type}</h3>
              <p className="lead">{result.diagnosis.summary}</p>
              <h4>Probable cause (not confirmed)</h4><p>{result.diagnosis.probable_root_cause}</p>
              {result.diagnosis.possible_causes?.length > 0 && <><h4>Other possible causes</h4><ul>{result.diagnosis.possible_causes.map((x, i) => <li key={i}>{x}</li>)}</ul></>}
              <h4>Observed in supplied logs</h4><ul>{result.diagnosis.evidence.map((x, i) => <li key={i}>{x}</li>)}</ul>
              <h4>Recommended checks</h4><ol>{result.diagnosis.recommended_checks.map((x, i) => <li key={i}>{x}</li>)}</ol>
              <div className="note">{result.note}</div>{result.diagnosis.failure_type === 'Port conflict' && <VerifyFix />}
            </div>}
          </section>
        </div>
        <footer>FailureForge AI · Hackathon prototype · No automatic command execution</footer>
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
