"""Localized explanation rendering and immutable snapshot persistence.

Renders situation / evidence / uncertainty / next-step / benign-context text from
the seeded ``explanation_templates`` for English and Bangla/Banglish, then stores
one immutable ``alert_explanations`` row per locale (docs/schema.md §10.3-10.4).
Anomaly/combined alerts always carry a benign-context render (DB trigger + here).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_TEMPLATE_KEY_BY_TYPE = {
    "liquidity": "liquidity_default",
    "anomaly": "anomaly_default",
    "combined": "combined_default",
    "data_quality": "data_quality_default",
}

# Locales rendered when a matching template exists (EN always; BN/Banglish demo).
_LOCALES = ("en", "bn", "bn_latn")


def _render(template: str | None, context: dict[str, Any]) -> str | None:
    if template is None:
        return None
    out = template
    for key, value in context.items():
        out = out.replace("{" + key + "}", "" if value is None else str(value))
    return out


async def render_and_persist(
    session: AsyncSession,
    *,
    alert_id: UUID,
    alert_type: str,
    context: dict[str, Any],
) -> list[UUID]:
    """Persist one explanation render per available locale. Returns their ids."""
    template_key = _TEMPLATE_KEY_BY_TYPE.get(alert_type, "liquidity_default")
    created: list[UUID] = []
    for locale in _LOCALES:
        result = await session.execute(
            text(
                """
                SELECT explanation_template_id, situation_template, evidence_template,
                       uncertainty_template, next_step_template, benign_context_template
                FROM explanation_templates
                WHERE template_key = :key AND locale = :locale
                  AND alert_type = :alert_type AND is_active
                ORDER BY version DESC
                LIMIT 1
                """
            ),
            {"key": template_key, "locale": locale, "alert_type": alert_type},
        )
        tmpl = result.mappings().first()
        if tmpl is None:
            continue
        benign = _render(tmpl["benign_context_template"], context)
        if alert_type in ("anomaly", "combined") and not benign:
            # Guardrail: anomaly/combined explanations must carry benign context.
            benign = context.get("plausible_benign_explanation") or (
                "This may reflect normal event-driven demand."
            )
        explanation_id = uuid4()
        await session.execute(
            text(
                """
                INSERT INTO alert_explanations (
                  alert_explanation_id, alert_id, explanation_template_id, locale,
                  situation_text, evidence_text, uncertainty_text, next_step_text,
                  benign_context_text
                ) VALUES (
                  :id, :alert_id, :template_id, :locale,
                  :situation, :evidence, :uncertainty, :next_step, :benign
                )
                ON CONFLICT (alert_id, locale) DO NOTHING
                """
            ),
            {
                "id": explanation_id,
                "alert_id": alert_id,
                "template_id": tmpl["explanation_template_id"],
                "locale": locale,
                "situation": _render(tmpl["situation_template"], context) or "",
                "evidence": _render(tmpl["evidence_template"], context) or "",
                "uncertainty": _render(tmpl["uncertainty_template"], context) or "",
                "next_step": _render(tmpl["next_step_template"], context) or "",
                "benign": benign,
            },
        )
        created.append(explanation_id)
    return created
