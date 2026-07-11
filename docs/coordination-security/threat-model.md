# Member 2 — Threat & Abuse-Case Model (P1-M2)

Owner: Member 2. Each row: asset · actor · attack path · expected control ·
test category · owning phase · residual risk. "Control" is what the frozen
contract/policy guarantees; several controls are proven now by pure tests,
others are enforced when runtime lands.

| # | Threat | Asset | Actor | Attack path | Expected control | Test category | Phase | Residual risk |
|---|---|---|---|---|---|---|---|---|
| 1 | Cross-provider enumeration | Alert/case existence | Provider B ops | Iterate IDs to learn Provider A records exist | Same `404` for missing + forbidden; `evaluate_read` deny | security/scope | P2/P4 | Timing side-channels not addressed in MVP |
| 2 | IDOR on alerts | Alert evidence | Any authed user | GET other-scope alert by ID | Scope check → safe 404 | scope | P3 | — |
| 3 | IDOR on cases | Case workflow | Any authed user | GET/POST other-scope case | Scope check → safe 404 | scope | P4 | — |
| 4 | IDOR on notes | Case notes | Any authed user | Read/append notes on other-scope case | Scope check on parent case | scope | P4 | — |
| 5 | IDOR on evidence refs | Source links | Any authed user | Read another provider's evidence | Typed links behind scope; no raw payload copy | candidate/scope | P3 | — |
| 6 | IDOR on notifications | Notifications | Any authed user | Read another user's notifications | Recipient-scoped queries | scope | P4 | — |
| 7 | IDOR on audit | Audit trail | Any authed user | Read other-scope audit events | Case-scope check on audit read | scope | P4 | — |
| 8 | Missing provider scope treated as wildcard | All provider rows | Mis-seeded user | Empty provider scope → sees all | `has_minimum_scope`/`evaluate_read` deny on empty | scope | P2 | — |
| 9 | Stale case update | Case integrity | Concurrent users | Write with old version | `409 VERSION_CONFLICT`, no mutation | transitions/concurrency | P4 | — |
| 10 | Concurrent case update | Case integrity | Two clients | Simultaneous writes | Version CAS + single-writer | concurrency | P4 | DB-level race handled in P4 |
| 11 | Duplicate POST | Workflow state | Retrying client | Replay mutating POST | `Idempotency-Key` returns original | routes/idempotency | P4 | Durable store in P4 |
| 12 | Duplicate candidate delivery | Alert dedup | M1 pipeline | Same candidate twice | Stable dedup key + active unique index | candidate | P3 | — |
| 13 | Evidence mutation after publication | Alert immutability | Insider/service bug | UPDATE alert payload | Immutability trigger; no update endpoint | (migration) | P4 | — |
| 14 | Confidence/evidence recalculation | Analytical integrity | M2 code | Recompute scores in M2 | Validator reads only; `CONFIDENCE_OVERRIDE_ATTEMPT` | candidate | P1✓ | — |
| 15 | Unsafe explanation rendering | Alert copy | Template author | Prohibited language via variable | Post-render safe-language scan | templates | P1✓ | — |
| 16 | Template injection | Alert copy | Variable content | Inject markup/commands | Structured-vars only; safe formatter; scan | templates | P1✓ | HTML escaping in UI layer (M2 UI phase) |
| 17 | Audit omission | Auditability | M2 code | Mutate without audit | Same-transaction audit rule; test in P4 | audit | P4 | — |
| 18 | Partial mutation without audit | Auditability | Crash mid-write | State changes, audit lost | Atomic transaction (state+audit) | audit | P4 | — |
| 19 | Token misuse | Session | Attacker | Reuse/forge token | JWT validation (P2); no token in logs/errors | auth/security | P2 | — |
| 20 | Expired token | Session | Attacker | Use expired token | `TOKEN_EXPIRED` 401 | auth | P2 | — |
| 21 | Inactive user | Access | Disabled user | Login/act while inactive | `INACTIVE_USER`; `evaluate_read` inactive deny | scope | P1✓/P2 | — |
| 22 | Inactive provider/outlet | Access | Any | Act on disabled ref | Lookup `is_active` checks | scope | P2 | — |
| 23 | Unauthorized role escalation | Privilege | Client | Self-grant role via API | Preferences endpoint locks to locale only | contracts | P1✓/P2 | — |
| 24 | Forged owner assignment | Ownership | Client | Assign case to self | Scope + owner/allowed-role checks | scope/transitions | P4 | — |
| 25 | Suppressed anomaly → alert | Analytical integrity | M1 pipeline | Send suppressed as anomaly | `SUPPRESSED_ANOMALY` rejection | candidate | P1✓ | — |
| 26 | Confidential info in error details | Confidentiality | Attacker | Read leaked IDs in errors | Allowlisted + leak-scanned details | contracts/security | P1✓ | — |
| 27 | Secrets/tokens in logs | Confidentiality | Log reader | Grep logs for creds | No creds in error details; logging policy | security | P2 | Structured-log redaction in P2 |
| 28 | Unsafe note/review content | Advisory boundary | User | Enter fraud/action wording | `assert_safe_workflow_text` on note/review | security | P4 | — |
| 29 | Fraud verdict via review | Advisory boundary | User | Record fraud disposition | `ReviewOutcome` has no fraud value | contracts | P1✓ | — |
| 30 | Financial action via structured variable | Advisory boundary | M1/user | Smuggle "transfer/freeze" | Safe-language scan on variables + next step | candidate/security | P1✓ | — |

**Proven now (Phase 1, `✓`):** 14, 15, 16, 21(policy), 23(contract), 25, 26, 29, 30.
**Deferred to runtime phases:** the remainder, with contracts/policies already frozen.
