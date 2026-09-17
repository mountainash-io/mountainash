"""Local capability assertions and physical segment authoring contracts.

Leaves export SEGMENT without registration side effects. BoundSegment validates
the enclosing scope, namespace and domain, then qualifies runtime facts once.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from mountainash.core.capabilities.capture import CapturedAddress, SourceOrigin, require_immutable
from mountainash.core.capabilities.schema import (
    CaptureValue,
    DivergenceKind,
    Scenario,
    Target,
    _UPSTREAM_REF_RE,
    _validate_external_target_scope,
    target_home,
)
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
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
class QualifiedManifestationKey:
    scope: Scope
    local: ManifestationKey

    def __post_init__(self) -> None:
        from mountainash.core.capabilities.identity import Scope

        if type(self.scope) is not Scope or type(self.local) is not ManifestationKey:
            raise TypeError("qualified key requires Scope and ManifestationKey")
        _validate_external_target_scope(self.local.target, self.scope)


@dataclass(frozen=True)
class QualifiedManifestation:
    key: QualifiedManifestationKey
    assertion: DivergenceManifestation
    origins: tuple[SourceOrigin, ...]

    def __post_init__(self) -> None:
        if type(self.key) is not QualifiedManifestationKey:
            raise TypeError("qualified manifestation requires a qualified key")
        if type(self.assertion) is not DivergenceManifestation:
            raise TypeError("qualified manifestation requires a divergence manifestation")
        if self.key.local != self.assertion.key:
            raise ValueError("qualified manifestation key disagrees with assertion")
        if type(self.origins) is not tuple or not self.origins:
            raise ValueError("qualified manifestation requires nonempty immutable origins")
        if any(type(origin) is not SourceOrigin for origin in self.origins):
            raise TypeError("qualified manifestation origins require source origins")
        require_immutable(self)


@dataclass(frozen=True)
class CapabilityAssertion:
    key: CapabilityKey
    level: CapabilityLevel
    since: str
    message: str = ""
    workaround: str | None = None
    issue: str | None = None
    boundary: Boundary = Boundary.BUILD
    native_errors: tuple[type[Exception], ...] = ()
    condition: str | None = None
    probe_exempt: str | None = None
    enforcement: Enforcement = Enforcement.GATE
    signal: ResidueSignal = ResidueSignal.EXCEPTION

    def __post_init__(self) -> None:
        if type(self.key) is not CapabilityKey:
            raise TypeError("assertion key requires CapabilityKey")
        _validate_since(self.since, "CapabilityAssertion")
        _validate_issue_reference(self.issue)
        require_immutable(self)

    def qualify(self, scope: Scope) -> CapabilityFact:
        from mountainash.core.capabilities.identity import Scope
        from mountainash.core.capabilities.registry import _validate_fact, _validate_payload

        if type(scope) is not Scope:
            raise TypeError("qualification requires Scope")
        selector = self.key.selector
        fact = CapabilityFact(
            operation_key=self.key.operation,
            param=self.key.subject,
            backend=scope.backend,
            dialect=scope.dialect,
            level=self.level,
            since=self.since,
            message=self.message,
            workaround=self.workaround,
            upstream_ref=self.issue,
            boundary=self.boundary,
            native_errors=self.native_errors,
            condition=self.condition,
            probe_exempt=self.probe_exempt,
            enforcement=self.enforcement,
            residue_signal=self.signal,
            option_value=selector.value if type(selector.value) is str else None,
            value_class=selector.value if type(selector.value) is ValueClass else None,
            predicate=selector.value if type(selector.value) is Predicate else None,
        )
        _validate_payload(fact)
        _validate_fact(scope.backend, fact)
        return fact


def _protocol_options(method) -> frozenset[str]:
    """Return metadata-owned options for a protocol method, if any."""
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationRegistry,
    )

    option_sets: set[frozenset[str]] = set()
    registries: tuple[type[ExpressionFunctionRegistry] | type[RelationOperationRegistry], ...] = (
        ExpressionFunctionRegistry,
        RelationOperationRegistry,
    )
    for registry in registries:
        for operation in registry.list_all():
            definition = registry.get(operation)
            if definition.protocol_method is method:
                option_sets.add(frozenset(definition.options))
    if len(option_sets) > 1:
        raise ValueError("scenario options require unambiguous operation metadata")
    return next(iter(option_sets), frozenset())


def _scenario_authority(target: Target):
    """Resolve a scenario signature from the target's captured authority."""
    import inspect

    from mountainash.core.capabilities.registry import _definition_for
    from mountainash.core.capabilities.schema import (
        ExternalEntrypointTarget,
        OperationTarget,
        ProtocolMethodTarget,
        _EXTERNAL_TABLE_OPTIONS,
        _EXTERNAL_TABLE_SIGNATURE,
        _target_callable,
    )

    if type(target) is ExternalEntrypointTarget:
        return _EXTERNAL_TABLE_SIGNATURE.parameters, _EXTERNAL_TABLE_OPTIONS
    if type(target) is OperationTarget:
        definition = _definition_for(target.operation)[1]
        method = definition.protocol_method
        options = frozenset(definition.options)
    else:
        method = _target_callable(target)
        options = _protocol_options(method) if type(target) is ProtocolMethodTarget else frozenset()
    if method is None:
        raise ValueError("scenario parameters require a resolved protocol signature")
    parameters = {
        name: parameter
        for name, parameter in inspect.signature(method).parameters.items()
        if name not in {"self", "cls"}
    }
    if not options.issubset(parameters):
        raise ValueError("operation option metadata disagrees with its protocol signature")
    return parameters, options


@dataclass(frozen=True)
class ManifestationKey:
    target: Target
    scenario: Scenario

    def __post_init__(self) -> None:
        target_home(self.target)
        if type(self.scenario) is not Scenario:
            raise TypeError("manifestation scenario requires Scenario")
        if not self.scenario.arguments and not self.scenario.options:
            return
        import inspect

        parameters, options = _scenario_authority(self.target)
        supplied = set()
        for channel, fields in (
            ("argument", self.scenario.arguments),
            ("option", self.scenario.options),
        ):
            for name, value in fields:
                parameter = parameters.get(name)
                if parameter is None:
                    raise ValueError(f"unknown scenario parameter {name!r}")
                if name in supplied:
                    raise ValueError(f"scenario parameter {name!r} occurs in both channels")
                supplied.add(name)
                if channel == "argument" and name in options:
                    raise ValueError(f"scenario option {name!r} must use the options channel")
                if channel == "option" and name not in options:
                    raise ValueError(f"scenario argument {name!r} must not use the options channel")
                if parameter.kind is inspect.Parameter.VAR_POSITIONAL and value.tag != "sequence":
                    raise ValueError(f"varargs scenario parameter {name!r} requires a sequence")
                if parameter.kind is inspect.Parameter.VAR_KEYWORD and value.tag != "mapping":
                    raise ValueError(f"keyword scenario parameter {name!r} requires a mapping")


@dataclass(frozen=True)
class DivergenceManifestation:
    key: ManifestationKey
    kind: DivergenceKind
    expected: CaptureValue
    observed: CaptureValue
    impact: str
    since: str
    workaround: str | None = None
    issue: str | None = None

    def __post_init__(self) -> None:
        if type(self.key) is not ManifestationKey or type(self.kind) is not DivergenceKind:
            raise TypeError("manifestation requires a typed key and divergence kind")
        if type(self.expected) is not CaptureValue or type(self.observed) is not CaptureValue:
            raise TypeError("manifestation outcomes require structured captured values")
        if type(self.impact) is not str or not self.impact:
            raise ValueError("manifestation requires an impact")
        _validate_since(self.since, "DivergenceManifestation")
        _validate_issue_reference(self.issue)
        require_immutable(self)


@dataclass(frozen=True)
class CapabilitySegment:
    domain: Domain
    capabilities: tuple[CapabilityAssertion, ...] = ()
    manifestations: tuple[DivergenceManifestation, ...] = ()
    changes: tuple[AssertionChange, ...] = ()

    def __post_init__(self) -> None:
        from mountainash.core.capabilities.retired import AssertionChange

        if type(self.domain) is not Domain:
            raise TypeError("segment domain requires Domain")
        for name in ("capabilities", "manifestations", "changes"):
            if type(getattr(self, name)) is not tuple:
                raise TypeError(f"segment {name} requires an immutable tuple")
        keys: dict[CapabilityKey, int] = {}
        for ordinal, assertion in enumerate(self.capabilities):
            if type(assertion) is not CapabilityAssertion:
                raise TypeError("segment capabilities require local assertions")
            if classify_domain(assertion.key.operation) is not self.domain:
                raise ValueError(f"segment domain disagrees with {assertion.key.operation}")
            if assertion.key in keys:
                raise ValueError(
                    f"duplicate capability key {assertion.key!r}: "
                    f"capabilities[{keys[assertion.key]}], capabilities[{ordinal}]"
                )
            keys[assertion.key] = ordinal
        if any(type(change) is not AssertionChange for change in self.changes):
            raise TypeError("segment changes require AssertionChange records")
        manifestation_keys: dict[ManifestationKey, int] = {}
        for ordinal, manifestation in enumerate(self.manifestations):
            if type(manifestation) is not DivergenceManifestation:
                raise TypeError("segment manifestations require local typed records")
            if target_home(manifestation.key.target)[2] is not self.domain:
                raise ValueError("manifestation home disagrees with segment domain")
            if manifestation.key in manifestation_keys:
                raise ValueError(
                    f"duplicate manifestation key: manifestations[{manifestation_keys[manifestation.key]}], "
                    f"manifestations[{ordinal}]"
                )
            manifestation_keys[manifestation.key] = ordinal
        require_immutable(self)


@dataclass(frozen=True)
class BoundSegment:
    module: str
    scope: Scope
    segment: CapabilitySegment
    source_capture: CapturedAddress | None = None
    facts: tuple[CapabilityFact, ...] = field(init=False)

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
        for assertion in self.segment.capabilities:
            if classify_source(assertion.key.operation) is not self.source:
                raise ValueError("physical source disagrees with assertion source")
            root = "relations" if type(assertion.key.operation).__name__.startswith("RKEY_") else "expressions"
            if root != parts[1]:
                raise ValueError("physical root disagrees with assertion operation")
        for manifestation in self.segment.manifestations:
            if target_home(manifestation.key.target) != (parts[1], self.source, self.segment.domain):
                raise ValueError("manifestation home disagrees with physical segment")
            _validate_external_target_scope(manifestation.key.target, self.scope)
        object.__setattr__(
            self, "facts", tuple(assertion.qualify(self.scope) for assertion in self.segment.capabilities)
        )

    @property
    def source(self) -> FactSource:
        index = 6 if self.scope.dialect is None else 7
        return FactSource.SUBSTRAIT if self.module.split(".")[index] == "substrait" else FactSource.MOUNTAINASH


@runtime_checkable
class CapabilitySegmentModule(Protocol):
    """Import-safe physical leaf authoring contract."""

    SEGMENT: CapabilitySegment
