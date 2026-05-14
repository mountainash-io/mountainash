from __future__ import annotations

from datetime import date, datetime
from typing import Any

from mountainash_pipelines.core.capabilities import PaginationHint, PushedPredicates
from mountainash_pipelines.integration.relation import PipelineStepRelNode


def apply_pushdown(node: Any) -> Any:
    from mountainash.relations.core.relation_nodes.substrait.reln_filter import FilterRelNode
    from mountainash.relations.core.relation_nodes.substrait.reln_project import ProjectRelNode
    from mountainash.relations.core.relation_nodes.substrait.reln_fetch import FetchRelNode

    if isinstance(node, FilterRelNode) and isinstance(node.input, PipelineStepRelNode):
        return _pushdown_filter(node)

    if isinstance(node, ProjectRelNode) and isinstance(node.input, PipelineStepRelNode):
        return _pushdown_project(node)

    if isinstance(node, FetchRelNode) and isinstance(node.input, PipelineStepRelNode):
        return _pushdown_fetch(node)

    return node


def _pushdown_filter(node: Any) -> Any:
    from mountainash.relations.core.relation_nodes.substrait.reln_filter import FilterRelNode

    pipeline_node: PipelineStepRelNode = node.input
    caps = pipeline_node.capabilities

    if caps.date_range is None:
        return node

    predicates = _extract_date_predicates(node.predicate, caps.date_range.column)

    if predicates.date_start is None and predicates.date_end is None:
        return node

    merged = PushedPredicates(
        date_start=predicates.date_start or pipeline_node.pushed_predicates.date_start,
        date_end=predicates.date_end or pipeline_node.pushed_predicates.date_end,
        limit=pipeline_node.pushed_predicates.limit,
        selected_fields=pipeline_node.pushed_predicates.selected_fields,
        pagination_hint=pipeline_node.pushed_predicates.pagination_hint,
    )

    hint = synthesise_pagination_hint(merged)
    if hint is not None:
        merged = PushedPredicates(
            date_start=merged.date_start,
            date_end=merged.date_end,
            limit=merged.limit,
            selected_fields=merged.selected_fields,
            pagination_hint=hint,
        )

    new_pipeline_node = PipelineStepRelNode(
        step_name=pipeline_node.step_name,
        pipeline=pipeline_node.pipeline,
        data_key=pipeline_node.data_key,
        executor=pipeline_node.executor,
        capabilities=pipeline_node.capabilities,
        pushed_predicates=merged,
    )

    return FilterRelNode(input=new_pipeline_node, predicate=node.predicate)


def _pushdown_project(node: Any) -> Any:
    from mountainash.relations.core.relation_nodes.substrait.reln_project import ProjectRelNode
    from mountainash.core.constants import ProjectOperation
    from mountainash.expressions.core.expression_nodes.substrait.exn_field_reference import FieldReferenceNode

    pipeline_node: PipelineStepRelNode = node.input
    caps = pipeline_node.capabilities

    if caps.field_selection is None:
        return node

    if node.operation != ProjectOperation.SELECT:
        return node

    requested = [
        expr.field for expr in node.expressions
        if isinstance(expr, FieldReferenceNode)
    ]
    if not requested:
        return node

    pushable = set(requested) & set(caps.field_selection.available_fields)
    if not pushable:
        return node

    if caps.field_selection.always_included:
        pushable |= set(caps.field_selection.always_included)

    merged = PushedPredicates(
        date_start=pipeline_node.pushed_predicates.date_start,
        date_end=pipeline_node.pushed_predicates.date_end,
        limit=pipeline_node.pushed_predicates.limit,
        selected_fields=sorted(pushable),
        pagination_hint=pipeline_node.pushed_predicates.pagination_hint,
    )

    new_pipeline_node = PipelineStepRelNode(
        step_name=pipeline_node.step_name,
        pipeline=pipeline_node.pipeline,
        data_key=pipeline_node.data_key,
        executor=pipeline_node.executor,
        capabilities=pipeline_node.capabilities,
        pushed_predicates=merged,
    )

    return ProjectRelNode(
        input=new_pipeline_node,
        expressions=node.expressions,
        operation=node.operation,
        rename_mapping=node.rename_mapping,
    )


def _pushdown_fetch(node: Any) -> Any:
    from mountainash.relations.core.relation_nodes.substrait.reln_fetch import FetchRelNode

    pipeline_node: PipelineStepRelNode = node.input
    caps = pipeline_node.capabilities

    if caps.limit is None:
        return node

    if node.from_end:
        return node

    count = node.count
    if count is None:
        return node

    if caps.limit.max_limit is not None and count > caps.limit.max_limit:
        count = caps.limit.max_limit

    merged = PushedPredicates(
        date_start=pipeline_node.pushed_predicates.date_start,
        date_end=pipeline_node.pushed_predicates.date_end,
        limit=count,
        selected_fields=pipeline_node.pushed_predicates.selected_fields,
        pagination_hint=pipeline_node.pushed_predicates.pagination_hint,
    )

    hint = synthesise_pagination_hint(merged)
    if hint is not None:
        merged = PushedPredicates(
            date_start=merged.date_start,
            date_end=merged.date_end,
            limit=merged.limit,
            selected_fields=merged.selected_fields,
            pagination_hint=hint,
        )

    new_pipeline_node = PipelineStepRelNode(
        step_name=pipeline_node.step_name,
        pipeline=pipeline_node.pipeline,
        data_key=pipeline_node.data_key,
        executor=pipeline_node.executor,
        capabilities=pipeline_node.capabilities,
        pushed_predicates=merged,
    )

    return FetchRelNode(
        input=new_pipeline_node,
        count=node.count,
        offset=node.offset,
        from_end=node.from_end,
    )


def _extract_date_predicates(expr: Any, column: str) -> PushedPredicates:
    from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import ScalarFunctionNode
    from mountainash.expressions.core.expression_nodes.substrait.exn_field_reference import FieldReferenceNode
    from mountainash.expressions.core.expression_nodes.substrait.exn_literal import LiteralNode
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI

    # Unwrap expression API wrappers (e.g. BooleanExpressionAPI) to get the node
    if isinstance(expr, BaseExpressionAPI):
        expr = expr._node

    if not isinstance(expr, ScalarFunctionNode):
        return PushedPredicates()

    fk = expr.function_key

    # Handle BETWEEN: 3 arguments (column, low, high)
    if fk == FKEY_SUBSTRAIT_SCALAR_COMPARISON.BETWEEN and len(expr.arguments) == 3:
        col_node, low_node, high_node = expr.arguments
        if isinstance(col_node, FieldReferenceNode) and col_node.field == column:
            low_val = _literal_to_date(low_node) if isinstance(low_node, LiteralNode) else None
            high_val = _literal_to_date(high_node) if isinstance(high_node, LiteralNode) else None
            return PushedPredicates(date_start=low_val, date_end=high_val)
        return PushedPredicates()

    # Handle binary comparisons: 2 arguments (column, value)
    if len(expr.arguments) == 2:
        left, right = expr.arguments

        if isinstance(left, FieldReferenceNode) and left.field == column and isinstance(right, LiteralNode):
            lit_date = _literal_to_date(right)
            if lit_date is None:
                return PushedPredicates()

            if fk in (FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT, FKEY_SUBSTRAIT_SCALAR_COMPARISON.GTE):
                return PushedPredicates(date_start=lit_date)
            elif fk in (FKEY_SUBSTRAIT_SCALAR_COMPARISON.LT, FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE):
                return PushedPredicates(date_end=lit_date)

    return PushedPredicates()


def _literal_to_date(node: Any) -> date | None:
    val = node.value
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        try:
            return date.fromisoformat(val[:10])
        except ValueError:
            return None
    return None


def synthesise_pagination_hint(predicates: PushedPredicates) -> PaginationHint | None:
    if predicates.date_end is None and predicates.limit is None:
        return None
    return PaginationHint(
        stop_after_records=predicates.limit,
        stop_after_date=predicates.date_end,
    )
