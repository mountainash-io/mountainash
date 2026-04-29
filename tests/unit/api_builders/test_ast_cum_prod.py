"""AST construction tests for cum_prod()."""
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import WindowFunctionNode, FieldReferenceNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_WINDOW


class TestCumProd:
    def test_cum_prod_creates_window_node(self):
        expr = ma.col("x").cum_prod()
        node = expr._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_WINDOW.CUM_PROD
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_cum_prod_reverse(self):
        expr = ma.col("x").cum_prod(reverse=True)
        node = expr._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_WINDOW.CUM_PROD
        assert node.options.get("reverse") is True
