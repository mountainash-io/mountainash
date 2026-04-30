"""Tests for Window API Builder and .over() method.

Tests:
- Each of the 11 window methods builds correct WindowFunctionNode
- .over() populates WindowFunctionNode.window_spec when inner node is WindowFunctionNode
- .over() wraps in OverNode when inner node is NOT WindowFunctionNode
- .over() handles order_by string and list
- .over() handles multiple partition_by args
- .over() handles rows_between tuple
"""

from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_api.boolean import BooleanExpressionAPI
from mountainash.expressions.core.expression_nodes import (
    FieldReferenceNode,
    LiteralNode,
    ScalarFunctionNode,
    WindowFunctionNode,
)
from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import (
    WindowBound,
    WindowSpec,
)
from mountainash.expressions.core.expression_nodes.mountainash_extensions.exn_ext_ma_over import (
    OverNode,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    SUBSTRAIT_ARITHMETIC_WINDOW,
    FKEY_MOUNTAINASH_WINDOW,
)
from mountainash.core.constants import SortField, WindowBoundType


# ========================================
# Helpers
# ========================================

def _col(name: str) -> BooleanExpressionAPI:
    """Create a BooleanExpressionAPI wrapping a FieldReferenceNode."""
    return BooleanExpressionAPI(FieldReferenceNode(field=name))


# ========================================
# Window Function Builder Methods
# ========================================


class TestWindowBuilderMethods:
    """Test that each of the 11 window methods builds the correct WindowFunctionNode."""

    def test_row_number(self):
        api = _col("x").row_number()
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER
        assert node.arguments == []
        # rank() family now pre-populates window_spec with order_by
        assert node.window_spec is not None
        assert len(node.window_spec.order_by) == 1
        assert node.window_spec.order_by[0].column == "x"

    def test_rank(self):
        api = _col("x").rank()
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        # Default method="average" maps to FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE
        assert node.function_key == FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE
        assert node.arguments == []
        assert node.window_spec is not None
        assert node.window_spec.order_by[0].column == "x"

    def test_rank_method_min(self):
        api = _col("x").rank(method="min")
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.RANK
        assert node.options["rank_method"] == "min"

    def test_rank_method_max(self):
        api = _col("x").rank(method="max")
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_WINDOW.RANK_MAX

    def test_dense_rank(self):
        api = _col("x").dense_rank()
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK
        assert node.arguments == []
        assert node.window_spec is not None
        assert node.window_spec.order_by[0].column == "x"

    def test_percent_rank(self):
        api = _col("x").percent_rank()
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK
        assert node.arguments == []
        assert node.window_spec is None

    def test_cume_dist(self):
        api = _col("x").cume_dist()
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST
        assert node.arguments == []
        assert node.window_spec is None

    def test_ntile(self):
        api = _col("x").ntile(4)
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.NTILE
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], LiteralNode)
        assert node.arguments[0].value == 4
        assert node.window_spec is None

    def test_lead_default_offset(self):
        api = _col("x").lead()
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.LEAD
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 1

    def test_lead_custom_offset(self):
        api = _col("x").lead(offset=3)
        node = api._node
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.LEAD
        assert node.arguments[1].value == 3

    def test_lead_with_default(self):
        api = _col("x").lead(offset=1, default=0)
        node = api._node
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.LEAD
        assert len(node.arguments) == 3
        assert isinstance(node.arguments[2], LiteralNode)
        assert node.arguments[2].value == 0

    def test_lag_default_offset(self):
        api = _col("x").lag()
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.LAG
        assert len(node.arguments) == 2
        assert node.arguments[1].value == 1

    def test_lag_custom_offset(self):
        api = _col("x").lag(offset=2)
        node = api._node
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.LAG
        assert node.arguments[1].value == 2

    def test_lag_with_default(self):
        api = _col("x").lag(offset=1, default=-1)
        node = api._node
        assert len(node.arguments) == 3
        assert node.arguments[2].value == -1

    def test_first_value(self):
        api = _col("x").first_value()
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_last_value(self):
        api = _col("x").last_value()
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_nth_value(self):
        api = _col("x").nth_value(3)
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 3


# ========================================
# .over() Method Tests
# ========================================


class TestOverMethodWindowFunctionNode:
    """.over() on WindowFunctionNode should populate window_spec."""

    def test_over_merges_window_spec(self):
        """rank() pre-populates order_by; .over() merges partition_by."""
        api = _col("x").rank().over("dept")
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE
        assert node.window_spec is not None
        # partition_by comes from .over()
        assert len(node.window_spec.partition_by) == 1
        assert isinstance(node.window_spec.partition_by[0], FieldReferenceNode)
        assert node.window_spec.partition_by[0].field == "dept"
        # order_by preserved from rank()
        assert len(node.window_spec.order_by) == 1
        assert node.window_spec.order_by[0].column == "x"

    def test_over_multiple_partition_by(self):
        api = _col("x").row_number().over("dept", "team")
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.window_spec is not None
        assert len(node.window_spec.partition_by) == 2
        assert node.window_spec.partition_by[0].field == "dept"
        assert node.window_spec.partition_by[1].field == "team"

    def test_over_order_by_preserved_from_rank(self):
        """rank()'s order_by takes precedence over .over()'s order_by."""
        api = _col("x").rank().over("dept", order_by="salary")
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        # rank()'s order_by ("x") wins over .over()'s ("salary")
        assert len(node.window_spec.order_by) == 1
        assert node.window_spec.order_by[0].column == "x"

    def test_over_order_by_on_non_ranking_window(self):
        """For non-ranking windows (no pre-populated spec), .over() sets order_by."""
        api = _col("x").first_value().over("dept", order_by="-salary")
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert len(node.window_spec.order_by) == 1
        assert node.window_spec.order_by[0].column == "salary"
        assert node.window_spec.order_by[0].descending is True

    def test_over_order_by_list_on_non_ranking_window(self):
        """For non-ranking windows, .over() order_by list works."""
        api = _col("x").first_value().over("dept", order_by=["salary", "-name"])
        node = api._node
        assert len(node.window_spec.order_by) == 2
        assert node.window_spec.order_by[0].column == "salary"
        assert node.window_spec.order_by[0].descending is False
        assert node.window_spec.order_by[1].column == "name"
        assert node.window_spec.order_by[1].descending is True

    def test_over_rows_between(self):
        api = _col("x").first_value().over("dept", rows_between=(-3, 0))
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.window_spec.lower_bound is not None
        assert node.window_spec.lower_bound.bound_type == WindowBoundType.PRECEDING
        assert node.window_spec.lower_bound.offset == 3
        assert node.window_spec.upper_bound is not None
        assert node.window_spec.upper_bound.bound_type == WindowBoundType.CURRENT_ROW

    def test_over_rows_between_unbounded(self):
        api = _col("x").last_value().over("dept", rows_between=(None, None))
        node = api._node
        assert node.window_spec.lower_bound.bound_type == WindowBoundType.UNBOUNDED_PRECEDING
        assert node.window_spec.upper_bound.bound_type == WindowBoundType.UNBOUNDED_FOLLOWING

    def test_over_rows_between_following(self):
        api = _col("x").first_value().over("dept", rows_between=(0, 5))
        node = api._node
        assert node.window_spec.lower_bound.bound_type == WindowBoundType.CURRENT_ROW
        assert node.window_spec.upper_bound.bound_type == WindowBoundType.FOLLOWING
        assert node.window_spec.upper_bound.offset == 5


class TestOverMethodNonWindowNode:
    """.over() on non-WindowFunctionNode wraps in OverNode."""

    def test_over_wraps_scalar_function_in_over_node(self):
        # col("x").add(1) produces a ScalarFunctionNode, not WindowFunctionNode
        api = _col("x").add(1).over("dept")
        node = api._node
        assert isinstance(node, OverNode)
        assert isinstance(node.expression, ScalarFunctionNode)
        assert node.window_spec is not None
        assert len(node.window_spec.partition_by) == 1
        assert node.window_spec.partition_by[0].field == "dept"

    def test_over_wraps_field_reference_in_over_node(self):
        api = _col("x").over("dept")
        node = api._node
        assert isinstance(node, OverNode)
        assert isinstance(node.expression, FieldReferenceNode)
        assert node.expression.field == "x"

    def test_over_on_non_window_with_order_by(self):
        api = _col("x").add(1).over("dept", order_by="name")
        node = api._node
        assert isinstance(node, OverNode)
        assert len(node.window_spec.order_by) == 1
        assert node.window_spec.order_by[0].column == "name"

    def test_over_on_non_window_with_rows_between(self):
        api = _col("x").add(1).over("dept", rows_between=(-1, 1))
        node = api._node
        assert isinstance(node, OverNode)
        assert node.window_spec.lower_bound.bound_type == WindowBoundType.PRECEDING
        assert node.window_spec.lower_bound.offset == 1
        assert node.window_spec.upper_bound.bound_type == WindowBoundType.FOLLOWING
        assert node.window_spec.upper_bound.offset == 1


class TestOverNoPartition:
    """.over() with no partition_by creates empty partition list."""

    def test_over_no_partition(self):
        api = _col("x").rank().over(order_by="salary")
        node = api._node
        assert isinstance(node, WindowFunctionNode)
        assert node.window_spec.partition_by == []
        # rank()'s order_by ("x") takes precedence
        assert len(node.window_spec.order_by) == 1
        assert node.window_spec.order_by[0].column == "x"
