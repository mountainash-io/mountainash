"""Local capability records and physical segment authoring contracts.

Leaves export SEGMENT without registration side effects. BoundSegment validates
the enclosing scope, namespace and domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from mountainash.core.capabilities.capture import CapturedAddress, SourceOrigin, require_immutable
from mountainash.core.capabilities.schema import CaptureValue, _UPSTREAM_REF_RE
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
    InformationKind,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
    Predicate,
    ResidueSignal,
    ValueClass,
    _validate_since,
)

if TYPE_CHECKING:
    from mountainash.core.capabilities.identity import Scope
    from mountainash.core.capabilities.retired import AssertionChange


class FactSource(Enum):
    SUBSTRAIT = "substrait"
    MOUNTAINASH = "mountainash"


class Domain(Enum):
    STRING = "string"
    BOOLEAN = "boolean"
    ARITHMETIC = "arithmetic"
    ROUNDING = "rounding"
    DATETIME = "datetime"
    LIST = "list"
    CATEGORICAL = "categorical"
    STRUCT = "struct"
    GEOSPATIAL = "geospatial"
    SET = "set"
    TERNARY = "ternary"
    VALUE = "value"
    RELATION = "relation"
    CAST = "cast"
    COMPARISON = "comparison"
    AGGREGATE = "aggregate"
    NULL = "null"
    WINDOW = "window"
    CONDITIONAL = "conditional"
    NATIVE_INPUT = "native_input"


# Enum-class-name suffix -> Domain. Extended only when a new FKEY/RKEY
# category gains declaration facts; classify_domain raises on unknowns so
# the extension is forced, not forgotten.
_DOMAIN_SUFFIXES: dict[str, Domain] = {
    "STRING": Domain.STRING,
    "BOOLEAN": Domain.BOOLEAN,
    "ARITHMETIC": Domain.ARITHMETIC,
    "ROUNDING": Domain.ROUNDING,
    "DATETIME": Domain.DATETIME,
    "LIST": Domain.LIST,
    "CATEGORICAL": Domain.CATEGORICAL,
    "STRUCT": Domain.STRUCT,
    "SET": Domain.SET,
    "GEOSPATIAL": Domain.GEOSPATIAL,
    "TERNARY": Domain.TERNARY,
    "VALUE": Domain.VALUE,
    "CAST": Domain.CAST,
    "COMPARISON": Domain.COMPARISON,
    "AGGREGATE": Domain.AGGREGATE,
    "NULL": Domain.NULL,
    "WINDOW": Domain.WINDOW,
    "CONDITIONAL": Domain.CONDITIONAL,
}


def classify_source(operation_key: Any) -> FactSource:
    name = type(operation_key).__name__
    if name.startswith(("FKEY_SUBSTRAIT", "RKEY_SUBSTRAIT", "SUBSTRAIT")):
        return FactSource.SUBSTRAIT
    if name.startswith(("FKEY_MOUNTAINASH", "RKEY_MOUNTAINASH")):
        return FactSource.MOUNTAINASH
    raise ValueError(f"cannot classify source of operation-key enum {name!r}")


def classify_domain(operation_key: Any) -> Domain:
    name = type(operation_key).__name__
    if name.startswith("RKEY_"):
        return Domain.RELATION
    for suffix, domain in _DOMAIN_SUFFIXES.items():
        if name.endswith(f"_{suffix}") or name.endswith(f"SCALAR_{suffix}"):
            return domain
    raise ValueError(
        f"cannot classify domain of operation-key enum {name!r}; extend "
        "Domain/_DOMAIN_SUFFIXES in core/capabilities/declarations.py"
    )


def _predicate_operand_identity(operand: object) -> tuple:
    if isinstance(operand, Enum):
        return (
            "enum",
            type(operand).__module__,
            type(operand).__qualname__,
            operand.name,
            CaptureValue.of(operand.value),
        )
    return ("value", CaptureValue.of(operand))


def _validate_issue_reference(issue: str | None) -> None:
    if issue is not None and (type(issue) is not str or _UPSTREAM_REF_RE.fullmatch(issue) is None):
        raise ValueError("issue requires a valid upstream reference")


@dataclass(frozen=True)
class Selector:
    kind: str = "unconditioned"
    value: str | ValueClass | Predicate | None = field(default=None, compare=False)
    _identity: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        expected = {
            "unconditioned": type(None),
            "exact": str,
            "value_class": ValueClass,
            "predicate": Predicate,
        }
        if self.kind not in expected or type(self.value) is not expected[self.kind]:
            raise ValueError("selector requires a supported tag and matching immutable value")
        require_immutable(self.value)
        identity: object
        if type(self.value) is Predicate:
            identity = tuple(
                (clause.path, clause.op.value, _predicate_operand_identity(clause.operand))
                for clause in self.value.clauses
            )
        else:
            identity = CaptureValue.of(self.value)
        object.__setattr__(self, "_identity", identity)


@dataclass(frozen=True)
class CapabilityKey:
    operation: Enum
    subject: str
    selector: Selector = Selector()

    def __post_init__(self) -> None:
        if not isinstance(self.operation, Enum):
            raise TypeError("operation requires an operation enum")
        if type(self.subject) is not str or not self.subject:
            raise ValueError("subject requires a nonempty protocol parameter")
        if type(self.selector) is not Selector:
            raise TypeError("selector requires Selector")
        classify_source(self.operation)
        classify_domain(self.operation)

    @classmethod
    def from_fact(cls, fact: CapabilityFact) -> CapabilityKey:
        if fact.predicate is not None:
            selector = Selector("predicate", fact.predicate)
        elif fact.value_class is not None:
            selector = Selector("value_class", fact.value_class)
        elif fact.option_value is not None:
            selector = Selector("exact", fact.option_value)
        else:
            selector = Selector()
        return cls(fact.operation_key, fact.param, selector)


@dataclass(frozen=True)
class QualifiedCapabilityKey:
    scope: Scope
    local: CapabilityKey

    def __post_init__(self) -> None:
        from mountainash.core.capabilities.identity import Scope

        if type(self.scope) is not Scope or type(self.local) is not CapabilityKey:
            raise TypeError("qualified key requires Scope and CapabilityKey")


@dataclass(frozen=True)
class QualifiedInformationKey:
    scope: Scope
    local: CapabilityKey
    layer: InformationLayer

    def __post_init__(self) -> None:
        from mountainash.core.capabilities.identity import Scope

        if type(self.scope) is not Scope or type(self.local) is not CapabilityKey:
            raise TypeError("qualified information key requires Scope and CapabilityKey")
        if type(self.layer) is not InformationLayer:
            raise TypeError("qualified information key requires InformationLayer")


@dataclass(frozen=True)
class CapabilityInformation:
    """Immutable descriptive information; it has no executable consumer."""

    key: CapabilityKey
    layer: InformationLayer
    level: CapabilityLevel
    since: str
    message: str
    workaround: str | None = None
    issue: str | None = None
    kinds: frozenset[InformationKind] = frozenset()

    def __post_init__(self) -> None:
        if type(self.key) is not CapabilityKey:
            raise TypeError("information key requires CapabilityKey")
        if type(self.layer) is not InformationLayer or type(self.level) is not CapabilityLevel:
            raise TypeError("information requires InformationLayer and CapabilityLevel")
        if type(self.kinds) is not frozenset or any(type(kind) is not InformationKind for kind in self.kinds):
            raise TypeError("information kinds requires a frozenset of InformationKind")
        if type(self.message) is not str or not self.message:
            raise ValueError("information requires a descriptive message")
        if self.workaround is not None and type(self.workaround) is not str:
            raise TypeError("information workaround requires text or None")
        _validate_since(self.since, "CapabilityInformation")
        _validate_issue_reference(self.issue)
        require_immutable(self)


@dataclass(frozen=True)
class QualifiedInformation:
    key: QualifiedInformationKey
    assertion: CapabilityInformation
    origins: tuple[SourceOrigin, ...]

    def __post_init__(self) -> None:
        if type(self.key) is not QualifiedInformationKey:
            raise TypeError("qualified information requires a qualified information key")
        if type(self.assertion) is not CapabilityInformation:
            raise TypeError("qualified information requires CapabilityInformation")
        if self.key.local != self.assertion.key or self.key.layer is not self.assertion.layer:
            raise ValueError("qualified information key disagrees with information")
        if type(self.origins) is not tuple or not self.origins:
            raise ValueError("qualified information requires nonempty immutable origins")
        if any(type(origin) is not SourceOrigin for origin in self.origins):
            raise TypeError("qualified information origins require source origins")
        require_immutable(self)


@dataclass(frozen=True)
class CapabilityPolicyRule:
    """Executable policy with an explicit consumer and action."""

    key: CapabilityKey
    level: CapabilityLevel
    since: str
    message: str
    consumer: PolicyConsumer
    action: PolicyAction
    native_errors: tuple[type[Exception], ...] = ()
    native_issue: str | None = None
    information: QualifiedInformationKey | None = None

    def __post_init__(self) -> None:
        if type(self.key) is not CapabilityKey or type(self.level) is not CapabilityLevel:
            raise TypeError("policy requires CapabilityKey and CapabilityLevel")
        if type(self.message) is not str or not self.message:
            raise ValueError("policy requires an intrinsic reason")
        if type(self.consumer) is not PolicyConsumer or type(self.action) is not PolicyAction:
            raise TypeError("policy requires explicit PolicyConsumer and PolicyAction")
        if type(self.native_errors) is not tuple or any(
            not isinstance(error, type) or not issubclass(error, Exception) for error in self.native_errors
        ):
            raise TypeError("policy native_errors requires exception classes")
        if self.native_issue is not None and (type(self.native_issue) is not str or not self.native_issue.strip()):
            raise ValueError("policy native_issue requires a nonempty code-owned identity")
        if self.information is not None and type(self.information) is not QualifiedInformationKey:
            raise TypeError("policy information requires QualifiedInformationKey or None")
        _validate_since(self.since, "CapabilityPolicyRule")
        if self.consumer is PolicyConsumer.GATE:
            if (
                self.action not in (PolicyAction.BLOCK, PolicyAction.PERMIT)
                or self.native_errors
                or self.native_issue is not None
            ):
                raise ValueError("gate policy requires BLOCK/PERMIT without native error identity")
            blocking_level = self.level in (CapabilityLevel.UNSUPPORTED, CapabilityLevel.LITERAL_ONLY)
            if (self.action is PolicyAction.BLOCK) != blocking_level:
                raise ValueError(
                    "gate BLOCK requires UNSUPPORTED or LITERAL_ONLY; PERMIT requires a non-blocking level"
                )
            if self.level is CapabilityLevel.LITERAL_ONLY and (
                self.key.subject == "*" or self.key.selector.kind != "unconditioned"
            ):
                raise ValueError("literal-only protection requires an unconditioned argument key")
        elif self.consumer in (PolicyConsumer.IMMEDIATE_ERROR, PolicyConsumer.MATERIALIZATION_ERROR):
            if self.action is not PolicyAction.ENRICH or not self.native_errors or self.native_issue is None:
                raise ValueError("error policy requires ENRICH, native exception classes and native_issue")
        elif self.consumer is PolicyConsumer.RESULT_PROTECTION:
            if (
                self.action is not PolicyAction.DETECT_NON_NULL_TO_NULL
                or self.native_errors
                or self.native_issue is not None
            ):
                raise ValueError(
                    "result-protection policy requires DETECT_NON_NULL_TO_NULL without native error identity"
                )
        require_immutable(self)

    def qualify(self, scope: Scope) -> CapabilityFact:
        from mountainash.core.capabilities.identity import Scope

        if type(scope) is not Scope:
            raise TypeError("policy qualification requires Scope")
        if scope.dialect is None:
            raise ValueError("policy requires a concrete dialect scope")
        if self.consumer is PolicyConsumer.GATE:
            enforcement, boundary, signal = Enforcement.GATE, Boundary.BUILD, ResidueSignal.EXCEPTION
        elif self.consumer in (PolicyConsumer.IMMEDIATE_ERROR, PolicyConsumer.MATERIALIZATION_ERROR):
            enforcement, boundary, signal = (
                Enforcement.MATERIALIZE_RESIDUE,
                Boundary.MATERIALIZE,
                ResidueSignal.EXCEPTION,
            )
        else:
            enforcement, boundary, signal = (
                Enforcement.MATERIALIZE_RESIDUE,
                Boundary.MATERIALIZE,
                ResidueSignal.NON_NULL_TO_NULL,
            )
        selector = self.key.selector
        return CapabilityFact(
            operation_key=self.key.operation,
            param=self.key.subject,
            backend=scope.backend,
            dialect=scope.dialect,
            level=self.level,
            since=self.since,
            message=self.message,
            boundary=boundary,
            native_errors=self.native_errors,
            enforcement=enforcement,
            residue_signal=signal,
            consumer=self.consumer,
            action=self.action,
            native_issue=self.native_issue,
            option_value=selector.value if type(selector.value) is str else None,
            value_class=selector.value if type(selector.value) is ValueClass else None,
            predicate=selector.value if type(selector.value) is Predicate else None,
        )


@dataclass(frozen=True)
class QualifiedPolicy:
    key: QualifiedCapabilityKey
    assertion: CapabilityPolicyRule
    origins: tuple[SourceOrigin, ...]

    def __post_init__(self) -> None:
        if type(self.key) is not QualifiedCapabilityKey:
            raise TypeError("qualified policy requires a qualified capability key")
        if type(self.assertion) is not CapabilityPolicyRule:
            raise TypeError("qualified policy requires CapabilityPolicyRule")
        if self.key.local != self.assertion.key:
            raise ValueError("qualified policy key disagrees with policy")
        if type(self.origins) is not tuple or not self.origins:
            raise ValueError("qualified policy requires nonempty immutable origins")
        if any(type(origin) is not SourceOrigin for origin in self.origins):
            raise TypeError("qualified policy origins require source origins")
        require_immutable(self)

    @property
    def native_issue(self) -> str | None:
        return self.assertion.native_issue


@dataclass(frozen=True)
class CapabilitySegment:
    domain: Domain
    information: tuple[CapabilityInformation, ...] = ()
    policies: tuple[CapabilityPolicyRule, ...] = ()
    changes: tuple[AssertionChange, ...] = ()

    def __post_init__(self) -> None:
        from mountainash.core.capabilities.retired import AssertionChange

        if type(self.domain) is not Domain:
            raise TypeError("segment domain requires Domain")
        for name in ("information", "policies", "changes"):
            if type(getattr(self, name)) is not tuple:
                raise TypeError(f"segment {name} requires an immutable tuple")
        information_keys: dict[tuple[CapabilityKey, InformationLayer], int] = {}
        for ordinal, information in enumerate(self.information):
            if type(information) is not CapabilityInformation:
                raise TypeError("segment information requires local information")
            if classify_domain(information.key.operation) is not self.domain:
                raise ValueError(f"segment domain disagrees with {information.key.operation}")
            key = information.key, information.layer
            if key in information_keys:
                raise ValueError(
                    f"duplicate information key {key!r}: information[{information_keys[key]}], information[{ordinal}]"
                )
            information_keys[key] = ordinal
        policy_keys: dict[CapabilityKey, int] = {}
        for ordinal, policy in enumerate(self.policies):
            if type(policy) is not CapabilityPolicyRule:
                raise TypeError("segment policies require explicit policy rules")
            if classify_domain(policy.key.operation) is not self.domain:
                raise ValueError(f"segment domain disagrees with {policy.key.operation}")
            if policy.key in policy_keys:
                raise ValueError(
                    f"duplicate policy key {policy.key!r}: policies[{policy_keys[policy.key]}], policies[{ordinal}]"
                )
            policy_keys[policy.key] = ordinal
        if any(type(change) is not AssertionChange for change in self.changes):
            raise TypeError("segment changes require AssertionChange records")
        require_immutable(self)


@dataclass(frozen=True)
class BoundSegment:
    module: str
    scope: Scope
    segment: CapabilitySegment
    source_capture: CapturedAddress | None = None

    def __post_init__(self) -> None:
        from mountainash.core.capabilities.identity import Scope

        if type(self.scope) is not Scope or type(self.segment) is not CapabilitySegment:
            raise TypeError("bound segment requires Scope and CapabilitySegment")
        if self.source_capture is not None and type(self.source_capture) is not CapturedAddress:
            raise TypeError("bound segment source requires CapturedAddress")
        if type(self.module) is not str:
            raise TypeError("segment module requires a physical module address")
        parts = self.module.split(".")
        if (
            len(parts) < 8
            or parts[0] != "mountainash"
            or parts[1] not in {"expressions", "relations"}
            or parts[2:4] != ["backends", "capabilities"]
        ):
            raise ValueError("segment module is outside capability roots")
        if parts[4] != self.scope.backend.value:
            raise ValueError("physical backend disagrees with segment scope")
        if self.scope.dialect is None:
            prefix = ["family"]
        else:
            prefix = ["dialects", self.scope.dialect.replace("-", "_")]
        if parts[5 : 5 + len(prefix)] != prefix:
            raise ValueError("physical applicability disagrees with segment scope")
        source_index = 5 + len(prefix)
        if len(parts) < source_index + 2:
            raise ValueError("segment module lacks source and domain")
        if parts[source_index] not in {"substrait", "extensions_mountainash"}:
            raise ValueError("segment module has unknown source namespace")
        if parts[source_index + 1] != self.segment.domain.value:
            raise ValueError("physical domain disagrees with segment domain")
        for information in self.segment.information:
            if classify_source(information.key.operation) is not self.source:
                raise ValueError("physical source disagrees with information source")
            root = "relations" if type(information.key.operation).__name__.startswith("RKEY_") else "expressions"
            if root != parts[1]:
                raise ValueError("physical root disagrees with information operation")
        for policy in self.segment.policies:
            if self.scope.dialect is None:
                raise ValueError("policy requires a concrete dialect scope")
            if classify_source(policy.key.operation) is not self.source:
                raise ValueError("physical source disagrees with policy source")
            root = "relations" if type(policy.key.operation).__name__.startswith("RKEY_") else "expressions"
            if root != parts[1]:
                raise ValueError("physical root disagrees with policy operation")

    @property
    def source(self) -> FactSource:
        index = 6 if self.scope.dialect is None else 7
        return FactSource.SUBSTRAIT if self.module.split(".")[index] == "substrait" else FactSource.MOUNTAINASH


@runtime_checkable
class CapabilitySegmentModule(Protocol):
    """Import-safe physical leaf authoring contract."""

    SEGMENT: CapabilitySegment
