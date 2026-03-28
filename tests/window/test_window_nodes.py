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
