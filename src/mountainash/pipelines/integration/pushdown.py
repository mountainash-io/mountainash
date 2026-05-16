from __future__ import annotations

from datetime import date, datetime
from typing import Any

from mountainash.pipelines.core.capabilities import (
    PaginationHint,
    PushableParam,
    PushedParam,
    PushedPredicates,
)
from mountainash.pipelines.integration.relation import PipelineStepRelNode


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

    if not caps.pushable_params:
        return node

    extracted = _extract_predicates(node.predicate, caps.pushable_params)

    if not extracted:
        return node

    merged_params = {**pipeline_node.pushed_predicates.params, **extracted}
    merged = PushedPredicates(
        params=merged_params,
        limit=pipeline_node.pushed_predicates.limit,
        selected_fields=pipeline_node.pushed_predicates.selected_fields,
        pagination_hint=pipeline_node.pushed_predicates.pagination_hint,
    )

    hint = synthesise_pagination_hint(merged, caps.pushable_params)
    if hint is not None:
        merged = PushedPredicates(
            params=merged.params,
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
        params=pipeline_node.pushed_predicates.params,
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
        params=pipeline_node.pushed_predicates.params,
        limit=count,
        selected_fields=pipeline_node.pushed_predicates.selected_fields,
        pagination_hint=pipeline_node.pushed_predicates.pagination_hint,
    )

    hint = synthesise_pagination_hint(merged, caps.pushable_params)
    if hint is not None:
        merged = PushedPredicates(
            params=merged.params,
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


def _extract_predicates(
    expr: Any,
    pushable: tuple[PushableParam, ...],
) -> dict[str, PushedParam]:
    from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import ScalarFunctionNode
    from mountainash.expressions.core.expression_nodes.substrait.exn_field_reference import FieldReferenceNode
    from mountainash.expressions.core.expression_nodes.substrait.exn_literal import LiteralNode
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_COMPARISON,
        FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
    )
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI

    if isinstance(expr, BaseExpressionAPI):
        expr = expr._node

    if not isinstance(expr, ScalarFunctionNode):
        return {}

    fk = expr.function_key
    params: dict[str, PushedParam] = {}

    # AND: recurse both arms, merge
    if fk == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND:
        for arg in expr.arguments:
            params.update(_extract_predicates(arg, pushable))
        return params

    # OR: cannot decompose safely
    if fk == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR:
        return {}

    # NOT: inversion is unsafe to push
    if fk == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT:
        return {}

    # BETWEEN: 3 arguments (column, low, high)
    if fk == FKEY_SUBSTRAIT_SCALAR_COMPARISON.BETWEEN and len(expr.arguments) == 3:
        col_node, low_node, high_node = expr.arguments
        if isinstance(col_node, FieldReferenceNode) and isinstance(low_node, LiteralNode) and isinstance(high_node, LiteralNode):
            for p in pushable:
                if p.column == col_node.field and "gte" in p.operators:
                    params[p.api_param] = PushedParam(
                        value=low_node.value, operator="gte", format=p.format,
                    )
                    break
            for p in pushable:
                if p.column == col_node.field and "lte" in p.operators:
                    params[p.api_param] = PushedParam(
                        value=high_node.value, operator="lte", format=p.format,
                    )
                    break
        return params

    # Binary comparisons: 2 arguments
    if len(expr.arguments) == 2:
        left, right = expr.arguments
        if isinstance(left, FieldReferenceNode) and isinstance(right, LiteralNode):
            op = _fkey_to_operator(fk)
            if op is not None:
                for p in pushable:
                    if p.column == left.field and op in p.operators:
                        params[p.api_param] = PushedParam(
                            value=right.value, operator=op, format=p.format,
                        )
                        break

    return params


def _fkey_to_operator(fk: Any) -> str | None:
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON

    mapping = {
        FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT: "gt",
        FKEY_SUBSTRAIT_SCALAR_COMPARISON.GTE: "gte",
        FKEY_SUBSTRAIT_SCALAR_COMPARISON.LT: "lt",
        FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE: "lte",
        FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL: "eq",
    }
    return mapping.get(fk)


def synthesise_pagination_hint(
    predicates: PushedPredicates,
    pushable_params: tuple[PushableParam, ...] = (),
) -> PaginationHint | None:
    stop_date = None
    for api_param, pushed in predicates.params.items():
        if pushed.operator in ("lt", "lte"):
            for p in pushable_params:
                if p.api_param == api_param and p.pagination_stop:
                    if isinstance(pushed.value, (date, datetime)):
                        stop_date = pushed.value
                    break

    if stop_date is None and predicates.limit is None:
        return None
    return PaginationHint(
        stop_after_records=predicates.limit,
        stop_after_date=stop_date,
    )
