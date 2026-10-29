"""AST construction tests for boolean aggregate methods any() and all()."""
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_AGGREGATE


class TestBooleanAggregates:
    def test_all_creates_bool_and(self):
        expr = ma.col("flag").all()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_AGGREGATE.BOOL_AND
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_any_creates_bool_or(self):
        expr = ma.col("flag").any()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_AGGREGATE.BOOL_OR
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)
