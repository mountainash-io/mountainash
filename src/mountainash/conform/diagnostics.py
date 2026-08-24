"""Diagnostic records carried from expression compilation to materialization."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import (
        ScalarFunctionNode,
    )

_SAFE_ROUTING_OPTION_NAMES = frozenset(
    {
        "item_type",
        "failure_behavior",
        "format",
        "source_representation",
        "kind",
        "value_type",
    }
)


def _string_value(value: Any) -> str:
    """Normalize an option value without exposing recursive configuration."""
    return str(value.value if isinstance(value, Enum) else value)


@dataclass(frozen=True)
class OperationDiagnostic:
    function_key: Any
    backend_family: str
    dialect: str | None
    conform_node_id: str | None
    routing_fingerprint: tuple[tuple[str, str], ...]
    failure_behavior: str | None
    field_name: str
    logical_type: str
    format: str


class OperationDiagnosticTrace:
    def __init__(self) -> None:
        self._records: list[OperationDiagnostic] = []

    @property
    def records(self) -> tuple[OperationDiagnostic, ...]:
        return tuple(self._records)

    def record(
        self,
        node: ScalarFunctionNode,
        *,
        backend_family: str,
        dialect: str | None,
        conform_node_id: str | None,
    ) -> None:
        fingerprint = tuple(
            sorted(
                (name, _string_value(value))
                for name, value in node.options.items()
                if name in _SAFE_ROUTING_OPTION_NAMES
            )
        )
        context = node.diagnostic_context
        failure_behavior = node.options.get("failure_behavior")
        self._records.append(
            OperationDiagnostic(
                function_key=node.function_key,
                backend_family=_string_value(backend_family),
                dialect=dialect,
                conform_node_id=conform_node_id,
                routing_fingerprint=fingerprint,
                failure_behavior=(
                    _string_value(failure_behavior)
                    if failure_behavior is not None
                    else None
                ),
                field_name=context.get("field_name", ""),
                logical_type=context.get("logical_type", ""),
                format=context.get("format", ""),
            )
        )


__all__ = ["OperationDiagnostic", "OperationDiagnosticTrace"]
