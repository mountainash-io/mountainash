"""Closed relation-lineage rules for transported structured physical carriers."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from mountainash.conform.errors import UnsupportedStructuredTransportUse
from mountainash.conform.structured_transport import (
    StructuredFieldPlan,
    StructuredFieldPlanMap,
    freeze_structured_field_plans,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL as RM,
    RKEY_SUBSTRAIT_REL as RS,
)

if TYPE_CHECKING:
    from enum import Enum


@dataclass(frozen=True)
class TransportLineagePolicy:
    """One closed semantic category for a registered relation operation."""

    name: str


_START = TransportLineagePolicy("start")
_CONFORM = TransportLineagePolicy("conform")
_REF = TransportLineagePolicy("ref")
_PRESERVE = TransportLineagePolicy("preserve")
_PROJECT_SELECT = TransportLineagePolicy("project_select")
_PROJECT_WITH_COLUMNS = TransportLineagePolicy("project_with_columns")
_PROJECT_DROP = TransportLineagePolicy("project_drop")
_PROJECT_RENAME = TransportLineagePolicy("project_rename")
_REJECT_CONSUMERS = TransportLineagePolicy("reject_consumers")
_JOIN = TransportLineagePolicy("join")
_AGGREGATE = TransportLineagePolicy("aggregate")
_UNPIVOT = TransportLineagePolicy("unpivot")
_UNION_ALL = TransportLineagePolicy("union_all")
_REJECT_REMAINING = TransportLineagePolicy("reject_remaining")


TRANSPORT_LINEAGE_POLICIES: Mapping[Enum, TransportLineagePolicy] = MappingProxyType(
    {
        RS.READ: _START,
        RS.PROJECT_SELECT: _PROJECT_SELECT,
        RS.PROJECT_WITH_COLUMNS: _PROJECT_WITH_COLUMNS,
        RS.PROJECT_DROP: _PROJECT_DROP,
        RS.PROJECT_RENAME: _PROJECT_RENAME,
        RS.FILTER: _REJECT_CONSUMERS,
        RS.SORT: _REJECT_CONSUMERS,
        RS.FETCH: _PRESERVE,
        RS.JOIN: _JOIN,
        RS.AGGREGATE: _AGGREGATE,
        RS.DISTINCT: _REJECT_REMAINING,
        RS.UNION_ALL: _UNION_ALL,
        RS.UNION_DISTINCT: _REJECT_REMAINING,
        RM.DROP_NULLS: _REJECT_CONSUMERS,
        RM.DROP_NANS: _REJECT_CONSUMERS,
        RM.WITH_ROW_INDEX: _PRESERVE,
        RM.EXPLODE: _REJECT_CONSUMERS,
        RM.SAMPLE: _PRESERVE,
        RM.UNPIVOT: _UNPIVOT,
        RM.PIVOT: _AGGREGATE,
        RM.TOP_K: _REJECT_CONSUMERS,
        RM.UNNEST: _REJECT_CONSUMERS,
        RM.SOURCE: _START,
        RM.REF: _REF,
        RM.READ_RESOURCE: _START,
        RM.CONFORM: _CONFORM,
        RM.FETCH_FROM_END: _PRESERVE,
        RM.JOIN_ASOF: _JOIN,
        RM.EMPTY_FRAME: _START,
    }
)


@runtime_checkable
class StructuredPlanResolver(Protocol):
    """Optional metadata side channel for the existing native ref resolver."""

    def __call__(self, name: str) -> Any: ...

    def structured_plans(self, name: str) -> StructuredFieldPlanMap: ...


def _empty() -> StructuredFieldPlanMap:
    return MappingProxyType({})


def _raise(field_name: str, plan: StructuredFieldPlan, node: Any, consumer: str) -> None:
    raise UnsupportedStructuredTransportUse(
        field_name=field_name,
        root=plan.root.value,
        node_type=type(node).__name__,
        consumer=consumer,
    )


def _expression_node(value: Any) -> Any:
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI

    return value._node if isinstance(value, BaseExpressionAPI) else value


def _referenced_fields(value: Any) -> set[str]:
    """Extract field references from an uncompiled expression tree."""
    from mountainash.expressions.core.expression_nodes import ExpressionNode
    from mountainash.expressions.core.expression_nodes.substrait.exn_field_reference import (
        FieldReferenceNode,
    )
    from mountainash.relations.core.unified_visitor.relation_visitor import _expression_children

    value = _expression_node(value)
    if isinstance(value, FieldReferenceNode):
        return {value.field}
    if isinstance(value, ExpressionNode):
        return set().union(*(_referenced_fields(child) for child in _expression_children(value)))
    if isinstance(value, Mapping):
        return set().union(*(_referenced_fields(item) for item in value.values()))
    if isinstance(value, (list, tuple)):
        return set().union(*(_referenced_fields(item) for item in value))
    return set()


def _direct_projection(value: Any) -> tuple[str, str] | None:
    """Return source and output names only for a direct field or direct alias."""
    from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
    from mountainash.expressions.core.expression_nodes.substrait.exn_field_reference import (
        FieldReferenceNode,
    )

    if isinstance(value, str):
        return value, value
    expression = _expression_node(value)
    if isinstance(expression, FieldReferenceNode):
        return expression.field, expression.field
    if (
        isinstance(expression, ScalarFunctionNode)
        and expression.function_key.name == "ALIAS"
        and len(expression.arguments) == 1
        and isinstance(expression.arguments[0], FieldReferenceNode)
    ):
        alias = expression.options.get("name")
        if isinstance(alias, str):
            return expression.arguments[0].field, alias
    return None


def _named_values(value: Any) -> set[str]:
    """Collect field-name literals from relation option and sort payloads."""
    from mountainash.core.constants import SortField
    from mountainash.expressions.core.expression_nodes.substrait.exn_field_reference import (
        FieldReferenceNode,
    )

    if isinstance(value, str):
        return {value}
    if isinstance(value, Mapping):
        return set().union(*(_named_values(item) for item in value.values()))
    if isinstance(value, (list, tuple, set, frozenset)):
        return set().union(*(_named_values(item) for item in value))
    if isinstance(value, FieldReferenceNode):
        return _named_values(value.field)
    if isinstance(value, SortField):
        return _named_values(value.column)
    return set()


def _reject_consumed_fields(
    node: Any, plans: StructuredFieldPlanMap, values: Any, consumer: str
) -> None:
    for name in _referenced_fields(values) | _named_values(values):
        plan = plans.get(name)
        if plan is not None:
            _raise(name, plan, node, consumer)


def _renamed(plan: StructuredFieldPlan, name: str) -> StructuredFieldPlan:
    return replace(plan, field_name=name)


def _relation_output_names(node: Any) -> set[str]:
    """Best-effort names for a relation's physical output columns."""
    try:
        from mountainash.relations.schema_inference import infer_schema

        return set(infer_schema(node, None))
    except Exception:
        return set()


def _join_child_maps(
    node: Any,
    left: StructuredFieldPlanMap,
    right: StructuredFieldPlanMap,
) -> Sequence[StructuredFieldPlanMap]:
    """Rename right-side plans to the join backend's output names."""
    if getattr(getattr(node, "join_type", None), "name", None) in {"SEMI", "ANTI"}:
        return [left]

    left_names = _relation_output_names(getattr(node, "left", None)) | set(left)
    shared_keys = set(getattr(node, "on", None) or ())
    suffix = getattr(node, "suffix", "_right") or "_right"
    mapped_right: dict[str, StructuredFieldPlan] = {}
    for name, plan in right.items():
        if name in shared_keys:
            continue
        output = f"{name}{suffix}" if name in left_names else name
        mapped_right[output] = _renamed(plan, output)
    return [left, freeze_structured_field_plans(mapped_right)]


def _merged_inputs(
    node: Any, child_maps: Sequence[StructuredFieldPlanMap], *, require_equal: bool
) -> StructuredFieldPlanMap:
    if not child_maps:
        return _empty()
    first = child_maps[0]
    if require_equal and any(dict(item) != dict(first) for item in child_maps[1:]):
        differing = next(
            (
                name
                for item in child_maps[1:]
                for name in set(first) | set(item)
                if first.get(name) != item.get(name)
            ),
            "<alignment>",
        )
        plan = first.get(differing) or next(iter(first.values()), None)
        if plan is not None:
            _raise(differing, plan, node, getattr(node.operation_key, "name", "union"))
        raise UnsupportedStructuredTransportUse(
            field_name=differing,
            root="structured",
            node_type=type(node).__name__,
            consumer=getattr(node.operation_key, "name", "union"),
        )
    merged: dict[str, StructuredFieldPlan] = {}
    for plans in child_maps:
        for name, plan in plans.items():
            existing = merged.get(name)
            if existing is not None and existing != plan:
                _raise(name, plan, node, "join output")
            merged[name] = plan
    return freeze_structured_field_plans(merged)


def propagate_structured_plans(
    node: Any,
    child_maps: Sequence[StructuredFieldPlanMap],
    conform_plans: StructuredFieldPlanMap,
) -> StructuredFieldPlanMap:
    """Validate one operation's transport use and derive its output field plans."""
    policy = TRANSPORT_LINEAGE_POLICIES.get(node.operation_key)
    incoming = child_maps[0] if child_maps else _empty()
    if policy is None:
        if incoming:
            name, plan = next(iter(incoming.items()))
            _raise(name, plan, node, "an unclassified relation operation")
        return _empty()
    if policy is _START:
        return _empty()
    if policy is _CONFORM:
        return freeze_structured_field_plans(conform_plans)
    if policy is _REF:
        return freeze_structured_field_plans(conform_plans)
    if policy is _PRESERVE:
        return freeze_structured_field_plans(incoming)
    if policy is _PROJECT_SELECT:
        carried: dict[str, StructuredFieldPlan] = {}
        for expression in getattr(node, "expressions", ()):
            direct = _direct_projection(expression)
            if direct is not None:
                source, output = direct
                if source in incoming:
                    carried[output] = _renamed(incoming[source], output)
                continue
            _reject_consumed_fields(node, incoming, expression, "a projection expression")
        return freeze_structured_field_plans(carried)
    if policy is _PROJECT_WITH_COLUMNS:
        carried = dict(incoming)
        from mountainash.relations.schema_inference import infer_expression_name

        for expression in getattr(node, "expressions", ()):
            direct = _direct_projection(expression)
            if direct is not None:
                source, output = direct
                if source in incoming:
                    carried[output] = _renamed(incoming[source], output)
                elif output in incoming:
                    carried.pop(output, None)
                continue
            output = infer_expression_name(expression)
            if output in incoming:
                carried.pop(output, None)
            _reject_consumed_fields(node, incoming, expression, "a projection expression")
        return freeze_structured_field_plans(carried)
    if policy is _PROJECT_DROP:
        dropped = _named_values(getattr(node, "expressions", ()))
        return freeze_structured_field_plans(
            {name: plan for name, plan in incoming.items() if name not in dropped}
        )
    if policy is _PROJECT_RENAME:
        renames = getattr(node, "rename_mapping", {}) or {}
        return freeze_structured_field_plans(
            {
                renames.get(name, name): _renamed(plan, renames.get(name, name))
                for name, plan in incoming.items()
            }
        )
    if policy is _REJECT_CONSUMERS:
        if node.operation_key is RM.DROP_NULLS:
            subset = (getattr(node, "options", {}) or {}).get("subset")
            if not subset:
                _reject_consumed_fields(
                    node,
                    incoming,
                    set(incoming),
                    getattr(node.operation_key, "name", "operation"),
                )
                return freeze_structured_field_plans(incoming)
        _reject_consumed_fields(node, incoming, vars(node), getattr(node.operation_key, "name", "operation"))
        return freeze_structured_field_plans(incoming)
    if policy is _JOIN:
        left = child_maps[0] if child_maps else _empty()
        right = child_maps[1] if len(child_maps) > 1 else _empty()
        _reject_consumed_fields(
            node,
            left,
            [getattr(node, "on", ()), getattr(node, "left_on", ()), getattr(node, "by", ())],
            getattr(node.operation_key, "name", "join"),
        )
        _reject_consumed_fields(
            node,
            right,
            [getattr(node, "on", ()), getattr(node, "right_on", ()), getattr(node, "by", ())],
            getattr(node.operation_key, "name", "join"),
        )
        return _merged_inputs(node, _join_child_maps(node, left, right), require_equal=False)
    if policy is _UNPIVOT:
        options = getattr(node, "options", {}) or {}
        on = options.get("on", ())
        _reject_consumed_fields(node, incoming, on, "unpivot values")
        index = options.get("index")
        if not index:
            return _empty()
        index_names = _named_values(index)
        return freeze_structured_field_plans(
            {name: plan for name, plan in incoming.items() if name in index_names}
        )
    if policy is _AGGREGATE:
        _reject_consumed_fields(node, incoming, vars(node), getattr(node.operation_key, "name", "aggregate"))
        return _empty()
    if policy is _UNION_ALL:
        return _merged_inputs(node, child_maps, require_equal=True)
    if policy is _REJECT_REMAINING:
        if incoming:
            name, plan = next(iter(incoming.items()))
            _raise(name, plan, node, getattr(node.operation_key, "name", "set operation"))
        return _empty()
    raise AssertionError(f"unhandled transport policy {policy.name}")


__all__ = [
    "StructuredPlanResolver",
    "TRANSPORT_LINEAGE_POLICIES",
    "TransportLineagePolicy",
    "propagate_structured_plans",
]
