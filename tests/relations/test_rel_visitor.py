"""Tests for UnifiedRelationVisitor.

Uses mock backends that record calls to verify every visit_* method
dispatches correctly to the relation system.
"""

from __future__ import annotations

import pytest

from mountainash.core.constants import (
    JoinType,
    SetType,
    SortField,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
    RKEY_SUBSTRAIT_REL,
)
from mountainash.expressions.core.expression_nodes import ExpressionNode
from mountainash.expressions.core.expression_nodes.substrait.exn_literal import LiteralNode
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
from mountainash.relations.core.unified_visitor import UnifiedRelationVisitor


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

class MockRelationSystem:
    """Records all calls for verification."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def read(self, dataframe):
        self.calls.append(("read", dataframe))
        return f"read({dataframe})"

    def project_select(self, relation, exprs):
        self.calls.append(("project_select", relation, exprs))
        return f"project_select({relation})"

    def project_with_columns(self, relation, exprs):
        self.calls.append(("project_with_columns", relation, exprs))
        return f"project_with_columns({relation})"

    def project_drop(self, relation, exprs):
        self.calls.append(("project_drop", relation, exprs))
        return f"project_drop({relation})"

    def project_rename(self, relation, mapping):
        self.calls.append(("project_rename", relation, mapping))
        return f"project_rename({relation})"

    def filter(self, relation, predicate):
        self.calls.append(("filter", relation, predicate))
        return f"filter({relation})"

    def sort(self, relation, sort_fields):
        self.calls.append(("sort", relation, sort_fields))
        return f"sort({relation})"

    def fetch(self, relation, offset, count):
        self.calls.append(("fetch", relation, offset, count))
        return f"fetch({relation})"

    def fetch_from_end(self, relation, count):
        self.calls.append(("fetch_from_end", relation, count))
        return f"fetch_from_end({relation})"

    def join(self, left, right, *, join_type, on, left_on, right_on, suffix):
        self.calls.append(("join", left, right, join_type))
        return f"join({left},{right})"

    def join_asof(self, left, right, *, on, by, strategy, tolerance):
        self.calls.append(("join_asof", left, right, on, strategy))
        return f"join_asof({left},{right})"

    def aggregate(self, relation, keys, measures):
        self.calls.append(("aggregate", relation, keys, measures))
        return f"aggregate({relation})"

    def distinct(self, relation, keys):
        self.calls.append(("distinct", relation, keys))
        return f"distinct({relation})"

    def union_all(self, relations):
        self.calls.append(("union_all", relations))
        return f"union_all({relations})"

    def drop_nulls(self, relation, **options):
        self.calls.append(("drop_nulls", relation, options))
        return f"drop_nulls({relation})"

    def sample(self, relation, **options):
        self.calls.append(("sample", relation, options))
        return f"sample({relation})"


class MockExpressionVisitor:
    """Returns a string representation for any expression node."""

    def visit(self, node):
        return f"compiled({node})"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def backend():
    return MockRelationSystem()


@pytest.fixture
def expr_visitor():
    return MockExpressionVisitor()


@pytest.fixture
def visitor(backend, expr_visitor):
    return UnifiedRelationVisitor(backend, expr_visitor)


def _read_node(name: str = "df") -> ReadRelNode:
    """Helper to create a read node with a string placeholder."""
    return ReadRelNode(dataframe=name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestReadRel:
    def test_visit_read(self, visitor, backend):
        node = _read_node("my_table")
        result = visitor.visit(node)
        assert result == "read(my_table)"
        assert backend.calls == [("read", "my_table")]


class TestFilterRel:
    def test_visit_filter_with_expression_node(self, visitor, backend):
        """ExpressionNode predicates are compiled via the expression visitor."""
        predicate = LiteralNode(value=True)
        node = FilterRelNode(input=_read_node(), predicate=predicate)
        result = visitor.visit(node)
        assert result == "filter(read(df))"
        assert backend.calls[0] == ("read", "df")
        assert backend.calls[1][0] == "filter"
        # The predicate was compiled
        assert backend.calls[1][2] == f"compiled({predicate})"

    def test_visit_filter_with_passthrough(self, visitor, backend):
        """Non-ExpressionNode predicates are passed through as-is."""
        node = FilterRelNode(input=_read_node(), predicate="native_predicate")
        visitor.visit(node)
        assert backend.calls[1][2] == "native_predicate"


class TestProjectRel:
    def test_project_select(self, visitor, backend):
        node = ProjectRelNode(
            input=_read_node(),
            expressions=["col_a", "col_b"],
            operation=RKEY_SUBSTRAIT_REL.PROJECT_SELECT,
        )
        result = visitor.visit(node)
        assert result == "project_select(read(df))"
        assert backend.calls[1][0] == "project_select"

    def test_project_with_columns(self, visitor, backend):
        node = ProjectRelNode(
            input=_read_node(),
            expressions=["col_a"],
            operation=RKEY_SUBSTRAIT_REL.PROJECT_WITH_COLUMNS,
        )
        result = visitor.visit(node)
        assert result == "project_with_columns(read(df))"

    def test_project_drop(self, visitor, backend):
        node = ProjectRelNode(
            input=_read_node(),
            expressions=["col_a"],
            operation=RKEY_SUBSTRAIT_REL.PROJECT_DROP,
        )
        result = visitor.visit(node)
        assert result == "project_drop(read(df))"

    def test_project_rename(self, visitor, backend):
        mapping = {"old_name": "new_name"}
        node = ProjectRelNode(
            input=_read_node(),
            expressions=[],
            operation=RKEY_SUBSTRAIT_REL.PROJECT_RENAME,
            rename_mapping=mapping,
        )
        result = visitor.visit(node)
        assert result == "project_rename(read(df))"
        assert backend.calls[1] == ("project_rename", "read(df)", mapping)

    def test_project_compiles_expression_nodes(self, visitor, backend):
        """ExpressionNode items in expressions list are compiled."""
        lit_node = LiteralNode(value=42)
        node = ProjectRelNode(
            input=_read_node(),
            expressions=[lit_node, "raw_string"],
            operation=RKEY_SUBSTRAIT_REL.PROJECT_SELECT,
        )
        visitor.visit(node)
        compiled_exprs = backend.calls[1][2]
        assert compiled_exprs[0] == f"compiled({lit_node})"
        assert compiled_exprs[1] == "raw_string"


class TestSortRel:
    def test_visit_sort(self, visitor, backend):
        fields = [SortField(column="price", descending=True)]
        node = SortRelNode(input=_read_node(), sort_fields=fields)
        result = visitor.visit(node)
        assert result == "sort(read(df))"
        assert backend.calls[1] == ("sort", "read(df)", fields)


class TestFetchRel:
    def test_fetch_head(self, visitor, backend):
        node = FetchRelNode(input=_read_node(), offset=0, count=10)
        result = visitor.visit(node)
        assert result == "fetch(read(df))"
        assert backend.calls[1] == ("fetch", "read(df)", 0, 10)

    def test_fetch_tail(self, visitor, backend):
        node = FetchRelNode(input=_read_node(), count=5, from_end=True)
        result = visitor.visit(node)
        assert result == "fetch_from_end(read(df))"
        assert backend.calls[1] == ("fetch_from_end", "read(df)", 5)


class TestJoinRel:
    def test_inner_join(self, visitor, backend):
        node = JoinRelNode(
            left=_read_node("left"),
            right=_read_node("right"),
            join_type=JoinType.INNER,
            on=["id"],
        )
        result = visitor.visit(node)
        assert result == "join(read(left),read(right))"
        assert backend.calls[2] == ("join", "read(left)", "read(right)", JoinType.INNER)

    def test_asof_join(self, visitor, backend):
        node = JoinRelNode(
            left=_read_node("left"),
            right=_read_node("right"),
            join_type=JoinType.ASOF,
            on=["timestamp"],
            strategy="backward",
            tolerance="1h",
        )
        result = visitor.visit(node)
        assert result == "join_asof(read(left),read(right))"
        assert backend.calls[2] == (
            "join_asof", "read(left)", "read(right)", "timestamp", "backward"
        )

    def test_asof_join_with_left_on(self, visitor, backend):
        """When on is empty, asof falls back to left_on[0]."""
        node = JoinRelNode(
            left=_read_node("left"),
            right=_read_node("right"),
            join_type=JoinType.ASOF,
            left_on=["ts_left"],
            right_on=["ts_right"],
        )
        visitor.visit(node)
        assert backend.calls[2][3] == "ts_left"


class TestAggregateRel:
    def test_aggregate_with_measures(self, visitor, backend):
        lit_node = LiteralNode(value="sum_expr")
        node = AggregateRelNode(
            input=_read_node(),
            keys=["group_col"],
            measures=[lit_node],
        )
        result = visitor.visit(node)
        assert result == "aggregate(read(df))"
        assert backend.calls[1][0] == "aggregate"
        # Measures are compiled
        assert backend.calls[1][3] == [f"compiled({lit_node})"]

    def test_aggregate_without_measures_is_distinct(self, visitor, backend):
        node = AggregateRelNode(
            input=_read_node(),
            keys=["group_col"],
            measures=[],
        )
        result = visitor.visit(node)
        assert result == "distinct(read(df))"
        assert backend.calls[1] == ("distinct", "read(df)", ["group_col"])


class TestSetRel:
    def test_union_all(self, visitor, backend):
        node = SetRelNode(
            inputs=[_read_node("a"), _read_node("b")],
            set_type=SetType.UNION_ALL,
        )
        result = visitor.visit(node)
        assert result == "union_all(['read(a)', 'read(b)'])"
        assert backend.calls[2][0] == "union_all"


class TestExtensionRel:
    def test_drop_nulls(self, visitor, backend):
        node = ExtensionRelNode(
            input=_read_node(),
            operation=RKEY_MOUNTAINASH_REL.DROP_NULLS,
            options={"subset": ["col_a"]},
        )
        result = visitor.visit(node)
        assert result == "drop_nulls(read(df))"
        assert backend.calls[1] == ("drop_nulls", "read(df)", {"subset": ["col_a"]})

    def test_sample(self, visitor, backend):
        node = ExtensionRelNode(
            input=_read_node(),
            operation=RKEY_MOUNTAINASH_REL.SAMPLE,
            options={"n": 100},
        )
        result = visitor.visit(node)
        assert result == "sample(read(df))"
        assert backend.calls[1] == ("sample", "read(df)", {"n": 100})


class TestChainedPlan:
    def test_read_filter_sort_head(self, visitor, backend):
        """Verify call order for a chained plan: read -> filter -> sort -> head."""
        read = _read_node("orders")
        filtered = FilterRelNode(input=read, predicate="active == True")
        sorted_node = SortRelNode(
            input=filtered,
            sort_fields=[SortField(column="date", descending=True)],
        )
        head = FetchRelNode(input=sorted_node, offset=0, count=10)

        result = visitor.visit(head)

        # Should have 4 calls in order
        assert len(backend.calls) == 4
        assert backend.calls[0][0] == "read"
        assert backend.calls[1][0] == "filter"
        assert backend.calls[2][0] == "sort"
        assert backend.calls[3][0] == "fetch"

        # Final result is the outermost operation
        assert result == "fetch(sort(filter(read(orders))))"



class TestExpressionChildrenWalker:
    """_expression_children / _iter_function_keys /
    _present_expression_function_keys (backlog item 88): explicit,
    Any-payload-safe expression-AST child extraction used to disambiguate
    enrich_materialization candidates."""

    def test_scalar_function_options_are_never_traversed(self):
        """The exact round-2 false-positive proof-of-concept: an
        ExpressionNode stuffed into another node's raw `options: Dict[str,
        Any]` payload must never surface as a structurally-present key --
        options are opaque per arguments-vs-options.md."""
        from mountainash.expressions.core.expression_nodes import (
            LiteralNode, ScalarFunctionNode,
        )
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
        )
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _iter_function_keys,
        )

        smuggled = ScalarFunctionNode(function_key=FK_STR.SPLIT, arguments=[])
        outer = ScalarFunctionNode(
            function_key=FK_STR.UPPER,
            arguments=[LiteralNode(value="x")],
            options={"smuggled": smuggled},
        )
        keys = set(_iter_function_keys(outer))
        assert keys == {FK_STR.UPPER}
        assert FK_STR.SPLIT not in keys

    def test_scalar_function_arguments_are_collected(self):
        from mountainash.expressions.core.expression_nodes import (
            FieldReferenceNode, LiteralNode, ScalarFunctionNode,
        )
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
            FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
        )
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _iter_function_keys,
        )

        inner = ScalarFunctionNode(
            function_key=FK_LIST.CONTAINS,
            arguments=[FieldReferenceNode(field="tags"), LiteralNode(value=2)],
        )
        outer = ScalarFunctionNode(function_key=FK_STR.SPLIT, arguments=[inner])
        assert set(_iter_function_keys(outer)) == {FK_STR.SPLIT, FK_LIST.CONTAINS}

    def test_cast_node_input_collected(self):
        from mountainash.expressions.core.expression_nodes import CastNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
        )
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _iter_function_keys,
        )

        inner = ScalarFunctionNode(function_key=FK_STR.UPPER, arguments=[])
        cast = CastNode(input=inner, target_type="string")
        assert set(_iter_function_keys(cast)) == {FK_STR.UPPER}

    def test_if_then_conditions_and_else_collected(self):
        from mountainash.expressions.core.expression_nodes import IfThenNode, LiteralNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_COMPARISON as FK_CMP,
            FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
        )
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _iter_function_keys,
        )

        cond = ScalarFunctionNode(function_key=FK_CMP.GT, arguments=[])
        result = ScalarFunctionNode(function_key=FK_STR.UPPER, arguments=[])
        else_clause = LiteralNode(value="x")
        node = IfThenNode(conditions=[(cond, result)], else_clause=else_clause)
        assert set(_iter_function_keys(node)) == {FK_CMP.GT, FK_STR.UPPER}

    def test_singular_or_list_value_and_options_collected(self):
        from mountainash.expressions.core.expression_nodes import (
            LiteralNode, ScalarFunctionNode, SingularOrListNode,
        )
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
            FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
        )
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _iter_function_keys,
        )

        node = SingularOrListNode(
            value=ScalarFunctionNode(function_key=FK_STR.UPPER, arguments=[]),
            options=[
                LiteralNode(value="active"),
                ScalarFunctionNode(function_key=FK_LIST.CONTAINS, arguments=[]),
            ],
        )
        # value AND every options element are actually reached -- both
        # function-bearing children must surface, not just one.
        assert set(_iter_function_keys(node)) == {FK_STR.UPPER, FK_LIST.CONTAINS}

    def test_window_function_arguments_and_partition_by_collected(self):
        from mountainash.expressions.core.expression_nodes import (
            FieldReferenceNode, ScalarFunctionNode, WindowFunctionNode, WindowSpec,
        )
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
            FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
        )
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _iter_function_keys,
        )

        node = WindowFunctionNode(
            arguments=[ScalarFunctionNode(function_key=FK_STR.UPPER, arguments=[])],
            window_spec=WindowSpec(
                partition_by=[
                    ScalarFunctionNode(function_key=FK_LIST.CONTAINS, arguments=[]),
                    FieldReferenceNode(field="grp"),  # non-ExpressionNode-key noise, ignored
                ]
            ),
        )
        assert set(_iter_function_keys(node)) == {FK_STR.UPPER, FK_LIST.CONTAINS}

    def test_over_node_expression_and_partition_by_collected(self):
        from mountainash.expressions.core.expression_nodes import (
            OverNode, ScalarFunctionNode, WindowSpec,
        )
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
            FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
        )
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _iter_function_keys,
        )

        node = OverNode(
            expression=ScalarFunctionNode(function_key=FK_ARITH.ADD, arguments=[]),
            window_spec=WindowSpec(
                partition_by=[ScalarFunctionNode(function_key=FK_STR.UPPER, arguments=[])]
            ),
        )
        assert set(_iter_function_keys(node)) == {FK_ARITH.ADD, FK_STR.UPPER}

    def test_present_expression_function_keys_filters_to_expression_args(self):
        """Only EXPRESSION/EXPRESSION_LIST-kind op.args are consulted --
        matches PROJECT_SELECT's real registration shape."""
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
            FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
        )
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_SUBSTRAIT_REL,
        )
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            RelationOperationRegistry,
        )
        from mountainash.relations.core.relation_nodes import ProjectRelNode
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _present_expression_function_keys,
        )

        op = RelationOperationRegistry.get(RKEY_SUBSTRAIT_REL.PROJECT_SELECT)
        node = ProjectRelNode(
            input=_read_node(),
            expressions=[
                ScalarFunctionNode(function_key=FK_STR.SPLIT, arguments=[]),
                ScalarFunctionNode(function_key=FK_LIST.CONTAINS, arguments=[]),
            ],
            operation=RKEY_SUBSTRAIT_REL.PROJECT_SELECT,
        )
        assert _present_expression_function_keys(node, op) == frozenset(
            {FK_STR.SPLIT, FK_LIST.CONTAINS}
        )

    def test_no_cycle_recursion_error_on_self_referential_options(self):
        """Defensive: a crafted self-referential options dict (round-2's
        RecursionError proof) must not be reachable at all since options is
        never traversed -- confirms the walker terminates cleanly."""
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
        )
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _iter_function_keys,
        )

        cyclic: dict = {}
        cyclic["self"] = cyclic
        node = ScalarFunctionNode(function_key=FK_STR.UPPER, arguments=[], options=cyclic)
        assert list(_iter_function_keys(node)) == [FK_STR.UPPER]


class TestMinimalBackendConstructionRegression:
    """Item 89 round-2: the per-ref identity resolver/swap logic added to
    RelationDAG._compile_with_refs lives entirely in dag.py and never
    reads backend_type/dialect off visitor.backend directly -- confirm
    UnifiedRelationVisitor itself still tolerates a relation system
    lacking those attributes entirely (unrelated to any DAG machinery)."""

    def test_visitor_constructs_and_dispatches_without_backend_type_or_dialect(
        self, backend, expr_visitor
    ):
        assert not hasattr(backend, "backend_type")
        assert not hasattr(backend, "dialect")
        visitor = UnifiedRelationVisitor(backend, expr_visitor)
        result = visitor.visit(ReadRelNode(dataframe="df"))
        assert result == "read(df)"