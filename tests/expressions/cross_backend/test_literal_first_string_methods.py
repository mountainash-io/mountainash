"""Cross-backend guard for item 226c (literal-receiver string methods).

`lit.str.contains(col)` (concrete string receiver + Deferred column argument)
crashed on ibis with the same root cause as literal-first arithmetic (item 226b
/ Ibis #11742), on the method-dispatch path. The fix (`_lift_deferred_receiver`)
is an **ibis** crash fix — its positive acceptance (all 15 routed methods
executing literal-first) lives in
tests/expressions/backends/ibis/test_string_lift_all_methods.py, because a
*columnar* string argument is not universally supported: restrictions depend
on the operand and concrete engine. Those required argument boundaries are
separate from the literal-receiver fix.

This module asserts the universally-portable shapes (literal arguments) still
behave identically across every backend — i.e. the receiver-lift did not disturb
any already-working path.
"""
import pytest

import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLiteralFirstStringMethodsNoRegression:
    def test_col_contains_lit_unchanged(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"s": ["abcx", "zzq"]}, backend_name)
        assert collect_expr(df, ma.col("s").str.contains(ma.lit("bc"))) == [True, False]

    def test_col_starts_with_lit_unchanged(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"s": ["abcx", "zzq"]}, backend_name)
        assert collect_expr(df, ma.col("s").str.starts_with(ma.lit("ab"))) == [True, False]

    def test_col_replace_lit_unchanged(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"s": ["abcx", "zzq"]}, backend_name)
        assert collect_expr(df, ma.col("s").str.replace(ma.lit("bc"), ma.lit("X"))) == ["aXx", "zzq"]


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "ibis-duckdb"])
@pytest.mark.parametrize(
    "operation,arguments,expected",
    [
        ("trim", ("-",), ["'-abc-'", "xyz"]),
        ("ltrim", ("-",), ["'-abc-'", "xyz--"]),
        ("rtrim", ("-",), ["'-abc-'", "--xyz"]),
        ("substring", (1, 2), ["-a", "-x"]),
        ("left", (2,), ["'-", "--"]),
        ("right", (2,), ["-'", "--"]),
        ("center", (9, "#"), ["#'-abc-'#", "#--xyz--#"]),
    ],
)
def test_required_arguments_without_catalogue(
    backend_name, backend_factory, select_and_extract, operation, arguments, expected
):
    """Internal argument preparation must survive absent declarations and guards."""
    from mountainash.core.backend_detection import identify_backend_identity
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.policy import (
        CapabilityPolicy, ProtectionMechanism, _new_execution_context,
    )
    from mountainash.core.types import BackendCapabilityError
    from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

    from fixtures.call_expectations import expect_call_failure

    df = backend_factory.create({"s": ["'-abc-'", "--xyz--"]}, backend_name)
    expression = getattr(ma.col("s").str, operation)(*arguments)
    identity = identify_backend_identity(df)
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        # gate-only bypass: disable GATE protection, keep error enrichment active.
        policy = CapabilityPolicy.checked(mechanisms=frozenset({ProtectionMechanism.MATERIALIZATION}))
        execution_context = _new_execution_context(df, policy=policy)
        system = get_expression_system(identity.family)(
            dialect=identity.dialect, execution_context=execution_context,
        )
        visitor = UnifiedExpressionVisitor(
            system, input_data=df, execution_context=execution_context,
        )
        if backend_name == "narwhals-polars" and operation == "center":
            with pytest.raises(BackendCapabilityError) as caught:
                visitor.visit(expression._node)
            assert caught.value.limitation is None
            return
        compiled = visitor.visit(expression._node)
        with expect_call_failure(
            when=backend_name == "narwhals-polars" and operation in ("ltrim", "rtrim"),
            errors=(AssertionError,),
            reason="Narwhals native trim siblings remove both sides; this is independent of required argument conversion",
        ):
            assert select_and_extract(df, compiled, "result", backend_name) == expected
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.cross_backend
@pytest.mark.string
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("dynamic_operand", ("pattern", "replacement"))
def test_dynamic_replacement_operands_without_catalogue(
    backend_name, backend_factory, select_and_extract, dynamic_operand,
):
    from mountainash.core.backend_detection import identify_backend_identity
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.policy import (
        CapabilityPolicy, ProtectionMechanism, _new_execution_context,
    )
    from mountainash.core.types import BackendCapabilityError
    from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING,
    )
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

    df = backend_factory.create(
        {"s": ["aba", "bba"], "pattern": ["a", "b"], "replacement": ["x", "y"]},
        backend_name,
    )
    if dynamic_operand == "pattern":
        expression = ma.col("s").str.replace(ma.col("pattern"), "x")
        unsupported = backend_name not in ("ibis-duckdb", "ibis-sqlite")
        expected = ["xbx", "xxa"]
    else:
        expression = ma.col("s").str.replace("a", ma.col("replacement"))
        unsupported = backend_name in ("pandas", "narwhals-pandas")
        expected = ["xbx", "bby"]
    identity = identify_backend_identity(df)
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        # gate-only bypass: disable GATE protection, keep error enrichment active.
        policy = CapabilityPolicy.checked(mechanisms=frozenset({ProtectionMechanism.MATERIALIZATION}))
        execution_context = _new_execution_context(df, policy=policy)
        system = get_expression_system(identity.family)(
            dialect=identity.dialect, execution_context=execution_context,
        )
        visitor = UnifiedExpressionVisitor(
            system, input_data=df, execution_context=execution_context,
        )
        if unsupported:
            with pytest.raises(BackendCapabilityError) as caught:
                visitor.visit(expression._node)
            assert caught.value.function_key is FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE
            assert caught.value.limitation is None
        else:
            compiled = visitor.visit(expression._node)
            assert select_and_extract(df, compiled, "result", backend_name) == expected
    finally:
        CapabilityRegistry.restore(snapshot)
