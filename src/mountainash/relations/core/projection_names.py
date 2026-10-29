"""AST-only projection normalization and complete output-name validation."""

from __future__ import annotations

from typing import Any

from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME
from mountainash.expressions.core.output_names import resolve_output_names


class ProjectionNameError(ValueError):
    """A projection has conflicting or non-projectable output names."""


class IncompleteProjectionSchemaError(ValueError):
    """The AST cannot establish every projection output name and cardinality."""


def normalize_projection(expressions, *, operation) -> list[Any]:
    """Encode proven scalar names as aliases, without inspecting the source."""
    normalized = []
    seen = set()
    for position, expression in enumerate(expressions):
        output = resolve_output_names(expression)
        context = f"{operation.name} expression {position}"
        if output.kind in {"unclassified", "internal"}:
            raise ProjectionNameError(
                f"{context}: {output.function_key}; use an explicit alias for a supported single-output expression"
            )
        name = output.scalar_name
        if output.kind == "single" and name is None:
            raise ProjectionNameError(f"{context} requires an explicit alias")
        if name is not None:
            if name in seen:
                raise ProjectionNameError(f"{context}: duplicate output {name!r}")
            seen.add(name)
            node = expression._node if isinstance(expression, BaseExpressionAPI) else expression
            already_named = isinstance(node, FieldReferenceNode) or (
                isinstance(node, ScalarFunctionNode) and node.function_key == FKEY_MOUNTAINASH_NAME.ALIAS
            )
            if not isinstance(expression, str) and not already_named:
                expression = ScalarFunctionNode(
                    function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
                    arguments=[node],
                    options={"name": name},
                )
        normalized.append(expression)
    return normalized


def require_projection_names(expressions, *, operation, input_names) -> tuple[str, ...]:
    """Return all output names in order, or fail rather than expose a partial schema."""
    names = []
    seen = set()
    input_names = None if input_names is None else tuple(input_names)
    for position, expression in enumerate(expressions):
        output = resolve_output_names(expression, input_names=input_names)
        context = f"{operation.name} expression {position}"
        if (
            output.kind in {"opaque", "unclassified", "internal"}
            or output.names is None
            or any(name is None for name in output.names)
        ):
            raise IncompleteProjectionSchemaError(
                f"{context}: incomplete output names/cardinality ({output.kind}; "
                f"{output.function_key}; {output.reason})"
            )
        for name in output.names:
            if name in seen:
                raise ProjectionNameError(f"{context}: duplicate output {name!r}")
            seen.add(name)
            names.append(name)
    return tuple(names)
