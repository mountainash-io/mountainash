"""Expression traversal boundaries used by relation error enrichment."""

from __future__ import annotations

from mountainash.relations.core.relation_nodes import ReadRelNode


def _read_node(name: str = "df") -> ReadRelNode:
    """Helper to create a read node with a string placeholder."""
    return ReadRelNode(dataframe=name)


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
            _present_operation_keys,
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
        assert _present_operation_keys(node, op) == frozenset(
            {FK_STR.SPLIT, FK_LIST.CONTAINS, RKEY_SUBSTRAIT_REL.PROJECT_SELECT}
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

