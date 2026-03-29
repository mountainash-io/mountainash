"""AST construction tests for scalar logarithmic API builders."""

import pytest
import mountainash_expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC


class TestLogarithmicMethods:
    """Test that logarithmic methods create correct ScalarFunctionNode."""

    def test_ln(self):
        expr = ma.col("x").ln()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_log10(self):
        expr = ma.col("x").log10()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG10
        assert len(node.arguments) == 1

    def test_log2(self):
        expr = ma.col("x").log2()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG2
        assert len(node.arguments) == 1

    def test_log_custom_base(self):
        expr = ma.col("x").log(10)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOGB
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 10
