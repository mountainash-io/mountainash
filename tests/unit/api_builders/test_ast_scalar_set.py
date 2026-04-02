"""AST construction tests for set operations API builders."""
import pytest
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_SET, FKEY_MOUNTAINASH_SCALAR_SET

class TestSetMethods:
    def test_is_in_list(self):
        expr = ma.col("x").is_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_SET.IS_IN
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert len(node.arguments) == 4  # self + 3 values

    def test_is_in_varargs(self):
        expr = ma.col("x").is_in(1, 2, 3)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_SET.IS_IN
        assert len(node.arguments) == 4

    def test_is_not_in(self):
        expr = ma.col("x").is_not_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN
        assert len(node.arguments) == 4

    def test_index_in(self):
        expr = ma.col("x").index_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_SET.INDEX_IN
