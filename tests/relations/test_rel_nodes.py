"""Tests for relational AST node types.

Covers construction, field access, visitor dispatch, immutability,
isinstance checks, and plan tree chaining for all 10 node types.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from mountainash.relations.core.relation_nodes import (
    RelationNode,
    ReadRelNode,
    ProjectRelNode,
    FilterRelNode,
    SortRelNode,
    FetchRelNode,
    JoinRelNode,
    AggregateRelNode,
    SetRelNode,
    ExtensionRelNode,
)
from mountainash.core.constants import (
    ProjectOperation,
    JoinType,
    SetType,
    SortField,
    ExtensionRelOperation,
    ExecutionTarget,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_df():
    """A stand-in for a real DataFrame."""
    return {"col_a": [1, 2, 3], "col_b": ["x", "y", "z"]}


@pytest.fixture
def read_node(mock_df):
    return ReadRelNode(dataframe=mock_df)


@pytest.fixture
def visitor():
    """Mock visitor with all visit methods."""
    v = MagicMock()
    v.visit_read_rel.return_value = "read"
    v.visit_project_rel.return_value = "project"
    v.visit_filter_rel.return_value = "filter"
    v.visit_sort_rel.return_value = "sort"
    v.visit_fetch_rel.return_value = "fetch"
    v.visit_join_rel.return_value = "join"
    v.visit_aggregate_rel.return_value = "aggregate"
    v.visit_set_rel.return_value = "set"
    v.visit_extension_rel.return_value = "extension"
    return v


# ---------------------------------------------------------------------------
# Construction and field access
# ---------------------------------------------------------------------------

class TestReadRelNode:
    def test_construction(self, mock_df):
        node = ReadRelNode(dataframe=mock_df)
        assert node.dataframe is mock_df

    def test_isinstance(self, read_node):
        assert isinstance(read_node, RelationNode)
        assert isinstance(read_node, ReadRelNode)

    def test_accept(self, read_node, visitor):
        result = read_node.accept(visitor)
        assert result == "read"
        visitor.visit_read_rel.assert_called_once_with(read_node)


class TestProjectRelNode:
    def test_construction(self, read_node):
        node = ProjectRelNode(
            input=read_node,
            expressions=["col_a", "col_b"],
            operation=ProjectOperation.SELECT,
        )
        assert node.input is read_node
        assert node.expressions == ["col_a", "col_b"]
        assert node.operation is ProjectOperation.SELECT
        assert node.rename_mapping is None

    def test_with_rename_mapping(self, read_node):
        node = ProjectRelNode(
            input=read_node,
            expressions=[],
            operation=ProjectOperation.RENAME,
            rename_mapping={"old": "new"},
        )
        assert node.rename_mapping == {"old": "new"}

    def test_isinstance(self, read_node):
        node = ProjectRelNode(
            input=read_node,
            expressions=[],
            operation=ProjectOperation.SELECT,
        )
        assert isinstance(node, RelationNode)

    def test_accept(self, read_node, visitor):
        node = ProjectRelNode(
            input=read_node,
            expressions=["col_a"],
            operation=ProjectOperation.SELECT,
        )
        result = node.accept(visitor)
        assert result == "project"
        visitor.visit_project_rel.assert_called_once_with(node)


class TestFilterRelNode:
    def test_construction(self, read_node):
        predicate = "col_a > 1"
        node = FilterRelNode(input=read_node, predicate=predicate)
        assert node.input is read_node
        assert node.predicate == predicate

    def test_isinstance(self, read_node):
        node = FilterRelNode(input=read_node, predicate="x")
        assert isinstance(node, RelationNode)

    def test_accept(self, read_node, visitor):
        node = FilterRelNode(input=read_node, predicate="x")
        result = node.accept(visitor)
        assert result == "filter"
        visitor.visit_filter_rel.assert_called_once_with(node)


class TestSortRelNode:
    def test_construction(self, read_node):
        sf = SortField(column="col_a", descending=True)
        node = SortRelNode(input=read_node, sort_fields=[sf])
        assert node.input is read_node
        assert len(node.sort_fields) == 1
        assert node.sort_fields[0].column == "col_a"
        assert node.sort_fields[0].descending is True

    def test_isinstance(self, read_node):
        node = SortRelNode(input=read_node, sort_fields=[])
        assert isinstance(node, RelationNode)

    def test_accept(self, read_node, visitor):
        node = SortRelNode(input=read_node, sort_fields=[])
        result = node.accept(visitor)
        assert result == "sort"
        visitor.visit_sort_rel.assert_called_once_with(node)


class TestFetchRelNode:
    def test_construction_defaults(self, read_node):
        node = FetchRelNode(input=read_node)
        assert node.offset == 0
        assert node.count is None
        assert node.from_end is False

    def test_construction_custom(self, read_node):
        node = FetchRelNode(input=read_node, offset=5, count=10, from_end=True)
        assert node.offset == 5
        assert node.count == 10
        assert node.from_end is True

    def test_isinstance(self, read_node):
        node = FetchRelNode(input=read_node)
        assert isinstance(node, RelationNode)

    def test_accept(self, read_node, visitor):
        node = FetchRelNode(input=read_node, count=10)
        result = node.accept(visitor)
        assert result == "fetch"
        visitor.visit_fetch_rel.assert_called_once_with(node)


class TestJoinRelNode:
    def test_construction_simple(self):
        left = ReadRelNode(dataframe="left_df")
        right = ReadRelNode(dataframe="right_df")
        node = JoinRelNode(
            left=left,
            right=right,
            join_type=JoinType.INNER,
            on=["key"],
        )
        assert node.left is left
        assert node.right is right
        assert node.join_type is JoinType.INNER
        assert node.on == ["key"]
        assert node.suffix == "_right"

    def test_construction_asymmetric_keys(self):
        left = ReadRelNode(dataframe="left_df")
        right = ReadRelNode(dataframe="right_df")
        node = JoinRelNode(
            left=left,
            right=right,
            join_type=JoinType.LEFT,
            left_on=["id"],
            right_on=["fk_id"],
        )
        assert node.left_on == ["id"]
        assert node.right_on == ["fk_id"]

    def test_construction_asof(self):
        left = ReadRelNode(dataframe="left_df")
        right = ReadRelNode(dataframe="right_df")
        node = JoinRelNode(
            left=left,
            right=right,
            join_type=JoinType.ASOF,
            on=["time"],
            strategy="backward",
            tolerance="1h",
            execute_on=ExecutionTarget.LEFT,
        )
        assert node.strategy == "backward"
        assert node.tolerance == "1h"
        assert node.execute_on is ExecutionTarget.LEFT

    def test_isinstance(self):
        left = ReadRelNode(dataframe="l")
        right = ReadRelNode(dataframe="r")
        node = JoinRelNode(left=left, right=right, join_type=JoinType.CROSS)
        assert isinstance(node, RelationNode)

    def test_accept(self, visitor):
        left = ReadRelNode(dataframe="l")
        right = ReadRelNode(dataframe="r")
        node = JoinRelNode(left=left, right=right, join_type=JoinType.INNER, on=["k"])
        result = node.accept(visitor)
        assert result == "join"
        visitor.visit_join_rel.assert_called_once_with(node)


class TestAggregateRelNode:
    def test_construction(self, read_node):
        node = AggregateRelNode(
            input=read_node,
            keys=["col_a"],
            measures=["sum(col_b)"],
        )
        assert node.input is read_node
        assert node.keys == ["col_a"]
        assert node.measures == ["sum(col_b)"]

    def test_isinstance(self, read_node):
        node = AggregateRelNode(input=read_node, keys=[], measures=[])
        assert isinstance(node, RelationNode)

    def test_accept(self, read_node, visitor):
        node = AggregateRelNode(input=read_node, keys=[], measures=[])
        result = node.accept(visitor)
        assert result == "aggregate"
        visitor.visit_aggregate_rel.assert_called_once_with(node)


class TestSetRelNode:
    def test_construction(self):
        r1 = ReadRelNode(dataframe="df1")
        r2 = ReadRelNode(dataframe="df2")
        node = SetRelNode(inputs=[r1, r2], set_type=SetType.UNION_ALL)
        assert len(node.inputs) == 2
        assert node.set_type is SetType.UNION_ALL

    def test_isinstance(self):
        node = SetRelNode(inputs=[], set_type=SetType.UNION_DISTINCT)
        assert isinstance(node, RelationNode)

    def test_accept(self, visitor):
        node = SetRelNode(inputs=[], set_type=SetType.UNION_ALL)
        result = node.accept(visitor)
        assert result == "set"
        visitor.visit_set_rel.assert_called_once_with(node)


class TestExtensionRelNode:
    def test_construction(self, read_node):
        node = ExtensionRelNode(
            input=read_node,
            operation=ExtensionRelOperation.DROP_NULLS,
        )
        assert node.input is read_node
        assert node.operation is ExtensionRelOperation.DROP_NULLS
        assert node.options == {}

    def test_construction_with_options(self, read_node):
        node = ExtensionRelNode(
            input=read_node,
            operation=ExtensionRelOperation.WITH_ROW_INDEX,
            options={"name": "idx", "offset": 0},
        )
        assert node.options == {"name": "idx", "offset": 0}

    def test_isinstance(self, read_node):
        node = ExtensionRelNode(
            input=read_node,
            operation=ExtensionRelOperation.EXPLODE,
        )
        assert isinstance(node, RelationNode)

    def test_accept(self, read_node, visitor):
        node = ExtensionRelNode(
            input=read_node,
            operation=ExtensionRelOperation.SAMPLE,
        )
        result = node.accept(visitor)
        assert result == "extension"
        visitor.visit_extension_rel.assert_called_once_with(node)


# ---------------------------------------------------------------------------
# Immutability (frozen)
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_read_node_frozen(self, read_node):
        with pytest.raises(Exception):
            read_node.dataframe = "something_else"

    def test_filter_node_frozen(self, read_node):
        node = FilterRelNode(input=read_node, predicate="x")
        with pytest.raises(Exception):
            node.predicate = "y"

    def test_project_node_frozen(self, read_node):
        node = ProjectRelNode(
            input=read_node,
            expressions=["a"],
            operation=ProjectOperation.SELECT,
        )
        with pytest.raises(Exception):
            node.operation = ProjectOperation.DROP

    def test_fetch_node_frozen(self, read_node):
        node = FetchRelNode(input=read_node, count=5)
        with pytest.raises(Exception):
            node.count = 10

    def test_join_node_frozen(self):
        left = ReadRelNode(dataframe="l")
        right = ReadRelNode(dataframe="r")
        node = JoinRelNode(left=left, right=right, join_type=JoinType.INNER)
        with pytest.raises(Exception):
            node.join_type = JoinType.LEFT


# ---------------------------------------------------------------------------
# Plan tree chaining
# ---------------------------------------------------------------------------

class TestPlanTreeChaining:
    def test_filter_on_read(self, read_node):
        filtered = FilterRelNode(input=read_node, predicate="col_a > 1")
        assert filtered.input is read_node
        assert isinstance(filtered.input, ReadRelNode)

    def test_project_on_filter(self, read_node):
        filtered = FilterRelNode(input=read_node, predicate="col_a > 1")
        projected = ProjectRelNode(
            input=filtered,
            expressions=["col_a"],
            operation=ProjectOperation.SELECT,
        )
        assert isinstance(projected.input, FilterRelNode)
        assert isinstance(projected.input.input, ReadRelNode)

    def test_deep_chain(self, mock_df):
        """Read -> Filter -> Sort -> Fetch -> Project — 5-level deep chain."""
        read = ReadRelNode(dataframe=mock_df)
        filtered = FilterRelNode(input=read, predicate="col_a > 0")
        sorted_ = SortRelNode(
            input=filtered,
            sort_fields=[SortField(column="col_a")],
        )
        fetched = FetchRelNode(input=sorted_, count=10)
        projected = ProjectRelNode(
            input=fetched,
            expressions=["col_a"],
            operation=ProjectOperation.SELECT,
        )

        # Walk the tree
        assert isinstance(projected, ProjectRelNode)
        assert isinstance(projected.input, FetchRelNode)
        assert isinstance(projected.input.input, SortRelNode)
        assert isinstance(projected.input.input.input, FilterRelNode)
        assert isinstance(projected.input.input.input.input, ReadRelNode)
        assert projected.input.input.input.input.dataframe is mock_df

    def test_join_chain(self):
        """Two reads joined then filtered."""
        left = ReadRelNode(dataframe="left")
        right = ReadRelNode(dataframe="right")
        joined = JoinRelNode(
            left=left,
            right=right,
            join_type=JoinType.INNER,
            on=["key"],
        )
        filtered = FilterRelNode(input=joined, predicate="val > 0")
        assert isinstance(filtered.input, JoinRelNode)
        assert isinstance(filtered.input.left, ReadRelNode)
        assert isinstance(filtered.input.right, ReadRelNode)

    def test_set_chain(self):
        """Union then project."""
        r1 = ReadRelNode(dataframe="df1")
        r2 = ReadRelNode(dataframe="df2")
        union = SetRelNode(inputs=[r1, r2], set_type=SetType.UNION_ALL)
        projected = ProjectRelNode(
            input=union,
            expressions=["col_a"],
            operation=ProjectOperation.SELECT,
        )
        assert isinstance(projected.input, SetRelNode)
        assert len(projected.input.inputs) == 2

    def test_extension_in_chain(self, mock_df):
        """Read -> Extension (drop_nulls) -> Filter."""
        read = ReadRelNode(dataframe=mock_df)
        cleaned = ExtensionRelNode(
            input=read,
            operation=ExtensionRelOperation.DROP_NULLS,
        )
        filtered = FilterRelNode(input=cleaned, predicate="col_a > 0")
        assert isinstance(filtered.input, ExtensionRelNode)
        assert isinstance(filtered.input.input, ReadRelNode)
