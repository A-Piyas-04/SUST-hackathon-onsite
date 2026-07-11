"""Versioned explanation templates + deterministic renderer (member-2 plan
Sections 6.5/9.13; schema.md 10.3-10.4).

Owner: Member 2. Pure-stdlib.

An explanation is rendered from ONE structured-variable object into fixed
sections and saved as an immutable snapshot (persistence is Phase 3). Templates:
  * use ONLY structured variables (no free-form financial commands);
  * never recalculate analytics — analytical values are inserted verbatim;
  * must render the required sections; benign context is required for
    anomaly/combined alerts;
  * are scanned for prohibited language after rendering;
  * render deterministically (same variables -> identical output).

Locale policy: requested locale -> saved render; fall back to English. English
must exist for every alert type; at least one demo alert type (`combined`) also
has Bangla (`bn`) and Banglish (`bn_latn`).
"""
from __future__ import annotations

import string
from dataclasses import dataclass
from typing import Any

from app.coordination.shared.enums import AlertType, LocaleCode
from app.coordination.shared.security import scan_workflow_text

REQUIRED_SECTIONS: tuple[str, ...] = ("situation", "evidence", "uncertainty", "next_step")
FALLBACK_LOCALE = LocaleCode.EN.value


class MissingTemplateVariable(KeyError):
    """Raised when a template references a variable not supplied. Fails safely
    (no partial/garbled render is persisted)."""


class UnsafeRenderedContent(ValueError):
    """Raised when a rendered section contains prohibited language."""


@dataclass(frozen=True)
class ExplanationTemplate:
    template_key: str
    locale: str
    version: int
    alert_type: str
    situation: str
    evidence: str
    uncertainty: str
    next_step: str
    benign_context: str | None = None

    def required_variables(self) -> set[str]:
        names: set[str] = set()
        parts = [self.situation, self.evidence, self.uncertainty, self.next_step]
        if self.benign_context:
            parts.append(self.benign_context)
        for part in parts:
            names |= {fn for _, fn, _, _ in string.Formatter().parse(part) if fn}
        return names


@dataclass(frozen=True)
class RenderedExplanation:
    template_key: str
    locale: str
    version: int
    situation: str
    evidence: str
    uncertainty: str
    next_step: str
    benign_context: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = {
            "template_key": self.template_key,
            "locale": self.locale,
            "version": self.version,
            "situation": self.situation,
            "evidence": self.evidence,
            "uncertainty": self.uncertainty,
            "next_step": self.next_step,
        }
        if self.benign_context is not None:
            data["benign_context"] = self.benign_context
        return data


# --- Placeholder template registry (EN for all types; BN + Banglish demo) ----
# These are Phase-1 placeholders using structured variables only. Copy is
# advisory and passes the prohibited-language scan.

_TEMPLATES: tuple[ExplanationTemplate, ...] = (
    ExplanationTemplate(
        template_key="liquidity.v1",
        locale="en",
        version=1,
        alert_type=AlertType.LIQUIDITY.value,
        situation="Possible liquidity pressure for {reserve_label} at outlet {outlet_label} requires review.",
        evidence="{evidence_summary}",
        uncertainty="Confidence is {confidence_level}. {uncertainty_statement} Latest data at {latest_source_at}.",
        next_step="{recommended_next_step}",
    ),
    ExplanationTemplate(
        template_key="anomaly.v1",
        locale="en",
        version=1,
        alert_type=AlertType.ANOMALY.value,
        situation="Unusual activity at outlet {outlet_label} on {provider_label} requires review.",
        evidence="{evidence_summary}",
        uncertainty="Confidence is {confidence_level}. {uncertainty_statement} Latest data at {latest_source_at}.",
        next_step="{recommended_next_step}",
        benign_context="Plausible benign context: {plausible_benign_explanation}",
    ),
    ExplanationTemplate(
        template_key="combined.v1",
        locale="en",
        version=1,
        alert_type=AlertType.COMBINED.value,
        situation="Possible liquidity pressure with unusual activity at outlet {outlet_label} on {provider_label} requires review.",
        evidence="{evidence_summary}",
        uncertainty="Confidence is {confidence_level}. {uncertainty_statement} Latest data at {latest_source_at}.",
        next_step="{recommended_next_step}",
        benign_context="Plausible benign context: {plausible_benign_explanation}",
    ),
    ExplanationTemplate(
        template_key="data_quality.v1",
        locale="en",
        version=1,
        alert_type=AlertType.DATA_QUALITY.value,
        situation="A potential data inconsistency for {provider_label} at outlet {outlet_label} should be checked.",
        evidence="{evidence_summary}",
        uncertainty="Confidence is {confidence_level}. {uncertainty_statement} Latest data at {latest_source_at}.",
        next_step="{recommended_next_step}",
    ),
    # --- Demo `combined` alert also in Bangla and Banglish ---
    ExplanationTemplate(
        template_key="combined.v1",
        locale="bn",
        version=1,
        alert_type=AlertType.COMBINED.value,
        situation="আউটলেট {outlet_label}-এ {provider_label} প্রোভাইডারে সম্ভাব্য তারল্য চাপ ও অস্বাভাবিক কার্যকলাপ পর্যালোচনা প্রয়োজন।",
        evidence="{evidence_summary}",
        uncertainty="নিশ্চয়তার মাত্রা {confidence_level}। {uncertainty_statement} সর্বশেষ তথ্য {latest_source_at}-এ।",
        next_step="{recommended_next_step}",
        benign_context="সম্ভাব্য স্বাভাবিক ব্যাখ্যা: {plausible_benign_explanation}",
    ),
    ExplanationTemplate(
        template_key="combined.v1",
        locale="bn_latn",
        version=1,
        alert_type=AlertType.COMBINED.value,
        situation="Outlet {outlet_label}-e {provider_label} provider-e shombhabbo tarolyo chap o osh'bhabik kajkormo review dorkar.",
        evidence="{evidence_summary}",
        uncertainty="Confidence level {confidence_level}. {uncertainty_statement} Latest data {latest_source_at}-e.",
        next_step="{recommended_next_step}",
        benign_context="Shombhabbo sh'bhabik bakkha: {plausible_benign_explanation}",
    ),
)

_INDEX: dict[tuple[str, str], ExplanationTemplate] = {}
for _t in _TEMPLATES:
    key = (_t.alert_type, _t.locale)
    # Keep the highest version for each (alert_type, locale).
    if key not in _INDEX or _t.version > _INDEX[key].version:
        _INDEX[key] = _t


def get_template(alert_type: str, locale: str) -> ExplanationTemplate | None:
    """Resolve a template, falling back to English if the locale is missing."""
    tmpl = _INDEX.get((alert_type, locale))
    if tmpl is not None:
        return tmpl
    return _INDEX.get((alert_type, FALLBACK_LOCALE))


def available_locales(alert_type: str) -> tuple[str, ...]:
    return tuple(sorted(loc for (at, loc) in _INDEX if at == alert_type))


def all_templates() -> tuple[ExplanationTemplate, ...]:
    return _TEMPLATES


class _SafeFormatter(string.Formatter):
    """Formatter that raises MissingTemplateVariable instead of silently
    inserting an empty/garbled value."""

    def get_value(self, key: Any, args: Any, kwargs: Any) -> Any:  # noqa: ANN401
        if isinstance(key, str):
            if key not in kwargs:
                raise MissingTemplateVariable(key)
            return kwargs[key]
        return super().get_value(key, args, kwargs)


_FORMATTER = _SafeFormatter()


def _render_part(template_part: str, variables: dict[str, Any]) -> str:
    rendered = _FORMATTER.format(template_part, **variables)
    if scan_workflow_text(rendered):
        raise UnsafeRenderedContent(f"prohibited language in rendered section: {rendered!r}")
    return rendered


def render(
    template: ExplanationTemplate,
    variables: dict[str, Any],
    *,
    require_benign: bool = False,
) -> RenderedExplanation:
    """Deterministically render a template. Raises on missing variables or
    prohibited language. `require_benign=True` (anomaly/combined) enforces a
    benign-context section."""
    if require_benign and not template.benign_context:
        raise MissingTemplateVariable("benign_context")
    benign = None
    if template.benign_context:
        benign = _render_part(template.benign_context, variables)
    return RenderedExplanation(
        template_key=template.template_key,
        locale=template.locale,
        version=template.version,
        situation=_render_part(template.situation, variables),
        evidence=_render_part(template.evidence, variables),
        uncertainty=_render_part(template.uncertainty, variables),
        next_step=_render_part(template.next_step, variables),
        benign_context=benign,
    )
