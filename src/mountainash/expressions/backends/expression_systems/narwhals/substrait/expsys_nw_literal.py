"""Narwhals LiteralExpressionProtocol implementation.

Implements literal/constant value operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitLiteralExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr




class SubstraitNarwhalsLiteralExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitLiteralExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of LiteralExpressionProtocol."""

    def _effective_literal_dtype(self, x: Any, dtype: Any) -> Any:
        from mountainash.core.dtypes import (
            TypeTarget, dtype_is_complete, registry, resolve_dtype_parameters,
        )
        from mountainash.core.dtypes.canonical import PARAMETERIZED_DTYPES

        if x is None or dtype is None or not isinstance(dtype, PARAMETERIZED_DTYPES):
            return dtype
        if dtype.native is not None:
            return dtype
        if dtype_is_complete(dtype):
            return dtype
        if self.dialect in {"narwhals-polars", "narwhals-lazy"}:
            return dtype
        if self.dialect == "narwhals-pandas" and not isinstance(x, (list, tuple, dict)):
            from mountainash.core.lazy_imports import import_pandas
            source = registry.from_native(
                import_pandas().Series([x]).dtype, target=TypeTarget.PANDAS,
            )
        else:
            from mountainash.core.lazy_imports import import_pyarrow
            from narwhals._arrow.utils import native_to_narwhals_dtype
            from narwhals._utils import Version

            source = registry.from_native(
                native_to_narwhals_dtype(import_pyarrow().scalar(x).type, Version.MAIN),
                target=TypeTarget.NARWHALS,
            )
        return resolve_dtype_parameters(dtype, source)

    def lit(self, x: Any, /, *, dtype: Any = None) -> NarwhalsExpr:
        """Create a literal, resolving partial targets from its native value."""
        from mountainash.core.dtypes import (
            SchemaTypeStatus, TypeTarget, dtype_is_complete, registry,
        )
        from mountainash.core.dtypes.canonical import PARAMETERIZED_DTYPES

        if dtype is None or dtype is SchemaTypeStatus.UNKNOWN:
            return nw.lit(x)
        if (
            x is not None and isinstance(dtype, PARAMETERIZED_DTYPES)
            and dtype.native is None and not dtype_is_complete(dtype)
            and self.dialect in {"narwhals-polars", "narwhals-lazy"}
        ):
            return self.cast(nw.lit(x), dtype)
        dtype = self._effective_literal_dtype(x, dtype)

        native_dtype = registry.to_native_cast(dtype, TypeTarget.NARWHALS)
        if x is None and self.dialect == "narwhals-pandas":
            resolved = self.literal_operand_type(x, dtype)
            if resolved.descriptor.storage_kind == "pandas_nullable":
                return self._pandas_typed_expression(
                    nw.lit(None), resolved.native_dtype
                )
        return nw.lit(x, dtype=native_dtype)
