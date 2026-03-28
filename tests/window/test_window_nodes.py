"""Tests for window function AST nodes and value objects."""

import pytest
from mountainash.core.constants import SortField, WindowBoundType
from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import (
    WindowBound,
    WindowSpec,
)


class TestWindowBound:
    def test_current_row(self):
        bound = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
        assert bound.bound_type == WindowBoundType.CURRENT_ROW
        assert bound.offset is None

    def test_preceding_with_offset(self):
        bound = WindowBound(bound_type=WindowBoundType.PRECEDING, offset=3)
        assert bound.bound_type == WindowBoundType.PRECEDING
        assert bound.offset == 3

    def test_unbounded_preceding(self):
        bound = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
        assert bound.bound_type == WindowBoundType.UNBOUNDED_PRECEDING

    def test_immutable(self):
        bound = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
        with pytest.raises(Exception):
            bound.offset = 5


class TestWindowSpec:
    def test_empty_spec(self):
        spec = WindowSpec()
        assert spec.partition_by == []
        assert spec.order_by == []
        assert spec.lower_bound is None
        assert spec.upper_bound is None

    def test_with_partition_by(self):
        spec = WindowSpec(partition_by=["group", "category"])
        assert spec.partition_by == ["group", "category"]

    def test_with_order_by(self):
        sort = SortField(column="date", descending=False)
        spec = WindowSpec(order_by=[sort])
        assert len(spec.order_by) == 1
        assert spec.order_by[0].column == "date"

    def test_with_bounds(self):
        spec = WindowSpec(
            lower_bound=WindowBound(bound_type=WindowBoundType.PRECEDING, offset=5),
            upper_bound=WindowBound(bound_type=WindowBoundType.CURRENT_ROW),
        )
        assert spec.lower_bound.offset == 5
        assert spec.upper_bound.bound_type == WindowBoundType.CURRENT_ROW

    def test_immutable(self):
        spec = WindowSpec(partition_by=["a"])
        with pytest.raises(Exception):
            spec.partition_by = ["b"]


from mountainash.expressions.core.expression_nodes import (
    WindowFunctionNode,
    OverNode,
    WindowSpec,
    FieldReferenceNode,
    ScalarFunctionNode,
    LiteralNode,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
    SUBSTRAIT_ARITHMETIC_WINDOW,
)


class TestWindowFunctionNode:
    def test_rank_node(self):
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
            arguments=[],
        )
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.RANK
        assert node.arguments == []
        assert node.window_spec is None

    def test_lag_node_with_args(self):
        col_node = FieldReferenceNode(field="price")
        offset_node = LiteralNode(value=1)
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.LAG,
            arguments=[col_node, offset_node],
        )
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.LAG
        assert len(node.arguments) == 2

    def test_window_function_with_spec(self):
        spec = WindowSpec(partition_by=["group"])
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
            arguments=[],
            window_spec=spec,
        )
        assert node.window_spec is not None
        assert node.window_spec.partition_by == ["group"]

    def test_immutable(self):
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
            arguments=[],
        )
        with pytest.raises(Exception):
            node.arguments = [LiteralNode(value=1)]


class TestOverNode:
    def test_over_wraps_expression(self):
        inner = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            arguments=[FieldReferenceNode(field="a"), LiteralNode(value=1)],
        )
        spec = WindowSpec(partition_by=["group"])
        node = OverNode(expression=inner, window_spec=spec)
        assert node.expression == inner
        assert node.window_spec.partition_by == ["group"]

    def test_over_accepts_visitor(self):
        inner = FieldReferenceNode(field="x")
        spec = WindowSpec(partition_by=["g"])
        node = OverNode(expression=inner, window_spec=spec)

        class MockVisitor:
            def visit_over(self, n):
                return "visited_over"

        assert node.accept(MockVisitor()) == "visited_over"

    def test_immutable(self):
        inner = FieldReferenceNode(field="x")
        spec = WindowSpec(partition_by=["g"])
        node = OverNode(expression=inner, window_spec=spec)
        with pytest.raises(Exception):
            node.expression = FieldReferenceNode(field="y")
