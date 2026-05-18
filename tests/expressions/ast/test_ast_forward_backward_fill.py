"""AST construction tests for forward_fill() and backward_fill()."""
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import WindowFunctionNode, FieldReferenceNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_WINDOW


class TestForwardFill:
    def test_forward_fill_default(self):
        expr = ma.col("x").forward_fill()
        node = expr._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_forward_fill_with_limit(self):
        expr = ma.col("x").forward_fill(limit=3)
        node = expr._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL
        assert node.options.get("limit") == 3


class TestBackwardFill:
    def test_backward_fill_default(self):
        expr = ma.col("x").backward_fill()
        node = expr._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_backward_fill_with_limit(self):
        expr = ma.col("x").backward_fill(limit=2)
        node = expr._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL
        assert node.options.get("limit") == 2
