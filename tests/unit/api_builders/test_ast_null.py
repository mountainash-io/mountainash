"""AST construction tests for null handling API builders."""
import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NULL


class TestNullMethods:
    def test_fill_null(self):
        expr = ma.col("x").fill_null(0)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NULL.FILL_NULL
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 0

    def test_null_if(self):
        expr = ma.col("x").null_if("UNKNOWN")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NULL.NULL_IF
        assert len(node.arguments) == 2
        assert node.arguments[1].value == "UNKNOWN"

    def test_fill_nan(self):
        expr = ma.col("x").fill_nan(0)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NULL.FILL_NAN
        assert len(node.arguments) == 2
        assert node.arguments[1].value == 0
