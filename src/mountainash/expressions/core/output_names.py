"""Pure AST projection naming, with output cardinality kept independently.

This resolver is deliberately separate from standalone compilation and grouped
aggregation inference. Native objects are opaque, including under aliases.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.core.expression_nodes import (
    CastNode,
    ExpressionNode,
    FieldReferenceNode,
    IfThenNode,
    LiteralNode,
    ScalarFunctionNode,
    SingularOrListNode,
    WindowFunctionNode,
)
from mountainash.expressions.core.expression_nodes.mountainash_extensions.exn_ext_ma_over import OverNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST,
    FKEY_MOUNTAINASH_SCALAR_SET,
    FKEY_MOUNTAINASH_SCALAR_STRUCT,
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
    FKEY_MOUNTAINASH_WINDOW,
    SUBSTRAIT_ARITHMETIC_WINDOW,
)
from mountainash.expressions.core.expression_system.function_mapping.registry import ExpressionFunctionRegistry

if TYPE_CHECKING:
    from enum import Enum

    from mountainash.expressions.core.expression_system.function_mapping.output_rules import ProjectionRule


@dataclass(frozen=True)
class ExpressionOutputs:
    """Names are None for unknown count, () for zero, (None,) for one unnamed.

    ``expansion`` remains distinct even when a selector currently matches one
    field. ``name_hint`` records naming intent only, never cardinality evidence.
    ``unclassified`` retains the offending key through enclosing operations.
    """

    kind: str
    names: tuple[str | None, ...] | None
    name_hint: str | None = None
    reason: str | None = None
    function_key: Enum | None = None

    @property
    def scalar_name(self) -> str | None:
        if self.kind == "single" and self.names is not None and len(self.names) == 1:
            return self.names[0]
        return None


def _is_selector(field: str) -> bool:
    return field == "*" or (field.startswith("^") and field.endswith("$"))


def _field_outputs(field: str, input_names: tuple[str, ...] | None) -> ExpressionOutputs:
    if not _is_selector(field):
        return ExpressionOutputs("single", (field,))
    names = None
    if input_names is not None:
        if field == "*":
            names = input_names
        elif re.fullmatch(r"\^[A-Za-z0-9_]+\$", field):
            names = tuple(name for name in input_names if name == field[1:-1])
    return ExpressionOutputs("expansion", names)


def _hint(output: ExpressionOutputs) -> str | None:
    if output.names is not None and len(output.names) == 1:
        return output.names[0]
    return output.name_hint


def _propagate(outputs: list[ExpressionOutputs], naming: int = 0) -> ExpressionOutputs:
    """Broadcast a single resolved expansion; never guess multi-selector pairing."""
    source = outputs[naming] if naming < len(outputs) else ExpressionOutputs("single", (None,))
    expansions = [
        output
        for output in outputs
        if output.kind == "expansion" or (output.names is not None and len(output.names) != 1)
    ]
    # Missing classification is relevant in every operand. A known-shape
    # naming limitation matters only in the operand that supplies our name.
    problem = next((output for output in outputs if output.kind == "unclassified" and output.names is None), None)
    naming_problem = source if source.kind == "unclassified" else None
    internal = next((output for output in outputs if output.kind == "internal"), None)
    opaque = next((output for output in outputs if output.kind == "opaque"), None)
    names = None
    if all(output.names is not None for output in outputs) and len(expansions) <= 1:
        count = len(expansions[0].names) if expansions else 1
        if source.kind == "expansion" or (source.names is not None and len(source.names) != 1):
            names = source.names
        else:
            names = (_hint(source),) * count
    kind = "expansion" if expansions else "single"
    failure = problem or internal or opaque or naming_problem
    if failure is not None:
        kind = failure.kind
    return ExpressionOutputs(
        kind,
        names,
        name_hint=_hint(source) if names is None else None,
        reason=failure.reason if failure else None,
        function_key=failure.function_key if failure else None,
    )


def _apply_name(output: ExpressionOutputs, transform) -> ExpressionOutputs:
    return replace(
        output,
        names=None if output.names is None else tuple(transform(name) for name in output.names),
        name_hint=transform(output.name_hint) if output.names is None else None,
    )


def _requires_alias(output: ExpressionOutputs, key: Enum | None, reason: str) -> ExpressionOutputs:
    if output.kind == "unclassified":
        return output
    if output.names == ():
        return output
    return replace(
        output,
        # A naming limitation must not turn native passthrough into a missing
        # Mountainash classification. An alias can retain intent, not shape.
        kind="opaque" if output.kind == "opaque" else "unclassified",
        names=None if output.names is None else (None,) * len(output.names),
        name_hint=None,
        reason=reason,
        function_key=key,
    )


def _first_order(node, outputs, input_names):
    spec = node.window_spec if isinstance(node, WindowFunctionNode) else None
    if spec is None or not spec.order_by:
        result = _propagate(outputs)
        return _requires_alias(result, node.function_key, "No retained ordinary order field; use an explicit alias")
    field = spec.order_by[0].column
    if not isinstance(field, str):
        result = _propagate([ExpressionOutputs("opaque", None), *outputs])
        return _requires_alias(
            result, node.function_key, "Opaque order field; use an explicit alias; cardinality remains unknown"
        )
    return _propagate([_field_outputs(field, input_names), *outputs])


def _list_context(node, outputs, input_names):
    # The body/mask runs inside each list, not against the outer input schema.
    # Its output name is immaterial; an unnamed receiver still has its known
    # shape. Missing classification remains visible even in a consumed body.
    failure = next((output for output in outputs if output.kind == "unclassified" and output.names is None), None)
    if failure is not None:
        return replace(failure, names=None)
    return (
        outputs[0]
        if outputs
        else _requires_alias(ExpressionOutputs("single", None), node.function_key, "Missing list receiver")
    )


def _struct_field(node, outputs, input_names):
    result = _propagate(outputs)
    field = node.options.get("field_name")
    if not isinstance(field, str):
        return _requires_alias(result, node.function_key, "No ordinary struct field name; use an explicit alias")
    if _is_selector(field):
        if result.kind == "unclassified" or result.names == ():
            return result
        # Top-level names provide no evidence about the nested struct schema.
        return replace(result, kind="expansion", names=None, name_hint=None)
    return _apply_name(result, lambda _: field)


_CONTEXTUAL_HANDLERS = {
    SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER: _first_order,
    SUBSTRAIT_ARITHMETIC_WINDOW.RANK: _first_order,
    SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK: _first_order,
    FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE: _first_order,
    FKEY_MOUNTAINASH_WINDOW.RANK_MAX: _first_order,
    FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD: _struct_field,
    FKEY_MOUNTAINASH_SCALAR_LIST.FILTER: _list_context,
    FKEY_MOUNTAINASH_SCALAR_LIST.AGG: _list_context,
}

_MEMBERSHIP_KEYS = frozenset(
    {
        FKEY_MOUNTAINASH_SCALAR_SET.IS_IN,
        FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN,
        FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN,
        FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_NOT_IN,
    }
)


def _function_outputs(node, input_names):
    key = node.function_key
    try:
        rule = ExpressionFunctionRegistry.get(key).projection_rule
    except KeyError:
        rule = None
    if rule is None:
        return ExpressionOutputs("unclassified", None, reason="Missing projection rule", function_key=key)

    outputs = [resolve_output_names(arg, input_names=input_names) for arg in node.arguments]
    if rule.cardinality_kind == "contextual":
        handler = _CONTEXTUAL_HANDLERS.get(key)
        if handler is None:
            return ExpressionOutputs(
                "unclassified", None, reason="Missing contextual projection handler", function_key=key
            )
        return handler(node, outputs, input_names)
    if rule.cardinality_kind == "internal_collection":
        failure = next((output for output in outputs if output.kind == "unclassified"), None)
        return failure or ExpressionOutputs("internal", None, reason=rule.reason, function_key=key)

    if key in _MEMBERSHIP_KEYS:
        # Only the membership encoder's declared internal collections are
        # consumed here. An ordinary selector/native haystack can still expand.
        outputs = [ExpressionOutputs("single", (None,)) if output.kind == "internal" else output for output in outputs]
    result = _propagate(outputs, rule.operand)
    if rule.cardinality_kind == "single" and result.kind not in {"unclassified", "internal"}:
        result = ExpressionOutputs("single", (_hint(result),))
    elif rule.cardinality_kind == "unknown":
        result = replace(result, names=None)
    return _name_by_rule(result, rule, node.options, key)


def _name_by_rule(
    result: ExpressionOutputs, rule: ProjectionRule, options: dict, key: Enum | None
) -> ExpressionOutputs:
    kind = rule.name_kind
    if kind == "requires_alias":
        return _requires_alias(result, key, rule.reason)
    if kind in {"alias", "fixed", "option"}:
        name = rule.value if kind == "fixed" else options.get(rule.value)
        if not isinstance(name, str):
            return _requires_alias(result, key, "Missing literal output name; use an explicit alias")
        named = _apply_name(result, lambda _: name)
        # Only an explicit alias discharges a requires-alias disposition with
        # known cardinality. Missing rules stay unknown and remain visible.
        if kind == "alias" and result.kind == "unclassified" and result.names is not None:
            named = replace(
                named, kind="single" if len(result.names) == 1 else "expansion", reason=None, function_key=None
            )
        return named
    if kind in {"prefix", "suffix"}:
        value = options.get(rule.value)
        if not isinstance(value, str):
            return _requires_alias(result, key, "Missing literal name transformation")
        return _apply_name(
            result, lambda name: None if name is None else (value + name if kind == "prefix" else name + value)
        )
    if kind in {"upper", "lower"}:
        return _apply_name(
            result, lambda name: None if name is None else (name.upper() if kind == "upper" else name.lower())
        )
    return result


def resolve_output_names(expression, *, input_names: tuple[str, ...] | None = None) -> ExpressionOutputs:
    """Resolve projection outputs without inspecting or compiling a backend.

    ``input_names`` must be complete evidence; None means unavailable, while ()
    means a known-empty input. Raw relation column-name strings remain literal
    names, unlike selector-bearing FieldReferenceNodes.
    """
    if isinstance(expression, BaseExpressionAPI):
        expression = expression._node
    if isinstance(expression, str):
        return ExpressionOutputs("single", (expression,))
    # Pydantic's instance check itself probes attributes. Check the concrete
    # class first so deferred/native objects never reach that machinery.
    if not issubclass(type(expression), ExpressionNode):
        return ExpressionOutputs("opaque", None)
    if isinstance(expression, FieldReferenceNode):
        return _field_outputs(expression.field, input_names)
    if isinstance(expression, LiteralNode):
        return ExpressionOutputs("opaque", None) if expression.is_native else ExpressionOutputs("single", ("literal",))
    if isinstance(expression, CastNode):
        return resolve_output_names(expression.input, input_names=input_names)
    if isinstance(expression, OverNode):
        return resolve_output_names(expression.expression, input_names=input_names)
    if isinstance(expression, IfThenNode):
        branches = [item for pair in expression.conditions for item in pair]
        branches.append(expression.else_clause)
        return _propagate([resolve_output_names(item, input_names=input_names) for item in branches], naming=1)
    if isinstance(expression, SingularOrListNode):
        return _propagate(
            [resolve_output_names(item, input_names=input_names) for item in [expression.value, *expression.options]]
        )
    if isinstance(expression, (ScalarFunctionNode, WindowFunctionNode)):
        return _function_outputs(expression, input_names)
    if isinstance(expression, ExpressionNode):
        return ExpressionOutputs(
            "unclassified", None, reason="Unclassified expression node", function_key=expression.function_key
        )
    return ExpressionOutputs("opaque", None)
