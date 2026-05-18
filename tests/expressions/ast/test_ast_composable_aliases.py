"""AST construction tests for Polars-compatible composable methods."""
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
    FKEY_SUBSTRAIT_SCALAR_COMPARISON,
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)


class TestComposableMath:
    def test_cot(self):
        expr = ma.col("x").cot()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE
        tan_node = node.arguments[1]
        assert isinstance(tan_node, ScalarFunctionNode)
        assert tan_node.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN

    def test_cbrt(self):
        expr = ma.col("x").cbrt()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER


class TestComposableNulls:
    def test_null_count(self):
        expr = ma.col("x").null_count()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM
        is_null_node = node.arguments[0]
        assert isinstance(is_null_node, ScalarFunctionNode)
        assert is_null_node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL

    def test_has_nulls(self):
        expr = ma.col("x").has_nulls()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT
        sum_node = node.arguments[0]
        assert isinstance(sum_node, ScalarFunctionNode)
        assert sum_node.function_key == FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM
