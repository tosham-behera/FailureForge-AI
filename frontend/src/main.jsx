import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'
import VerifyFix from './VerifyFix'
import { requestJson } from './api'
import Diagnosis from './Diagnosis'
import Timeline from './Timeline'
import { readLogFiles } from './uploads'

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
  const [history, setHistory] = useState([])
  const [incidentName, setIncidentName] = useState('')
  const [additionalEvidence, setAdditionalEvidence] = useState('')
  const [sources, setSources] = useState([])
  const [readingFiles, setReadingFiles] = useState(false)
  const [verifications, setVerifications] = useState([])
  const [verificationBusy, setVerificationBusy] = useState(false)
  const [incidentId, setIncidentId] = useState(0)

  useEffect(() => {
    requestJson('/api/health').then(setStatus).catch(() => setStatus(null))
  }, [])

  async function analyze(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await requestJson('/api/analyze', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ logs, app_name: appName, sources })
      })
      setResult(data)
      setHistory([{ evidence: data.input_evidence || logs, result: data }])
      setIncidentName(appName)
      setIncidentId(id => id + 1)
      setVerifications([])
      setAdditionalEvidence('')
    } catch (err) {
      setError(err.message || 'Cannot reach backend. Start FastAPI on the port configured in the Vite proxy.')
    } finally {
      setLoading(false)
    }
  }

  async function continueInvestigation() {
    setLoading(true)
    setError('')
    try {
      const data = await requestJson('/api/investigate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_name: incidentName, evidence: additionalEvidence, history: history.map(turn => ({
          evidence: turn.evidence, result: {mode:turn.result.mode, model:turn.result.model, diagnosis:turn.result.diagnosis, note:turn.result.note}
        })) })
      })
      setHistory([...history, { evidence: data.input_evidence, result: data }])
      setResult(data)
      setAdditionalEvidence('')
    } catch (err) {
      setError(err.message)
    } finally { setLoading(false) }
  }

  async function selectFiles(e) {
    const files = Array.from(e.target.files)
    setReadingFiles(true)
    setError('')
    try { setSources(await readLogFiles(files)) }
    catch (err) { setSources([]); setError(err.message); e.target.value = '' }
    finally { setReadingFiles(false) }
  }

  async function downloadReport() {
    setLoading(true)
    setError('')
    try {
      const data = await requestJson('/api/report', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({app_name:incidentName, history, verifications})})
      const url = URL.createObjectURL(new Blob([data.markdown], {type:'text/markdown;charset=utf-8'}))
      const link = document.createElement('a')
      link.href = url
      link.download = data.filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
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
              <label htmlFor="files">Optional log files (.log / .txt)</label>
              <input id="files" type="file" accept=".log,.txt" multiple disabled={loading || readingFiles} onChange={selectFiles} />
              <small>Up to 4 UTF-8 files, 16 KiB each; combined evidence: 20,000 characters / 32 KiB / 600 lines. Files are sent only when you click Analyze.</small>
              <ul>{sources.map(s => <li key={s.name}>{s.name} ({s.content.length} characters)</li>)}</ul>
              <textarea id="logs" rows={13} value={logs} maxLength={12000} onChange={e => setLogs(e.target.value)} spellCheck="false" placeholder="Paste your application logs here..." />
              <div className="below-input"><small>{logs.length.toLocaleString()} / 12,000 characters</small><small>Remove secrets and personal information</small></div>
              <button className="primary" type="submit" disabled={loading || readingFiles || verificationBusy || (logs + sources.map(s => s.content).join('')).trim().length < 8}>{loading ? 'Investigating…' : 'Analyze incident →'}</button>
            </form>
          </section>
          <section className="panel analysis">
            <div className="panel-heading"><h2>02 / Diagnosis</h2><span className="muted">Evidence first</span></div>
            {error && <div className="error" role="alert">{error}</div>}
            {!result && !error && <div className="empty"><div className="pulse">⌕</div><h3>Awaiting an incident</h3><p>Select a sample or paste your logs, then click Analyze.</p></div>}
            {history.map((turn, i) => <article key={i} aria-label={`Investigation round ${i + 1}`}>
              <h3>Round {i + 1} / {incidentName}</h3>
              <details><summary>Evidence supplied this round</summary><pre style={{ whiteSpace: 'pre-wrap' }}>{turn.evidence}</pre></details>
              <Diagnosis result={turn.result} />
              <Timeline events={turn.result.timeline} />
            </article>)}
            {result && <>
              <h4>Investigate Further</h4>
              <p>Each click explicitly requests one additional analysis. Up to 5 rounds; history is held in this tab and is lost on reload.</p>
              <label htmlFor="additional">Additional evidence or answers</label>
              <textarea id="additional" rows={5} maxLength={6000} value={additionalEvidence} onChange={e => setAdditionalEvidence(e.target.value)} />
              <button className="primary" type="button" disabled={loading || verificationBusy || history.length >= 5 || additionalEvidence.trim().length < 8} onClick={continueInvestigation}>Continue Investigation</button>
              {history.length >= 5 && <p>Round limit reached. Start a new incident with a concise summary.</p>}
              <h4>Verified findings — controlled samples only</h4>
              <p>Diagnosis alone verifies no fix. Only a completed Docker test can supply experimental sample findings.</p>
              <VerifyFix key={incidentId} disabled={loading || verifications.length >= 10} onBusy={setVerificationBusy} onResult={data => setVerifications(previous => [...previous, {round:history.length, result:data}])} />
              {verifications.length > 0 && <details><summary>Recorded sample runs ({verifications.length})</summary>{verifications.map((v, i) => <p key={i}>Round {v.round}: {v.result.scenario} — {v.result.status}; cleanup {String(v.result.cleanup_succeeded)}</p>)}</details>}
              <button className="primary" type="button" disabled={loading || verificationBusy} onClick={downloadReport}>Download Incident Report</button>
            </>}
          </section>
        </div>
        <footer>FailureForge AI · Hackathon prototype · No automatic command execution</footer>
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
