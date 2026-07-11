"""Safe-language / prohibited-action policy (schema.md 13.20; master 6.3, 9.6).

Owner: Member 2. Pure-stdlib, machine-testable.

Scope: this scanner runs over **user-visible or persisted workflow content only**
— structured alert variables, rendered explanations, recommended next steps,
case notes, and review summaries. It is deliberately NOT run over documentation
or source comments, so a sentence like "the system must never freeze funds" in a
design doc is out of scope by construction.

Two prohibited categories:
  1. Fraud / criminal *verdicts* — declaring a subject fraudulent, criminal,
     guilty, a scammer, etc. Member 2 output is advisory; it never delivers a
     final fraud determination.
  2. Financial-action / punitive *directives* — instructing a transfer, refill,
     reversal, settlement, conversion, block, freeze, seizure, suspension, or
     punishment.

Negation handling: a prohibited term preceded (within a short window) by a
negation cue is treated as safe advisory language. This lets legitimate copy
such as "this is not proof of fraud" or "the platform does not block accounts"
pass, while "confirmed fraud" or "block the account" is rejected.

Also rejects synthetic-data violations at the fixture level (phone-number-like
strings) via `looks_like_phone_number`, per schema.md invariant 19.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# --- Prohibited vocabulary -------------------------------------------------

# Fraud / criminal verdict terms (word-boundary matched, case-insensitive).
_VERDICT_TERMS: tuple[str, ...] = (
    "fraud",
    "fraudulent",
    "fraudster",
    "criminal",
    "crime",
    "launder",
    "laundering",
    "scam",
    "scammer",
    "thief",
    "theft",
    "guilty",
    "culprit",
    "offender",
)

# Financial-action / punitive directive phrases. Multi-word where a bare verb
# would be ambiguous, so observed-fact descriptions (e.g. a "reversed"
# transaction status) are not falsely flagged.
_ACTION_PATTERNS: tuple[str, ...] = (
    r"freeze\s+(the\s+|this\s+)?(account|funds|wallet|balance)",
    r"frozen\s+(account|funds|wallet)",
    r"block\s+(the\s+|this\s+)?(account|user|customer|agent|wallet)",
    r"suspend\s+(the\s+|this\s+)?(account|user|customer|agent)",
    r"deactivate\s+(the\s+|this\s+)?(account|user)",
    r"disable\s+(the\s+|this\s+)?(account|user)",
    r"transfer\s+(the\s+)?funds?",
    r"transfer\s+money",
    r"wire\s+(the\s+)?funds?",
    r"send\s+money",
    r"refill\s+(the\s+)?wallet",
    r"top[\s\-]?up\s+(the\s+)?wallet",
    r"reverse\s+(the\s+|this\s+)?(transaction|payment|transfer)",
    r"settle\s+(the\s+)?(balance|account)",
    r"convert\s+(the\s+)?(balance|wallet|funds?|e-?money)",
    r"recover\s+(the\s+)?funds?",
    r"seize\s+(the\s+)?(funds?|account|balance)",
    r"confiscate",
    r"punish",
    r"penali[sz]e",
    r"arrest",
)

# Negation cues that neutralise a prohibited term when they appear shortly
# before it.
_NEGATIONS: tuple[str, ...] = (
    "no",
    "not",
    "never",
    "without",
    "cannot",
    "can't",
    "isn't",
    "doesn't",
    "does",  # "does not"
    "do",  # "do not"
    "must",  # "must not"
    "won't",
    "n't",
    "non",
    "avoid",
    "prohibit",
    "prohibited",
    "forbid",
    "forbidden",
)

_NEGATION_WINDOW = 5  # tokens of look-back
_WORD_RE = re.compile(r"[A-Za-z']+")
_VERDICT_RE = re.compile(r"\b(" + "|".join(_VERDICT_TERMS) + r")\b", re.IGNORECASE)
_ACTION_RE = re.compile("|".join(_ACTION_PATTERNS), re.IGNORECASE)
# Phone-like: 11 digits (BD mobile) or +88/8801 forms, allowing spaces/dashes.
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?88)?0?1[0-9](?:[\s\-]?\d){8}(?!\d)")


@dataclass(frozen=True)
class Violation:
    category: str  # "fraud_verdict" | "financial_action"
    term: str
    position: int


def _is_negated(text: str, match_start: int) -> bool:
    """True if a negation cue appears within _NEGATION_WINDOW words before the
    match, marking the mention as safe/advisory."""
    preceding = text[:match_start]
    words = _WORD_RE.findall(preceding.lower())
    window = words[-_NEGATION_WINDOW:]
    return any(neg in window for neg in _NEGATIONS)


def scan_workflow_text(text: str | None) -> list[Violation]:
    """Return prohibited-language violations in a single workflow string.

    Empty list == safe. Negated/advisory mentions are not reported.
    """
    if not text:
        return []
    violations: list[Violation] = []
    for m in _VERDICT_RE.finditer(text):
        if not _is_negated(text, m.start()):
            violations.append(Violation("fraud_verdict", m.group(0), m.start()))
    for m in _ACTION_RE.finditer(text):
        if not _is_negated(text, m.start()):
            violations.append(Violation("financial_action", m.group(0), m.start()))
    return violations


def is_safe_workflow_text(text: str | None) -> bool:
    return not scan_workflow_text(text)


def scan_structured_variables(variables: dict) -> list[Violation]:
    """Recursively scan all string leaves of a structured-variable object."""
    found: list[Violation] = []

    def walk(value: object) -> None:
        if isinstance(value, str):
            found.extend(scan_workflow_text(value))
        elif isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                walk(v)

    walk(variables)
    return found


def looks_like_phone_number(value: str | None) -> bool:
    """Heuristic used by synthetic-data fixture checks (schema.md 13.19)."""
    if not value:
        return False
    return bool(_PHONE_RE.search(value))


def assert_safe_workflow_text(text: str | None, *, field: str = "content") -> None:
    """Raise ApiError(UNSAFE_CONTENT) if `text` contains prohibited language.

    Imported lazily to keep this module dependency-free for pure scans.
    """
    violations = scan_workflow_text(text)
    if violations:
        from app.coordination.shared.errors import ApiError, ErrorCode

        raise ApiError(
            code=ErrorCode.UNSAFE_CONTENT,
            message="Content contains prohibited fraud-verdict or financial-action language.",
            details={"field": field, "reason": violations[0].category},
        )
