"""Self-healing probes (spec Section 3).

For every LITERAL_ONLY/UNSUPPORTED expression fact (without probe_exempt):
bypass the visitor gate and drive the NATIVE backend path with a dynamic
argument, as a strict xfail. When upstream adds support the probe XPASSes,
CI fails, and the declaration must be flipped (or dialect-refined).

Also enforces integrity guard #2: every gating fact resolves to an OpSpec
or carries probe_exempt.
"""
from __future__ import annotations

import importlib
from typing import Any

import pytest

import mountainash as ma
from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.constants import CONST_BACKEND

# Trigger fact registration (replaced by bootstrap.load_all_capability_declarations()
# in Task 12, same PR).
import mountainash.expressions.backends.expression_systems.polars.base  # noqa: F401
import mountainash.expressions.backends.expression_systems.ibis.base  # noqa: F401
import mountainash.expressions.backends.expression_systems.narwhals.base  # noqa: F401

_CATEGORY_MODULES = [
    "test_arg_types_aggregate", "test_arg_types_arithmetic",
    "test_arg_types_boolean", "test_arg_types_comparison",
    "test_arg_types_datetime", "test_arg_types_list",
    "test_arg_types_logarithmic", "test_arg_types_misc",
    "test_arg_types_name", "test_arg_types_null",
    "test_arg_types_rounding", "test_arg_types_string",
    "test_arg_types_struct", "test_arg_types_window",
]

# Test-fixture backend(s) on which each fact's gating actually applies.
_FAMILY_DEFAULT_FIXTURES = {
    CONST_BACKEND.POLARS: ("polars",),
    CONST_BACKEND.IBIS: ("ibis",),
    CONST_BACKEND.NARWHALS: ("narwhals-polars", "narwhals-pandas"),
}
_FIXTURE_DIALECT = {
    "polars": "polars",
    "ibis": None,
    "ibis-polars": "ibis-polars",
    "narwhals-polars": "narwhals-polars",
    "narwhals-pandas": "narwhals-pandas",
}

# Relation-domain facts probed elsewhere; expression probes need FKEY facts only.
_GATING = (CapabilityLevel.LITERAL_ONLY, CapabilityLevel.UNSUPPORTED)


def _op_spec_index() -> dict[tuple[Any, str], Any]:
    index: dict[tuple[Any, str], Any] = {}
    for mod_name in _CATEGORY_MODULES:
        mod = importlib.import_module(f"expressions.argument_types.{mod_name}")
        for spec in getattr(mod, "OP_SPECS", []):
            index.setdefault((spec.function_key, spec.param_name), spec)
    return index


def _is_expression_fact(fact) -> bool:
    """Registry membership, NOT enum-class-name heuristics — the window
    fkey enum is named SUBSTRAIT_ARITHMETIC_WINDOW (no FKEY_ prefix)."""
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )

    try:
        ExpressionFunctionRegistry.get(fact.operation_key)
    except KeyError:
        return False
    return True


def _gating_expression_facts():
    return [
        f
        for f in CapabilityRegistry.facts()
        if f.level in _GATING
        and f.option_value is None
        and f.value_class is None  # value-class facts route to the class probe system, not the argument-probe guard (items 63/64, round-2 I-1)
        and f.predicate is None  # predicate facts carry option_value=None/value_class=None and route to the compound-cell guard (item 66b)
        and f.probe_exempt is None
        and _is_expression_fact(f)
    ]


def test_value_class_facts_do_not_enter_argument_probe_system() -> None:
    gating_facts = _gating_expression_facts()
    assert not any(f.value_class is not None for f in gating_facts), (
        "value-class facts must not enter the argument-probe system"
    )



# Dialects the argument-types matrix cannot instantiate (closed-by-default:
# a skipped dialect must be listed here with a reason, never silently dropped).
# narwhals-lazy shares the narwhals-polars implementation — its facts are
# exercised through the narwhals-polars fixture.
_UNPROBEABLE_DIALECTS = {
    "narwhals-lazy": "same polars implementation as narwhals-polars; probed via that fixture",
}


def _probe_fixtures(fact) -> list[str]:
    """Fixtures where the resolved level is actually gating for this fact
    (dialect-scoped EXPR_CAPABLE refinements exclude their dialects)."""
    fixtures = (
        (fact.dialect,) if fact.dialect else _FAMILY_DEFAULT_FIXTURES[fact.backend]
    )
    out = []
    for fixture in fixtures:
        if fixture not in _FIXTURE_DIALECT:
            assert fixture in _UNPROBEABLE_DIALECTS, (
                f"dialect {fixture!r} is neither probeable (_FIXTURE_DIALECT) nor "
                "explicitly exempted (_UNPROBEABLE_DIALECTS) — add it to one"
            )
            continue
        resolved = CapabilityRegistry.capability_for(
            fact.operation_key, fact.param, fact.backend, _FIXTURE_DIALECT[fixture]
        )
        if resolved is not None and resolved.level in _GATING:
            out.append(fixture)
    return out


def test_every_gating_fact_has_op_spec_or_exemption():
    """Integrity guard #2 (spec Section 2) — the D1 bridge, structural form."""
    index = _op_spec_index()
    missing = sorted(
        f"{fact.operation_key}/{fact.param} [{fact.backend.value}]"
        for fact in _gating_expression_facts()
        if (fact.operation_key, fact.param) not in index
    )
    assert not missing, (
        "Gating capability facts with no OpSpec probe and no probe_exempt "
        f"reason — author an OpSpec or exempt with a reason: {missing}"
    )


def _probe_params():
    index = _op_spec_index()
    params = []
    for fact in _gating_expression_facts():
        spec = index.get((fact.operation_key, fact.param))
        if spec is None:
            continue  # the guard test above reports it
        for fixture in _probe_fixtures(fact):
            params.append(
                pytest.param(
                    fact, spec, fixture,
                    id=f"{fact.operation_key.name}-{fact.param}-{fixture}",
                    marks=pytest.mark.xfail(
                        strict=True,
                        reason=(
                            f"probe: native path expected to fail — {fact.message} "
                            "(XPASS => upstream added support: flip the declaration)"
                        ),
                    ),
                )
            )
    return params


@pytest.mark.parametrize("fact,spec,backend", _probe_params())
def test_native_path_probe(fact, spec, backend):
    from expressions.argument_types.conftest import make_df

    from mountainash.expressions.core.expression_system.expsys_base import (
        get_expression_system,
    )
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

    df = make_df(spec.data, backend)
    arg = ma.col(spec.arg_col_name)  # dynamic argument — the gated shape
    expr = spec.build(ma.col(spec.input_col), arg)

    system_cls = get_expression_system(fact.backend)
    system = system_cls(dialect=_FIXTURE_DIALECT[backend])
    visitor = UnifiedExpressionVisitor(system, enforce_capabilities=False)

    compiled = visitor.visit(expr._node)
    # Materialize to force lazy failures — reuse the harness materializer.
    from expressions.argument_types._test_template import _materialize_result

    _materialize_result(df, compiled, backend)
    # Reaching here without an exception = native path succeeded = XPASS(strict).
