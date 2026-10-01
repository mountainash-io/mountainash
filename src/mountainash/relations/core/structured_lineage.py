"""Closed relation-lineage rules for transported structured physical carriers."""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from mountainash.conform.errors import UnsupportedStructuredTransportUse
from mountainash.conform.structured_transport import (
    StructuredFieldPlan,
    StructuredFieldPlanMap,
    freeze_structured_field_plans,
)
from mountainash.expressions.core.output_names import resolve_output_names
from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
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


def _projection_outputs(value, node, output_names_resolver):
    output = resolve_output_names(_expression_node(value))
    if output.kind == "expansion" and output.names is None:
        names = _relation_output_names(node.input, output_names_resolver)
        output = resolve_output_names(_expression_node(value), input_names=tuple(names))
    return output


def _direct_projection_pairs(value, node, output_names_resolver):
    """Prove direct source/output carriage, including empty selector expansion."""
    from mountainash.expressions.core.expression_nodes import FieldReferenceNode

    direct = _direct_projection(value)
    if direct is None:
        return None
    source, target = direct
    sources = _projection_outputs(source, node, output_names_resolver)
    if sources.names is None:
        raise IncompleteProjectionSchemaError(
            f"Unresolved projection source mapping for {source!r} with active metadata"
        )
    aliased = not isinstance(_expression_node(value), (str, FieldReferenceNode))
    return [(name, target if aliased else name) for name in sources.names]


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


def _relation_output_names(
    node: Any,
    output_names_resolver: Callable[[Any], set[str] | None] | None = None,
) -> set[str]:
    """Require complete names when metadata needs a collision decision."""
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
    from mountainash.relations.schema_inference import SchemaTypeStatus, infer_schema

    def ref_schema(name):
        names = output_names_resolver(RefRelNode(name=name)) if output_names_resolver else None
        if names is None:
            raise IncompleteProjectionSchemaError(f"Unresolved lineage output names for ref {name!r}")
        return {field: SchemaTypeStatus.UNKNOWN for field in names}

    try:
        return set(infer_schema(node, ref_schema))
    except IncompleteProjectionSchemaError:
        raise
    except Exception as exc:
        raise IncompleteProjectionSchemaError(
            f"Incomplete lineage output names for {type(node).__name__}"
        ) from exc


def _join_child_maps(
    node: Any,
    left: StructuredFieldPlanMap,
    right: StructuredFieldPlanMap,
    *,
    output_names_resolver: Callable[[Any], set[str] | None] | None = None,
    backend: Any = None,
) -> Sequence[StructuredFieldPlanMap]:
    """Rename joined-side plans to the backend's output names."""
    name_maps = _join_name_maps(
        node, [left, right], output_names_resolver=output_names_resolver, backend=backend,
    )
    return [
        freeze_structured_field_plans({
            name_maps[index][name]: _renamed(plan, name_maps[index][name])
            for name, plan in plans.items() if name in name_maps[index]
        })
        for index, plans in enumerate((left, right))
    ]


def _join_name_maps(
    node: Any,
    child_maps: Sequence[Mapping[str, Any]],
    *,
    output_names_resolver: Callable[[Any], set[str] | None] | None = None,
    backend: Any = None,
) -> list[dict[str, str]]:
    """One physical join-name rule for structured fields and residue markers."""
    left, right = child_maps
    if not left and not right:
        return [{}, {}]
    if getattr(getattr(node, "join_type", None), "name", None) in {"SEMI", "ANTI"}:
        return [{name: name for name in left}, {}]

    shared_keys = set(getattr(node, "on", None) or ())
    suffix = getattr(node, "suffix", "_right") or "_right"
    join_type = getattr(node, "join_type", None)
    backend_name = getattr(backend, "backend_type", backend)
    backend_name = getattr(backend_name, "value", backend_name)
    is_narwhals_right = (
        backend_name == "narwhals"
        and getattr(join_type, "name", None) == "RIGHT"
    )

    if is_narwhals_right:
        left_outputs = {name: name for name in left if name not in shared_keys}
        if not left_outputs:
            return [{}, {name: name for name in right}]
        base_names = _relation_output_names(
            getattr(node, "right", None), output_names_resolver
        ) | set(right)
        return [
            {name: (f"{name}{suffix}" if name in base_names else name)
             for name in left_outputs},
            {name: name for name in right},
        ]

    right_outputs = {name: name for name in right if name not in shared_keys}
    if not right_outputs:
        return [{name: name for name in left}, {}]
    left_names = _relation_output_names(
        getattr(node, "left", None), output_names_resolver
    ) | set(left)
    return [
        {name: name for name in left},
        {name: (f"{name}{suffix}" if name in left_names else name)
         for name in right_outputs},
    ]


def propagate_owned_residue(
    node: Any,
    child_checks: Sequence[Sequence[Any]],
    *,
    output_names_resolver: Callable[[Any], set[str] | None] | None = None,
    backend: Any = None,
) -> tuple[Any, ...]:
    """Carry source-owned markers through the same name rules as lineage.

    A projection which removes a pending marker must discharge the check at
    its source boundary first; silently forgetting the check is unsafe.
    """
    from dataclasses import replace as replace_check

    if not any(child_checks):
        return ()

    policy = TRANSPORT_LINEAGE_POLICIES.get(node.operation_key)
    if any(child_checks) and policy not in {
        _JOIN, _PROJECT_RENAME, _PROJECT_SELECT, _PROJECT_DROP,
        _PROJECT_WITH_COLUMNS, _PRESERVE, _REJECT_CONSUMERS,
    }:
        raise ValueError(f"Pending residue marker must be checked before {node.operation_key}")
    if policy is _JOIN:
        maps = _join_name_maps(
            node, [{owned.check.marker: owned for owned in checks} for checks in child_checks[:2]],
            output_names_resolver=output_names_resolver, backend=backend,
        )
    elif policy is _PROJECT_RENAME:
        renames = getattr(node, "rename_mapping", {}) or {}
        maps = [{owned.check.marker: renames.get(owned.check.marker, owned.check.marker)
                 for owned in checks} for checks in child_checks]
    elif policy is _PROJECT_SELECT:
        projections = {}
        for expression in getattr(node, "expressions", ()):
            direct = _direct_projection_pairs(expression, node, output_names_resolver)
            if direct is not None:
                projections.update(direct)
            else:
                output = _projection_outputs(expression, node, output_names_resolver)
                if output.names is None or any(name is None for name in output.names):
                    raise ValueError(f"Pending residue marker must be checked before {node.operation_key}")
        maps = [{owned.check.marker: projections[owned.check.marker]
                 for owned in checks if owned.check.marker in projections} for checks in child_checks]
    elif policy is _PROJECT_DROP:
        dropped = _named_values(getattr(node, "expressions", ()))
        maps = [{owned.check.marker: owned.check.marker for owned in checks
                 if owned.check.marker not in dropped} for checks in child_checks]
    elif policy is _PROJECT_WITH_COLUMNS:
        markers = {owned.check.marker for checks in child_checks for owned in checks}
        for expression in getattr(node, "expressions", ()):
            direct = _direct_projection_pairs(expression, node, output_names_resolver)
            if direct is not None:
                for source, output in direct:
                    if output in markers and source != output:
                        raise ValueError(f"Pending residue marker {output!r} must be checked before {node.operation_key}")
            else:
                output = _projection_outputs(expression, node, output_names_resolver)
                if output.names is None or any(name is None or name in markers for name in output.names):
                    raise ValueError(f"Pending residue marker must be checked before {node.operation_key}")
        maps = [{owned.check.marker: owned.check.marker for owned in checks}
                for checks in child_checks]
    elif policy in {_START, _CONFORM, _REF}:
        maps = [{} for _ in child_checks]
    else:
        maps = [{owned.check.marker: owned.check.marker for owned in checks}
                for checks in child_checks]
    carried = []
    for checks, names in zip(child_checks, maps):
        for owned in checks:
            marker = owned.check.marker
            if marker not in names:
                raise ValueError(f"Pending residue marker {marker!r} must be checked before {node.operation_key}")
            output = names[marker]
            carried.append(owned if output == marker else replace_check(
                owned, check=replace_check(owned.check, marker=output)
            ))
    return tuple(carried)


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
    *,
    output_names_resolver: Callable[[Any], set[str] | None] | None = None,
    backend: Any = None,
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
        if not incoming:
            return _empty()
        carried: dict[str, StructuredFieldPlan] = {}
        for expression in getattr(node, "expressions", ()):
            direct = _direct_projection_pairs(expression, node, output_names_resolver)
            if direct is not None:
                for source, output in direct:
                    if source in incoming:
                        carried[output] = _renamed(incoming[source], output)
                continue
            output = _projection_outputs(expression, node, output_names_resolver)
            if output.names == ():
                continue
            if output.kind == "expansion" or output.names is None or any(name is None for name in output.names):
                _reject_consumed_fields(node, incoming, set(incoming), "an unresolved projection expression")
            _reject_consumed_fields(node, incoming, expression, "a projection expression")
        return freeze_structured_field_plans(carried)
    if policy is _PROJECT_WITH_COLUMNS:
        if not incoming:
            return _empty()
        carried = dict(incoming)

        for expression in getattr(node, "expressions", ()):
            direct = _direct_projection_pairs(expression, node, output_names_resolver)
            if direct is not None:
                for source, output in direct:
                    if source in incoming:
                        carried[output] = _renamed(incoming[source], output)
                    elif output in incoming:
                        carried.pop(output, None)
                continue
            output = _projection_outputs(expression, node, output_names_resolver)
            if output.names == ():
                continue
            _reject_consumed_fields(node, incoming, expression, "a projection expression")
            if output.kind == "expansion" or output.names is None or any(name is None for name in output.names):
                if incoming:
                    _reject_consumed_fields(
                        node, incoming, set(incoming), "a projection expression"
                    )
                continue
            for name in output.names:
                carried.pop(name, None)
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
        return _merged_inputs(
            node,
            _join_child_maps(
                node,
                left,
                right,
                output_names_resolver=output_names_resolver,
                backend=backend,
            ),
            require_equal=False,
        )
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
        for plans in child_maps:
            if plans:
                name, plan = next(iter(plans.items()))
                _raise(name, plan, node, getattr(node.operation_key, "name", "set operation"))
        return _empty()
    raise AssertionError(f"unhandled transport policy {policy.name}")


__all__ = [
    "StructuredPlanResolver",
    "TRANSPORT_LINEAGE_POLICIES",
    "TransportLineagePolicy",
    "propagate_structured_plans",
    "propagate_owned_residue",
]
