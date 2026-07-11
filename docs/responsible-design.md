# Responsible design

## Purpose and decision boundary

The platform is advisory decision support. It helps authorized users understand possible liquidity pressure, unusual activity, evidence, uncertainty, ownership, and workflow status. It does not decide guilt, execute financial actions, or replace provider procedures and human judgment.

An unusual-activity flag means only that a documented pattern met a configured review condition. It is not proof of fraud, misconduct, or customer intent.

## Synthetic data and privacy

- All domain data is synthetic.
- Synthetic party and account references are opaque and are validated to avoid phone-number-like or real-account-like values.
- Seeded demo users use fixed UUIDs and reserved `.test` email addresses without passwords or credentials.
- The application stores no PIN, OTP, password, private key, production token, or real customer identity.
- Database audits and logs report sanitized targets and must not print passwords or service-role keys.

## Provider and reserve separation

Shared physical cash belongs to an outlet and has no provider identifier. Provider-specific e-money belongs to exactly one outlet/provider account. Constraints, views, services, contracts, and tests prevent a blended total or cross-provider account mismatch.

Provider-confidential transactions, alerts, cases, notes, notifications, evidence, similar-case retrieval, and audit history remain provider-scoped. A provider user cannot use the combined outlet view to control or inspect another provider's confidential data.

## Human review and false positives

Every actionable unusual-activity result contains:

- the named pattern;
- exact synthetic evidence or linked observations;
- confidence and quality context;
- a plausible benign explanation; and
- a next step framed as review or authorized coordination.

Benign demand spikes, common round amounts, recurring payments, new customer patterns, delayed feeds, and synchronization problems can resemble unusual behavior. The validation dataset deliberately contains false positives and dismissed-benign outcomes. Human reviewers must consider outlet context, provider procedures, data quality, and prior resolved cases before recording a review outcome.

Similar-case retrieval is context only. It returns provider-filtered human-authored case history and similarity scores; it does not generate a conclusion or automatically copy a past outcome.

## Data quality, confidence, and uncertainty

Missing, conflicting, stale, insufficient, or malformed data is never silently treated as healthy.

- Quality issues are retained as evidence.
- Missing/conflicting input lowers the confidence modifier.
- Liquidity projections may become non-actionable.
- Otherwise detectable unusual activity may be stored as `suppressed_data_quality` and cannot be published as an anomaly alert.
- Forecast time is shown with confidence bounds and may change when new data arrives.
- Cold-start analytics explicitly return insufficient-history or insufficient-sample states.

An optional learned confidence calibrator is allowed only when a valid artifact contains sufficient labeled support. Otherwise deterministic scoring remains active.

## Roles and scopes

| Role | Intended boundary |
|---|---|
| Agent | Combined operational view for one assigned outlet; no provider-control authority. |
| Provider operations | Confidential records and workflow for one provider. |
| Area manager | One provider within an assigned synthetic area. |
| Risk analyst | Provider-scoped unusual-activity review. |
| Management | Aggregate readiness and evidence; not a wildcard for raw provider records. |
| Admin/service | Demo setup, internal analytics, and controlled ingestion. |

The frontend hides unauthorized actions for clarity, but the backend remains authoritative.

## Authorization and PostgreSQL RLS

FastAPI resolves the synthetic bearer identity and applies explicit outlet/provider/area/action checks. PostgreSQL RLS mirrors provider and outlet boundaries for defense in depth. Missing scope means deny. Confidential unauthorized lookups use the same safe `404` shape as missing records to avoid leaking existence.

The service role can bypass RLS only so authorized backend workflows can perform controlled writes. It must never be exposed to the browser.

## Auditability and evidence integrity

- Transactions, balance observations, ingestion events, analytical results, explanation renders, notes, histories, and audit events are append-only or permission-protected.
- Published alert evidence and source links are immutable.
- Cases remain mutable only through explicit legal actions with optimistic version checks.
- Assignment, acknowledgement, escalation, review, resolution, and notification are traceable.
- A resolved case requires a human-authored resolution summary.
- Important mutations use idempotency protection and request identifiers.

## Safe language

User-visible output uses terms such as “unusual activity,” “requires review,” “possible liquidity pressure,” “confidence,” and “plausible benign explanation.” It avoids definitive accusations and does not label a person or transaction as criminal or fraudulent.

The automated safety scan searches user-facing material for prohibited definitive language and unsafe financial-action endpoints. Passing this scan is a narrow repository check, not a complete content or security review.

## Fairness and unsupported profiling

The prototype does not use real demographic, geographic, device, contact-list, identity, or protected-attribute features. Provider code is used only to keep operational records separated, not to rank providers or people. Behavioral comparison is restricted to the same provider/outlet history and presents nearest evidence rather than a hidden universal risk score.

Because the data is synthetic, the project cannot claim demographic fairness. A real deployment would require representative data, subgroup analysis, appeal/review procedures, drift monitoring, and provider governance before any consequential use.

## Security assumptions

- Demo authentication is enabled only in a controlled demonstration environment.
- Database credentials remain in backend environment variables.
- TLS, secret rotation, production identity, rate limiting, backup/restore, incident response, penetration testing, and operational monitoring are deployment responsibilities not proven by this prototype.
- Supabase RLS is defense in depth; application authorization is still required because the backend may connect with a privileged role.

## Explicitly prohibited capabilities

The prototype cannot and must not:

- transfer or convert balances;
- settle funds;
- refill wallets;
- recover or reverse real transactions;
- block users;
- freeze funds;
- accuse an agent or customer;
- make a final fraud determination;
- access real provider APIs or customer accounts;
- collect PINs, OTPs, passwords, private keys, or private credentials;
- expose one provider's confidential evidence to another provider;
- automatically execute a recommendation or case outcome; or
- claim regulatory approval or production readiness.

Transaction statuses such as `reversed` in synthetic data are observations, not operations the platform can execute.

## Known limitations

- Demo tokens are not production authentication.
- Synthetic labels and outcomes cannot establish real-world accuracy or fairness.
- The moderate evaluation set is small and primarily covers near-identical-amount behavior.
- Forecasts use a transparent burn-rate model rather than a production demand model.
- Similar-case retrieval requires migration `011` and a sufficient provider-scoped corpus.
- No production load, resilience, privacy-impact, legal, compliance, or security assessment has been performed.

These boundaries are enforced partly in code and database policy and partly by the explicit scope of the demonstration. Any future expansion must preserve human review, provider authorization, evidence integrity, and non-execution of financial actions.
