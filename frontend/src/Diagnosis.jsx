import React from 'react'

export default function Diagnosis({ result }) {
  const d = result.diagnosis
  const references = quote => (result.evidence_locations || []).find(e => e.quote === quote)?.locations?.map(l => `${l.source}:${l.line} [${l.ref}]`).join(', ')
  const support = hypothesis => {
    const quotes = d.hypothesis_support?.find(s => s.hypothesis === hypothesis)?.evidence || []
    return quotes.length ? <ul>{quotes.map((quote, i) => <li key={i}>{quote} <small>{references(quote)}</small></li>)}</ul> : <small>No specific supporting line attributed to this hypothesis.</small>
  }
  return <div className="result">
    <div className="pills"><span className={`pill ${d.severity}`}>{d.severity.toUpperCase()} SEVERITY</span><span className="pill">{d.confidence.toUpperCase()} CONFIDENCE</span><span className="pill">{result.mode === 'meta' ? 'META MODEL' : 'OFFLINE RULES'}</span></div>
    <h3>{d.failure_type}</h3><p className="lead">{d.summary}</p>
    <h4>Observations from supplied evidence</h4><ul>{d.evidence.map((x, i) => <li key={i}>{x} <small>{references(x)}</small></li>)}</ul>
    <h4>Hypothesis — not confirmed</h4><p>{d.probable_root_cause}</p>
    {support(d.probable_root_cause)}
    {d.possible_causes?.length > 0 && <><h4>Other possible causes</h4><ul>{d.possible_causes.map((x, i) => <li key={i}>{x}{support(x)}</li>)}</ul></>}
    <h4>What changed</h4><p>{d.what_changed}</p>
    <h4>Recommended checks</h4><ol>{d.recommended_checks.map((x, i) => <li key={i}>{x}</li>)}</ol>
    <h4>Questions for the next round</h4><ul>{d.questions?.map((x, i) => <li key={i}>{x}</li>)}</ul>
    <p className="note">{result.note}</p>
  </div>
}
