"""CapabilityRegistry — the spine's single lookup surface (spec Section 1).

Registration validates each complete batch before publishing it:
unknown op keys, params, dialects, or duplicate keys raise ValueError.
Execution queries use concrete-scope policy indexes only. Information never
participates in execution, and whole-operation checks are not parameter defaults.
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
    PolicyAction,
    PolicyConsumer,
    Predicate,
    ResidueSignal,
    WILDCARD_PARAM,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND

if TYPE_CHECKING:
    from collections.abc import Mapping
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        QualifiedCapabilityKey,
        QualifiedInformation,
        QualifiedInformationKey,
        QualifiedPolicy,
    )
    from mountainash.core.capabilities.capture import SourceOrigin
    from mountainash.core.capabilities.predicates import BoundCall
    from mountainash.core.capabilities.catalogue import CatalogueCapture, IssueSnapshot, ScopeReader
    from mountainash.core.capabilities.identity import Scope
    from mountainash.core.capabilities.gaps import GapInventory

_Key = Tuple[Any, str, CONST_BACKEND, Optional[str], Optional[str], Optional[str]]
_ValueClassBucketKey = Tuple[Any, str, CONST_BACKEND, Optional[str], Optional[str]]
_PolicyCandidateKey = Tuple[Any, str, CONST_BACKEND, Optional[str], Optional[str]]
_ValueClassCandidateKey = Tuple[Any, str, CONST_BACKEND, Optional[str]]


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
        fact.variant or "",
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
            "reserved for serialization targets; executable policies must leave it None"
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
    if fact.level is CapabilityLevel.LITERAL_ONLY and kind != "expression":
        raise ValueError("literal-only protection requires an expression argument")
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
    # silently-dead declarations at registration. Residue policies are exempt:
    # they act during dispatch or materialization, never via gate_params.
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
    segments: tuple[BoundSegment, ...]
    information: Mapping[QualifiedInformationKey, QualifiedInformation]
    policies: Mapping[QualifiedCapabilityKey, QualifiedPolicy]
    policy_origins: Mapping[QualifiedCapabilityKey, tuple[SourceOrigin, ...]]
    policy_facts: Mapping[_Key, CapabilityFact]
    policy_value_class_facts: Mapping[_ValueClassBucketKey, tuple[CapabilityFact, ...]]
    policy_predicate_facts: tuple[CapabilityFact, ...]
    policy_candidate_buckets: Mapping[_PolicyCandidateKey, tuple[CapabilityFact, ...]]
    policy_value_class_buckets: Mapping[_ValueClassCandidateKey, tuple[CapabilityFact, ...]]
    prepared_applicability: Mapping[CapabilityFact, Any]
    load_state: _LoadState
    load_error: BaseException | None
    predicate_buckets: Mapping[tuple[Any, CONST_BACKEND], tuple[tuple[CapabilityFact, bool], ...]]
    views: Mapping[tuple[CONST_BACKEND | None, Enforcement | None], tuple[CapabilityFact, ...]]


def _prepare_state(
    *,
    segments,
    information,
    policies,
    policy_origins,
    policy_facts,
    policy_value_class_facts,
    policy_predicate_facts,
    load_state,
    load_error=None,
) -> _RegistryState:
    """Own all backing maps and prepare finite declaration-derived views once."""
    from mountainash.core.capabilities.predicates import metadata_arguments

    direct_buckets: dict[_PolicyCandidateKey, list[CapabilityFact]] = {}
    value_class_buckets: dict[_ValueClassCandidateKey, list[CapabilityFact]] = {}
    prepared_applicability: dict[CapabilityFact, Any] = {}
    for fact in policy_facts.values():
        prepared_applicability[fact] = fact.applicability.prepare()
        direct_buckets.setdefault(
            (fact.operation_key, fact.param, fact.backend, fact.dialect, fact.option_value),
            [],
        ).append(fact)
    for bucket in policy_value_class_facts.values():
        for fact in bucket:
            prepared_applicability[fact] = fact.applicability.prepare()
            value_class_buckets.setdefault(
                (fact.operation_key, fact.param, fact.backend, fact.dialect),
                [],
            ).append(fact)

    buckets: dict[tuple[Any, CONST_BACKEND], list[tuple[CapabilityFact, bool]]] = {}
    for fact in policy_predicate_facts:
        prepared_applicability[fact] = fact.applicability.prepare()
        if fact.consumer is not PolicyConsumer.GATE:
            continue
        metadata = metadata_arguments(fact.predicate)
        buckets.setdefault((fact.operation_key, fact.backend), []).append((fact, bool(metadata)))
    ordered = tuple(
        sorted(
            (
                *policy_facts.values(),
                *(f for bucket in policy_value_class_facts.values() for f in bucket),
                *policy_predicate_facts,
            ),
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
        tuple(segments),
        MappingProxyType(dict(information)),
        MappingProxyType(dict(policies)),
        MappingProxyType(dict(policy_origins)),
        MappingProxyType(dict(policy_facts)),
        MappingProxyType(dict(policy_value_class_facts)),
        tuple(policy_predicate_facts),
        MappingProxyType({key: tuple(value) for key, value in direct_buckets.items()}),
        MappingProxyType({key: tuple(value) for key, value in value_class_buckets.items()}),
        MappingProxyType(dict(prepared_applicability)),
        load_state,
        load_error,
        MappingProxyType({key: tuple(value) for key, value in buckets.items()}),
        MappingProxyType(views),
    )


def _empty_state(load_state=_LoadState.UNINITIALIZED) -> _RegistryState:
    return _prepare_state(
        segments=(),
        information={},
        policies={},
        policy_origins={},
        policy_facts={},
        policy_value_class_facts={},
        policy_predicate_facts=(),
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
    for name, expected in (("consumer", PolicyConsumer), ("action", PolicyAction)):
        value = getattr(fact, name)
        if value is not None:
            _require_type(value, expected, name)
    if fact.native_issue is not None:
        _require_type(fact.native_issue, str, "native_issue")
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


def _policy_domain(key):
    from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate

    selector = key.selector
    if selector.kind == "predicate":
        return selector.value
    if selector.kind == "exact":
        return Predicate((Clause(key.subject, ClauseOp.EQ, selector.value),))
    if selector.kind == "value_class":
        return Predicate((Clause(key.subject, ClauseOp.MATCHES_CLASS, selector.value),))
    return None


def _compare_policy_domains(left, right):
    from mountainash.core.capabilities.predicates import DomainComparison, DomainRelation, compare_domains
    from mountainash.core.capabilities.schema import ClauseOp

    # Single-answer option queries currently use their normalized string value;
    # bound-call predicates use actual values. Never prove disjointness by
    # pretending that these two domains have identical equality semantics.
    if (left.selector.kind == "predicate") != (right.selector.kind == "predicate"):
        predicate_key, option_key = (left, right) if left.selector.kind == "predicate" else (right, left)
        if option_key.selector.kind != "unconditioned":
            for clause in predicate_key.selector.value.clauses:
                if clause.path.split(".")[0] != option_key.subject:
                    continue
                if (
                    clause.op in (ClauseOp.IS_LITERAL, ClauseOp.IS_NULL)
                    or (clause.op is ClauseOp.EQ and type(clause.operand) is not str)
                    or (clause.op is ClauseOp.IN and any(type(value) is not str for value in clause.operand))
                ):
                    return DomainComparison(DomainRelation.NOT_PROVEN)
    return compare_domains(_policy_domain(left), _policy_domain(right))


def _literal_only_disjoint(protection, other):
    from mountainash.core.capabilities.schema import ClauseOp, PolicyConsumer

    if (
        protection.consumer is not PolicyConsumer.GATE
        or protection.level is not CapabilityLevel.LITERAL_ONLY
        or other.key.selector.kind != "predicate"
    ):
        return False
    subject = protection.key.subject
    for clause in other.key.selector.value.clauses:
        if clause.op is ClauseOp.IS_LITERAL and clause.path.split(".")[0] == subject:
            return True
        if clause.path == subject and clause.op in (
            ClauseOp.EQ,
            ClauseOp.IN,
            ClauseOp.MATCHES_CLASS,
            ClauseOp.IS_NULL,
        ):
            # Value comparisons reject dynamic ExpressionNodes. The retained
            # literal-only guard refuses precisely those non-literal nodes.
            return True
    return False




def _base_key(key):
    return key.operation, key.subject, key.selector


def _resolve_information_reference(reference, information, policy_key, policy_scope):
    try:
        record = information[reference]
    except KeyError:
        raise ValueError(f"policy information reference was not published: {reference!r}") from None
    if _base_key(reference.local) != _base_key(policy_key):
        raise ValueError("policy information reference has a different call identity")
    if reference.scope.backend is not policy_scope.backend:
        raise ValueError("policy information reference has a different backend")
    if reference.scope.dialect not in (None, policy_scope.dialect):
        raise ValueError("policy information reference has a different dialect")
    return record


def _check_policy_conflicts(key, policy, incoming_origins, policies):
    from mountainash.core.capabilities.applicability import (
        EnvironmentDomainRelation,
        compare_applicability,
    )
    from mountainash.core.capabilities.predicates import DomainRelation
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer

    for previous in policies.values():
        other = previous.assertion
        if (
            previous.key.scope != key.scope
            or other.key.operation != policy.key.operation
            or other.consumer is not policy.consumer
        ):
            continue
        environment_relation = compare_applicability(policy.applicability, other.applicability)
        if environment_relation is EnvironmentDomainRelation.DISJOINT:
            continue
        call_comparison = _compare_policy_domains(policy.key, other.key)
        if call_comparison.relation is DomainRelation.DISJOINT:
            continue
        if policy.consumer is PolicyConsumer.GATE:
            both_block = policy.action is PolicyAction.BLOCK and other.action is PolicyAction.BLOCK
            if both_block and (
                (policy.key.selector.kind == "predicate" and other.key.selector.kind == "predicate")
                or policy.key.subject != other.key.subject
            ):
                # These consumers collect independent refusals; neither can
                # cancel or select an alternative answer in place of the other.
                continue
        if _literal_only_disjoint(policy, other) or _literal_only_disjoint(other, policy):
            continue
        message = (
            f"conflicting policies: {previous.key!r} from {_origin_labels(previous.origins)!r} "
            f"and {key!r} from {_origin_labels(incoming_origins)!r}; "
            f"call={call_comparison.relation.value}; "
            f"environment={environment_relation.value}; "
            f"selectors=({other.key.selector!r}, {policy.key.selector!r}); "
            f"applicability=({other.applicability!r}, {policy.applicability!r})"
        )
        if call_comparison.witness is not None:
            message += f"; call_witness={call_comparison.witness!r}"
        raise ValueError(message)


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
    return tuple(f"{origin.module}:{origin.entry}" for origin in origins)


def _stage_information(segment, information):
    from mountainash.core.capabilities.declarations import QualifiedInformation, QualifiedInformationKey
    from mountainash.core.capabilities.catalogue import _validate_operation_subject

    for ordinal, assertion in enumerate(segment.segment.information):
        _validate_operation_subject(assertion.key.operation, assertion.key.subject)
        assertion.applicability.prepare()
        key = QualifiedInformationKey(segment.scope, assertion.key, assertion.layer)
        origins = _source_origins(segment, "information", ordinal)
        if key in information:
            raise ValueError(
                f"duplicate information key: {key!r}; "
                f"existing origins={_origin_labels(information[key].origins)!r}; "
                f"incoming origins={_origin_labels(origins)!r}"
            )
        information[key] = QualifiedInformation(key, assertion, origins)


def _stage_segment_policies(
    family,
    segment,
    policies,
    policy_origins,
    policy_facts,
    policy_value_class_facts,
    policy_predicate_facts,
    information,
):
    from mountainash.core.capabilities.declarations import QualifiedCapabilityKey, QualifiedPolicy

    for ordinal, policy in enumerate(segment.segment.policies):
        key = QualifiedCapabilityKey(segment.scope, policy.key)
        origins_for_policy = _source_origins(segment, "policies", ordinal)
        if key in policies:
            raise ValueError(
                f"duplicate policy key: {key!r}; "
                f"existing origins={_origin_labels(policy_origins[key])!r}; "
                f"incoming origins={_origin_labels(origins_for_policy)!r}"
            )
        explanation = (
            _resolve_information_reference(policy.information, information, policy.key, segment.scope)
            if policy.information is not None
            else None
        )
        _check_policy_conflicts(key, policy, origins_for_policy, policies)
        fact = policy.qualify(segment.scope)
        if explanation is not None:
            fact = replace(fact, workaround=explanation.assertion.workaround, upstream_ref=explanation.assertion.issue)
        _validate_payload(fact)
        _validate_fact(family, fact)
        if fact.predicate is not None:
            policy_predicate_facts.append(fact)
        elif fact.value_class is not None:
            bucket = (fact.operation_key, fact.param, fact.backend, fact.dialect, fact.variant)
            policy_value_class_facts[bucket] = policy_value_class_facts.get(bucket, ()) + (fact,)
        else:
            fact_key = (fact.operation_key, fact.param, fact.backend, fact.dialect, fact.option_value, fact.variant)
            if fact_key in policy_facts:
                raise ValueError(f"duplicate prepared policy fact: {key!r}")
            policy_facts[fact_key] = fact
        policies[key] = QualifiedPolicy(key, policy, origins_for_policy)
        policy_origins[key] = origins_for_policy


def _selected(state, fact, execution_context):
    from mountainash.core.capabilities.applicability import ApplicabilityResult

    if execution_context is None:
        return fact.applicability.regions is None
    if not execution_context.policy.selects(fact.consumer, fact.issue_classes):
        return False
    return (
        state.prepared_applicability[fact].match(execution_context.environment)
        is ApplicabilityResult.APPLICABLE
    )


def _single_selected(state, candidates, consumer, execution_context):
    answer = None
    for fact in candidates:
        if fact.consumer is not consumer or not _selected(state, fact, execution_context):
            continue
        if answer is not None:
            raise ValueError(f"ambiguous policy answer: {answer.fact_key!r} and {fact.fact_key!r}")
        answer = fact
    return answer

class CapabilityRegistry:
    """Transactional declarations with accessor-level immutable snapshots.

    Registration accepts exact, immutable declaration payloads and publishes
    whole batches. Queries capture one generation, not an entire compilation.
    Operand descriptors remain input-scoped and are never cached here.
    """

    _state = _empty_state()
    _load_lock = threading.RLock()
    _guards = threading.local()

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
                information = dict(state.information)
                policies, policy_origins = dict(state.policies), dict(state.policy_origins)
                policy_facts = dict(state.policy_facts)
                policy_vclass = dict(state.policy_value_class_facts)
                policy_predicates = list(state.policy_predicate_facts)
                addresses = {segment.module for segment in state.segments}
                for segment in segments:
                    if segment.module in addresses:
                        raise ValueError(f"duplicate segment address: {segment.module}")
                    addresses.add(segment.module)
                    _stage_information(segment, information)
                for segment in segments:
                    _stage_segment_policies(
                        segment.scope.backend,
                        segment,
                        policies,
                        policy_origins,
                        policy_facts,
                        policy_vclass,
                        policy_predicates,
                        information,
                    )
                candidate = _prepare_state(
                    segments=state.segments + segments,
                    information=information,
                    policies=policies,
                    policy_origins=policy_origins,
                    policy_facts=policy_facts,
                    policy_value_class_facts=policy_vclass,
                    policy_predicate_facts=policy_predicates,
                    load_state=_LoadState.LOADED,
                )
            except BaseException as exc:
                cls._state = replace(state, load_state=_LoadState.FAILED, load_error=exc)
                raise
            finally:
                cls._guards.loading = False
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
    def _publish_segment(cls, segment):
        with cls._load_lock:
            state = cls._state
            if any(prior.module == segment.module for prior in state.segments):
                raise ValueError(f"duplicate segment address: {segment.module}")
            information = dict(state.information)
            policies, policy_origins = dict(state.policies), dict(state.policy_origins)
            policy_facts = dict(state.policy_facts)
            policy_vclass = dict(state.policy_value_class_facts)
            policy_predicates = list(state.policy_predicate_facts)
            _stage_information(segment, information)
            _stage_segment_policies(
                segment.scope.backend,
                segment,
                policies,
                policy_origins,
                policy_facts,
                policy_vclass,
                policy_predicates,
                information,
            )
            candidate = _prepare_state(
                segments=state.segments + (segment,),
                information=information,
                policies=policies,
                policy_origins=policy_origins,
                policy_facts=policy_facts,
                policy_value_class_facts=policy_vclass,
                policy_predicate_facts=policy_predicates,
                load_state=state.load_state,
                load_error=state.load_error,
            )
            cls._state = candidate

    @classmethod
    def register_segment(cls, segment: BoundSegment) -> None:
        """Publish one physical segment and its origins as a single generation."""
        from mountainash.core.capabilities.capture import require_immutable
        from mountainash.core.capabilities.declarations import BoundSegment

        with cls._mutation():
            _require_type(segment, BoundSegment, "segment")
            require_immutable(segment)
            cls._publish_segment(segment)

    @classmethod
    def segments(cls):
        return cls._acquire_state().segments

    @classmethod
    def _report_inputs(cls):
        state = cls._acquire_state(enumeration=True)
        return state.views[None, None], state.segments

    @classmethod
    def metadata_operand_names(
        cls,
        operation_key,
        backend,
        dialect=None,
        *,
        execution_context=None,
    ) -> frozenset[str]:
        """Return selected declaration-derived names, never input descriptors."""
        from mountainash.core.capabilities.predicates import metadata_arguments

        state = cls._acquire_state()
        if type(backend) is not CONST_BACKEND:
            return _EMPTY_NAMES
        names = set()
        for fact, _ in state.predicate_buckets.get((operation_key, backend), ()):
            if (
                fact.dialect == dialect
                and fact.consumer is PolicyConsumer.GATE
                and _selected(state, fact, execution_context)
            ):
                assert fact.predicate is not None
                names.update(metadata_arguments(fact.predicate))
        return frozenset(names) if names else _EMPTY_NAMES

    @staticmethod
    def _value_class_fact(
        state,
        operation_key,
        param,
        backend,
        dialect,
        value,
        consumer,
        execution_context,
    ):
        from mountainash.core.capabilities.value_classes import matches

        answer = None
        for fact in state.policy_value_class_buckets.get(
            (operation_key, param, backend, dialect),
            (),
        ):
            if fact.consumer is not consumer or not _selected(state, fact, execution_context):
                continue
            assert fact.value_class is not None
            if not matches(fact.value_class, value):
                continue
            if answer is not None:
                raise ValueError(f"ambiguous policy answer: {answer.fact_key!r} and {fact.fact_key!r}")
            answer = fact
        return answer

    @classmethod
    def _capability_for(
        cls,
        state,
        operation_key,
        param,
        backend,
        dialect,
        option_value=None,
        *,
        consumer=PolicyConsumer.GATE,
        execution_context=None,
    ):
        if type(backend) is not CONST_BACKEND or dialect is None:
            return None
        answer = _single_selected(
            state,
            state.policy_candidate_buckets.get(
                (operation_key, param, backend, dialect, None),
                (),
            ),
            consumer,
            execution_context,
        )
        if option_value is None:
            return answer
        exact = _single_selected(
            state,
            state.policy_candidate_buckets.get(
                (operation_key, param, backend, dialect, option_value),
                (),
            ),
            consumer,
            execution_context,
        )
        if exact is not None:
            if answer is not None:
                raise ValueError(f"ambiguous policy answer: {answer.fact_key!r} and {exact.fact_key!r}")
            answer = exact
        classified = cls._value_class_fact(
            state,
            operation_key,
            param,
            backend,
            dialect,
            option_value,
            consumer,
            execution_context,
        )
        if classified is not None:
            if answer is not None:
                raise ValueError(f"ambiguous policy answer: {answer.fact_key!r} and {classified.fact_key!r}")
            answer = classified
        return answer

    @classmethod
    def capability_for(
        cls,
        operation_key: Any,
        param: str,
        backend: CONST_BACKEND,
        dialect: str | None = None,
        option_value: str | None = None,
        *,
        consumer: PolicyConsumer = PolicyConsumer.GATE,
        execution_context=None,
    ) -> CapabilityFact | None:
        _require_type(consumer, PolicyConsumer, "consumer")
        return cls._capability_for(
            cls._acquire_state(),
            operation_key,
            param,
            backend,
            dialect,
            option_value,
            consumer=consumer,
            execution_context=execution_context,
        )

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
        return ScopeReader(scope, state.information, state.policies)

    @classmethod
    def capture(
        cls,
        *,
        scopes: frozenset[Scope] | None = None,
        inventories: tuple[GapInventory, ...] | None = None,
        issues: IssueSnapshot | None = None,
    ) -> CatalogueCapture:
        from mountainash.core.capabilities.catalogue import CatalogueCapture, _validate_scopes

        _validate_scopes(scopes)
        state = cls._acquire_state(enumeration=True)
        if scopes is None:
            scopes = (
                frozenset(key.scope for key in state.information)
                | frozenset(key.scope for key in state.policies)
                | frozenset(segment.scope for segment in state.segments)
            )
        segments = tuple(segment for segment in state.segments if segment.scope in scopes)
        return CatalogueCapture(
            scopes,
            segments,
            state.information,
            state.policies,
            inventories,
            issues,
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
    def residue_for(
        cls,
        backend: CONST_BACKEND,
        dialect: str | None = None,
        *,
        execution_context=None,
    ) -> Dict[Tuple[Any, str], CapabilityFact]:
        """Fresh enrichment mapping for one exact concrete scope."""
        state = cls._acquire_state()
        out: dict[tuple[Any, str], CapabilityFact] = {}
        for fact in cls._view(state, backend, Enforcement.MATERIALIZE_RESIDUE):
            if fact.dialect != dialect or not _selected(state, fact, execution_context):
                continue
            key = (fact.operation_key, fact.param)
            if key in out:
                raise ValueError(f"ambiguous MATERIALIZE_RESIDUE policies for {key}")
            out[key] = fact
        return out

    @classmethod
    def residue_candidates(
        cls,
        backend: CONST_BACKEND,
        dialect: str | None = None,
        *,
        operation_key: Any | None = None,
        execution_context=None,
    ) -> tuple[CapabilityFact, ...]:
        state = cls._acquire_state()
        return tuple(
            fact
            for fact in cls._view(state, backend, Enforcement.MATERIALIZE_RESIDUE)
            if (
                fact.dialect == dialect
                and (operation_key is None or fact.operation_key == operation_key)
                and _selected(state, fact, execution_context)
            )
        )

    @classmethod
    def violations_for(
        cls,
        bound_call: BoundCall,
        *,
        phase: str = "complete",
        execution_context=None,
    ) -> frozenset[CapabilityFact]:
        from mountainash.core.capabilities.predicates import predicate_holds

        if phase not in ("raw", "complete"):
            raise ValueError(f"unknown capability evaluation phase {phase!r}")
        state = cls._acquire_state()
        out = set()
        for fact, needs_metadata in state.predicate_buckets.get(
            (bound_call.operation_key, bound_call.backend),
            (),
        ):
            if fact.backend is not bound_call.backend or fact.dialect != bound_call.dialect:
                continue
            if fact.enforcement is not Enforcement.GATE or fact.level is not CapabilityLevel.UNSUPPORTED:
                continue
            if not _selected(state, fact, execution_context):
                continue
            if phase == "raw" and needs_metadata:
                continue
            assert fact.predicate is not None
            if predicate_holds(
                fact.predicate,
                bound_call.bindings,
                bound_call.supplied,
                operand_types=bound_call.operand_types,
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
