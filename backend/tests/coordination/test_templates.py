"""Explanation template tests: EN coverage, Bangla/Banglish demo, required
sections, missing-variable failure, unsafe-variable rejection, determinism,
analytical-value insertion (not recalculation), English fallback."""
from __future__ import annotations

import pytest

from app.coordination.alerts.templates import (
    FALLBACK_LOCALE,
    REQUIRED_SECTIONS,
    MissingTemplateVariable,
    UnsafeRenderedContent,
    all_templates,
    available_locales,
    get_template,
    render,
)
from app.coordination.shared.enums import AlertType

VARS = {
    "reserve_label": "bKash e-money",
    "outlet_label": "OUTLET-001",
    "provider_label": "bKash",
    "evidence_summary": "Five near-identical cash-outs of about BDT 1,000 in 12 minutes.",
    "confidence_level": "medium",
    "uncertainty_statement": "This may reflect normal event-driven demand.",
    "latest_source_at": "2026-07-11T08:00:00Z",
    "plausible_benign_explanation": "Possible pre-Eid demand.",
    "recommended_next_step": "Review the transactions before coordinating support.",
}


def test_english_exists_for_every_alert_type():
    for at in AlertType:
        assert get_template(at.value, "en") is not None


def test_demo_combined_has_bangla_and_banglish():
    locales = set(available_locales(AlertType.COMBINED.value))
    assert {"en", "bn", "bn_latn"} <= locales


def test_required_sections_present_in_render():
    tmpl = get_template(AlertType.COMBINED.value, "en")
    rendered = render(tmpl, VARS, require_benign=True)
    d = rendered.as_dict()
    for section in REQUIRED_SECTIONS:
        assert d.get(section), f"missing section {section}"
    assert d.get("benign_context")


def test_missing_variable_fails_safely():
    tmpl = get_template(AlertType.COMBINED.value, "en")
    incomplete = {k: v for k, v in VARS.items() if k != "evidence_summary"}
    with pytest.raises(MissingTemplateVariable):
        render(tmpl, incomplete)


def test_unsafe_variable_rejected_at_render():
    tmpl = get_template(AlertType.ANOMALY.value, "en")
    bad = dict(VARS)
    bad["evidence_summary"] = "Confirmed fraud; block the account."
    with pytest.raises(UnsafeRenderedContent):
        render(tmpl, bad, require_benign=True)


def test_rendering_is_deterministic():
    tmpl = get_template(AlertType.COMBINED.value, "bn")
    a = render(tmpl, VARS, require_benign=True).as_dict()
    b = render(tmpl, VARS, require_benign=True).as_dict()
    assert a == b


def test_analytical_values_inserted_not_recalculated():
    tmpl = get_template(AlertType.LIQUIDITY.value, "en")
    rendered = render(tmpl, VARS)
    # The confidence_level is inserted verbatim; no recomputation occurs.
    assert "medium" in rendered.uncertainty
    assert VARS["latest_source_at"] in rendered.uncertainty


def test_english_fallback_for_unsupported_locale():
    # data_quality has no bn template -> falls back to en.
    tmpl = get_template(AlertType.DATA_QUALITY.value, "bn")
    assert tmpl is not None
    assert tmpl.locale == FALLBACK_LOCALE


def test_all_templates_use_only_declared_variables():
    # Every template's referenced variables are a subset of the known set, so
    # rendering with the standard variable object never silently drops content.
    known = set(VARS.keys())
    for tmpl in all_templates():
        assert tmpl.required_variables() <= known, f"{tmpl.template_key}/{tmpl.locale} uses unknown vars"


def test_no_template_contains_prohibited_language():
    from app.coordination.shared.security import scan_workflow_text

    for tmpl in all_templates():
        for part in (tmpl.situation, tmpl.evidence, tmpl.uncertainty, tmpl.next_step, tmpl.benign_context or ""):
            # Templates are placeholders with {vars}; the literal text must be safe.
            literal = part.replace("{", "").replace("}", "")
            assert not scan_workflow_text(literal), f"prohibited literal in {tmpl.template_key}/{tmpl.locale}"
