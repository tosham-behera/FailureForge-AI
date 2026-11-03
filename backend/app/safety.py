"""Best-effort redaction; review real logs before sending them to any AI service."""
import re
import os


PATTERNS = [
    (re.compile(r"(?i)\b(authorization\s*:\s*bearer\s+)[^\s]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b((?:password|passwd|token|api[_-]?key|secret)\s*[=:]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\bsk-[a-z0-9_-]{12,}"), "[REDACTED_KEY]"),
]


def redact_secrets(text: str) -> str:
    # Also remove the configured key if it appears without a recognizable prefix.
    key = os.getenv("MODEL_API_KEY", "").strip()
    if key:
        text = text.replace(key, "[REDACTED_KEY]")
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text
