"""Phase 5 coordination domain: alerts, cases, notifications, audit.

Modular services (docs Phase 5 quality bar):
  * ``audit``          — atomic append-only audit-event writes;
  * ``notifications``  — in-app notification queue/read;
  * ``routing``        — provider+area -> provider -> area -> fallback routing;
  * ``explanations``   — localized EN/BN/Banglish render snapshots;
  * ``alerts``         — candidate-to-alert publication (immutable evidence);
  * ``cases``          — legal case lifecycle with optimistic concurrency.
"""
