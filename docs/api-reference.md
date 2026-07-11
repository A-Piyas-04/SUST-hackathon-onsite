# API reference

This is a concise guide to the implemented REST API. The generated technical contract is [`openapi/openapi.v1.json`](openapi/openapi.v1.json); request/response schemas should not be duplicated manually here.

## Base URLs

- Health: `/health`
- Metrics: `/metrics`
- Versioned application API: `/api/v1`
- Interactive OpenAPI UI in development: `/docs`

## Authentication

Confidential routes use HTTP bearer authentication. Demo mode accepts tokens returned by:

```http
POST /api/v1/auth/demo-login
Content-Type: application/json

{"user_key":"bkash_ops"}
```

The returned token represents a seeded synthetic identity. Demo authentication must be disabled or replaced outside a controlled demo environment.

## Authorization scopes

Authorization is evaluated using role plus optional provider, area, and outlet scope:

- agent: assigned outlet;
- provider operations/risk: assigned provider;
- area manager: assigned provider and area;
- management: aggregate read access, not raw provider wildcard access; and
- admin: controlled setup/internal operations.

Application checks are authoritative for API requests. PostgreSQL RLS provides defense in depth. Unauthorized confidential identifiers return the same safe `404` shape as missing identifiers.

## Request IDs and errors

Clients may send `X-Request-ID`; otherwise the middleware generates one. Responses include `X-Request-ID`, and structured logs carry the same value.

Error shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "request_id": "uuid",
    "details": {}
  }
}
```

Validation failures use HTTP `422`; optimistic-version conflicts use `409`; missing/unauthorized confidential resources use a non-revealing `404`.

## Money, time, and locale

- Money is serialized as a decimal string and persisted as exact numeric values.
- API timestamps are ISO 8601 UTC values.
- Saved alert explanations are returned as separate `en`, `bn`, and `bn_latn` renders.
- `PATCH /api/v1/me/preferences` changes the user's preferred locale.
- Alert explanation selection is currently performed by the client from the returned saved renders; `Accept-Language` negotiation is not implemented.

## Filters and limits

Implemented list filters vary by endpoint and are defined in OpenAPI. Current examples include:

- alert `outlet_id` and `state`;
- case `status`;
- validation `dataset_split` and `status`;
- transaction provider and `limit`; and
- balance-history reserve/provider and `limit`.

Transaction and balance-history limits accept `1–500` rows and default to `100`. Cursor pagination is not implemented.

## Idempotency and optimistic concurrency

Case mutation request bodies may contain `idempotency_key`. The backend stores the action/scope/result and returns the prior result for an exact replay.

Versioned case mutations may contain `expected_version`. A stale version returns `409` rather than overwriting a concurrent workflow change. These values are JSON fields in the current API, not `Idempotency-Key` or `If-Match` headers.

## Endpoint groups

| Group | Implemented responsibility |
|---|---|
| Health and observability | Liveness/readiness, protected process and validation metrics. |
| Authentication | Demo login, current principal/scopes, locale preference. |
| Reference and ledger | Providers, areas, outlets, dashboard, transactions, balance history, data-quality reads. |
| Simulation and ingestion | Scenario catalog, deterministic run/reset, fault control, normalized batch ingestion. |
| Analytics | Liquidity projections, unusual-activity flags/evidence, internal analytics triggers. |
| Alerts | Authorized alert list/detail, saved explanation renders, internal publication. |
| Cases | Queue/detail, assignment, acknowledgement, escalation, notes, review, resolution, timeline, audit. |
| Notifications | Authorized list and read acknowledgement. |
| Validation | Persisted validation runs and metric results. |

## Internal-only controls

The following routes require an admin/service-authorized demo identity and are not public analytical services:

- `POST /api/v1/ingestion/batches`
- `POST /api/v1/internal/analytics/liquidity/run`
- `POST /api/v1/internal/analytics/anomalies/run`
- `POST /api/v1/internal/alerts/publish`
- scenario run/reset/fault mutation routes

They produce synthetic decision-support records only. There are no transfer, settlement, refill, reversal, block, freeze, accusation, or final-decision endpoints.

## Similar-case response

At repository head, `GET /api/v1/cases/{case_id}` may include a `similar_cases` panel containing provider-scoped resolved-case matches, similarity scores, stored outcomes, and corpus origin. It requires migration `011_case_similar_embeddings.sql` and a seeded/resolved corpus. Below the minimum corpus it returns an explicit insufficient/unavailable state rather than inventing context.

## OpenAPI generation

From `backend`:

```powershell
python -m app.scripts.generate_openapi
```

Generated artifact: [`docs/openapi/openapi.v1.json`](openapi/openapi.v1.json).
