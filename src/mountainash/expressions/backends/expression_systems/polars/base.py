"""Polars backend base class.

Provides the base ExpressionSystem class for the Polars backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

from mountainash.expressions.core.constants import CONST_BACKEND
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem

if TYPE_CHECKING:
    from mountainash.core.dtypes.metadata import LogicalKind


class PolarsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Polars expression system components.

    Provides common functionality and backend identification for all
    Polars protocol implementations.
    """

    BACKEND_NAME: str = "polars"

    @property
    def backend_type(self) -> CONST_BACKEND:
        """Return the Polars backend type identifier."""
        return CONST_BACKEND.POLARS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Polars expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a pl.Expr instance.
        """
        return isinstance(expr, pl.Expr)
    def fixed_result_type(
        self,
        logical_kind: LogicalKind,
        nullable: bool | None,
        input_type: Any = None,
        node: Any = None,
    ) -> Any:
        """Associate declared fixed results with their emitted Polars dtype."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        native = pl.Boolean if logical_kind == "boolean" else pl.String if logical_kind == "text" else None
        return ResolvedOperand(OperandType(logical_kind, "native", nullable), native)

    def field_operand_type(self, input_data: Any, field: str) -> Any:
        """Resolve a Polars field through schema metadata without a projection."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        schema = input_data.collect_schema()
        try:
            dtype = schema[field]
        except KeyError as error:
            raise BackendCapabilityError(
                f"operand metadata is unresolved: field {field!r} is absent",
                backend=self.BACKEND_NAME,
                function_key=None,
            ) from error
        name = str(dtype).split("(", 1)[0]
        if dtype == pl.Object:
            descriptor = OperandType("unknown", "polars_object", None)
        elif dtype == pl.Null:
            descriptor = OperandType("null", "native", True)
        elif dtype == pl.Boolean:
            descriptor = OperandType("boolean", "native", None)
        elif name.startswith(("Int", "UInt")):
            descriptor = OperandType("integer", "native", None)
        elif name.startswith("Float"):
            descriptor = OperandType("float", "native", None)
        elif dtype == pl.String:
            descriptor = OperandType("text", "native", None)
        else:
            descriptor = OperandType("other", "native", None)
        return ResolvedOperand(descriptor, dtype)

    def infer_expression_operand_type(self, input_data: Any, expression: Any) -> Any:
        """Infer a Polars expression dtype through LazyFrame schema resolution."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        name = "__mountainash_operand_metadata__"
        lazy = input_data if isinstance(input_data, pl.LazyFrame) else input_data.lazy()
        dtype = lazy.select(expression.alias(name)).collect_schema()[name]
        dtype_name = str(dtype).split("(", 1)[0]
        if dtype == pl.Object:
            descriptor = OperandType("unknown", "polars_object", None)
        elif dtype == pl.Null:
            descriptor = OperandType("null", "native", True)
        elif dtype == pl.Boolean:
            descriptor = OperandType("boolean", "native", None)
        elif dtype_name.startswith(("Int", "UInt")):
            descriptor = OperandType("integer", "native", None)
        elif dtype_name.startswith("Float"):
            descriptor = OperandType("float", "native", None)
        elif dtype == pl.String:
            descriptor = OperandType("text", "native", None)
        else:
            descriptor = OperandType("other", "native", None)
        return ResolvedOperand(descriptor, dtype)
