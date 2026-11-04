"""Markdown export of supplied snapshots. No model calls or command execution."""
import json
from datetime import datetime, timezone
from .safety import redact_tree


def block(value):
    # Indented code blocks keep untrusted Markdown/HTML from becoming report markup.
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    return '\n'.join('    ' + line for line in text.splitlines()) + '\n'


def incident_report(request):
    data = redact_tree(request.model_dump())
    parts = ['# FailureForge AI Incident Report',
             f'Exported: {datetime.now(timezone.utc).isoformat()}',
             '## Application', block(data['app_name']),
             '## Scope and limitations',
             'AI diagnoses are hypotheses, not confirmed causes or verified repairs. Observations are supplied log statements, not independent measurements. Timestamp correlation does not establish causation. Missing dates/timezones and clock skew limit ordering. Docker results concern fixed disposable samples only, never the real application or MySQL. This export records client-supplied investigation snapshots; it is not a signed audit record. Secret redaction is best-effort; review before sharing.']
    for number, turn in enumerate(data['history'], 1):
        result = turn['result']
        d = result['diagnosis']
        parts += [f'## Investigation round {number}', '### Mode and model',
                  block({'mode': result['mode'], 'model': result['model']}),
                  '### Provided context and evidence', block(turn['evidence']),
                  '### Error summary', block(d['summary']),
                  '### Confidence and severity', block({'confidence': d['confidence'], 'severity': d['severity']}),
                  '### Observed log evidence', block(d['evidence']),
                  '### Source and line references', block(result['evidence_locations']),
                  '### Root-cause hypothesis (unverified)', block(d['probable_root_cause']),
                  '### Alternatives (unverified)', block(d['possible_causes']),
                  '### Evidence attributed to hypotheses', block(d['hypothesis_support']),
                  '### What changed', block(d['what_changed']),
                  '### Recommended diagnostic checks', block(d['recommended_checks']),
                  '### Questions / missing evidence', block(d['questions']),
                  '### Timeline (separate clock groups; no inferred global order)', block(result['timeline']),
                  '### Analysis limitations', block(result['note'])]
    parts += ['## Docker verification results']
    if not data['verifications']:
        parts.append('No Docker verification was recorded. No fix has been experimentally verified.')
    for record in data['verifications']:
        result = record['result']
        parts += [f"### Sample run recorded after round {record['round']}", block(result),
                  'A passed status applies only to this sample, with the recorded before/after evidence and cleanup outcome. It does not confirm the incident root cause or repair the real application.']
    return '\n\n'.join(parts) + '\n'
