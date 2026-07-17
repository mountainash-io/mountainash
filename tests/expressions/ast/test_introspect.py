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


from mountainash.expressions.introspect import walk


class TestWalk:
    # (col("a") + col("b")) * col("c"): root MULTIPLY, args [ADD(a,b), c].
    def _expr(self):
        return (ma.col("a") + ma.col("b")) * ma.col("c")

    def test_dfs_order_left_to_right(self):
        nodes = list(walk(self._expr(), order="depth_first"))
        assert [type(n).__name__ for n in nodes] == [
            "ScalarFunctionNode",  # MULTIPLY (root)
            "ScalarFunctionNode",  # ADD
            "FieldReferenceNode",  # a
            "FieldReferenceNode",  # b
            "FieldReferenceNode",  # c
        ]
        assert _fields(nodes) == ["a", "b", "c"]

    def test_bfs_order_level_by_level(self):
        nodes = list(walk(self._expr(), order="breadth_first"))
        # level 0: MULTIPLY; level 1: ADD, c; level 2: a, b
        assert _fields(nodes) == ["c", "a", "b"]

    def test_root_is_yielded_first(self):
        expr = self._expr()
        first = next(iter(walk(expr)))
        assert first is expr._node

    def test_default_order_is_depth_first(self):
        assert list(walk(self._expr())) == list(walk(self._expr(), order="depth_first"))

    def test_bad_order_raises_valueerror(self):
        with pytest.raises(ValueError):
            list(walk(self._expr(), order="sideways"))

    def test_input_checked_before_order(self):
        # Non-node input raises TypeError even with a bad order (input first).
        with pytest.raises(TypeError):
            walk(42, order="sideways")

    def test_non_expression_input_raises_typeerror(self):
        with pytest.raises(TypeError):
            walk(42)

    def test_shared_subtree_yielded_once_per_edge(self):
        # §3.5 invariant: no de-duplication. col("a") + col("a") has two edges
        # to value-equal FieldReferenceNodes; walk yields both.
        nodes = list(walk(ma.col("a") + ma.col("a")))
        assert _fields(nodes) == ["a", "a"]


from mountainash.expressions.introspect import collect_field_references


class TestCollectFieldReferences:
    def test_bare_column(self):
        assert collect_field_references(ma.col("a")) == {"a"}

    def test_compound(self):
        assert collect_field_references(ma.col("a") + ma.col("b")) == {"a", "b"}

    def test_nested_when_then(self):
        expr = ma.when(ma.col("a") > ma.lit(1)).then(ma.col("b")).otherwise(ma.col("c"))
        assert collect_field_references(expr) == {"a", "b", "c"}

    def test_window_partition_included_C1(self):
        # C1 headline — hard assert, no hedge.
        assert collect_field_references(ma.col("x").sum().over("g")) == {"x", "g"}

    def test_window_order_by_column_is_absent_documented_gap(self):
        # order_by columns are SortField.column (raw str), never a
        # FieldReferenceNode, so a node-based collector cannot see them.
        # This is the documented §3.3 limitation, asserted intentionally.
        expr = ma.col("x").sum().over("g", order_by="t")
        assert collect_field_references(expr) == {"x", "g"}  # "t" absent by design

    def test_alias_name_is_not_a_field_ref(self):
        assert collect_field_references(ma.col("a").alias("z")) == {"a"}

    def test_literal_only_is_empty(self):
        assert collect_field_references(ma.lit(1) + ma.lit(2)) == set()

    def test_duplicate_columns_dedup(self):
        assert collect_field_references(ma.col("a") + ma.col("a")) == {"a"}

    def test_wrapper_and_raw_node_agree(self):
        expr = ma.col("a") + ma.col("b")
        assert collect_field_references(expr) == collect_field_references(expr._node)

    def test_non_expression_input_raises_typeerror(self):
        with pytest.raises(TypeError):
            collect_field_references(42)

    def test_bare_string_column_is_rejected(self):
        # §3.4 scope boundary: bare-string columns are a relations concern,
        # explicitly out of scope for expressions.introspect.
        with pytest.raises(TypeError):
            collect_field_references("a")

    def test_none_is_rejected(self):
        with pytest.raises(TypeError):
            collect_field_references(None)


class TestPublicExport:
    def test_reexported_from_expressions_package(self):
        import mountainash.expressions as mexpr

        assert mexpr.collect_field_references(mexpr.col("a")) == {"a"}
        assert callable(mexpr.iter_child_nodes)
        assert callable(mexpr.walk)
        for name in ("iter_child_nodes", "walk", "collect_field_references"):
            assert name in mexpr.__all__
