# Member 2 — Unresolved Dependencies & Cross-Member Questions (P1-M2)

Status line: **Implementation complete; external contract validation pending.**

Member 1's `AlertCandidate` v1 and Member 3's `ResultEnvelope`/suppression truth
table are **not yet published in code**. Member 2's consumer, reference
interface, and evidence requirements are therefore built against clearly
labelled **provisional** contracts. No external approval is claimed.

---

## Questions for Member 1 (reference/scope + persistence + composition)

1. **Reference/scope lookup contract.** Please confirm or amend the
   `ReferenceLookup` Protocol in `app/coordination/shared/references.py`
   (`get_provider/outlet/account`, `account_matches`, `get_source_result`,
   `source_matches_scope`, `CallerScope`). Field names + return shapes are
   Member 2's proposal.
2. **`is_alertable` / `is_suppressed` on persisted results.** Member 2 needs
   these booleans exposed on the persisted analytical result (reflecting Member
   3's truth table) so it never recomputes suppression. Confirm they will be
   available via the lookup.
3. **Stable IDs.** Confirm provider/area/outlet/account/analytical-result IDs are
   stable UUID strings usable as opaque references (fixtures currently use
   synthetic string IDs like `prov_bkash`, `outlet_001`).
4. **Identity/access migration numbering.** `schema.md` §20 placed
   `app_users`/`user_access_scopes` in migration `001` (foundation), but
   `001_foundation.sql` implemented only §6.1–6.4. Member 2 owns the
   identity/access migration
   (`migrations/member_2_identity_access/001_identity_access.sql`). **Decision
   needed:** promote it as a new numbered slot between `001` and `002`, or fold
   into `001_foundation.sql`? It must apply before the workflow migration.
5. **Route composition.** Member 1 composes Member 2's surface via
   `app.coordination.router.include_member2_routers(app)` — no edits to Member 2
   internals. Confirm this is acceptable for the OpenAPI merge.
6. **`AlertCandidate` v1 shape.** Please review §11 of
   `coordination-security-contract.md` and confirm the field set + typed
   `source_result_ids` (`{result_type, source_result_id}`). Member 1 produces
   candidates; Member 2 only consumes.
7. **Middleware scope attachment.** Agree how authorized `CallerScope` is
   attached to a request (dependency vs middleware) for Phase 2.

## Questions for Member 3 (evidence semantics)

1. **Evidence variable set.** Confirm the structured variables Member 2 needs for
   rendering (`evidence_summary`, `evidence_items`, `confidence_level`,
   `uncertainty_statement`, `latest_source_at`, `contributing_signals`,
   `plausible_benign_explanation`, `data_quality_warning`) are all present in the
   `ResultEnvelope`.
2. **Benign context.** Confirm every anomaly/combined result carries a
   `plausible_benign_explanation` (Member 2 **rejects** anomaly/combined
   candidates without one).
3. **Suppression semantics.** Confirm `disposition = suppressed_data_quality`
   results are marked non-alertable so they cannot become anomaly/combined
   alerts, and may still surface as a data-quality advisory.
4. **No recomputation.** Confirm Member 2 may treat confidence/evidence/
   uncertainty as opaque and immutable — Member 2 will not recalculate them.
5. **Latest source time + confidence level** are provided as display-ready
   values (Member 2 inserts them verbatim into templates).

## Pending approvals (do not mark complete)

- [ ] Member 1 confirms `AlertCandidate` v1 field set.
- [ ] Member 1 confirms reference/scope lookup contract.
- [ ] Member 1 confirms identity/access migration numbering.
- [ ] Member 1 confirms OpenAPI composition path.
- [ ] Member 3 confirms evidence/uncertainty/benign/suppression semantics.
