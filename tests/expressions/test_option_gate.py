"""Value-aware capability gating for scalar-function options."""

import pytest

from expressions.argument_types.conftest import make_df
from mountainash.core.backend_detection import identify_backend_identity
from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_nodes import (
    FieldReferenceNode,
    ScalarFunctionNode,
)
from mountainash.expressions.core.expression_system.expsys_base import (
    get_expression_system,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STRING,
)
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor


_TEST_DIALECT = "polars"
_UNSUPPORTED_OPTION_VALUE = "__UNIT_TEST_UNSUPPORTED__"


@pytest.fixture(autouse=True)
def _isolate_registry():
    snap = CapabilityRegistry.snapshot()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snap)


def _abs_node_with_options(options):
    return ScalarFunctionNode(
        function_key=FK_ARITH.ABS,
        arguments=[FieldReferenceNode(field="v")],
        options=options,
    )


def _compile_node(node, df, backend):
    identity = identify_backend_identity(df)
    assert identity.family is CONST_BACKEND(backend)
    system_cls = get_expression_system(identity.family)
    visitor = UnifiedExpressionVisitor(system_cls(dialect=identity.dialect))
    return visitor.visit(node)


def test_declared_unsupported_option_raises_before_dispatch():
    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_ARITH.ABS,
                param="overflow",
                option_value=_UNSUPPORTED_OPTION_VALUE,
                level=CapabilityLevel.UNSUPPORTED,
                backend=CONST_BACKEND.POLARS,
                dialect=_TEST_DIALECT,
                message="polars abs has no checked overflow",
                since="2026-07-21",
                condition=(
                    "options['overflow'] == '__UNIT_TEST_UNSUPPORTED__'"
                ),
            ),
        ],
    )
    df = make_df({"v": [1]}, "polars")
    node = _abs_node_with_options({"overflow": _UNSUPPORTED_OPTION_VALUE})

    with pytest.raises(BackendCapabilityError):
        _compile_node(node, df, "polars")


def _trim_node_with_characters(characters):
    return ScalarFunctionNode(
        function_key=FK_STRING.TRIM,
        arguments=[FieldReferenceNode(field="v")],
        options={"characters": characters},
    )


def test_literal_only_option_allows_a_raw_literal_value():
    df = make_df({"v": ["xvaluex"]}, "narwhals-polars")
    node = _trim_node_with_characters("x")

    _compile_node(node, df, "narwhals")


def test_literal_only_option_rejects_an_expression_value():
    df = make_df({"v": ["xvaluex"]}, "narwhals-polars")
    node = _trim_node_with_characters(FieldReferenceNode(field="policy"))

    with pytest.raises(BackendCapabilityError, match="literal string value"):
        _compile_node(node, df, "narwhals")


@pytest.mark.parametrize("method", ["to_timezone", "local_timestamp"])
def test_timezone_ops_reject_non_iana_value(method):
    """Gate domain == production domain: only IANA zones may reach the visitor."""
    import mountainash as ma
    from mountainash.core.errors import InvalidOptionValueError

    with pytest.raises(InvalidOptionValueError, match="timezone"):
        getattr(ma.col("x").dt, method)("Not/AZone")

