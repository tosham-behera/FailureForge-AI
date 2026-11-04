"""Bounded text evidence preparation. No files are written or executed."""
import re
from collections import Counter
from datetime import datetime, timezone
from .safety import redact_secrets

STAMP = re.compile(r'(?<!\d)(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?|\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)(?!\d)')
ERROR = re.compile(r'error|fail|exception|refused|timeout|deadlock|stopped|fatal', re.I)


def timestamp(text):
    match = STAMP.search(text)
    if not match:
        return None, 'undated', None, text
    raw = match.group(1)
    value = raw.replace(',', '.')
    try:
        if len(value.split(':')[0]) == 2:
            parsed = datetime.strptime(value.split('.')[0], '%H:%M:%S')
            group = 'clock-only — date/timezone unknown'
            sort = value
        else:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            group = 'UTC' if parsed.tzinfo else 'local — timezone unknown'
            sort = (parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed).isoformat()
        return raw, group, sort, (text[:match.start()] + text[match.end():]).strip(' []-—')
    except ValueError:
        return raw, 'undated', None, text


def prepare_evidence(req):
    sources = [('manual', req.logs)] + [(s.name, s.content) for s in req.sources]
    events, lines = [], []
    for source_index, (name, content) in enumerate(sources):
        for number, text in enumerate(redact_secrets(content).splitlines(), 1):
            if not text.strip():
                continue
            stamp, group, sort, message = timestamp(text)
            ref = f'S{source_index}:L{number}'
            events.append(dict(ref=ref, source=redact_secrets(name), line=number, text=text,
                               timestamp=stamp, group=group, sort=sort,
                               is_error=bool(ERROR.search(text)), message=message))
            lines.append(f'[{ref} {redact_secrets(name)}] {text}')
    counts = Counter(' '.join(e['message'].split()) for e in events)
    for event in events:
        event['repetitions'] = counts[' '.join(event['message'].split())]
    # Sort only within comparable groups. Undated entries retain source/line order.
    events.sort(key=lambda e: (e['group'], e['sort'] or ''))
    combined = '\n'.join(lines) if req.sources else redact_secrets(req.logs)
    if len(combined) > 24000:
        raise ValueError('Evidence plus source references exceeds 24,000 characters; use shorter excerpts.')
    return combined, events


def locate_evidence(diagnosis, events):
    locations = []
    for quote in diagnosis.evidence:
        hits = [dict(ref=e['ref'], source=e['source'], line=e['line']) for e in events
                if quote in e['text'] or quote == f"[{e['ref']} {e['source']}] {e['text']}"]
        locations.append(dict(quote=quote, locations=hits))
    return locations


def investigation_events(history, evidence):
    """Rebuild line identity from evidence, never from prior AI hypotheses."""
    events = []
    for round_number, text in enumerate([t['evidence'] for t in history] + [evidence], 1):
        for number, line in enumerate(text.splitlines(), 1):
            match = re.match(r'^\[(S\d+:L(\d+)) ([^\]]+)\] (.*)$', line)
            ref, source, content, line_number = f'R{round_number}:L{number}', f'round {round_number} input', line, number
            if match:
                ref, source, content, line_number = match[1], match[3], match[4], int(match[2])
            events.append(dict(ref=ref, source=source, line=line_number, text=content))
    return events
