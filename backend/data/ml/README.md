# ML artifacts (non-production)

This directory stores offline-trained model parameters for demo and development.
Artifacts here are **not** operational ledger data and are not required for
cold-start operation.

## Confidence calibration (`confidence_calibration.json`)

- **Training:** `python -m app.scripts.train_confidence_calibration --include-synthetic`
- **Cold start:** If the file is missing or was trained on fewer than 20 labeled
  examples, the Quality engine uses the fixed penalty formula unchanged.
- **Threshold (20):** Logistic regression needs enough mixed outcomes to fit
  ~8 coefficients without overfitting; six real case reviews alone are insufficient.
- **Provider independence:** The model is global but never uses `provider_id` as
  a feature; each runtime assessment scores one provider's inputs in isolation.
- **Option B features:** Status one-hots plus continuous `age_minutes` (the fixed
  formula only uses age indirectly via stale status).

Human review labels and synthetic ground-truth labels are reported separately
during training — they are not blended in training output.
