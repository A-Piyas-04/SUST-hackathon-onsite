# AI/ML feature notes

This supporting document records the implemented, evidence-preserving AI/ML additions referenced by migrations and ADRs. The deterministic liquidity, quality, and rule-based unusual-activity core remains functional without a trained model or external AI service.

## 1. Learned confidence calibration

**Repository status:** implemented with deterministic cold start; no trained artifact is committed.

`backend/app/services/quality/calibration.py` can load a locally trained logistic-regression artifact. Features are quality status one-hots, sample count/adequacy, rejection rate, and source age. Provider identity is not a feature.

`backend/app/scripts/train_confidence_calibration.py` can train from human case reviews and, only when explicitly requested, separately identified synthetic ground-truth examples. The artifact records label counts and coefficients. Runtime uses it only when validation succeeds and the labeled population meets the configured minimum; otherwise the original deterministic quality formula remains active.

This feature adjusts confidence only. It does not create alerts, change case state, or perform an action. A real deployment would require calibration error, subgroup behavior, drift, and label-quality evaluation.

## 2. Behavioral embedding unusual-activity detector

**Repository status:** implemented and enabled by migration `010`.

`detect_behavioral_embedding` converts provider/outlet transaction history into a five-dimensional feature representation covering amount, time of day, party frequency, provider code, and transaction type. It calculates mean k-nearest-neighbor distance in memory; it does not call an external embedding API or train an autoencoder.

Boundary and evidence rules:

- history is limited to the same provider/outlet account and earlier transactions;
- fewer than the configured minimum history rows returns `insufficient_history` and is not alertable;
- degraded quality suppresses alert publication;
- reviewable output includes nearest historical transaction records, distance context, confidence, and a plausible benign explanation; and
- it remains an independent pattern rather than contributing to a combined risk score.

The moderate validation dataset does not contain an equally sized held-out evaluation for this detector, so no precision/recall claim is made for it.

See [ADR 0007](adr/0007-behavioral-embedding-anomaly-detector.md).

## 3. Provider-scoped similar-case retrieval

**Repository status:** code and migration implemented at repository head; migration `011` was pending on the configured audited Supabase target.

Resolved case text is embedded using scikit-learn `HashingVectorizer` with 512 features, non-alternating signs, and L2 normalization. Retrieval uses cosine similarity. It is retrieval-only: no generative model summarizes, rewrites, or recommends an outcome.

The index text combines the immutable alert evidence summary with human case notes, review summary, and resolution summary. SQL filters the corpus by provider before similarity is calculated. Shared-cash cases without a provider are unavailable. Fewer than two comparable provider cases returns `insufficient_corpus` and “No comparable cases yet.”

Migration `011_case_similar_embeddings.sql` adds storage and RLS. The idempotent seed command adds nine clearly labeled `seeded_demo` resolved cases after migration `011` is applied; live resolved cases are labeled `live_resolved`.

Retrieved cases are context for human review. Past outcomes must not be copied automatically or treated as proof that the current case has the same cause.

See [ADR 0008](adr/0008-rag-similar-case-retrieval.md).

## Shared guardrails

- No external provider or generative-AI API is required.
- No feature merges provider data or bypasses provider authorization.
- No feature moves funds or automatically changes a case.
- Cold starts are explicit and safe.
- Evidence remains visible and human review remains mandatory.
- Synthetic validation does not establish production accuracy, fairness, or regulatory suitability.
