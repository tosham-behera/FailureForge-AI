import React from 'react'

export default function Timeline({ events }) {
  if (!events?.length) return null
  const groups = [...new Set(events.map(e => e.group))]
  return <details><summary>Evidence timeline — {events.length} log lines</summary>
    <p>Order is shown only within each timestamp group. Clock-only values show clock order, not confirmed dates. Timezones, clock skew and missing dates can prevent cross-source ordering. Temporal correlation does not prove causation. Undated lines retain source order.</p>
    {groups.map(group => <section key={group}><h4>{group}</h4><ol>{events.filter(e => e.group === group).map(e => <li key={e.ref}>
      <strong>{e.source}:{e.line} [{e.ref}]</strong> {e.timestamp || 'No recognized timestamp'}{e.is_error ? ' · error/event' : ''}
      <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{e.text}</pre>
      {e.repetitions > 1 && <small>Repeated message: {e.repetitions} occurrences</small>}
    </li>)}</ol></section>)}
  </details>
}
