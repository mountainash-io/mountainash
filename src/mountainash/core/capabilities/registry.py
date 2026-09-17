"""CapabilityRegistry — the spine's single lookup surface (spec Section 1).

Registration validates each complete batch before publishing it:
unknown op keys, params, dialects, or duplicate keys raise ValueError.
Lookup is a chain of at most six dictionary hits: value-specific dialect and
family facts, value-agnostic dialect and family facts, then dialect and family
wildcards.
"""

from __future__ import annotations

import inspect
import math
from contextlib import contextmanager
import threading
from dataclasses import dataclass, replace
from enum import Enum as _Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple

from mountainash.core.capabilities.identity import KNOWN_DIALECTS
from mountainash.core.capabilities.schema import (
    Boundary,
    Clause,
    ClauseOp,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
    Fidelity,
    Predicate,
    ResidueSignal,
    TargetKind,
    WILDCARD_PARAM,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND

if TYPE_CHECKING:
    from collections.abc import Mapping
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        QualifiedCapabilityKey,
        QualifiedManifestation,
        QualifiedManifestationKey,
    )
    from mountainash.core.capabilities.capture import EvidenceCapture, RuntimeOrigin, SourceOrigin
    from mountainash.core.capabilities.predicates import BoundCall
    from mountainash.core.capabilities.catalogue import CatalogueCapture, IssueSnapshot, ScopeReader
    from mountainash.core.capabilities.identity import Scope
    from mountainash.core.capabilities.gaps import VerificationSnapshot

# backend slot is CONST_BACKEND | str: str families arrive only via the
# serialization workstream's register_target (spec 2026-07-06); register_backend
# rejects them via the family-identity check in _validate_fact.
_Key = Tuple[Any, str, "CONST_BACKEND | str", Optional[str], Optional[str]]
_ValueClassBucketKey = Tuple[Any, str, "CONST_BACKEND | str", Optional[str]]


class _LoadState(_Enum):
    UNINITIALIZED = "uninitialized"
    LOADED = "loaded"
    FAILED = "failed"
    ISOLATED = "isolated"


@dataclass(frozen=True)
class CapabilityViolation:
    operation_key: Any
    param: str
    fact: CapabilityFact


def _definition_for(operation_key: Any):
    """Resolve the registry definition for an FKEY or RKEY member.

    Returns ``(kind, definition)`` where kind is ``"expression"`` or
    ``"relation"``. Both def types expose ``protocol_method`` and ``options``.
    Lazy imports avoid core→expressions import cycles: registration happens
    from backend modules that already import both subsystems.
    """
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )

    try:
        return "expression", ExpressionFunctionRegistry.get(operation_key)
    except KeyError:
        pass
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationRegistry,
    )

    try:
        return "relation", RelationOperationRegistry.get(operation_key)
    except KeyError:
        raise ValueError(
            f"CapabilityFact operation_key {operation_key!r} resolves in neither "
            "the expression nor the relation registry"
        )


def _enum_key(fact: CapabilityFact):
    return (
        str(getattr(fact.operation_key, "name", fact.operation_key)),
        fact.param,
        str(fact.backend.value if hasattr(fact.backend, "value") else fact.backend),
        fact.dialect or "",
        fact.option_value or "",
        fact.value_class.value if fact.value_class is not None else "",
        fact.residue_signal.value,
        fact.fact_key,
    )


def _validate_fact(family: CONST_BACKEND, fact: CapabilityFact) -> None:
    if fact.backend is not family:
        raise ValueError(
            f"CapabilityFact({fact.operation_key}, {fact.param}): backend "
            f"{fact.backend} registered under family {family}"
        )
    if fact.fidelity is not None:
        raise ValueError(
            f"CapabilityFact({fact.operation_key}, {fact.param}): fidelity is "
            "reserved for SERIALIZE-target facts (spec 2026-07-06); facts "
            "registered via register_backend (EXECUTE) must leave it None"
        )
    if fact.dialect is not None and fact.dialect not in KNOWN_DIALECTS[family]:
        raise ValueError(
            f"CapabilityFact({fact.operation_key}, {fact.param}): dialect "
            f"{fact.dialect!r} is not a known {family.value} dialect "
            f"{sorted(KNOWN_DIALECTS[family])}"
        )
    kind, definition = _definition_for(fact.operation_key)
    if fact.option_value is not None:
        if fact.param == WILDCARD_PARAM:
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): value-scoped facts cannot use WILDCARD_PARAM"
            )
        if fact.boundary is not Boundary.BUILD:
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): value-scoped facts must use the BUILD boundary"
            )
        if kind != "expression":
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): "
                "value-scoped facts require an expression operation"
            )
    if fact.value_class is not None:
        if fact.param == WILDCARD_PARAM:
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): value-class facts cannot use WILDCARD_PARAM"
            )
        if fact.boundary is not Boundary.BUILD:
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): value-class facts must use the BUILD boundary"
            )
        if kind != "expression":
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): value-class facts require an expression operation"
            )
    method = definition.protocol_method
    from mountainash.core.capabilities.predicates import (
        OPERAND_TYPES_ROOT,
        metadata_arguments,
        validate_metadata_predicate,
    )

    if OPERAND_TYPES_ROOT in definition.options or (
        method is not None and OPERAND_TYPES_ROOT in inspect.signature(method).parameters
    ):
        raise ValueError(f"{OPERAND_TYPES_ROOT} is reserved compiler metadata")
    if fact.predicate is not None and metadata_arguments(fact.predicate):
        if (
            kind != "expression"
            or fact.level is not CapabilityLevel.UNSUPPORTED
            or fact.enforcement is not Enforcement.GATE
            or fact.boundary is not Boundary.BUILD
        ):
            raise ValueError("operand metadata facts require expression UNSUPPORTED/GATE/BUILD")
        validate_metadata_predicate(fact.predicate, method)
    if fact.param != WILDCARD_PARAM and method is not None:
        sig = inspect.signature(method)
        params = set(sig.parameters) - {"self"}
        if fact.param not in params:
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param!r}): protocol "
                f"method '{method.__qualname__}' has no parameter {fact.param!r} "
                f"(has: {sorted(params)})"
            )
    # Level-dependent classification (spec Section 1 validation rules):
    # LITERAL_ONLY / POLYMORPHIC describe how an *argument* arrives — they are
    # meaningless on option-typed params (options are always raw literals).
    # Classifier: per arguments-vs-options.md (ENFORCED), argument params are
    # annotated ExpressionT in the protocol; option params carry literal types.
    # Do NOT use ExpressionFunctionDef.options for this — it is not reliably
    # aligned with the protocol (e.g. SUBSTRING lists its ExpressionT-typed
    # start/length there), and contains' case_sensitivity option is not
    # keyword-only, so parameter kind is no classifier either.
    if (
        fact.param != WILDCARD_PARAM
        and kind == "expression"
        and method is not None
        and fact.level in (CapabilityLevel.LITERAL_ONLY, CapabilityLevel.POLYMORPHIC)
        and fact.enforcement is Enforcement.GATE
    ):
        annotation = inspect.signature(method).parameters[fact.param].annotation
        if "ExpressionT" not in str(annotation):
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param!r}): "
                f"{fact.level.name} declared on an option-typed param "
                f"(annotation {annotation!r}, not ExpressionT) — options are "
                "always literal; use UNSUPPORTED, or declare a non-GATE enforcement role, "
                "or drop the fact"
            )
    # Gateability (Codex plan-review c1): a param-scoped GATE fact on a
    # handler-routed relation op only ever fires through gate_params — reject
    # silently-dead declarations at registration. Non-GATE roles are exempt:
    # ROUTER_METADATA is consumed by the backend router and
    # MATERIALIZE_RESIDUE enriches a native error raised during dispatch
    # (item 88) or materialization, never via gate_params.
    if (
        kind == "relation"
        and fact.param != WILDCARD_PARAM
        and fact.level is CapabilityLevel.UNSUPPORTED
        and fact.enforcement is Enforcement.GATE
        and getattr(definition, "handler", None) is not None
    ):
        gateable = (
            {b.field for b in getattr(definition, "args", ()) or ()}
            | set(getattr(definition, "options", ()) or ())
            | set(getattr(definition, "gate_params", ()) or ())
        )
        if fact.param not in gateable:
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param!r}): the op is "
                "handler-routed and this param is not in its args/options/"
                "gate_params — the fact could never gate. Add the param to the "
                "op's gate_params (RelationOperationDef) or declare a non-GATE enforcement role."
            )
    # Residue reachability (item 98): a handler-routed op's MATERIALIZE_RESIDUE
    # fact can only ever fire if the handler wraps its native call via
    # _enrich_native_call (relation_visitor.py) — reject a silently-dead
    # declaration on an unwrapped handler at registration.
    if (
        kind == "relation"
        and fact.enforcement is Enforcement.MATERIALIZE_RESIDUE
        and getattr(definition, "handler", None) is not None
        and not getattr(definition, "wraps_native_call", False)
    ):
        raise ValueError(
            f"CapabilityFact({fact.operation_key!r}): the op is handler-routed "
            "and does not declare wraps_native_call=True, so a "
            "MATERIALIZE_RESIDUE fact could never fire through per-op enrichment."
        )


_EMPTY_NAMES: frozenset[str] = frozenset()


@dataclass(frozen=True)
class _RegistryState:
    facts: Mapping[_Key, CapabilityFact]
    kinds: Mapping[str, TargetKind]
    value_class_facts: Mapping[_ValueClassBucketKey, tuple[CapabilityFact, ...]]
    predicate_facts: tuple[CapabilityFact, ...]
    segments: tuple[BoundSegment, ...]
    stored: Mapping[QualifiedCapabilityKey, CapabilityFact]
    origins: Mapping[QualifiedCapabilityKey, tuple[SourceOrigin | RuntimeOrigin, ...]]
    manifestations: Mapping[QualifiedManifestationKey, QualifiedManifestation]
    load_state: _LoadState
    load_error: BaseException | None
    predicate_buckets: Mapping[tuple[Any, CONST_BACKEND], tuple[tuple[CapabilityFact, bool], ...]]
    metadata_names: Mapping[tuple[Any, CONST_BACKEND, str | None], frozenset[str]]
    views: Mapping[tuple[CONST_BACKEND | None, Enforcement | None], tuple[CapabilityFact, ...]]


def _prepare_state(
    *,
    facts,
    kinds,
    value_class_facts,
    predicate_facts,
    segments,
    stored,
    origins,
    manifestations=None,
    load_state,
    load_error=None,
) -> _RegistryState:
    """Own all backing maps and prepare finite declaration-derived views once."""
    from mountainash.core.capabilities.predicates import metadata_arguments

    buckets: dict[tuple[Any, CONST_BACKEND], list[tuple[CapabilityFact, bool]]] = {}
    names: dict[tuple[Any, CONST_BACKEND, str | None], set[str]] = {}
    for fact in predicate_facts:
        metadata = metadata_arguments(fact.predicate)
        buckets.setdefault((fact.operation_key, fact.backend), []).append((fact, bool(metadata)))
        key = (fact.operation_key, fact.backend, fact.dialect)
        names.setdefault(key, set()).update(metadata)
    frozen_names: dict[tuple[Any, CONST_BACKEND, str | None], frozenset[str]] = {}
    for (op, backend, dialect), required in names.items():
        if dialect is not None:
            required.update(names.get((op, backend, None), ()))
        frozen_names[op, backend, dialect] = frozenset(required) if required else _EMPTY_NAMES
    ordered = tuple(
        sorted(
            (*facts.values(), *(f for bucket in value_class_facts.values() for f in bucket), *predicate_facts),
            key=_enum_key,
        )
    )
    views: dict[tuple[CONST_BACKEND | None, Enforcement | None], tuple[CapabilityFact, ...]] = {(None, None): ordered}
    groups: dict[tuple[CONST_BACKEND | None, Enforcement | None], list[CapabilityFact]] = {}
    for fact in ordered:
        for view_key in ((fact.backend, None), (None, fact.enforcement), (fact.backend, fact.enforcement)):
            groups.setdefault(view_key, []).append(fact)
    views.update((key, tuple(value)) for key, value in groups.items())
    return _RegistryState(
        MappingProxyType(dict(facts)),
        MappingProxyType(dict(kinds)),
        MappingProxyType(dict(value_class_facts)),
        tuple(predicate_facts),
        tuple(segments),
        MappingProxyType(dict(stored)),
        MappingProxyType(dict(origins)),
        MappingProxyType(dict(manifestations or {})),
        load_state,
        load_error,
        MappingProxyType({key: tuple(value) for key, value in buckets.items()}),
        MappingProxyType(frozen_names),
        MappingProxyType(views),
    )


def _empty_state(load_state=_LoadState.UNINITIALIZED) -> _RegistryState:
    return _prepare_state(
        facts={},
        kinds={},
        value_class_facts={},
        predicate_facts=(),
        segments=(),
        stored={},
        origins={},
        manifestations={},
        load_state=load_state,
    )


def _require_type(value, expected, field):
    if type(value) is not expected:
        raise ValueError(f"{field} must have exact type {expected.__name__}")


def _enum_domain(value):
    domain = type(value.value)
    if domain not in (str, int, bool, float, type(None)):
        raise ValueError("Enum operands require homogeneous scalar values")
    for member in type(value).__members__.values():
        if type(member.value) is not domain or (domain is float and not math.isfinite(member.value)):
            raise ValueError("Enum operands require homogeneous finite scalar values")
    return domain


def _validate_payload(fact):
    _require_type(fact, CapabilityFact, "fact")
    if not isinstance(fact.operation_key, _Enum):
        raise ValueError("operation_key must be a recognized operation Enum member")
    _enum_domain(fact.operation_key)
    for name in ("param", "message", "since"):
        _require_type(getattr(fact, name), str, name)
    for name in ("dialect", "workaround", "upstream_ref", "condition", "option_value", "probe_exempt"):
        value = getattr(fact, name)
        if value is not None:
            _require_type(value, str, name)
    for name, expected in (
        ("backend", CONST_BACKEND),
        ("level", CapabilityLevel),
        ("boundary", Boundary),
        ("enforcement", Enforcement),
        ("residue_signal", ResidueSignal),
    ):
        _require_type(getattr(fact, name), expected, name)
    for name, expected in (("fidelity", Fidelity), ("value_class", ValueClass)):
        value = getattr(fact, name)
        if value is not None:
            _require_type(value, expected, name)
    _require_type(fact.native_errors, tuple, "native_errors")
    if any(not isinstance(error, type) or not issubclass(error, Exception) for error in fact.native_errors):
        raise ValueError("native_errors must contain exception classes")
    if fact.predicate is not None:
        _require_type(fact.predicate, Predicate, "predicate")
        _require_type(fact.predicate.clauses, tuple, "clauses")
        domains = {}
        for clause in fact.predicate.clauses:
            _require_type(clause, Clause, "clause")
            _require_type(clause.path, str, "clause.path")
            _require_type(clause.op, ClauseOp, "clause.op")
            operand = clause.operand
            if isinstance(operand, _Enum):
                domain = _enum_domain(operand)
                group = (clause.path, clause.op, type(operand).__name__)
                if domains.setdefault(group, domain) is not domain:
                    raise ValueError("mixed Enum scalar domains in predicate sort group")
            elif type(operand) is frozenset:
                if any(type(member) not in (str, int, bool) for member in operand):
                    raise ValueError("clause IN requires exact scalar members")
            elif operand is not None and type(operand) not in (str, int, bool):
                raise ValueError("clause operand must have an immutable supported shape")


def _register_identity(kinds, name: str, kind: TargetKind) -> None:
    if kind is TargetKind.SERIALIZE and name in {b.value for b in CONST_BACKEND}:
        raise ValueError(f"SERIALIZE family {name!r} collides with executing backend namespace")
    existing = kinds.get(name)
    if existing is not None and existing is not kind:
        raise ValueError(f"family {name!r} already registered as {existing.value}")
    kinds[name] = kind


def _check_predicate_conflicts(fact: CapabilityFact, predicates: Iterable[CapabilityFact]) -> None:
    from mountainash.core.capabilities.predicates import predicate_implies, predicates_overlap

    blocking = fact.level is CapabilityLevel.UNSUPPORTED
    for other in predicates:
        if other.operation_key != fact.operation_key or other.backend is not fact.backend:
            continue
        if other.dialect is not None and fact.dialect is not None and other.dialect != fact.dialect:
            continue
        if (other.level is CapabilityLevel.UNSUPPORTED) == blocking:
            continue
        if not predicates_overlap(fact.predicate, other.predicate):
            continue
        if predicate_implies(fact.predicate, other.predicate) != predicate_implies(other.predicate, fact.predicate):
            continue
        raise ValueError(
            f"conflicting predicate facts for ({fact.operation_key}, {fact.backend}, "
            f"{fact.dialect!r}): one blocks and one permits the same call, "
            "and neither strictly subsumes the other"
        )


def _source_origins(segment, family, ordinal):
    from mountainash.core.capabilities.capture import SourceOrigin

    entry = f"{family}[{ordinal}]"
    return (
        SourceOrigin(
            segment.module,
            segment.scope,
            segment.source,
            segment.segment.domain,
            entry,
            replace(segment.source_capture, entry=entry) if segment.source_capture is not None else None,
        ),
    )


def _origin_labels(origins):
    from mountainash.core.capabilities.capture import SourceOrigin

    return tuple(
        f"{origin.module}:{origin.entry}"
        if type(origin) is SourceOrigin
        else f"runtime:{origin.generation}:{origin.batch}:{origin.ordinal}"
        for origin in origins
    )


def _stage_batch(
    family,
    incoming,
    facts,
    kinds,
    value_class_facts,
    predicate_facts,
    stored,
    origins,
    manifestations,
    generation,
    segment=None,
):
    from mountainash.core.capabilities.capture import RuntimeOrigin
    from mountainash.core.capabilities.declarations import (
        CapabilityKey,
        QualifiedCapabilityKey,
        QualifiedManifestation,
        QualifiedManifestationKey,
    )
    from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope

    _register_identity(kinds, family.value, TargetKind.EXECUTE)
    for ordinal, fact in enumerate(incoming):
        _validate_fact(family, fact)
        scope = (
            segment.scope
            if segment is not None
            else Scope(
                family,
                FamilyWide() if fact.dialect is None else Dialect(fact.dialect),
            )
        )
        local = segment.segment.capabilities[ordinal].key if segment is not None else CapabilityKey.from_fact(fact)
        qualified = QualifiedCapabilityKey(scope, local)
        if segment is None:
            fact_origins = (RuntimeOrigin(generation, 0, ordinal),)
        else:
            fact_origins = _source_origins(segment, "capabilities", ordinal)
        if qualified in stored:
            raise ValueError(
                f"duplicate capability key: {qualified!r}; "
                f"existing origins={_origin_labels(origins[qualified])!r}; "
                f"incoming origins={_origin_labels(fact_origins)!r}"
            )
        if fact.predicate is not None:
            _check_predicate_conflicts(fact, predicate_facts)
            predicate_facts.append(fact)
        elif fact.value_class is not None:
            key = (fact.operation_key, fact.param, fact.backend, fact.dialect)
            value_class_facts[key] = value_class_facts.get(key, ()) + (fact,)
        else:
            key = (fact.operation_key, fact.param, fact.backend, fact.dialect, fact.option_value)
            facts[key] = fact
        stored[qualified] = fact
        origins[qualified] = fact_origins
    if segment is not None:
        for ordinal, manifestation in enumerate(segment.segment.manifestations):
            key = QualifiedManifestationKey(segment.scope, manifestation.key)
            manifestation_origins = _source_origins(segment, "manifestations", ordinal)
            if key in manifestations:
                raise ValueError(
                    f"duplicate manifestation key: {key!r}; "
                    f"existing origins={_origin_labels(manifestations[key].origins)!r}; "
                    f"incoming origins={_origin_labels(manifestation_origins)!r}"
                )
            manifestations[key] = QualifiedManifestation(key, manifestation, manifestation_origins)


class CapabilityRegistry:
    """Transactional declarations with accessor-level immutable snapshots.

    Registration accepts exact, immutable declaration payloads and publishes
    whole batches. Queries capture one generation, not an entire compilation.
    Operand descriptors remain input-scoped and are never cached here.
    """

    _state = _empty_state()
    _load_lock = threading.RLock()
    _guards = threading.local()
    _generation = 0

    @classmethod
    @contextmanager
    def _mutation(cls):
        if getattr(cls._guards, "mutation", False) or getattr(cls._guards, "loading", False):
            raise RuntimeError("reentrant capability registry mutation")
        cls._guards.mutation = True
        try:
            yield
        finally:
            cls._guards.mutation = False

    @staticmethod
    def _ready(state, enumeration):
        if state.load_state is _LoadState.LOADED:
            return True
        if state.load_state is _LoadState.ISOLATED:
            if enumeration:
                raise RuntimeError("registry is ISOLATED; refusing production enumeration")
            return True
        if state.load_state is _LoadState.FAILED:
            assert state.load_error is not None
            raise state.load_error
        return False

    @classmethod
    def _acquire_state(cls, *, enumeration=False):
        if getattr(cls._guards, "loading", False):
            raise RuntimeError("recursive capability registry first-load query")
        state = cls._state
        if cls._ready(state, enumeration):
            return state
        if getattr(cls._guards, "mutation", False):
            raise RuntimeError("cannot autoload during capability registry mutation")
        with cls._load_lock:
            state = cls._state
            if cls._ready(state, enumeration):
                return state
            from mountainash.core.capabilities.bootstrap import _load_segments

            cls._guards.loading = True
            try:
                segments = _load_segments()
                facts = dict(state.facts)
                kinds = dict(state.kinds)
                vclass = dict(state.value_class_facts)
                predicates = list(state.predicate_facts)
                stored, origins, manifestations = (dict(state.stored), dict(state.origins), dict(state.manifestations))
                addresses = {segment.module for segment in state.segments}
                for segment in segments:
                    if segment.module in addresses:
                        raise ValueError(f"duplicate segment address: {segment.module}")
                    addresses.add(segment.module)
                    _stage_batch(
                        segment.scope.backend,
                        segment.facts,
                        facts,
                        kinds,
                        vclass,
                        predicates,
                        stored,
                        origins,
                        manifestations,
                        cls._generation + 1,
                        segment,
                    )
                candidate = _prepare_state(
                    facts=facts,
                    kinds=kinds,
                    value_class_facts=vclass,
                    predicate_facts=predicates,
                    segments=state.segments + segments,
                    stored=stored,
                    origins=origins,
                    manifestations=manifestations,
                    load_state=_LoadState.LOADED,
                )
            except BaseException as exc:
                cls._state = replace(state, load_state=_LoadState.FAILED, load_error=exc)
                raise
            finally:
                cls._guards.loading = False
            cls._generation += 1
            cls._state = candidate
            return candidate

    @classmethod
    def ensure_loaded(cls) -> None:
        """Autoload only from UNINITIALIZED; isolated queries stay isolated.

        Load failures retain pre-attempt data and rethrow the original error.
        Recursive first-load queries and public mutations are rejected.
        """
        cls._acquire_state()

    @classmethod
    def _publish_batch(cls, family, incoming, segment=None):
        with cls._load_lock:
            state = cls._state
            if not incoming and segment is None and family.value in state.kinds:
                return
            if segment is not None and any(prior.module == segment.module for prior in state.segments):
                raise ValueError(f"duplicate segment address: {segment.module}")
            facts = dict(state.facts)
            kinds = dict(state.kinds)
            vclass = dict(state.value_class_facts)
            predicates = list(state.predicate_facts)
            stored, origins, manifestations = (dict(state.stored), dict(state.origins), dict(state.manifestations))
            _stage_batch(
                family,
                incoming,
                facts,
                kinds,
                vclass,
                predicates,
                stored,
                origins,
                manifestations,
                cls._generation + 1,
                segment,
            )
            candidate = _prepare_state(
                facts=facts,
                kinds=kinds,
                value_class_facts=vclass,
                predicate_facts=predicates,
                segments=state.segments + (() if segment is None else (segment,)),
                stored=stored,
                origins=origins,
                manifestations=manifestations,
                load_state=state.load_state,
                load_error=state.load_error,
            )
            cls._generation += 1
            cls._state = candidate

    @classmethod
    def register_backend(cls, family: CONST_BACKEND, facts: Iterable[CapabilityFact]) -> None:
        """Publish all facts or none; caller iteration runs outside the writer lock."""
        with cls._mutation():
            _require_type(family, CONST_BACKEND, "backend")
            incoming = tuple(facts)
            for fact in incoming:
                _validate_payload(fact)
            cls._publish_batch(family, incoming)

    @classmethod
    def register_segment(cls, segment: BoundSegment) -> None:
        """Publish one physical segment and its origins as a single generation."""
        from mountainash.core.capabilities.capture import require_immutable
        from mountainash.core.capabilities.declarations import BoundSegment

        with cls._mutation():
            _require_type(segment, BoundSegment, "segment")
            require_immutable(segment)
            for fact in segment.facts:
                _validate_payload(fact)
            cls._publish_batch(segment.scope.backend, segment.facts, segment)

    @classmethod
    def segments(cls):
        return cls._acquire_state().segments

    @classmethod
    def origins(cls):
        return cls._acquire_state().origins

    @classmethod
    def _report_inputs(cls):
        state = cls._acquire_state(enumeration=True)
        return state.views[None, None], state.segments

    @classmethod
    def metadata_operand_names(cls, operation_key, backend, dialect=None) -> frozenset[str]:
        """Return declaration-derived names, never input-dependent descriptors."""
        state = cls._acquire_state()
        if type(backend) is not CONST_BACKEND:
            return _EMPTY_NAMES
        result = state.metadata_names.get((operation_key, backend, dialect))
        if result is not None:
            return result
        return state.metadata_names.get((operation_key, backend, None), _EMPTY_NAMES)

    @staticmethod
    def _value_class_fact(state, operation_key, param, backend, dialect, value):
        from mountainash.core.capabilities.value_classes import matches

        for scope in (dialect, None):
            hits = [
                f
                for f in state.value_class_facts.get((operation_key, param, backend, scope), ())
                if f.value_class is not None and matches(f.value_class, value)
            ]
            if len(hits) > 1:
                classes = sorted(f.value_class.value for f in hits if f.value_class is not None)
                raise ValueError(
                    f"two distinct value classes match {value!r} at "
                    f"({operation_key}, {param}, {backend}, {scope}): {classes}"
                )
            if hits:
                return hits[0]
        return None

    @classmethod
    def _capability_for(cls, state, operation_key, param, backend, dialect, option_value=None):
        for key in (
            (operation_key, param, backend, dialect, option_value),
            (operation_key, param, backend, None, option_value),
        ):
            fact = state.facts.get(key)
            if fact is not None:
                return fact
        if option_value is not None:
            fact = cls._value_class_fact(state, operation_key, param, backend, dialect, option_value)
            if fact is not None:
                return fact
            conditioned = [
                fact
                for fact, _ in state.predicate_buckets.get((operation_key, backend), ())
                if fact.param == param
                and fact.option_value == option_value
                and fact.backend is backend
                and (fact.dialect is None or fact.dialect == dialect)
            ]
            if conditioned:
                return min(conditioned, key=lambda fact: fact.fact_key)
        for key in (
            (operation_key, param, backend, dialect, None),
            (operation_key, param, backend, None, None),
            (operation_key, WILDCARD_PARAM, backend, dialect, None),
            (operation_key, WILDCARD_PARAM, backend, None, None),
        ):
            fact = state.facts.get(key)
            if fact is not None:
                return fact
        return None

    @classmethod
    def capability_for(
        cls,
        operation_key: Any,
        param: str,
        backend: CONST_BACKEND,
        dialect: str | None = None,
        option_value: str | None = None,
    ) -> CapabilityFact | None:
        return cls._capability_for(cls._acquire_state(), operation_key, param, backend, dialect, option_value)

    @staticmethod
    def _view(state, backend=None, enforcement=None):
        # StrEnum equality must not relax the original identity-based filter.
        if backend is not None and type(backend) is not CONST_BACKEND:
            return ()
        if enforcement is not None and type(enforcement) is not Enforcement:
            return ()
        return state.views.get((backend, enforcement), ())

    @classmethod
    def reader(cls, scope: Scope) -> ScopeReader:
        from mountainash.core.capabilities.catalogue import ScopeReader

        state = cls._acquire_state()
        return ScopeReader(scope, state.stored, state.manifestations)

    @classmethod
    def capture(
        cls,
        *,
        scopes: frozenset[Scope] | None = None,
        verification: VerificationSnapshot | None = None,
        issues: IssueSnapshot | None = None,
        evidence: tuple[EvidenceCapture, ...] | None = None,
    ) -> CatalogueCapture:
        from mountainash.core.capabilities.catalogue import CatalogueCapture, _validate_scopes

        _validate_scopes(scopes)
        state = cls._acquire_state(enumeration=True)
        if scopes is None:
            scopes = frozenset(key.scope for key in state.stored) | frozenset(
                segment.scope for segment in state.segments
            )
        segments = tuple(segment for segment in state.segments if segment.scope in scopes)
        return CatalogueCapture(
            scopes,
            segments,
            state.stored,
            state.origins,
            state.manifestations,
            verification,
            issues,
            evidence,
        )

    @classmethod
    def facts(
        cls,
        *,
        level: CapabilityLevel | None = None,
        backend: CONST_BACKEND | None = None,
        boundary: Boundary | None = None,
        conditioned: bool | None = None,
        enforcement: Enforcement | None = None,
    ) -> List[CapabilityFact]:
        state = cls._acquire_state()
        return [
            fact
            for fact in cls._view(state, backend, enforcement)
            if (level is None or fact.level is level)
            and (boundary is None or fact.boundary is boundary)
            and (conditioned is None or (fact.condition is not None) == conditioned)
        ]

    @classmethod
    def residue_for(cls, backend: CONST_BACKEND, dialect: str | None = None) -> Dict[Tuple[Any, str], CapabilityFact]:
        """Fresh enrichment mapping with dialect-over-family precedence."""
        state = cls._acquire_state()
        out: dict[tuple[Any, str], CapabilityFact] = {}
        for fact in cls._view(state, backend, Enforcement.MATERIALIZE_RESIDUE):
            if fact.dialect is None or fact.dialect == dialect:
                key = (fact.operation_key, fact.param)
                existing = out.get(key)
                if existing is not None:
                    if (existing.dialect is None) == (fact.dialect is None):
                        raise ValueError(f"ambiguous MATERIALIZE_RESIDUE facts for {key}")
                    if existing.dialect is not None:
                        continue
                out[key] = fact
        return out

    @classmethod
    def residue_candidates(
        cls, backend: CONST_BACKEND, dialect: str | None = None, *, operation_key: Any | None = None
    ) -> tuple[CapabilityFact, ...]:
        state = cls._acquire_state()
        return tuple(
            fact
            for fact in cls._view(state, backend, Enforcement.MATERIALIZE_RESIDUE)
            if (fact.dialect is None or fact.dialect == dialect)
            and (operation_key is None or fact.operation_key == operation_key)
        )

    @classmethod
    def router_facts(
        cls, operation_key: Any, backend: CONST_BACKEND, dialect: str | None = None
    ) -> Tuple[CapabilityFact, ...]:
        """Canonical routing metadata; these facts never gate."""
        state = cls._acquire_state()
        return tuple(
            fact
            for fact in cls._view(state, backend, Enforcement.ROUTER_METADATA)
            if fact.operation_key == operation_key and (fact.dialect is None or fact.dialect == dialect)
        )

    @classmethod
    def violations_for(cls, bound_call: BoundCall, *, phase: str = "complete") -> frozenset[CapabilityFact]:
        from mountainash.core.capabilities.predicates import predicate_holds

        if phase not in ("raw", "complete"):
            raise ValueError(f"unknown capability evaluation phase {phase!r}")
        state = cls._acquire_state()
        out = set()
        for fact, needs_metadata in state.predicate_buckets.get((bound_call.operation_key, bound_call.backend), ()):
            if fact.backend is not bound_call.backend:
                continue
            if fact.dialect is not None and fact.dialect != bound_call.dialect:
                continue
            if fact.enforcement is not Enforcement.GATE or fact.level is not CapabilityLevel.UNSUPPORTED:
                continue
            if phase == "raw" and needs_metadata:
                continue
            assert fact.predicate is not None
            if predicate_holds(
                fact.predicate, bound_call.bindings, bound_call.supplied, operand_types=bound_call.operand_types
            ):
                out.add(fact)
        return frozenset(out)

    @classmethod
    def validate_plan_capabilities(
        cls, operation_keys: Iterable[Any], backend: CONST_BACKEND, dialect: str | None = None
    ) -> List[CapabilityViolation]:
        state = cls._acquire_state()
        violations = []
        for op_key in operation_keys:
            fact = cls._capability_for(state, op_key, WILDCARD_PARAM, backend, dialect)
            if fact is not None and fact.enforcement is Enforcement.GATE and fact.level is CapabilityLevel.UNSUPPORTED:
                violations.append(CapabilityViolation(operation_key=op_key, param=fact.param, fact=fact))
        return violations

    @classmethod
    def snapshot(cls) -> _RegistryState:
        """Capture an opaque round-trip token without triggering loading."""
        return cls._state

    @classmethod
    def restore(cls, snapshot: _RegistryState) -> None:
        """Publish an opaque token, including its original load status/error."""
        with cls._mutation():
            _require_type(snapshot, _RegistryState, "snapshot")
            with cls._load_lock:
                cls._state = snapshot

    @classmethod
    def reset(cls) -> None:
        """Enter empty ISOLATED state; snapshot first to retain production state."""
        with cls._mutation():
            with cls._load_lock:
                cls._state = _empty_state(_LoadState.ISOLATED)
