"""AST construction tests for n_unique() count distinct."""
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode


class TestNUnique:
    def test_n_unique_creates_node(self):
        expr = ma.col("category").n_unique()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_n_unique_function_key(self):
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_AGGREGATE,
        )
        expr = ma.col("category").n_unique()
        assert expr._node.function_key == FKEY_MOUNTAINASH_SCALAR_AGGREGATE.COUNT_DISTINCT
