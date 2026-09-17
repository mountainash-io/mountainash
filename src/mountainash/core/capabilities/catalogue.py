"""Exact stored access, separate from effective capability resolution."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from mountainash.core.capabilities.capture import (
    BindingRole, CapturedAddress, CapturedAssertion, EvidenceCapture,
    VerificationBinding, require_immutable,
)
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityKey,
    QualifiedCapabilityKey,
    Selector,
    ManifestationKey,
    QualifiedManifestation,
    QualifiedManifestationKey,
)
from mountainash.core.capabilities.identity import Scope
from mountainash.core.capabilities.gaps import GapKey, InventoryGap, InventoryWide, VerificationSnapshot
from mountainash.core.capabilities.retired import AssertionChange, ChangeDisposition
from mountainash.core.capabilities.schema import (
    WILDCARD_PARAM,
    CaptureValue,
    _UPSTREAM_REF_RE,
    CapabilityLevel,
    Enforcement,
    DivergenceKind,
    Scenario,
    GapKind,
    Target,
    target_order_key,
    Predicate,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mountainash.core.capabilities.schema import CapabilityFact
    from mountainash.core.capabilities.capture import RuntimeOrigin, SourceOrigin


def _validate_operation_subject(operation: Enum, subject: str | None) -> None:
    from mountainash.core.capabilities.registry import _definition_for

    if not isinstance(operation, Enum):
        raise TypeError("operation requires an operation enum")
    _, definition = _definition_for(operation)
    method = definition.protocol_method
    if subject is not None and subject != WILDCARD_PARAM and method is not None:
        parameters = inspect.signature(method).parameters
        if subject in {"self", "cls"} or subject not in parameters:
            raise ValueError(f"unknown protocol subject {subject!r} for {operation!r}")


def _selector_order(selector: Selector) -> tuple:
    return selector.kind, selector._identity


def _key_order(key: CapabilityKey) -> tuple:
    operation = key.operation
    return (
        type(operation).__module__,
        type(operation).__qualname__,
        operation.name,
        key.subject,
        _selector_order(key.selector),
    )


@dataclass(frozen=True)
class CapabilityQuery:
    operation: Enum | None = None
    subject: str | None = None
    selector_kind: Literal["unconditioned", "exact", "value_class", "predicate"] | None = None
    selector_value: str | ValueClass | Predicate | None = None
    level: CapabilityLevel | None = None
    enforcement: Enforcement | None = None
    has_predicate: bool | None = None
    has_condition_text: bool | None = None
    _selector: Selector | None = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.subject is not None and (type(self.subject) is not str or not self.subject):
            raise ValueError("subject requires a nonempty protocol parameter")
        if self.operation is not None:
            _validate_operation_subject(self.operation, self.subject)
        kinds = {"unconditioned", "exact", "value_class", "predicate"}
        if self.selector_kind is not None and self.selector_kind not in kinds:
            raise ValueError("unknown selector kind")
        selector = None
        if self.selector_value is not None:
            value_kind = {str: "exact", ValueClass: "value_class", Predicate: "predicate"}.get(
                type(self.selector_value)
            )
            if value_kind is None:
                raise TypeError("selector value requires text, ValueClass or Predicate")
            selector = Selector(self.selector_kind or value_kind, self.selector_value)
        object.__setattr__(self, "_selector", selector)
        for name, expected in (
            ("level", CapabilityLevel),
            ("enforcement", Enforcement),
            ("has_predicate", bool),
            ("has_condition_text", bool),
        ):
            value = getattr(self, name)
            if value is not None and type(value) is not expected:
                raise TypeError(f"{name} requires {expected.__name__}")

    def matches(self, key: CapabilityKey, fact: CapabilityFact) -> bool:
        if self.operation is not None and key.operation != self.operation:
            return False
        if self.subject is not None and key.subject != self.subject:
            return False
        if self.selector_kind is not None and key.selector.kind != self.selector_kind:
            return False
        if self._selector is not None and key.selector != self._selector:
            return False
        return (
            (self.level is None or fact.level is self.level)
            and (self.enforcement is None or fact.enforcement is self.enforcement)
            and (self.has_predicate is None or (fact.predicate is not None) == self.has_predicate)
            and (
                self.has_condition_text is None
                or (fact.condition is not None) == self.has_condition_text
            )
        )


@dataclass(frozen=True)
class ManifestationQuery:
    target: Target | None = None
    scenario: Scenario | None = None
    kind: DivergenceKind | None = None
    issue: str | None = None

    def __post_init__(self) -> None:
        if self.target is not None:
            target_order_key(self.target)
        if self.scenario is not None and type(self.scenario) is not Scenario:
            raise TypeError("scenario requires Scenario")
        if self.kind is not None and type(self.kind) is not DivergenceKind:
            raise TypeError("kind requires DivergenceKind")
        if self.issue is not None and (
            type(self.issue) is not str or not _UPSTREAM_REF_RE.fullmatch(self.issue)
        ):
            raise ValueError("issue requires a valid upstream reference")

    def matches(self, record: QualifiedManifestation) -> bool:
        return (
            (self.target is None or self.target == record.key.local.target)
            and (self.scenario is None or self.scenario == record.key.local.scenario)
            and (self.kind is None or self.kind is record.assertion.kind)
            and (self.issue is None or self.issue == record.assertion.issue)
        )


@dataclass(frozen=True)
class EvidenceQuery:
    capture_ref: CapturedAddress | None = None
    subject: CapturedAssertion | None = None
    observation_layer: Literal["native", "public", "gate_disabled", "structural", "historical_unknown"] | None = None

    def __post_init__(self) -> None:
        if self.capture_ref is not None and type(self.capture_ref) is not CapturedAddress:
            raise TypeError("capture_ref requires CapturedAddress")
        if self.subject is not None and type(self.subject) is not CapturedAssertion:
            raise TypeError("subject requires a complete CapturedAssertion")
        if self.observation_layer is not None and self.observation_layer not in {
            "native", "public", "gate_disabled", "structural", "historical_unknown",
        }:
            raise ValueError("unknown observation layer")

    def matches(self, record: EvidenceCapture) -> bool:
        return (
            (self.capture_ref is None or self.capture_ref == record.capture_ref)
            and (self.subject is None or self.subject in record.subjects)
            and (self.observation_layer is None or self.observation_layer == record.observation_layer)
        )


@dataclass(frozen=True)
class ChangeQuery:
    family: Literal["capability", "manifestation", "gap"] | None = None
    prior: CapturedAssertion | None = None
    disposition: ChangeDisposition | None = None
    change_ref: CapturedAddress | None = None
    inventory: str | None = None

    def __post_init__(self) -> None:
        if self.family is not None and self.family not in {"capability", "manifestation", "gap"}:
            raise ValueError("unknown assertion family")
        for name, expected in (
            ("prior", CapturedAssertion), ("disposition", ChangeDisposition),
            ("change_ref", CapturedAddress),
        ):
            value = getattr(self, name)
            if value is not None and type(value) is not expected:
                raise TypeError(f"{name} requires {expected.__name__}")
        if self.inventory is not None:
            if type(self.inventory) is not str or not self.inventory:
                raise ValueError("inventory requires nonempty text")
            if self.family not in (None, "gap"):
                raise ValueError("inventory filter applies only to gap history")

    def matches(self, record: AssertionChange) -> bool:
        return (
            (self.family is None or self.family == record.prior.family)
            and (self.prior is None or self.prior == record.prior)
            and (self.disposition is None or self.disposition is record.disposition)
            and (self.change_ref is None or self.change_ref == record.change_ref)
            and (
                self.inventory is None
                or (type(record.prior.key) is GapKey and self.inventory == record.prior.key.inventory)
            )
        )


@dataclass(frozen=True)
class BindingQuery:
    captured_claim: CapturedAssertion | None = None
    scenario: Scenario | None = None
    role: BindingRole | None = None
    observer: CapturedAddress | None = None
    stage: Literal["construction", "compilation", "materialization"] | None = None

    def __post_init__(self) -> None:
        for name, expected in (
            ("captured_claim", CapturedAssertion), ("scenario", Scenario),
            ("role", BindingRole), ("observer", CapturedAddress),
        ):
            value = getattr(self, name)
            if value is not None and type(value) is not expected:
                raise TypeError(f"{name} requires {expected.__name__}")
        if self.stage is not None and self.stage not in {"construction", "compilation", "materialization"}:
            raise ValueError("unknown execution stage")

    def matches(self, record: VerificationBinding) -> bool:
        return (
            (self.captured_claim is None or self.captured_claim == record.captured_claim)
            and (self.scenario is None or self.scenario == record.scenario)
            and (self.role is None or self.role is record.role)
            and (self.observer is None or self.observer == record.observer)
            and (self.stage is None or self.stage == record.stage)
        )


@dataclass(frozen=True)
class ScopeReader:
    """One exact scope over retained immutable publication mappings."""

    scope: Scope
    _records: Mapping[QualifiedCapabilityKey, CapabilityFact]
    _manifestations: Mapping[QualifiedManifestationKey, QualifiedManifestation]

    def __post_init__(self) -> None:
        if type(self.scope) is not Scope:
            raise TypeError("reader scope requires Scope")
        if type(self._records) is not MappingProxyType or type(self._manifestations) is not MappingProxyType:
            raise TypeError("reader requires published immutable mappings")

    def _locate(self, key: CapabilityKey | ManifestationKey):
        if type(key) is CapabilityKey:
            _validate_operation_subject(key.operation, key.subject)
            return self._records, QualifiedCapabilityKey(self.scope, key)
        if type(key) is ManifestationKey:
            return self._manifestations, QualifiedManifestationKey(self.scope, key)
        raise TypeError("scope reader requires a local capability or manifestation key")

    def get(self, key: CapabilityKey | ManifestationKey) -> CapabilityFact | QualifiedManifestation:
        records, qualified = self._locate(key)
        return records[qualified]

    def get_optional(self, key: CapabilityKey | ManifestationKey) -> CapabilityFact | QualifiedManifestation | None:
        records, qualified = self._locate(key)
        return records.get(qualified)

    def search(self, query: CapabilityQuery | ManifestationQuery) -> tuple[CapabilityFact, ...] | tuple[QualifiedManifestation, ...]:
        if type(query) is ManifestationQuery:
            keys = sorted(
                (key for key, record in self._manifestations.items()
                 if key.scope == self.scope and query.matches(record)),
                key=_manifestation_order,
            )
            return tuple(self._manifestations[key] for key in keys)
        if type(query) is not CapabilityQuery:
            raise TypeError("scope search requires a capability or manifestation query")
        keys = sorted(
            (key for key, fact in self._records.items()
             if key.scope == self.scope and query.matches(key.local, fact)),
            key=_qualified_order,
        )
        return tuple(self._records[key] for key in keys)


class UncapturedScopeError(ValueError):
    """A valid scope was not requested by this catalogue capture."""


def _validate_scopes(scopes: frozenset[Scope] | None) -> None:
    if scopes is not None and (
        type(scopes) is not frozenset or any(type(scope) is not Scope for scope in scopes)
    ):
        raise TypeError("scopes requires a frozenset of Scope values or None")


def _qualified_order(key: QualifiedCapabilityKey) -> tuple:
    return (
        key.scope.backend.value,
        type(key.scope.applicability).__name__,
        key.scope.dialect or "",
        _key_order(key.local),
    )


def _manifestation_order(key: QualifiedManifestationKey) -> tuple:
    return (
        key.scope.backend.value, type(key.scope.applicability).__name__,
        key.scope.dialect or "", target_order_key(key.local.target), key.local.scenario,
    )


def _address_order(address: CapturedAddress) -> tuple:
    return address.repository, address.path, address.entry, address.revision or "", address.artifact or b""


def _claim_scope(claim: CapturedAssertion) -> Scope | InventoryWide | None:
    if type(claim.key) in (QualifiedCapabilityKey, QualifiedManifestationKey):
        return claim.key.scope
    if type(claim.key) is GapKey:
        return claim.key.coverage_scope
    return None


def _scope_matches(scope: Scope | InventoryWide | None, scopes: frozenset[Scope], query: CatalogueQuery) -> bool:
    if type(scope) is Scope:
        return scope in scopes and (query.backend is None or scope.backend is query.backend)
    return query.backend is None and query.scopes is None


def _captured_claim_order(claim: CapturedAssertion) -> tuple:
    key = claim.key
    capture_context = (
        _address_order(claim.address),
        tuple(_address_order(reference) for reference in claim.reference_context),
    )
    if type(key) is QualifiedCapabilityKey:
        return "capability", _qualified_order(key), capture_context
    if type(key) is QualifiedManifestationKey:
        return "manifestation", _manifestation_order(key), capture_context
    if type(key) is GapKey:
        scope = key.coverage_scope
        scope_order = (
            ("inventory",)
            if type(scope) is InventoryWide
            else ("scope", scope.backend.value, type(scope.applicability).__name__, scope.dialect or "")
        )
        return "gap", key.inventory, target_order_key(key.target), key.obligation, scope_order, capture_context
    raise TypeError("binding claim requires a resolved qualified key")


def _binding_order(binding: VerificationBinding) -> tuple:
    return (
        _captured_claim_order(binding.captured_claim), binding.scenario,
        binding.role.value, _address_order(binding.observer),
    )


class UncapturedNamespaceError(ValueError):
    """A requested external authority was not supplied to the capture."""


@dataclass(frozen=True)
class IssueSnapshot:
    """Already-acquired YAML issue metadata, with its immutable source identity."""

    source: CapturedAddress
    entries: tuple[tuple[str, CaptureValue], ...]

    def __post_init__(self) -> None:
        if type(self.source) is not CapturedAddress:
            raise TypeError("issue snapshot requires a captured source")
        entries = CaptureValue("mapping", self.entries).value
        for reference, payload in entries:
            if not _UPSTREAM_REF_RE.fullmatch(reference):
                raise ValueError(f"invalid upstream issue reference: {reference!r}")
            if payload.tag != "mapping" or not any(
                name == "id" and value.tag == "text" and value.value == reference
                for name, value in payload.value
            ):
                raise ValueError("issue payload must retain its matching original id")
        object.__setattr__(self, "entries", entries)
        require_immutable(self)

    def get(self, reference: str) -> CaptureValue:
        if type(reference) is not str or not _UPSTREAM_REF_RE.fullmatch(reference):
            raise ValueError("issue lookup requires a valid upstream reference")
        for key, payload in self.entries:
            if key == reference:
                return payload
        raise KeyError(reference)


@dataclass(frozen=True)
class GapQuery:
    inventory: str | None = None
    target: Target | None = None
    obligation: str | None = None
    kind: GapKind | None = None
    coverage_scope: Scope | InventoryWide | None = None

    def __post_init__(self) -> None:
        for name in ("inventory", "obligation"):
            value = getattr(self, name)
            if value is not None and (type(value) is not str or not value):
                raise ValueError(f"{name} requires nonempty text")
        if self.target is not None:
            target_order_key(self.target)
        if self.kind is not None and type(self.kind) is not GapKind:
            raise TypeError("kind requires GapKind")
        if self.coverage_scope is not None and type(self.coverage_scope) not in (Scope, InventoryWide):
            raise TypeError("coverage_scope requires Scope or InventoryWide")

    def matches(self, record: InventoryGap) -> bool:
        return (
            (self.inventory is None or self.inventory == record.key.inventory)
            and (self.target is None or self.target == record.key.target)
            and (self.obligation is None or self.obligation == record.key.obligation)
            and (self.kind is None or self.kind is record.payload.gap_kind)
            and (self.coverage_scope is None or self.coverage_scope == record.key.coverage_scope)
        )


@dataclass(frozen=True)
class CatalogueQuery:
    capabilities: CapabilityQuery | None = None
    gaps: GapQuery | None = None
    backend: CONST_BACKEND | None = None
    scopes: frozenset[Scope] | None = None
    manifestations: ManifestationQuery | None = None
    evidence: EvidenceQuery | None = None
    changes: ChangeQuery | None = None
    bindings: BindingQuery | None = None

    def __post_init__(self) -> None:
        for name, expected in (
            ("capabilities", CapabilityQuery), ("gaps", GapQuery),
            ("manifestations", ManifestationQuery), ("evidence", EvidenceQuery),
            ("changes", ChangeQuery), ("bindings", BindingQuery),
        ):
            value = getattr(self, name)
            if value is not None and type(value) is not expected:
                raise TypeError(f"{name} requires {expected.__name__} or None")
        if self.backend is not None and type(self.backend) is not CONST_BACKEND:
            raise TypeError("backend requires CONST_BACKEND or None")
        _validate_scopes(self.scopes)


@dataclass(frozen=True)
class CatalogueResult:
    capabilities: tuple[CapabilityFact, ...] | None
    gaps: tuple[InventoryGap, ...] | None = None
    manifestations: tuple[QualifiedManifestation, ...] | None = None
    evidence: tuple[EvidenceCapture, ...] | None = None
    changes: tuple[AssertionChange, ...] | None = None
    bindings: tuple[VerificationBinding, ...] | None = None


@dataclass(frozen=True)
class CatalogueCapture:
    """Retained publication records and origins, not a durable source export.

    RuntimeOrigin remains explicitly session-local. Capturing this view does
    not invent source artifacts or a historical execution for registered rows.
    """

    scopes: frozenset[Scope]
    segments: tuple[BoundSegment, ...]
    _records: Mapping[QualifiedCapabilityKey, CapabilityFact]
    _origins: Mapping[QualifiedCapabilityKey, tuple[SourceOrigin | RuntimeOrigin, ...]]
    _manifestations: Mapping[QualifiedManifestationKey, QualifiedManifestation]
    verification: VerificationSnapshot | None = None
    issues: IssueSnapshot | None = None
    evidence: tuple[EvidenceCapture, ...] | None = None
    _changes: tuple[AssertionChange, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _validate_scopes(self.scopes)
        if self.scopes is None:
            raise TypeError("capture requires an explicit scope set")
        if type(self.segments) is not tuple or any(
            type(segment) is not BoundSegment or segment.scope not in self.scopes
            for segment in self.segments
        ):
            raise TypeError("capture segments must belong to captured scopes")
        if any(type(records) is not MappingProxyType for records in (
            self._records, self._origins, self._manifestations,
        )):
            raise TypeError("capture requires published immutable mappings")
        if self.verification is not None and type(self.verification) is not VerificationSnapshot:
            raise TypeError("verification requires an explicit VerificationSnapshot")
        if self.verification is not None and self.verification.bindings is not None:
            captured_claims: dict[tuple, CapturedAssertion] = {}
            for binding in self.verification.bindings:
                identity = _captured_claim_order(binding.captured_claim)
                previous = captured_claims.setdefault(identity, binding.captured_claim)
                if previous != binding.captured_claim:
                    raise ValueError("conflicting payload for one captured claim source")
        if self.issues is not None and type(self.issues) is not IssueSnapshot:
            raise TypeError("issues requires an explicit IssueSnapshot")
        if self.evidence is not None:
            if type(self.evidence) is not tuple or any(
                type(record) is not EvidenceCapture for record in self.evidence
            ):
                raise TypeError("evidence requires an explicit immutable capture tuple")
            require_immutable(self.evidence)
            if len({record.capture_ref for record in self.evidence}) != len(self.evidence):
                raise ValueError("duplicate evidence capture address")
            object.__setattr__(self, "evidence", tuple(sorted(
                self.evidence, key=lambda record: _address_order(record.capture_ref),
            )))
        changes = tuple(
            change for segment in self.segments for change in segment.segment.changes
        ) + (() if self.verification is None else self.verification.changes)
        if len({change.change_ref for change in changes}) != len(changes):
            raise ValueError("duplicate assertion change address")
        object.__setattr__(self, "_changes", tuple(sorted(
            changes, key=lambda change: _address_order(change.change_ref),
        )))

    def reader(self, scope: Scope) -> ScopeReader:
        if type(scope) is not Scope:
            raise TypeError("reader requires Scope")
        if scope not in self.scopes:
            raise UncapturedScopeError(f"scope was not captured: {scope!r}")
        return ScopeReader(scope, self._records, self._manifestations)

    def _locate(self, key: QualifiedCapabilityKey | QualifiedManifestationKey):
        if type(key) not in (QualifiedCapabilityKey, QualifiedManifestationKey):
            raise TypeError("catalogue requires a qualified capability or manifestation key")
        if key.scope not in self.scopes:
            raise UncapturedScopeError(f"scope was not captured: {key.scope!r}")
        if type(key) is QualifiedCapabilityKey:
            _validate_operation_subject(key.local.operation, key.local.subject)
            return self._records
        return self._manifestations

    def get(self, key: QualifiedCapabilityKey | QualifiedManifestationKey) -> CapabilityFact | QualifiedManifestation:
        return self._locate(key)[key]

    def get_optional(self, key: QualifiedCapabilityKey | QualifiedManifestationKey) -> CapabilityFact | QualifiedManifestation | None:
        return self._locate(key).get(key)

    def origins(self, key: QualifiedCapabilityKey | QualifiedManifestationKey) -> tuple[SourceOrigin | RuntimeOrigin, ...]:
        record = self.get(key)
        if type(key) is QualifiedManifestationKey:
            return record.origins
        return self._origins[key]

    def issue(self, reference: str) -> CaptureValue:
        if type(reference) is not str or not _UPSTREAM_REF_RE.fullmatch(reference):
            raise ValueError("issue lookup requires a valid upstream reference")
        if self.issues is None:
            raise UncapturedNamespaceError("upstream issues were not captured")
        return self.issues.get(reference)

    def _require_inventory(self, name: str | None) -> None:
        if self.verification is None:
            raise UncapturedNamespaceError("verification inventories were not captured")
        if name is not None and not any(
            inventory.name == name for inventory in self.verification.inventories
        ):
            raise UncapturedNamespaceError(f"inventory was not captured: {name!r}")

    def search(self, query: CatalogueQuery) -> CatalogueResult:
        if type(query) is not CatalogueQuery:
            raise TypeError("catalogue search requires CatalogueQuery")
        scopes = self.scopes if query.scopes is None else query.scopes
        if not scopes <= self.scopes:
            raise UncapturedScopeError("query includes scopes outside this capture")
        capabilities = None
        if query.capabilities is not None:
            keys = sorted(
                (key for key, fact in self._records.items()
                 if _scope_matches(key.scope, scopes, query)
                 and query.capabilities.matches(key.local, fact)),
                key=_qualified_order,
            )
            capabilities = tuple(self._records[key] for key in keys)
        manifestations = None
        if query.manifestations is not None:
            keys = sorted(
                (key for key, record in self._manifestations.items()
                 if _scope_matches(key.scope, scopes, query)
                 and query.manifestations.matches(record)),
                key=_manifestation_order,
            )
            manifestations = tuple(self._manifestations[key] for key in keys)
        gaps = None
        if query.gaps is not None:
            self._require_inventory(query.gaps.inventory)
            gaps = tuple(
                record for record in self.verification.gaps
                if query.gaps.matches(record)
                and _scope_matches(record.key.coverage_scope, scopes, query)
            )
        evidence = None
        if query.evidence is not None:
            if self.evidence is None:
                raise UncapturedNamespaceError("evidence captures were not supplied")
            evidence = tuple(
                record for record in self.evidence
                if query.evidence.matches(record)
                and any(
                    (query.evidence.subject is None or query.evidence.subject == subject)
                    and _scope_matches(_claim_scope(subject), scopes, query)
                    for subject in record.subjects
                )
            )
        changes = None
        if query.changes is not None:
            requires_verification = (
                query.changes.family == "gap"
                or query.changes.inventory is not None
                or (
                    query.changes.family is None
                    and (
                        query.changes.prior is None
                        or query.changes.prior.family == "gap"
                    )
                )
            )
            if requires_verification:
                self._require_inventory(query.changes.inventory)
            changes = tuple(
                record for record in self._changes
                if query.changes.matches(record)
                and _scope_matches(_claim_scope(record.prior), scopes, query)
            )
        bindings = None
        if query.bindings is not None:
            if self.verification is None or self.verification.bindings is None:
                raise UncapturedNamespaceError("verification bindings were not captured")
            bindings = tuple(sorted(
                (record for record in self.verification.bindings
                 if query.bindings.matches(record) and _scope_matches(record.scope, scopes, query)),
                key=_binding_order,
            ))
        return CatalogueResult(
            capabilities=capabilities, manifestations=manifestations, gaps=gaps,
            evidence=evidence, changes=changes, bindings=bindings,
        )
