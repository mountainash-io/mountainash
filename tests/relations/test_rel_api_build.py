"""Tests for the Relation fluent API — build phase only.

These tests verify that each API method produces the correct AST node type
and fields.  No backend execution occurs.
"""

from __future__ import annotations

import pytest

from mountainash.core.constants import (
    ExecutionTarget,
    ExtensionRelOperation,
    JoinType,
    ProjectOperation,
    SetType,
    SortField,
)
from mountainash.relations.core.relation_api import Relation, relation, concat
from mountainash.relations.core.relation_api.grouped_relation import GroupedRelation
from mountainash.relations.core.relation_nodes import (
    AggregateRelNode,
    ExtensionRelNode,
    FetchRelNode,
    FilterRelNode,
    JoinRelNode,
    ProjectRelNode,
    ReadRelNode,
    SetRelNode,
    SortRelNode,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rel() -> Relation:
    """A basic Relation wrapping a dummy string data source."""
    return relation("df")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class TestRelationFactory:
    def test_relation_creates_read_node(self):
        r = relation("df")
        assert isinstance(r, Relation)
        assert isinstance(r._node, ReadRelNode)
        assert r._node.dataframe == "df"


# ---------------------------------------------------------------------------
# Projection methods
# ---------------------------------------------------------------------------

class TestSelect:
    def test_select(self, rel: Relation):
        r = rel.select("a", "b")
        node = r._node
        assert isinstance(node, ProjectRelNode)
        assert node.operation == ProjectOperation.SELECT
        assert node.expressions == ["a", "b"]
        assert isinstance(node.input, ReadRelNode)


class TestWithColumns:
    def test_with_columns(self, rel: Relation):
        r = rel.with_columns("expr1", "expr2")
        node = r._node
        assert isinstance(node, ProjectRelNode)
        assert node.operation == ProjectOperation.WITH_COLUMNS
        assert node.expressions == ["expr1", "expr2"]


class TestDrop:
    def test_drop(self, rel: Relation):
        r = rel.drop("x", "y")
        node = r._node
        assert isinstance(node, ProjectRelNode)
        assert node.operation == ProjectOperation.DROP
        assert node.expressions == ["x", "y"]


class TestRename:
    def test_rename(self, rel: Relation):
        r = rel.rename({"old": "new"})
        node = r._node
        assert isinstance(node, ProjectRelNode)
        assert node.operation == ProjectOperation.RENAME
        assert node.rename_mapping == {"old": "new"}
        assert node.expressions == []


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------

class TestFilter:
    def test_single_predicate(self, rel: Relation):
        r = rel.filter("pred")
        node = r._node
        assert isinstance(node, FilterRelNode)
        assert node.predicate == "pred"
        assert isinstance(node.input, ReadRelNode)

    def test_multiple_predicates_chain(self, rel: Relation):
        r = rel.filter("p1", "p2")
        # Outermost is the last predicate
        assert isinstance(r._node, FilterRelNode)
        assert r._node.predicate == "p2"
        inner = r._node.input
        assert isinstance(inner, FilterRelNode)
        assert inner.predicate == "p1"
        assert isinstance(inner.input, ReadRelNode)


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------

class TestSort:
    def test_single_column(self, rel: Relation):
        r = rel.sort("age")
        node = r._node
        assert isinstance(node, SortRelNode)
        assert len(node.sort_fields) == 1
        assert node.sort_fields[0] == SortField(column="age", descending=False)

    def test_multiple_columns_mixed_descending(self, rel: Relation):
        r = rel.sort("a", "b", descending=[False, True])
        node = r._node
        assert isinstance(node, SortRelNode)
        assert len(node.sort_fields) == 2
        assert node.sort_fields[0] == SortField(column="a", descending=False)
        assert node.sort_fields[1] == SortField(column="b", descending=True)

    def test_descending_bool_broadcast(self, rel: Relation):
        r = rel.sort("x", "y", descending=True)
        node = r._node
        assert all(sf.descending for sf in node.sort_fields)

    def test_mismatched_descending_raises(self, rel: Relation):
        with pytest.raises(ValueError, match="Length of descending"):
            rel.sort("a", "b", descending=[True])


# ---------------------------------------------------------------------------
# Fetch (head / tail / slice)
# ---------------------------------------------------------------------------

class TestFetch:
    def test_head(self, rel: Relation):
        r = rel.head(10)
        node = r._node
        assert isinstance(node, FetchRelNode)
        assert node.count == 10
        assert node.from_end is False
        assert node.offset == 0

    def test_tail(self, rel: Relation):
        r = rel.tail(5)
        node = r._node
        assert isinstance(node, FetchRelNode)
        assert node.count == 5
        assert node.from_end is True

    def test_slice(self, rel: Relation):
        r = rel.slice(10, 20)
        node = r._node
        assert isinstance(node, FetchRelNode)
        assert node.offset == 10
        assert node.count == 20


# ---------------------------------------------------------------------------
# Joins
# ---------------------------------------------------------------------------

class TestJoin:
    def test_inner_join_on(self, rel: Relation):
        other = relation("other_df")
        r = rel.join(other, on="id")
        node = r._node
        assert isinstance(node, JoinRelNode)
        assert node.join_type == JoinType.INNER
        assert node.on == ["id"]
        assert isinstance(node.right, ReadRelNode)
        assert node.right.dataframe == "other_df"

    def test_left_join_raw_data(self, rel: Relation):
        r = rel.join("raw_data", on="id", how="left")
        node = r._node
        assert isinstance(node, JoinRelNode)
        assert node.join_type == JoinType.LEFT
        assert isinstance(node.right, ReadRelNode)
        assert node.right.dataframe == "raw_data"

    def test_join_left_on_right_on(self, rel: Relation):
        other = relation("other")
        r = rel.join(other, left_on="a", right_on="b")
        node = r._node
        assert node.left_on == ["a"]
        assert node.right_on == ["b"]

    def test_join_execute_on(self, rel: Relation):
        other = relation("other")
        r = rel.join(other, on="id", execute_on=ExecutionTarget.LEFT)
        assert r._node.execute_on == ExecutionTarget.LEFT

    def test_join_asof(self, rel: Relation):
        other = relation("other")
        r = rel.join_asof(other, on="ts", strategy="forward", tolerance=5)
        node = r._node
        assert isinstance(node, JoinRelNode)
        assert node.join_type == JoinType.ASOF
        assert node.strategy == "forward"
        assert node.tolerance == 5
        assert node.on == ["ts"]


# ---------------------------------------------------------------------------
# Aggregation / unique
# ---------------------------------------------------------------------------

class TestGroupBy:
    def test_group_by_returns_grouped(self, rel: Relation):
        g = rel.group_by("cat")
        assert isinstance(g, GroupedRelation)
        assert g._keys == ["cat"]

    def test_group_by_agg(self, rel: Relation):
        r = rel.group_by("cat").agg("e1", "e2")
        node = r._node
        assert isinstance(node, AggregateRelNode)
        assert node.keys == ["cat"]
        assert node.measures == ["e1", "e2"]
        assert isinstance(node.input, ReadRelNode)


class TestUnique:
    def test_unique(self, rel: Relation):
        r = rel.unique("id")
        node = r._node
        assert isinstance(node, AggregateRelNode)
        assert node.keys == ["id"]
        assert node.measures == []


# ---------------------------------------------------------------------------
# Set operations
# ---------------------------------------------------------------------------

class TestConcat:
    def test_concat(self):
        r1 = relation("a")
        r2 = relation("b")
        r = concat([r1, r2])
        node = r._node
        assert isinstance(node, SetRelNode)
        assert node.set_type == SetType.UNION_ALL
        assert len(node.inputs) == 2
        assert all(isinstance(n, ReadRelNode) for n in node.inputs)


# ---------------------------------------------------------------------------
# Extension operations
# ---------------------------------------------------------------------------

class TestExtensionOps:
    def test_drop_nulls(self, rel: Relation):
        r = rel.drop_nulls(subset=["a"])
        node = r._node
        assert isinstance(node, ExtensionRelNode)
        assert node.operation == ExtensionRelOperation.DROP_NULLS
        assert node.options == {"subset": ["a"]}

    def test_drop_nulls_no_subset(self, rel: Relation):
        r = rel.drop_nulls()
        assert r._node.options == {}

    def test_with_row_index(self, rel: Relation):
        r = rel.with_row_index(name="idx")
        node = r._node
        assert isinstance(node, ExtensionRelNode)
        assert node.operation == ExtensionRelOperation.WITH_ROW_INDEX
        assert node.options == {"name": "idx"}

    def test_explode(self, rel: Relation):
        r = rel.explode("tags")
        node = r._node
        assert isinstance(node, ExtensionRelNode)
        assert node.operation == ExtensionRelOperation.EXPLODE
        assert node.options == {"columns": ["tags"]}

    def test_sample_n(self, rel: Relation):
        r = rel.sample(n=100)
        node = r._node
        assert isinstance(node, ExtensionRelNode)
        assert node.operation == ExtensionRelOperation.SAMPLE
        assert node.options == {"n": 100}

    def test_sample_fraction(self, rel: Relation):
        r = rel.sample(fraction=0.5)
        assert r._node.options == {"fraction": 0.5}

    def test_top_k(self, rel: Relation):
        r = rel.top_k(5, by="score")
        node = r._node
        assert isinstance(node, ExtensionRelNode)
        assert node.operation == ExtensionRelOperation.TOP_K
        assert node.options["k"] == 5
        assert node.options["by"] == ["score"]

    def test_unpivot(self, rel: Relation):
        r = rel.unpivot(on=["a", "b"], index="id")
        node = r._node
        assert isinstance(node, ExtensionRelNode)
        assert node.operation == ExtensionRelOperation.UNPIVOT
        assert node.options["on"] == ["a", "b"]
        assert node.options["index"] == ["id"]

    def test_pivot(self, rel: Relation):
        r = rel.pivot(on="cat", index="id", values="val")
        node = r._node
        assert isinstance(node, ExtensionRelNode)
        assert node.operation == ExtensionRelOperation.PIVOT
        assert node.options["on"] == ["cat"]


# ---------------------------------------------------------------------------
# Chaining
# ---------------------------------------------------------------------------

class TestChaining:
    def test_filter_sort_head(self, rel: Relation):
        r = rel.filter("p").sort("n").head(10)
        # Outermost: FetchRelNode
        assert isinstance(r._node, FetchRelNode)
        assert r._node.count == 10
        # Next: SortRelNode
        sort_node = r._node.input
        assert isinstance(sort_node, SortRelNode)
        # Next: FilterRelNode
        filter_node = sort_node.input
        assert isinstance(filter_node, FilterRelNode)
        assert filter_node.predicate == "p"
        # Leaf: ReadRelNode
        assert isinstance(filter_node.input, ReadRelNode)


# ---------------------------------------------------------------------------
# Pipe
# ---------------------------------------------------------------------------

class TestPipe:
    def test_pipe_calls_function(self, rel: Relation):
        def my_func(r: Relation, x: int) -> int:
            return x + 1

        result = rel.pipe(my_func, 5)
        assert result == 6


# ---------------------------------------------------------------------------
# RelationBase helpers
# ---------------------------------------------------------------------------

class TestFindLeafReadNode:
    def test_finds_through_project(self, rel: Relation):
        r = rel.select("a")
        leaf = Relation._find_leaf_read_node(r._node)
        assert isinstance(leaf, ReadRelNode)

    def test_finds_through_join(self):
        r1 = relation("left")
        r2 = relation("right")
        r = r1.join(r2, on="id")
        leaf = Relation._find_leaf_read_node(r._node)
        assert leaf.dataframe == "left"

    def test_finds_through_set(self):
        r1 = relation("a")
        r2 = relation("b")
        r = concat([r1, r2])
        leaf = Relation._find_leaf_read_node(r._node)
        assert leaf.dataframe == "a"

    def test_raises_on_bare_read(self):
        # ReadRelNode itself is a valid leaf
        node = ReadRelNode(dataframe="x")
        leaf = Relation._find_leaf_read_node(node)
        assert leaf.dataframe == "x"
