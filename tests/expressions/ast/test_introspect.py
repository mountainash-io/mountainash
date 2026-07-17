"""Public expression-AST introspection (item 226a).

Pure AST introspection — backend-agnostic, no compilation, no DataFrame.
This is a justified exception to the cross-backend-test-coverage principle
(which governs expression *execution* parity): there is no backend execution
here, only tree structure, so these tests are not cross-backend parametrised.
"""
import pytest

import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import (
    ExpressionNode,
    FieldReferenceNode,
)
from mountainash.expressions.introspect import iter_child_nodes


def _fields(nodes):
    return [n.field for n in nodes if isinstance(n, FieldReferenceNode)]


class TestIterChildNodes:
    def test_leaf_has_no_children(self):
        assert iter_child_nodes(ma.col("a")._node) == []

    def test_binary_returns_both_args_in_order(self):
        node = (ma.col("a") + ma.col("b"))._node
        children = iter_child_nodes(node)
        assert _fields(children) == ["a", "b"]

    def test_nested_container_ifthen_surfaces_branch_nodes(self):
        # when(cond).then(b).otherwise(c) -> IfThenNode; direct children are the
        # condition ScalarFunctionNode and the two branch FieldReferenceNodes.
        node = ma.when(ma.col("a") > ma.lit(1)).then(ma.col("b")).otherwise(ma.col("c"))._node
        children = iter_child_nodes(node)
        # 'a' is nested one level deeper inside the condition node, so the
        # direct-child field refs are exactly b and c.
        assert _fields(children) == ["b", "c"]
        assert any(not isinstance(c, FieldReferenceNode) for c in children)  # the condition node

    def test_over_node_surfaces_partition_field_ref_C1(self):
        # C1 anchor: WindowSpec is a non-node BaseModel; its partition_by holds
        # FieldReferenceNode("g"). The un-generalized primitive drops it.
        node = ma.col("x").sum().over("g")._node
        children = iter_child_nodes(node)
        assert "g" in _fields(children)

    def test_window_function_node_surfaces_partition_field_ref_C1(self):
        # The OTHER WindowSpec carrier: WindowFunctionNode.window_spec
        # (Optional[WindowSpec]). cum_sum().over("g") builds a
        # WindowFunctionNode, not an OverNode — same partition-descent path.
        node = ma.col("x").cum_sum().over("g")._node
        assert type(node).__name__ == "WindowFunctionNode"
        assert "g" in _fields(iter_child_nodes(node))

    def test_wrapper_argument_is_unwrapped(self):
        expr = ma.col("a") + ma.col("b")
        assert _fields(iter_child_nodes(expr)) == _fields(iter_child_nodes(expr._node))

    def test_non_expression_input_raises_typeerror(self):
        with pytest.raises(TypeError):
            iter_child_nodes(42)
