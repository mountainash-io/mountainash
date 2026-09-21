"""Immutable descriptive, policy and inventory views; never execution authority."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, cast

from mountainash.core.capabilities.capture import CapturedAddress, CapturedAssertion, require_immutable
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityKey,
    QualifiedCapabilityKey,
    QualifiedInformation,
    QualifiedInformationKey,
    QualifiedPolicy,
    Selector,
)
from mountainash.core.capabilities.gaps import GapInventory, GapKey, InventoryGap, InventoryWide, gap_order_key
from mountainash.core.capabilities.identity import Scope
from mountainash.core.capabilities.retired import AssertionChange, ChangeDisposition
from mountainash.core.capabilities.schema import (
    WILDCARD_PARAM,
    CaptureValue,
    _UPSTREAM_REF_RE,
    CapabilityLevel,
    CapabilityIssueClass,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
    GapKind,
    Target,
    target_order_key,
)
from mountainash.core.constants import CONST_BACKEND

if TYPE_CHECKING:
    from collections.abc import Mapping
    from mountainash.core.capabilities.capture import SourceOrigin


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
        key.variant or "",
    )


@dataclass(frozen=True)
class InformationQuery:
    operation: Enum | None = None
    subject: str | None = None
    layer: InformationLayer | None = None
    level: CapabilityLevel | None = None
    kind: CapabilityIssueClass | None = None

    def __post_init__(self) -> None:
        if self.subject is not None and (type(self.subject) is not str or not self.subject):
            raise ValueError("subject requires a nonempty protocol parameter")
        if self.operation is not None:
            _validate_operation_subject(self.operation, self.subject)
        if self.layer is not None and type(self.layer) is not InformationLayer:
            raise TypeError("layer requires InformationLayer")
        if self.level is not None and type(self.level) is not CapabilityLevel:
            raise TypeError("level requires CapabilityLevel")
        if self.kind is not None and type(self.kind) is not CapabilityIssueClass:
            raise TypeError("kind requires CapabilityIssueClass")

    def matches(self, record: QualifiedInformation) -> bool:
        return (
            (self.operation is None or self.operation == record.key.local.operation)
            and (self.subject is None or self.subject == record.key.local.subject)
            and (self.layer is None or self.layer is record.key.layer)
            and (self.level is None or self.level is record.assertion.level)
            and (self.kind is None or self.kind in record.assertion.kinds)
        )


@dataclass(frozen=True)
class PolicyQuery:
    operation: Enum | None = None
    subject: str | None = None
    level: CapabilityLevel | None = None
    consumer: PolicyConsumer | None = None
    action: PolicyAction | None = None

    def __post_init__(self) -> None:
        if self.subject is not None and (type(self.subject) is not str or not self.subject):
            raise ValueError("subject requires a nonempty protocol parameter")
        if self.operation is not None:
            _validate_operation_subject(self.operation, self.subject)
        for name, expected in (
            ("level", CapabilityLevel),
            ("consumer", PolicyConsumer),
            ("action", PolicyAction),
        ):
            value = getattr(self, name)
            if value is not None and type(value) is not expected:
                raise TypeError(f"{name} requires {expected.__name__}")

    def matches(self, record: QualifiedPolicy) -> bool:
        return (
            (self.operation is None or self.operation == record.key.local.operation)
            and (self.subject is None or self.subject == record.key.local.subject)
            and (self.level is None or self.level is record.assertion.level)
            and (self.consumer is None or self.consumer is record.assertion.consumer)
            and (self.action is None or self.action is record.assertion.action)
        )


@dataclass(frozen=True)
class ChangeQuery:
    family: Literal["capability", "gap"] | None = None
    prior: CapturedAssertion | None = None
    disposition: ChangeDisposition | None = None
    change_ref: CapturedAddress | None = None
    inventory: str | None = None

    def __post_init__(self) -> None:
        if self.family is not None and self.family not in {"capability", "gap"}:
            raise ValueError("unknown assertion family")
        for name, expected in (
            ("prior", CapturedAssertion),
            ("disposition", ChangeDisposition),
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
class ScopeReader:
    """One exact scope over retained immutable publication mappings."""

    scope: Scope
    _information: Mapping[QualifiedInformationKey, QualifiedInformation]
    _policies: Mapping[QualifiedCapabilityKey, QualifiedPolicy]

    def __post_init__(self) -> None:
        if type(self.scope) is not Scope:
            raise TypeError("reader scope requires Scope")
        if any(type(records) is not MappingProxyType for records in (self._information, self._policies)):
            raise TypeError("reader requires published immutable mappings")

    def policy(self, key: CapabilityKey) -> QualifiedPolicy:
        if type(key) is not CapabilityKey:
            raise TypeError("scope policy requires CapabilityKey")
        _validate_operation_subject(key.operation, key.subject)
        return self._policies[QualifiedCapabilityKey(self.scope, key)]

    def policy_optional(self, key: CapabilityKey) -> QualifiedPolicy | None:
        if type(key) is not CapabilityKey:
            raise TypeError("scope policy requires CapabilityKey")
        _validate_operation_subject(key.operation, key.subject)
        return self._policies.get(QualifiedCapabilityKey(self.scope, key))

    def search(
        self,
        query: InformationQuery | PolicyQuery,
    ) -> tuple[QualifiedInformation, ...] | tuple[QualifiedPolicy, ...]:
        if type(query) is InformationQuery:
            keys = sorted(
                (key for key, record in self._information.items() if key.scope == self.scope and query.matches(record)),
                key=_information_order,
            )
            return tuple(self._information[key] for key in keys)
        if type(query) is PolicyQuery:
            policy_keys = sorted(
                (key for key, record in self._policies.items() if key.scope == self.scope and query.matches(record)),
                key=_qualified_order,
            )
            return tuple(self._policies[key] for key in policy_keys)
        raise TypeError("scope search requires an information or policy query")


def _information_order(key: QualifiedInformationKey) -> tuple:
    return (
        key.scope.backend.value,
        type(key.scope.applicability).__name__,
        key.scope.dialect or "",
        _key_order(key.local),
        key.layer.value,
    )


class UncapturedScopeError(ValueError):
    """A valid scope was not requested by this catalogue capture."""


def _validate_scopes(scopes: frozenset[Scope] | None) -> None:
    if scopes is not None and (type(scopes) is not frozenset or any(type(scope) is not Scope for scope in scopes)):
        raise TypeError("scopes requires a frozenset of Scope values or None")


def _qualified_order(key: QualifiedCapabilityKey) -> tuple:
    return (
        key.scope.backend.value,
        type(key.scope.applicability).__name__,
        key.scope.dialect or "",
        _key_order(key.local),
    )


def _address_order(address: CapturedAddress) -> tuple:
    return address.repository, address.path, address.entry, address.revision or "", address.artifact or b""


def _claim_scope(claim: CapturedAssertion) -> Scope | InventoryWide | None:
    if type(claim.key) in (QualifiedCapabilityKey, QualifiedInformationKey):
        return claim.key.scope
    if type(claim.key) is GapKey:
        return claim.key.coverage_scope
    return None


def _scope_matches(scope: Scope | InventoryWide | None, scopes: frozenset[Scope], query: CatalogueQuery) -> bool:
    if type(scope) is Scope:
        return scope in scopes and (query.backend is None or scope.backend is query.backend)
    return query.backend is None and query.scopes is None


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
                name == "id" and value.tag == "text" and value.value == reference for name, value in payload.value
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
    information: InformationQuery | None = None
    policies: PolicyQuery | None = None
    gaps: GapQuery | None = None
    backend: CONST_BACKEND | None = None
    scopes: frozenset[Scope] | None = None
    changes: ChangeQuery | None = None

    def __post_init__(self) -> None:
        for name, expected in (
            ("information", InformationQuery),
            ("policies", PolicyQuery),
            ("gaps", GapQuery),
            ("changes", ChangeQuery),
        ):
            value = getattr(self, name)
            if value is not None and type(value) is not expected:
                raise TypeError(f"{name} requires {expected.__name__} or None")
        if self.backend is not None and type(self.backend) is not CONST_BACKEND:
            raise TypeError("backend requires CONST_BACKEND or None")
        _validate_scopes(self.scopes)


@dataclass(frozen=True)
class CatalogueResult:
    information: tuple[QualifiedInformation, ...] | None = None
    policies: tuple[QualifiedPolicy, ...] | None = None
    gaps: tuple[InventoryGap, ...] | None = None
    changes: tuple[AssertionChange, ...] | None = None


@dataclass(frozen=True)
class CatalogueCapture:
    """Retained publication records and explicitly acquired external inventories."""

    scopes: frozenset[Scope]
    segments: tuple[BoundSegment, ...]
    _information: Mapping[QualifiedInformationKey, QualifiedInformation]
    _policies: Mapping[QualifiedCapabilityKey, QualifiedPolicy]
    inventories: tuple[GapInventory, ...] | None = None
    issues: IssueSnapshot | None = None
    _changes: tuple[AssertionChange, ...] = field(init=False, repr=False)
    _gaps: tuple[InventoryGap, ...] | None = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _validate_scopes(self.scopes)
        if self.scopes is None:
            raise TypeError("capture requires an explicit scope set")
        if type(self.segments) is not tuple or any(
            type(segment) is not BoundSegment or segment.scope not in self.scopes for segment in self.segments
        ):
            raise TypeError("capture segments must belong to captured scopes")
        if any(type(records) is not MappingProxyType for records in (self._information, self._policies)):
            raise TypeError("capture requires published immutable mappings")
        if self.inventories is not None:
            if type(self.inventories) is not tuple or any(
                type(inventory) is not GapInventory for inventory in self.inventories
            ):
                raise TypeError("inventories requires an immutable GapInventory tuple")
            if len({inventory.name for inventory in self.inventories}) != len(self.inventories):
                raise ValueError("duplicate inventory name")
        if self.issues is not None and type(self.issues) is not IssueSnapshot:
            raise TypeError("issues requires an explicit IssueSnapshot")
        gaps = (
            None
            if self.inventories is None
            else tuple(
                sorted(
                    (gap for inventory in self.inventories for gap in inventory.gaps),
                    key=gap_order_key,
                )
            )
        )
        object.__setattr__(self, "_gaps", gaps)
        changes = tuple(
            change
            for segment in self.segments
            for change in segment.segment.changes
            if change.prior.family == "capability"
        ) + (
            ()
            if self.inventories is None
            else tuple(change for inventory in self.inventories for change in inventory.changes)
        )
        if len({change.change_ref for change in changes}) != len(changes):
            raise ValueError("duplicate assertion change address")
        object.__setattr__(
            self,
            "_changes",
            tuple(
                sorted(
                    changes,
                    key=lambda change: _address_order(change.change_ref),
                )
            ),
        )

    def reader(self, scope: Scope) -> ScopeReader:
        if type(scope) is not Scope:
            raise TypeError("reader requires Scope")
        if scope not in self.scopes:
            raise UncapturedScopeError(f"scope was not captured: {scope!r}")
        return ScopeReader(scope, self._information, self._policies)

    def composed_information(self, dialect_scope: Scope) -> tuple[QualifiedInformation, ...]:
        """Compose only captured family/local descriptions, preserving original keys."""
        if type(dialect_scope) is not Scope:
            raise TypeError("composed information requires Scope")
        if dialect_scope not in self.scopes:
            raise UncapturedScopeError(f"scope was not captured: {dialect_scope!r}")
        scopes = {dialect_scope}
        if dialect_scope.dialect is not None:
            from mountainash.core.capabilities.identity import FamilyWide

            family_scope = Scope(dialect_scope.backend, FamilyWide())
            if family_scope in self.scopes:
                scopes.add(family_scope)
        keys = sorted(
            (key for key in self._information if key.scope in scopes),
            key=_information_order,
        )
        return tuple(self._information[key] for key in keys)

    def _locate(self, key: QualifiedCapabilityKey | QualifiedInformationKey):
        if type(key) not in (QualifiedCapabilityKey, QualifiedInformationKey):
            raise TypeError("catalogue requires a qualified policy or information key")
        if key.scope not in self.scopes:
            raise UncapturedScopeError(f"scope was not captured: {key.scope!r}")
        _validate_operation_subject(key.local.operation, key.local.subject)
        return self._policies if type(key) is QualifiedCapabilityKey else self._information

    def get(self, key: QualifiedCapabilityKey | QualifiedInformationKey) -> QualifiedPolicy | QualifiedInformation:
        return self._locate(key)[key]

    def get_optional(
        self,
        key: QualifiedCapabilityKey | QualifiedInformationKey,
    ) -> QualifiedPolicy | QualifiedInformation | None:
        return self._locate(key).get(key)

    def policy(self, key: QualifiedCapabilityKey) -> QualifiedPolicy:
        if type(key) is not QualifiedCapabilityKey:
            raise TypeError("catalogue policy requires QualifiedCapabilityKey")
        return self._locate(key)[key]

    def policy_optional(self, key: QualifiedCapabilityKey) -> QualifiedPolicy | None:
        if type(key) is not QualifiedCapabilityKey:
            raise TypeError("catalogue policy requires QualifiedCapabilityKey")
        return self._locate(key).get(key)

    def origins(
        self,
        key: QualifiedCapabilityKey | QualifiedInformationKey,
    ) -> tuple[SourceOrigin, ...]:
        return self.get(key).origins

    def issue(self, reference: str) -> CaptureValue:
        if type(reference) is not str or not _UPSTREAM_REF_RE.fullmatch(reference):
            raise ValueError("issue lookup requires a valid upstream reference")
        if self.issues is None:
            raise UncapturedNamespaceError("upstream issues were not captured")
        return self.issues.get(reference)

    def _require_inventory(self, name: str | None) -> None:
        if self.inventories is None:
            raise UncapturedNamespaceError("gap inventories were not captured")
        if name is not None and not any(inventory.name == name for inventory in self.inventories):
            raise UncapturedNamespaceError(f"inventory was not captured: {name!r}")

    def search(self, query: CatalogueQuery) -> CatalogueResult:
        if type(query) is not CatalogueQuery:
            raise TypeError("catalogue search requires CatalogueQuery")
        scopes = self.scopes if query.scopes is None else query.scopes
        if not scopes <= self.scopes:
            raise UncapturedScopeError("query includes scopes outside this capture")
        information = None
        if query.information is not None:
            keys = sorted(
                (
                    key
                    for key, record in self._information.items()
                    if _scope_matches(key.scope, scopes, query) and query.information.matches(record)
                ),
                key=_information_order,
            )
            information = tuple(self._information[key] for key in keys)
        policies = None
        if query.policies is not None:
            policy_keys = sorted(
                (
                    key
                    for key, record in self._policies.items()
                    if _scope_matches(key.scope, scopes, query) and query.policies.matches(record)
                ),
                key=_qualified_order,
            )
            policies = tuple(self._policies[key] for key in policy_keys)
        gaps = None
        if query.gaps is not None:
            self._require_inventory(query.gaps.inventory)
            gaps = tuple(
                record
                for record in cast("tuple[InventoryGap, ...]", self._gaps)
                if query.gaps.matches(record) and _scope_matches(record.key.coverage_scope, scopes, query)
            )
        changes = None
        if query.changes is not None:
            if (
                query.changes.family == "gap"
                or query.changes.inventory is not None
                or (
                    query.changes.family is None
                    and (query.changes.prior is None or query.changes.prior.family == "gap")
                )
            ):
                self._require_inventory(query.changes.inventory)
            changes = tuple(
                record
                for record in self._changes
                if query.changes.matches(record) and _scope_matches(_claim_scope(record.prior), scopes, query)
            )
        return CatalogueResult(information=information, policies=policies, gaps=gaps, changes=changes)
