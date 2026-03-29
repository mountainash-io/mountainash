"""AST construction tests for scalar rounding API builders."""

import pytest
import mountainash_expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ROUNDING


class TestRoundingMethods:
    """Test that rounding methods create correct ScalarFunctionNode."""

    def test_round(self):
        expr = ma.col("x").round(2)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 2

    def test_ceil(self):
        expr = ma.col("x").ceil()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ROUNDING.CEIL
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_floor(self):
        expr = ma.col("x").floor()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ROUNDING.FLOOR
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)
