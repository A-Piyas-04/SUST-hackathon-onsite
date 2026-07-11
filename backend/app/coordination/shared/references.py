"""Member 1 reference / scope lookup interface (member-2 plan Section 6.2;
master Section 11).

Owner of the CONTRACT: Member 2 (this is what Member 2 needs).
Owner of the IMPLEMENTATION: Member 1 (backed by their repositories).

Member 2 modules MUST depend only on this narrow, versioned, read-only
interface — never on Member 1 repositories directly. That keeps the
provider-boundary rules testable (via `InMemoryReferenceLookup`) and lets
Member 1 drop in the real implementation without editing Member 2 code.

Design rules:
  * Return the minimum required data; never leak confidential evidence or
    repository internals.
  * Existence checks return booleans / small value objects, so a caller cannot
    distinguish "missing" from "forbidden" — that decision stays in the Member 2
    service, which maps both to the same safe 404.
  * Pure-stdlib: `Protocol` + dataclasses, no ORM/pydantic import.

STATUS: PROVISIONAL. Member 1's concrete lookup contract is not yet published;
the field set below is Member 2's proposed v1 and is pending Member 1 approval
(see docs/coordination-security/unresolved-dependencies.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

REFERENCE_CONTRACT_VERSION = "v1-provisional"


@dataclass(frozen=True)
class ProviderRef:
    provider_id: str
    code: str  # bkash | nagad | rocket
    is_active: bool


@dataclass(frozen=True)
class OutletRef:
    outlet_id: str
    area_id: str | None
    is_active: bool


@dataclass(frozen=True)
class AccountRef:
    outlet_provider_account_id: str
    outlet_id: str
    provider_id: str
    is_active: bool


@dataclass(frozen=True)
class SourceResultRef:
    """A persisted Member 1/Member 3 analytical result an alert may cite.

    `result_type` is one of `liquidity_projection`, `anomaly_flag`,
    `data_quality_assessment`. `is_alertable` reflects Member 3's
    alertability/suppression truth table as persisted by Member 1 — Member 2
    consumes it and NEVER recomputes it.
    """

    source_result_id: str
    result_type: str
    outlet_id: str
    provider_id: str | None
    is_alertable: bool
    is_suppressed: bool = False


@dataclass(frozen=True)
class CallerScope:
    """The authenticated caller's resolved provider/area/outlet reach, derived
    from `user_access_scopes`. Empty sets mean "no reach", never "all"."""

    user_id: str
    roles: frozenset[str] = field(default_factory=frozenset)
    provider_ids: frozenset[str] = field(default_factory=frozenset)
    area_ids: frozenset[str] = field(default_factory=frozenset)
    outlet_ids: frozenset[str] = field(default_factory=frozenset)
    is_active: bool = True


@runtime_checkable
class ReferenceLookup(Protocol):
    """Read-only lookups Member 2 needs from Member 1. All methods are safe to
    call for any ID; they never raise on "not found" — they return None/False so
    the Member 2 service controls the safe-404 mapping."""

    def get_provider(self, provider_id: str) -> ProviderRef | None: ...

    def get_outlet(self, outlet_id: str) -> OutletRef | None: ...

    def get_account(self, outlet_provider_account_id: str) -> AccountRef | None: ...

    def account_matches(self, outlet_id: str, provider_id: str, account_id: str) -> bool:
        """True iff the account belongs to exactly that outlet+provider pair."""
        ...

    def get_source_result(self, source_result_id: str) -> SourceResultRef | None: ...

    def source_matches_scope(
        self, source_result_id: str, outlet_id: str, provider_id: str | None
    ) -> bool:
        """True iff the analytical source belongs to the claimed outlet/provider."""
        ...


class InMemoryReferenceLookup:
    """A mockable, dependency-free implementation for Member 2 tests and
    fixtures. Member 1's real implementation replaces this at composition time.
    Satisfies the `ReferenceLookup` Protocol structurally.
    """

    def __init__(
        self,
        providers: dict[str, ProviderRef] | None = None,
        outlets: dict[str, OutletRef] | None = None,
        accounts: dict[str, AccountRef] | None = None,
        sources: dict[str, SourceResultRef] | None = None,
    ) -> None:
        self._providers = providers or {}
        self._outlets = outlets or {}
        self._accounts = accounts or {}
        self._sources = sources or {}

    def get_provider(self, provider_id: str) -> ProviderRef | None:
        return self._providers.get(provider_id)

    def get_outlet(self, outlet_id: str) -> OutletRef | None:
        return self._outlets.get(outlet_id)

    def get_account(self, outlet_provider_account_id: str) -> AccountRef | None:
        return self._accounts.get(outlet_provider_account_id)

    def account_matches(self, outlet_id: str, provider_id: str, account_id: str) -> bool:
        acct = self._accounts.get(account_id)
        return bool(acct and acct.outlet_id == outlet_id and acct.provider_id == provider_id)

    def get_source_result(self, source_result_id: str) -> SourceResultRef | None:
        return self._sources.get(source_result_id)

    def source_matches_scope(
        self, source_result_id: str, outlet_id: str, provider_id: str | None
    ) -> bool:
        src = self._sources.get(source_result_id)
        if src is None:
            return False
        if src.outlet_id != outlet_id:
            return False
        # shared-cash sources carry provider_id is None on both sides.
        return src.provider_id == provider_id
