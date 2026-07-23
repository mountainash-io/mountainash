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
    TargetKind,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND

# backend slot is CONST_BACKEND | str: str families arrive only via the
# serialization workstream's register_target (spec 2026-07-06); register_backend
# rejects them via the family-identity check in _validate_fact.
_Key = Tuple[Any, str, "CONST_BACKEND | str", Optional[str], Optional[str]]


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
        and fact.condition is None
    ):
        annotation = inspect.signature(method).parameters[fact.param].annotation
        if "ExpressionT" not in str(annotation):
            raise ValueError(
                f"CapabilityFact({fact.operation_key}, {fact.param!r}): "
                f"{fact.level.name} declared on an option-typed param "
                f"(annotation {annotation!r}, not ExpressionT) — options are "
                "always literal; use UNSUPPORTED (with condition if "
                "value-dependent) or drop the fact"
            )
    # Gateability (Codex plan-review c1): a param-scoped, UNCONDITIONED,
    # gating fact on a handler-routed relation op only ever fires through
    # gate_params — reject silently-dead declarations at registration.
    # Conditioned facts are exempt: their condition may be finer than the
    # gate can evaluate (e.g. CSV dialect.escape_char) and they are
    # legitimately enforced backend/router-side outside gate_params.
    if (
        kind == "relation"
        and fact.param != WILDCARD_PARAM
        and fact.level is CapabilityLevel.UNSUPPORTED
        and fact.condition is None
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
                "op's gate_params (RelationOperationDef) or use a wildcard/"
                "conditioned fact."
            )


class CapabilityRegistry:
    """Class-level registry, mirroring ExpressionFunctionRegistry's pattern."""

    _facts: Dict[_Key, CapabilityFact] = {}
    _kinds: Dict[str, TargetKind] = {}  # family name -> kind (spec 2026-07-06)

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
    ) -> List[CapabilityFact]:
        out = []
        for fact in cls._facts.values():
            if level is not None and fact.level is not level:
                continue
            if backend is not None and fact.backend is not backend:
                continue
            if boundary is not None and fact.boundary is not boundary:
                continue
            if conditioned is not None and (fact.condition is not None) != conditioned:
                continue
            out.append(fact)
        return out

    @classmethod
    def residue_for(
        cls, backend: CONST_BACKEND, dialect: str | None = None
    ) -> Dict[Tuple[Any, str], CapabilityFact]:
        """MATERIALIZE-boundary facts as an enrichment mapping (op, param) -> fact."""
        out: Dict[Tuple[Any, str], CapabilityFact] = {}
        for fact in cls.facts(backend=backend, boundary=Boundary.MATERIALIZE):
            if fact.dialect is None or fact.dialect == dialect:
                out[(fact.operation_key, fact.param)] = fact
        return out

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
            if fact is not None and fact.level is CapabilityLevel.UNSUPPORTED:
                violations.append(
                    CapabilityViolation(operation_key=op_key, param=fact.param, fact=fact)
                )
        return violations

    # -- test isolation -----------------------------------------------------
    @classmethod
    def snapshot(cls) -> Tuple[Dict[_Key, CapabilityFact], Dict[str, TargetKind]]:
        """Opaque round-trip token for test isolation — captures BOTH _facts
        and _kinds so restore() is symmetric with reset(). Callers must treat
        the return value as opaque (feed it only to restore())."""
        return dict(cls._facts), dict(cls._kinds)

    @classmethod
    def restore(
        cls, snapshot: Tuple[Dict[_Key, CapabilityFact], Dict[str, TargetKind]]
    ) -> None:
        facts, kinds = snapshot
        cls._facts = dict(facts)
        cls._kinds = dict(kinds)

    @classmethod
    def reset(cls) -> None:
        cls._facts = {}
        cls._kinds = {}
