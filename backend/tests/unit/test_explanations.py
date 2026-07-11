"""Unit tests for coordination explanation rendering (docs/schema.md §10.3-10.4).

render_and_persist reads seeded templates and writes immutable renders through
session.execute() only, so a stub session exercises template-key fallback,
per-locale rendering, and the anomaly benign-context guardrail without a DB.
"""

from __future__ import annotations

from uuid import uuid4

from app.services.coordination.explanations import _render, render_and_persist

ALERT_ID = uuid4()
TEMPLATE_ID = uuid4()


# ------------------------------------------------------------------- _render
def test_render_substitutes_placeholders_and_stringifies():
    out = _render("Cash at {outlet} runs out ~{eta}.", {"outlet": "O-001", "eta": 43})
    assert out == "Cash at O-001 runs out ~43."


def test_render_none_value_becomes_empty_and_unknown_keys_survive():
    out = _render("{missing} and {kept}", {"missing": None})
    assert out == " and {kept}"


def test_render_none_template_returns_none():
    assert _render(None, {"any": "thing"}) is None


# --------------------------------------------------------- render_and_persist
class _StubResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row


class _StubSession:
    """Serves explanation_templates SELECTs per locale; records INSERTs."""

    def __init__(self, templates_by_locale):
        self.templates_by_locale = templates_by_locale
        self.inserts: list[dict] = []
        self.selected_keys: list[tuple[str, str]] = []

    async def execute(self, statement, params=None):
        sql = str(statement)
        if "FROM explanation_templates" in sql:
            self.selected_keys.append((params["key"], params["locale"]))
            return _StubResult(self.templates_by_locale.get(params["locale"]))
        if "INSERT INTO alert_explanations" in sql:
            self.inserts.append(params)
            return _StubResult(None)
        raise AssertionError(f"unexpected SQL: {sql}")


def _template(**overrides):
    row = {
        "explanation_template_id": TEMPLATE_ID,
        "situation_template": "Shortage at {outlet}.",
        "evidence_template": "Burn {burn}/h.",
        "uncertainty_template": "Confidence {confidence}.",
        "next_step_template": "Rebalance cash.",
        "benign_context_template": "Possibly {benign_reason}.",
    }
    row.update(overrides)
    return row


async def test_renders_only_locales_with_templates():
    session = _StubSession({"en": _template()})  # bn / bn_latn have no template
    created = await render_and_persist(
        session,
        alert_id=ALERT_ID,
        alert_type="liquidity",
        context={"outlet": "O-001", "burn": "3000", "confidence": "high", "benign_reason": "Eid"},
    )
    assert len(created) == 1
    assert len(session.inserts) == 1
    ins = session.inserts[0]
    assert ins["situation"] == "Shortage at O-001."
    assert ins["evidence"] == "Burn 3000/h."
    assert ins["locale"] == "en"
    # All three locales were attempted.
    assert [loc for _, loc in session.selected_keys] == ["en", "bn", "bn_latn"]


async def test_unknown_alert_type_falls_back_to_liquidity_template_key():
    session = _StubSession({})
    await render_and_persist(
        session, alert_id=ALERT_ID, alert_type="mystery", context={}
    )
    assert session.selected_keys[0][0] == "liquidity_default"


async def test_anomaly_guardrail_uses_context_benign_explanation():
    session = _StubSession({"en": _template(benign_context_template=None)})
    await render_and_persist(
        session,
        alert_id=ALERT_ID,
        alert_type="anomaly",
        context={"outlet": "O-001", "plausible_benign_explanation": "pre-Eid surge"},
    )
    assert session.inserts[0]["benign"] == "pre-Eid surge"


async def test_anomaly_guardrail_default_when_no_benign_available():
    session = _StubSession({"en": _template(benign_context_template=None)})
    await render_and_persist(
        session, alert_id=ALERT_ID, alert_type="combined", context={}
    )
    assert session.inserts[0]["benign"] == "This may reflect normal event-driven demand."


async def test_liquidity_alert_allows_missing_benign_context():
    session = _StubSession({"en": _template(benign_context_template=None)})
    await render_and_persist(
        session, alert_id=ALERT_ID, alert_type="liquidity", context={}
    )
    assert session.inserts[0]["benign"] is None
