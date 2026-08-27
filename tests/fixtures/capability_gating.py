"""Spine-derived test expectations — the single surface a test uses to ask
"what does the capability spine say about (op, family, dialect)?".
Nothing here is hand-maintained; see spec 2026-08-01-spine-derived-test-expectations.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import (
        ScalarFunctionNode,
    )

from mountainash.core.capabilities.divergences import divergence_by_id
from mountainash.core.capabilities.identity import KNOWN_DIALECTS, BackendIdentity
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    ClauseOp,
    Enforcement,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError

_DIALECT_TO_FAMILY: dict[str, CONST_BACKEND] = {}
for _family, _dialects in KNOWN_DIALECTS.items():
    for _dialect in _dialects:
        if _dialect in _DIALECT_TO_FAMILY:  # pragma: no cover
            raise ValueError(f"dialect {_dialect!r} owned by two families")
        _DIALECT_TO_FAMILY[_dialect] = _family

_FAMILY_PREFIXES = (
    ("narwhals", CONST_BACKEND.NARWHALS),
    ("ibis", CONST_BACKEND.IBIS),
    ("pandas", CONST_BACKEND.PANDAS),
    ("pyarrow", CONST_BACKEND.PYARROW),
    ("polars", CONST_BACKEND.POLARS),
)


def identity_for(backend_name: str) -> BackendIdentity:
    """Name-string path (parametrized tests only). Prefer resolve_identity() with the real object."""
    fam = _DIALECT_TO_FAMILY.get(backend_name)
    if fam is not None:
        return BackendIdentity(family=fam, dialect=backend_name)
    for prefix, f in _FAMILY_PREFIXES:
        if backend_name == prefix or backend_name.startswith(prefix + "-"):
            return BackendIdentity(family=f, dialect=None)
    raise ValueError(f"cannot resolve backend family for {backend_name!r}")


def resolve_identity(backend_or_name) -> BackendIdentity:
    """Identity from the REAL backend object via production detection (rev-2 new-I2); the name-string
    map is a fallback only for a bare str. Objects are authoritative — the test factory routes e.g.
    pandas THROUGH Narwhals, so the fixture name alone resolves the wrong family."""
    if isinstance(backend_or_name, str):
        return identity_for(backend_or_name)
    from mountainash.core.backend_detection import identify_backend_identity

    return identify_backend_identity(backend_or_name)


def gate_family(backend_or_name) -> CONST_BACKEND:
    return resolve_identity(backend_or_name).family


def gate_dialect(backend_or_name) -> str | None:
    return resolve_identity(backend_or_name).dialect


_GATING = {
    (Enforcement.GATE, Boundary.BUILD),
    (Enforcement.MATERIALIZE_RESIDUE, Boundary.MATERIALIZE),
}


def capability_gate(operation_key, family, *, dialect=None,
                    param=WILDCARD_PARAM, option_value=None) -> CapabilityFact | None:
    fact = CapabilityRegistry.capability_for(
        operation_key, param, family, dialect=dialect, option_value=option_value
    )
    if fact is None or fact.level is not CapabilityLevel.UNSUPPORTED:
        return None
    if (fact.enforcement, fact.boundary) not in _GATING:
        return None
    return fact


def assert_capability_gated(operation_key, family, *, dialect=None, build,
                            materialize=None, param=WILDCARD_PARAM, option_value=None):
    """Assert the spine's gate fact is enforced at the right site.

    Consults :func:`capability_gate`; then, depending on the fact's boundary:
    - no fact  -> ``build()`` (and ``materialize`` if given) must simply run;
    - BUILD    -> ``build()`` must raise ``BackendCapabilityError`` carrying the
      gate fact as ``.limitation``;
    - MATERIALIZE -> ``build()`` must succeed and ``materialize(built)`` must
      raise the enriched ``BackendCapabilityError`` (``.limitation`` is the
      residue fact, ``.__cause__`` an instance of its declared ``native_errors``).
    """
    fact = capability_gate(operation_key, family, dialect=dialect, param=param, option_value=option_value)
    if fact is None:
        built = build()
        return materialize(built) if materialize is not None else built

    if fact.boundary is Boundary.BUILD:
        with pytest.raises(BackendCapabilityError) as ei:
            build()
        assert ei.value.limitation is fact, (
            f"expected error.limitation to be the gate fact for {operation_key} "
            f"on {dialect or family}, got {ei.value.limitation!r}")
        assert ei.value.function_key == operation_key
        return None

    # MATERIALIZE_RESIDUE: build MUST succeed, materialize MUST raise the enriched error.
    assert materialize is not None, "materialize callback required for a MATERIALIZE fact"
    built = build()
    with pytest.raises(BackendCapabilityError) as ei:
        materialize(built)
    err = ei.value
    assert err.limitation is fact, (
        f"expected enriched error.limitation to be the residue fact for {operation_key} "
        f"on {dialect or family}, got {err.limitation!r}")
    assert err.function_key == operation_key
    assert isinstance(err.__cause__, fact.native_errors), (
        f"enriched error should chain the declared native cause {fact.native_errors}, "
        f"got {type(err.__cause__)!r}")
    return None


def assert_predicate_capability_gated(build) -> BackendCapabilityError:
    """Assert ``build()`` raises ``BackendCapabilityError`` from a
    predicate-gated ``CapabilityFact`` (item 108: the ibis-polars
    join_asof ``strategy`` gate).

    Not a case ``assert_capability_gated`` can express: ``capability_gate()``
    resolves a fact via ``CapabilityRegistry.capability_for``, which reads only
    ``_facts``/``_value_class_facts`` — never ``_predicate_facts``. A predicate
    fact's applicability depends on the ACTUAL bound call values (e.g.
    ``strategy="forward"`` vs ``"backward"``), which only exist once ``build()``
    actually runs through the real dispatch and its predicate is evaluated —
    there is no static ``(operation_key, family, dialect, param)`` tuple to
    pre-declare. This helper is the predicate-fact counterpart:
    ``pytest.raises`` plus the ``.limitation.predicate is not None`` check
    lives here, once, so no call site needs its own hand-coded reconstruction
    (the pattern ``test_no_migrated_site_carries_a_raw_capability_form`` polices
    out of migrated test files).

    Returns the raised error so the caller can assert further fields
    (e.g. ``.function_key``).
    """
    with pytest.raises(BackendCapabilityError) as ei:
        build()
    assert ei.value.limitation.predicate is not None, (
        f"expected a predicate-gated BackendCapabilityError, got "
        f"limitation={ei.value.limitation!r}"
    )
    return ei.value


def assert_predicate_clauses(fact: CapabilityFact, **expected: object) -> None:
    """Assert each ``name=value`` pair appears as an EQ clause on ``fact.predicate``.

    Predicate facts carry their selectors as clauses, never ``option_value``
    (the schema forces ``option_value`` to ``None`` whenever a predicate is
    present). Assertions on predicate-gated limitations must inspect clauses.
    """
    assert fact.predicate is not None, (
        f"expected predicate clauses on {fact.operation_key} fact, got {fact!r}"
    )
    actual = {
        clause.path: getattr(clause.operand, "value", clause.operand)
        for clause in fact.predicate.clauses
        if clause.op is ClauseOp.EQ
    }
    missing = {
        name: value
        for name, value in expected.items()
        if actual.get(name) != getattr(value, "value", value)
    }
    assert not missing, (
        f"expected EQ clauses {missing} on {fact.operation_key} predicate; "
        f"actual clauses: {actual}"
    )


def xfail_divergence(divergence_id, *, backend, strict=True) -> pytest.MarkDecorator:
    """Mark a test xfail when a known DivergenceFact applies to ``backend``.

    Divergences are id-keyed. ``DivergenceFact.backends`` may hold dialect-scoped
    names (e.g. "ibis-duckdb") or bare family names (e.g. "ibis"); a backend matches
    canonically on either its literal name or its resolved family. When the divergence
    does not apply, a no-op ``usefixtures()`` mark is returned so the test runs normally.
    """
    d = divergence_by_id(divergence_id)
    fam = gate_family(backend).value  # lowercase family, e.g. "ibis" — matches DivergenceFact.backends
    if backend not in d.backends and fam not in d.backends:
        return pytest.mark.usefixtures()  # divergence does not apply here — no-op mark
    return pytest.mark.xfail(
        strict=strict,
        reason=f"[{divergence_id}] {d.summary} — workaround: {d.workaround}",
    )


def build_gate_fact(
    operation_key: Any,
    identity: BackendIdentity,
    *,
    param: str,
    option_value: str | None = None,
) -> CapabilityFact | None:
    """A GATE/BUILD fact for ``(operation_key, param)`` on this identity, or None.

    Does not filter by ``level`` — ``LITERAL_ONLY`` needs the caller's actual
    node form (literal argument vs. dynamic expression) to decide whether it
    blocks; see ``first_scalar_build_gate``.
    """
    fact = CapabilityRegistry.capability_for(
        operation_key,
        param,
        identity.family,
        dialect=identity.dialect,
        option_value=option_value,
    )
    if fact is None:
        return None
    if fact.enforcement is not Enforcement.GATE or fact.boundary is not Boundary.BUILD:
        return None
    return fact


def first_scalar_build_gate(
    node: "ScalarFunctionNode", identity: BackendIdentity
) -> CapabilityFact | None:
    """The first actual ``GATE``/``BUILD`` blocker for a bound ``ScalarFunctionNode``,
    in production visitor order: whole-op WILDCARD fact (UNSUPPORTED only, mirroring
    ``visit_scalar_function``'s op-wide check), then arguments in protocol-signature
    order (mirroring ``_gate_and_resolve_args``), then emitted options in insertion
    order (mirroring the options loop). Returns ``None`` when no build gate applies —
    the caller then falls back to ``CapabilityRegistry.residue_for()``.

    Never invoke this for a ``WindowFunctionNode``; non-scalar nodes have no
    equivalent option-gating semantics in production.
    """
    from mountainash.expressions.core.expression_nodes import LiteralNode
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    from mountainash.expressions.core.unified_visitor.visitor import (
        _param_name_for,
        _protocol_sig_params,
    )

    wildcard_fact = build_gate_fact(node.function_key, identity, param=WILDCARD_PARAM)
    if wildcard_fact is not None and wildcard_fact.level is CapabilityLevel.UNSUPPORTED:
        return wildcard_fact

    func_def = ExpressionFunctionRegistry.get(node.function_key)
    protocol_method = func_def.protocol_method if func_def is not None else None
    sig_params = _protocol_sig_params(protocol_method) if protocol_method is not None else ()

    for i, argument in enumerate(node.arguments):
        param_name = _param_name_for(sig_params, i)
        if param_name is None:
            continue
        fact = build_gate_fact(node.function_key, identity, param=param_name)
        if fact is not None and (
            fact.level is CapabilityLevel.UNSUPPORTED
            or (
                fact.level is CapabilityLevel.LITERAL_ONLY
                and not isinstance(argument, LiteralNode)
            )
        ):
            return fact

    for option_name, option_value in (node.options or {}).items():
        fact = build_gate_fact(
            node.function_key, identity, param=option_name, option_value=str(option_value)
        )
        if fact is not None and fact.level is CapabilityLevel.UNSUPPORTED:
            return fact

    return None
