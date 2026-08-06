"""CapabilityRegistry — the spine's single lookup surface (spec Section 1).

Registration is validated at import time (fail-at-import, not at use):
unknown op keys, params, dialects, or duplicate keys raise ValueError.
Lookup is a chain of at most six dictionary hits: value-specific dialect and
family facts, value-agnostic dialect and family facts, then dialect and family
wildcards.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from mountainash.core.capabilities.identity import KNOWN_DIALECTS
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
    TargetKind,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND

# backend slot is CONST_BACKEND | str: str families arrive only via the
# serialization workstream's register_target (spec 2026-07-06); register_backend
# rejects them via the family-identity check in _validate_fact.
_Key = Tuple[Any, str, "CONST_BACKEND | str", Optional[str], Optional[str]]
_ValueClassBucketKey = Tuple[Any, str, "CONST_BACKEND | str", Optional[str]]


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
                f"CapabilityFact({fact.operation_key}, {fact.param}): "
                "value-scoped facts cannot use WILDCARD_PARAM"
            )
        if fact.boundary is not Boundary.BUILD:
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): "
                "value-scoped facts must use the BUILD boundary"
            )
        if kind != "expression":
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): "
                "value-scoped facts require an expression operation"
            )
    if fact.value_class is not None:
        if fact.param == WILDCARD_PARAM:
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): "
                "value-class facts cannot use WILDCARD_PARAM"
            )
        if fact.boundary is not Boundary.BUILD:
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): "
                "value-class facts must use the BUILD boundary"
            )
        if kind != "expression":
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param}): "
                "value-class facts require an expression operation"
            )
    method = definition.protocol_method
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
    # MATERIALIZE_RESIDUE fires after the visitor returns.
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


class CapabilityRegistry:
    """Class-level registry, mirroring ExpressionFunctionRegistry's pattern."""

    _facts: Dict[_Key, CapabilityFact] = {}
    _kinds: Dict[str, TargetKind] = {}  # family name -> kind (spec 2026-07-06)
    _value_class_facts: Dict[_ValueClassBucketKey, Tuple[CapabilityFact, ...]] = {}

    @classmethod
    def _register_identity(cls, name: str, kind: TargetKind) -> None:
        """Record a family's kind; enforce EXECUTE/SERIALIZE namespace disjointness.

        Phase 1 only ever passes EXECUTE (via register_backend); the SERIALIZE
        branch is exercised when the serialization workstream adds
        register_target(). Idempotent for a repeated same-kind registration.
        """
        if kind is TargetKind.SERIALIZE and name in {b.value for b in CONST_BACKEND}:
            raise ValueError(
                f"SERIALIZE family {name!r} collides with executing backend "
                "namespace CONST_BACKEND"
            )
        existing = cls._kinds.get(name)
        if existing is not None and existing is not kind:
            raise ValueError(
                f"family {name!r} already registered as {existing.value}; "
                f"cannot re-register as {kind.value}"
            )
        cls._kinds[name] = kind

    @classmethod
    def register_backend(
        cls, family: CONST_BACKEND, facts: Iterable[CapabilityFact]
    ) -> None:
        cls._register_identity(family.value, TargetKind.EXECUTE)
        for fact in facts:
            _validate_fact(family, fact)
            if fact.value_class is not None:
                bkey: _ValueClassBucketKey = (
                    fact.operation_key,
                    fact.param,
                    fact.backend,
                    fact.dialect,
                )
                bucket = cls._value_class_facts.get(bkey, ())
                if any(f.value_class is fact.value_class for f in bucket):
                    raise ValueError(
                        f"duplicate value-class CapabilityFact key: {bkey + (fact.value_class,)}"
                    )
                cls._value_class_facts[bkey] = bucket + (fact,)
                continue
            key: _Key = (
                fact.operation_key,
                fact.param,
                fact.backend,
                fact.dialect,
                fact.option_value,
            )
            if key in cls._facts:
                raise ValueError(f"duplicate CapabilityFact key: {key}")
            cls._facts[key] = fact

    @classmethod
    def _value_class_fact(
        cls,
        operation_key: Any,
        param: str,
        backend: CONST_BACKEND,
        dialect: str | None,
        value: str,
    ) -> CapabilityFact | None:
        from mountainash.core.capabilities.value_classes import matches

        for scope in (dialect, None):  # dialect slice before family slice
            bucket = cls._value_class_facts.get(
                (operation_key, param, backend, scope), ()
            )
            hits = [
                f
                for f in bucket
                if f.value_class is not None and matches(f.value_class, value)
            ]
            if len(hits) > 1:
                classes = sorted(
                    f.value_class.value for f in hits if f.value_class is not None
                )
                raise ValueError(
                    f"two distinct value classes match {value!r} at "
                    f"({operation_key}, {param}, {backend}, {scope}): {classes}"
                )
            if hits:
                return hits[0]
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
        for key in (
            (operation_key, param, backend, dialect, option_value),
            (operation_key, param, backend, None, option_value),
        ):
            fact = cls._facts.get(key)
            if fact is not None:
                return fact
        if option_value is not None:
            vc_fact = cls._value_class_fact(
                operation_key, param, backend, dialect, option_value
            )
            if vc_fact is not None:
                return vc_fact
        for key in (
            (operation_key, param, backend, dialect, None),
            (operation_key, param, backend, None, None),
            (operation_key, WILDCARD_PARAM, backend, dialect, None),
            (operation_key, WILDCARD_PARAM, backend, None, None),
        ):
            fact = cls._facts.get(key)
            if fact is not None:
                return fact
        return None

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
        out = []
        for fact in (
            *cls._facts.values(),
            *(f for bucket in cls._value_class_facts.values() for f in bucket),
        ):
            if level is not None and fact.level is not level:
                continue
            if backend is not None and fact.backend is not backend:
                continue
            if boundary is not None and fact.boundary is not boundary:
                continue
            if conditioned is not None and (fact.condition is not None) != conditioned:
                continue
            if enforcement is not None and fact.enforcement is not enforcement:
                continue
            out.append(fact)
        return sorted(out, key=_enum_key)

    @classmethod
    def residue_for(
        cls, backend: CONST_BACKEND, dialect: str | None = None
    ) -> Dict[Tuple[Any, str], CapabilityFact]:
        """MATERIALIZE-boundary facts as an enrichment mapping (op, param) -> fact."""
        out: Dict[Tuple[Any, str], CapabilityFact] = {}
        for fact in cls.facts(
            backend=backend, enforcement=Enforcement.MATERIALIZE_RESIDUE
        ):
            if fact.dialect is None or fact.dialect == dialect:
                key = (fact.operation_key, fact.param)
                existing = out.get(key)
                if existing is not None:
                    if (existing.dialect is None) == (fact.dialect is None):
                        raise ValueError(
                            f"ambiguous MATERIALIZE_RESIDUE facts for {key}"
                        )
                    if existing.dialect is not None:
                        continue
                out[key] = fact
        return out

    @classmethod
    def router_facts(
        cls,
        operation_key: Any,
        backend: CONST_BACKEND,
        dialect: str | None = None,
    ) -> Tuple[CapabilityFact, ...]:
        """ROUTER_METADATA facts for an op on a backend, in registration order.

        These never gate. They document WHY a backend takes a non-native
        path; the routing decision itself stays in the router, and no
        production router calls this accessor yet. On polars/narwhals the
        declared condition matches their routing predicate exactly; ibis
        routes more broadly, which is why routing is not derived from facts
        (see the 66a plan's spec-deviation note). The bridge test in
        tests/relations/backends/test_resource_files.py fails on any router
        fact with no registered probe, so a declaration cannot go unexercised.
        """
        return tuple(
            sorted(
                (
                    fact
                    for fact in cls.facts(
                        backend=backend, enforcement=Enforcement.ROUTER_METADATA
                    )
                    if fact.operation_key == operation_key
                    and (fact.dialect is None or fact.dialect == dialect)
                ),
                key=_enum_key,
            )
        )

    @classmethod
    def validate_plan_capabilities(
        cls,
        operation_keys: Iterable[Any],
        backend: CONST_BACKEND,
        dialect: str | None = None,
    ) -> List[CapabilityViolation]:
        """Substrait-interop hook (spec Section 1): op-level violations only."""
        violations = []
        for op_key in operation_keys:
            fact = cls.capability_for(op_key, WILDCARD_PARAM, backend, dialect)
            if (
                fact is not None
                and fact.enforcement is Enforcement.GATE
                and fact.level is CapabilityLevel.UNSUPPORTED
            ):
                violations.append(
                    CapabilityViolation(operation_key=op_key, param=fact.param, fact=fact)
                )
        return violations

    # -- test isolation -----------------------------------------------------
    @classmethod
    def snapshot(
        cls,
    ) -> Tuple[
        Dict[_Key, CapabilityFact],
        Dict[str, TargetKind],
        Dict[_ValueClassBucketKey, Tuple[CapabilityFact, ...]],
    ]:
        """Opaque round-trip token for test isolation — captures BOTH _facts
        and _kinds so restore() is symmetric with reset(). Callers must treat
        the return value as opaque (feed it only to restore())."""
        return dict(cls._facts), dict(cls._kinds), dict(cls._value_class_facts)

    @classmethod
    def restore(
        cls,
        snapshot: Tuple[
            Dict[_Key, CapabilityFact],
            Dict[str, TargetKind],
            Dict[_ValueClassBucketKey, Tuple[CapabilityFact, ...]],
        ],
    ) -> None:
        facts, kinds, vclass = snapshot
        cls._facts = dict(facts)
        cls._kinds = dict(kinds)
        cls._value_class_facts = dict(vclass)

    @classmethod
    def reset(cls) -> None:
        cls._facts = {}
        cls._kinds = {}
        cls._value_class_facts = {}
