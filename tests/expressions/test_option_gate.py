"""Value-aware capability gating for scalar-function options."""

import pytest

from expressions.argument_types.conftest import make_df
from mountainash.core.backend_detection import identify_backend_identity
from mountainash.core.capabilities import (
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.capabilities.declarations import (
    BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain, Selector,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_nodes import (
    FieldReferenceNode,
    LiteralNode,
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
    policy = CapabilityPolicyRule(
        CapabilityKey(FK_ARITH.ABS, "overflow", Selector("exact", _UNSUPPORTED_OPTION_VALUE)),
        CapabilityLevel.UNSUPPORTED, "2026-09-18", "synthetic option refusal",
        PolicyConsumer.GATE, PolicyAction.BLOCK,
    )
    CapabilityRegistry.register_segment(BoundSegment(
        "mountainash.expressions.backends.capabilities.polars.dialects.polars.substrait.arithmetic.option_gate",
        Scope(CONST_BACKEND.POLARS, Dialect(_TEST_DIALECT)),
        CapabilitySegment(Domain.ARITHMETIC, policies=(policy,)),
    ))
    df = make_df({"v": [1]}, "polars")
    node = _abs_node_with_options({"overflow": _UNSUPPORTED_OPTION_VALUE})

    with pytest.raises(BackendCapabilityError) as raised:
        _compile_node(node, df, "polars")
    assert raised.value.function_key is FK_ARITH.ABS
    assert raised.value.limitation is not None


def _trim_node_with_characters(characters):
    return ScalarFunctionNode(
        function_key=FK_STRING.TRIM,
        arguments=[
            FieldReferenceNode(field="v"),
            characters if isinstance(characters, FieldReferenceNode) else LiteralNode(value=characters),
        ],
    )


def test_literal_only_argument_allows_a_raw_literal_value():
    df = make_df({"v": ["xvaluex"]}, "narwhals-polars")
    node = _trim_node_with_characters("x")

    compiled = _compile_node(node, df, "narwhals")
    assert df.select(compiled.alias("result")).to_dict()["result"].to_list() == ["value"]


def test_literal_only_argument_rejects_an_expression_value():
    df = make_df({"v": ["xvaluex"], "policy": ["x"]}, "narwhals-polars")
    node = _trim_node_with_characters(FieldReferenceNode(field="policy"))

    with pytest.raises(BackendCapabilityError) as raised:
        _compile_node(node, df, "narwhals")
    assert raised.value.function_key is FK_STRING.TRIM


@pytest.mark.parametrize("method", ["to_timezone", "local_timestamp"])
def test_timezone_ops_reject_non_iana_value(method):
    """Gate domain == production domain: only IANA zones may reach the visitor."""
    import mountainash as ma
    from mountainash.core.errors import InvalidOptionValueError

    with pytest.raises(InvalidOptionValueError, match="timezone"):
        getattr(ma.col("x").dt, method)("Not/AZone")

