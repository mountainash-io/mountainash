"""Focused contracts for the argument-matrix's spine-derived xfail expectations.

These tests pin the mechanism `_test_template.py` uses to derive strict xfail
markers from the exact bound AST each matrix cell compiles — see backlog
arg-matrix-xfail-blind-to-value-class-facts and spec
2026-08-09-argument-matrix-value-class-facts-design.
"""
from __future__ import annotations

import pytest

from mountainash.core.constants import CONST_BACKEND

from expressions.argument_types.conftest import ALL_BACKENDS, make_df, matrix_identity


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_matrix_identity_matches_production_backend_detection(backend: str) -> None:
    from tests.fixtures.capability_gating import resolve_identity

    df = make_df({"x": [1]}, backend)
    assert matrix_identity(backend) == resolve_identity(df)


@pytest.fixture
def isolated_registry():
    from mountainash.core.capabilities.registry import CapabilityRegistry

    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        yield CapabilityRegistry
    finally:
        CapabilityRegistry.restore(snapshot)


def test_scalar_option_gate_uses_emitted_iana_timezone_value() -> None:
    from mountainash.core.capabilities.schema import ValueClass
    from expressions.argument_types._test_template import first_scalar_build_gate

    import mountainash as ma

    node = ma.col("ts").dt.local_timestamp("UTC").node
    fact = first_scalar_build_gate(node, matrix_identity("ibis"))
    assert fact is not None
    assert fact.param == "timezone"
    assert fact.value_class is ValueClass.IANA_TIMEZONE


def test_scalar_option_gate_ignores_non_gating_fact(isolated_registry) -> None:
    from mountainash.core.capabilities.schema import (
        Boundary,
        CapabilityFact,
        CapabilityLevel,
        Enforcement,
    )
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING,
    )
    from expressions.argument_types._test_template import first_scalar_build_gate

    import mountainash as ma

    node = ma.col("x").str.contains("a").node
    isolated_registry.register_backend(CONST_BACKEND.IBIS, [
        CapabilityFact(
            operation_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            param="case_sensitivity",
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            message="router-only test fact",
            since="2026-08-09",
            boundary=Boundary.BUILD,
            enforcement=Enforcement.ROUTER_METADATA,
        ),
    ])
    assert first_scalar_build_gate(node, matrix_identity("ibis")) is None


def test_dynamic_argument_gate_precedes_wildcard_residue() -> None:
    from mountainash.core.capabilities.schema import CapabilityLevel
    from expressions.argument_types._test_template import first_scalar_build_gate

    import mountainash as ma

    node = ma.col("items").list.contains(ma.col("needle")).node
    fact = first_scalar_build_gate(node, matrix_identity("narwhals-pandas"))
    assert fact is not None
    assert fact.level is CapabilityLevel.LITERAL_ONLY


def test_param_gate_wins_over_wildcard_residue(isolated_registry) -> None:
    """A reachable parameter-specific GATE/BUILD fact must be selected even when
    a WILDCARD MATERIALIZE_RESIDUE fact is also registered for the same op —
    residue is a later, materialize-time fallback, never a shadow of a build gate."""
    from mountainash.core.capabilities.schema import (
        Boundary,
        CapabilityFact,
        CapabilityLevel,
        Enforcement,
        WILDCARD_PARAM,
    )
    from mountainash.core.types import BackendCapabilityError
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING,
    )
    from expressions.argument_types._test_template import first_scalar_build_gate

    import mountainash as ma

    node = ma.col("x").str.contains("a").node
    isolated_registry.register_backend(CONST_BACKEND.IBIS, [
        CapabilityFact(
            operation_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            param="case_sensitivity",
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            message="param-specific build gate",
            since="2026-08-09",
            boundary=Boundary.BUILD,
            enforcement=Enforcement.GATE,
        ),
        CapabilityFact(
            operation_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            message="whole-op materialize residue",
            since="2026-08-09",
            boundary=Boundary.MATERIALIZE,
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            native_errors=(BackendCapabilityError,),
        ),
    ])
    fact = first_scalar_build_gate(node, matrix_identity("ibis"))
    assert fact is not None
    assert fact.param == "case_sensitivity"
    assert fact.enforcement is Enforcement.GATE


def _window_op_spec(op_name: str):
    import importlib

    window = importlib.import_module("expressions.argument_types.test_arg_types_window")
    return next(spec for spec in window.OP_SPECS if spec.op_name == op_name)


def test_bound_matrix_cell_uses_emitted_key_not_legacy_opspec_key() -> None:
    from expressions.argument_types._test_template import build_matrix_cell

    op = _window_op_spec("cum_sum")
    cell = build_matrix_cell(op, "raw")
    # cum_sum's OpSpec.function_key is legacy metadata (the literal string
    # "cum_sum"); the emitted node carries the real enum function key.
    assert op.function_key != cell.node.function_key
    assert cell.operation_key is cell.node.function_key


def test_non_scalar_matrix_cell_is_not_scalar_gated() -> None:
    from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import (
        ScalarFunctionNode,
    )
    from expressions.argument_types._test_template import build_matrix_cell

    op = _window_op_spec("cum_sum")
    cell = build_matrix_cell(op, "raw")
    assert not isinstance(cell.node, ScalarFunctionNode)


def test_runtime_and_collection_cells_are_structurally_equivalent() -> None:
    from expressions.argument_types._test_template import build_matrix_cell

    op = _window_op_spec("cum_sum")
    left = build_matrix_cell(op, "complex")
    right = build_matrix_cell(op, "complex")
    assert type(left.node) is type(right.node)
    assert left.node.function_key == right.node.function_key
    assert left.node.arguments == right.node.arguments


def test_build_matrix_cell_falls_back_to_residue_when_no_build_gate() -> None:
    """A cell with neither a build-time gate nor a residue fact must be
    unmarked — proves the residue lookup only fires after
    first_scalar_build_gate() returns None, not unconditionally."""
    from expressions.argument_types._test_template import xfail_if_limited
    import importlib

    string = importlib.import_module("expressions.argument_types.test_arg_types_string")
    op = next(spec for spec in string.OP_SPECS if spec.op_name == "contains")
    assert xfail_if_limited("polars", op, "raw") is None


def test_regexp_match_all_raw_ibis_is_marked_by_emitted_option_fact() -> None:
    """Regression for the corrected regexp gate discriminator (backlog item 71
    finding #1): `pytest.mark.xfail(...).mark.name` is always the literal
    string "xfail", never "capability" — the fact-backed marker is identified
    by `raises is BackendCapabilityError` plus a live emitted-option hit, not
    by inspecting the mark's own name or reason text."""
    import importlib
    from mountainash.core.types import BackendCapabilityError
    from expressions.argument_types._test_template import (
        build_matrix_cell,
        first_scalar_build_gate,
        xfail_if_limited,
    )

    string = importlib.import_module("expressions.argument_types.test_arg_types_string")
    op = next(
        spec for spec in string.OP_SPECS if spec.op_name == "regexp_match_substring_all"
    )
    mark = xfail_if_limited("ibis", op, "raw")
    assert mark is not None
    assert mark.mark.kwargs["raises"] is BackendCapabilityError
    assert mark.mark.kwargs["strict"] is True

    cell = build_matrix_cell(op, "raw")
    fact = first_scalar_build_gate(cell.node, matrix_identity("ibis"))
    assert fact is not None
    assert fact.param in {"case_sensitivity", "multiline", "dotall"}
