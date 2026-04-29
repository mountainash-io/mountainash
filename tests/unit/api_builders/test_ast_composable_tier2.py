"""AST construction tests for Tier 2 composable methods."""
import pytest
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import (
    ScalarFunctionNode, WindowFunctionNode, FieldReferenceNode, LiteralNode,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
    FKEY_MOUNTAINASH_WINDOW,
)


class TestZfill:
    def test_zfill_is_lpad_with_zero(self):
        expr = ma.col("x").str.zfill(5)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.LPAD
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 5
        assert isinstance(node.arguments[2], LiteralNode)
        assert node.arguments[2].value == "0"


class TestSumHorizontal:
    def test_sum_horizontal_two_args(self):
        expr = ma.sum_horizontal(ma.col("a"), ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD
        assert len(node.arguments) == 2

    def test_sum_horizontal_three_args_nested(self):
        expr = ma.sum_horizontal(ma.col("a"), ma.col("b"), ma.col("c"))
        node = expr._node
        # Outer node: ADD(ADD(a, b), c)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD
        assert len(node.arguments) == 2
        # Inner node: ADD(a, b)
        inner = node.arguments[0]
        assert isinstance(inner, ScalarFunctionNode)
        assert inner.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD
        assert len(inner.arguments) == 2

    def test_sum_horizontal_requires_two_args(self):
        with pytest.raises(ValueError, match="at least 2"):
            ma.sum_horizontal(ma.col("a"))


class TestPctChange:
    def test_pct_change_default(self):
        expr = ma.col("x").pct_change()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE
        assert len(node.arguments) == 2
        # First arg: DIFF node
        diff_node = node.arguments[0]
        assert isinstance(diff_node, ScalarFunctionNode)
        assert diff_node.function_key == FKEY_MOUNTAINASH_WINDOW.DIFF
        # Second arg: LAG node (WindowFunctionNode)
        lag_node = node.arguments[1]
        assert isinstance(lag_node, WindowFunctionNode)

    def test_pct_change_custom_n(self):
        expr = ma.col("x").pct_change(n=3)
        node = expr._node
        diff_node = node.arguments[0]
        assert diff_node.options.get("n") == 3
