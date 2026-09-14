"""Narwhals backend base class.

Provides the base ExpressionSystem class for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import narwhals as nw

from mountainash.core.capabilities import CapabilityFact
from mountainash.expressions.core.constants import CONST_BACKEND
from mountainash.expressions.backends.capabilities.narwhals import (
    NARWHALS_EXPR_CAPABILITIES,
)
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem

if TYPE_CHECKING:
    from mountainash.core.dtypes.metadata import LogicalKind, StorageKind


class NarwhalsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Narwhals expression system components.

    Provides common functionality and backend identification for all
    Narwhals protocol implementations.
    """

    BACKEND_NAME: str = "narwhals"

    CAPABILITIES: tuple[CapabilityFact, ...] = NARWHALS_EXPR_CAPABILITIES

    @property
    def backend_type(self) -> CONST_BACKEND:
        """Return the Narwhals backend type identifier."""
        return CONST_BACKEND.NARWHALS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Narwhals expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a nw.Expr instance.
        """
        return isinstance(expr, nw.Expr)

    def field_operand_type(self, input_data: Any, field: str) -> Any:
        """Resolve direct Narwhals field metadata without evaluating a projection."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.core.transit import BoundaryKey, transit_call
        from mountainash.core.types import (
            BackendCapabilityError,
            is_pandas_dataframe,
            is_polars_lazyframe,
        )
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        native = (
            input_data
            if is_pandas_dataframe(input_data)
            else transit_call(
                BoundaryKey.EXPRESSION_NARWHALS_SCHEMA_UNWRAP, input_data.to_native
            )
        )
        if is_pandas_dataframe(native):
            try:
                dtype = native.dtypes[field]
            except KeyError as error:
                raise BackendCapabilityError(
                    f"operand metadata is unresolved: field {field!r} is absent",
                    backend=self.BACKEND_NAME,
                    function_key=None,
                ) from error
            return ResolvedOperand(self._pandas_descriptor(dtype), dtype)

        try:
            schema = (
                input_data.collect_schema()
                if is_polars_lazyframe(native)
                else input_data.schema
            )
            dtype = schema[field]
        except KeyError as error:
            raise BackendCapabilityError(
                f"operand metadata is unresolved: field {field!r} is absent",
                backend=self.BACKEND_NAME,
                function_key=None,
            ) from error
        name = type(dtype).__name__
        if name == "Object":
            return ResolvedOperand(OperandType("unknown", "polars_object", None), dtype)
        logical: LogicalKind
        if name == "Boolean":
            logical = "boolean"
        elif name.startswith(("Int", "UInt")):
            logical = "integer"
        elif name.startswith("Float"):
            logical = "float"
        elif name in {"String", "Categorical", "Enum"}:
            logical = "text"
        elif name == "Null":
            logical = "null"
        else:
            logical = "other"
        return ResolvedOperand(OperandType(logical, "native", None), dtype)

    def literal_operand_type(self, value: Any, dtype: Any = None) -> Any:
        """Keep declared Pandas null literals in storage that can represent null."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        resolved = super().literal_operand_type(value, dtype)
        if (
            self.dialect == "narwhals-pandas"
            and dtype is None
            and resolved.descriptor.logical_kind == "float"
        ):
            from mountainash.core.lazy_imports import import_numpy

            numpy = import_numpy()
            return ResolvedOperand(
                OperandType("float", "pandas_numpy", bool(numpy.isnan(value))),
                numpy.dtype(type(value)),
            )
        if (
            self.dialect != "narwhals-pandas"
            or value is not None
            or dtype is None
            or resolved.descriptor.logical_kind not in {"boolean", "integer", "text"}
        ):
            return resolved
        from mountainash.core.lazy_imports import import_pandas

        native_dtype = (
            import_pandas().StringDtype()
            if resolved.descriptor.logical_kind == "text"
            else self._pandas_nullable_dtype(resolved)
        )
        return ResolvedOperand(
            OperandType(
                resolved.descriptor.logical_kind,
                "pandas_nullable",
                True,
            ),
            native_dtype,
        )

    def cast_operand_type(self, target_type: Any, input_type: Any) -> Any:
        """Describe Narwhals cast output rather than retaining source object storage."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        resolved = super().cast_operand_type(target_type, input_type)
        if self.dialect == "narwhals-pandas":
            source_storage = input_type.storage_kind if input_type is not None else "pandas_numpy"
            storage: StorageKind = (
                "pandas_numpy"
                if source_storage == "pandas_object"
                else source_storage
            )
            return ResolvedOperand(
                OperandType(
                    resolved.descriptor.logical_kind,
                    storage,
                    resolved.descriptor.nullable,
                ),
                resolved.native_dtype,
            )
        return ResolvedOperand(
            OperandType(
                resolved.descriptor.logical_kind,
                "native",
                resolved.descriptor.nullable,
            ),
            resolved.native_dtype,
        )
    def fixed_result_type(
        self,
        logical_kind: LogicalKind,
        nullable: bool | None,
        input_type: Any = None,
        node: Any = None,
    ) -> Any:
        """Describe declared value outputs using the lowering's real storage."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_BOOLEAN,
            FKEY_MOUNTAINASH_SCALAR_VALUE,
        )
        native_dtype = (
            nw.Boolean
            if logical_kind == "boolean"
            else nw.String
            if logical_kind == "text"
            else input_type.native_dtype if input_type is not None else None
        )

        if input_type is None:
            if (
                self.dialect == "narwhals-pandas"
                and node is not None
                and node.function_key is FKEY_MOUNTAINASH_SCALAR_BOOLEAN.PARSE_TOKENS
            ):
                from mountainash.core.lazy_imports import import_pandas

                return ResolvedOperand(
                    OperandType(logical_kind, "pandas_nullable", nullable),
                    import_pandas().BooleanDtype(),
                )
            return super().fixed_result_type(logical_kind, nullable, input_type, node)
        storage = input_type.descriptor.storage_kind
        if storage == "pandas_object":
            return ResolvedOperand(
                OperandType(logical_kind, "pandas_nullable", nullable), native_dtype
            )
        if storage == "polars_object":
            return ResolvedOperand(
                OperandType(logical_kind, "native", nullable), native_dtype
            )
        if storage.startswith("pandas_"):
            key = node.function_key
            preserve = (
                key is FKEY_MOUNTAINASH_SCALAR_VALUE.TEXT_VALUE
                and input_type.descriptor.logical_kind == "text"
            ) or (
                key is FKEY_MOUNTAINASH_SCALAR_VALUE.BOOLEAN_VALUE
                and input_type.descriptor.logical_kind == "boolean"
                and node.options.get("source", "boolean") == "boolean"
            )
            output_storage: StorageKind = storage if preserve else "pandas_nullable"
            return ResolvedOperand(
                OperandType(logical_kind, output_storage, nullable), native_dtype
            )
        return super().fixed_result_type(logical_kind, nullable, input_type, node)

    def common_result_type(
        self,
        operands: list[Any],
        nullable: bool,
        *,
        composition: str,
        concrete_nodes: list[Any],
        has_literal_null: bool,
        has_nullable_storage: bool,
    ) -> Any:
        """Describe the Pandas carrier chosen by Narwhals' bounded lowerings."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.expression_nodes import LiteralNode
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        result = super().common_result_type(
            operands,
            nullable,
            composition=composition,
            concrete_nodes=concrete_nodes,
            has_literal_null=has_literal_null,
            has_nullable_storage=has_nullable_storage,
        )
        if self.dialect != "narwhals-pandas":
            return result

        first = operands[0]
        storage = result.descriptor.storage_kind
        native_dtype = result.native_dtype
        if isinstance(concrete_nodes[0], LiteralNode):
            storage = (
                "pandas_object"
                if first.descriptor.logical_kind == "text"
                else "pandas_numpy"
            )
            # Literal dtype inference is native lowering behavior, not evidence
            # retained by the generic literal descriptor.
            native_dtype = None
        source_storages = {
            operand.descriptor.storage_kind for operand in operands
        }
        mixed_storage = len(source_storages) > 1
        different_dtypes = any(
            operand.native_dtype != first.native_dtype for operand in operands[1:]
        )
        requires_null_carrier = has_literal_null or different_dtypes or (
            has_nullable_storage and mixed_storage
        )
        if (
            first.descriptor.logical_kind == "integer"
            and has_nullable_storage
            and (mixed_storage or different_dtypes)
        ):
            # Extension where/fillna may narrow silently, including 256 -> 0
            # for Int8. Establish object storage before either native operation.
            native_dtype = None
            storage = "pandas_object"
        elif first.descriptor.logical_kind == "float" and requires_null_carrier:
            native_dtype, storage = self._pandas_common_float_dtype(
                operands, concrete_nodes, source_storages
            )
        elif composition == "conditional" and requires_null_carrier:
            kind = first.descriptor.logical_kind
            if kind == "boolean":
                # Boolean has no width or signedness to lose. A single
                # nullable Boolean carrier is faithful across Pandas storage.
                native_dtype = self._pandas_nullable_dtype(first)
                storage = "pandas_nullable"
            elif has_nullable_storage and mixed_storage:
                # Do not allow Pandas where() to float-promote mixed native
                # integer storage before the object fallback is established.
                native_dtype = None
                storage = "pandas_object"
            elif (
                has_literal_null
                and storage == "pandas_numpy"
                and kind == "integer"
            ):
                if native_dtype is None:
                    native_dtype = None
                    storage = "pandas_object"
                else:
                    native_dtype = self._pandas_nullable_dtype(first)
                    storage = "pandas_nullable"

        return ResolvedOperand(
            OperandType(first.descriptor.logical_kind, storage, nullable), native_dtype
        )

    def _pandas_common_float_dtype(
        self, operands: list[Any], nodes: list[Any], storages: set[str]
    ) -> tuple[Any, StorageKind]:
        """Widen floating metadata without losing native precision or validity."""
        from mountainash.core.lazy_imports import import_numpy, import_pandas, import_pyarrow
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_nodes import LiteralNode

        numpy = import_numpy()
        native = []
        try:
            for operand, node in zip(operands, nodes, strict=True):
                dtype = operand.native_dtype
                if dtype is None:
                    if not isinstance(node, LiteralNode):
                        raise TypeError("native floating width is unknown")
                    dtype = numpy.dtype(type(node.value))
                numpy_dtype = getattr(dtype, "numpy_dtype", None)
                native.append(
                    numpy.dtype(str(dtype).lower()) if numpy_dtype is None else numpy_dtype
                )
            common = numpy.result_type(*native)
            if common.kind != "f":
                raise TypeError("floating operands require floating native dtypes")
            if {"pandas_nullable", "pandas_arrow"}.intersection(storages):
                if common.itemsize not in (4, 8):
                    raise TypeError("no lossless nullable carrier for this floating precision")
                pandas = import_pandas()
                if "pandas_arrow" in storages:
                    return pandas.ArrowDtype(import_pyarrow().from_numpy_dtype(common)), "pandas_arrow"
                return pandas.api.types.pandas_dtype(f"Float{common.itemsize * 8}"), "pandas_nullable"
            return common, "pandas_numpy"
        except TypeError as error:
            raise BackendCapabilityError(
                f"operand metadata is unresolved: {error}",
                backend=self.BACKEND_NAME,
                function_key=None,
            ) from error

    def prepare_coalesce_arguments(
        self,
        arguments: list[Any],
        null_scalars: list[bool],
        result_type: Any = None,
    ) -> list[Any]:
        """Remove proven scalar nulls and establish the resolved native carrier."""
        if self.dialect != "narwhals-pandas":
            return arguments
        retained = [
            argument
            for argument, is_null in zip(arguments, null_scalars, strict=True)
            if not is_null
        ]
        if not retained:
            return arguments
        if result_type is not None and result_type.descriptor.storage_kind == "pandas_object":
            retained = [self._pandas_object_expression(argument) for argument in retained]
        elif (
            result_type is not None
            and result_type.descriptor.logical_kind == "float"
            and result_type.native_dtype is not None
        ):
            retained = [
                self._pandas_nullable_expression(argument, result_type.native_dtype)
                for argument in retained
            ]
        if null_scalars[0]:
            from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_value import (
                _ElementwiseBatchExpr,
            )

            retained[0] = _ElementwiseBatchExpr(
                retained[0], None, None,
                native_polars=False, name_source=arguments[0],
            )
        return retained

    def normalize_conditional_branch(
        self,
        expression: Any,
        branch_type: Any,
        result_type: Any,
        *,
        requires_null_carrier: bool,
    ) -> Any:
        """Normalize every concrete branch to the declared Pandas carrier."""
        if (
            self.dialect != "narwhals-pandas"
            or not requires_null_carrier
            or branch_type.descriptor.logical_kind
            not in {"null", result_type.descriptor.logical_kind}
        ):
            return expression
        storage = result_type.descriptor.storage_kind
        if storage == "pandas_nullable" or (
            result_type.descriptor.logical_kind == "float"
            and result_type.native_dtype is not None
        ):
            return self._pandas_nullable_expression(
                expression, result_type.native_dtype
            )
        if storage == "pandas_object":
            return self._pandas_object_expression(expression)
        return expression

    @staticmethod
    def _pandas_nullable_expression(expression: Any, dtype: Any) -> Any:
        """Reuse the typed elementwise adapter so Pandas keeps row metadata."""
        from mountainash.core.lazy_imports import import_pandas
        from mountainash.core.transit import BoundaryKey, transit_call
        from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_value import (
            _pandas_elementwise_batches,
        )

        pandas = import_pandas()

        def cast_nullable(series: Any) -> Any:
            native = series.native
            if native.dtype == dtype:
                return series
            output = transit_call(
                BoundaryKey.EXPRESSION_NARWHALS_PANDAS_TYPED_CALLBACK,
                pandas.Series,
                pandas.array(native, dtype=dtype),
                index=native.index,
                name=native.name,
                trace_source=series,
            )
            return series._with_native(output)

        return _pandas_elementwise_batches(expression, cast_nullable, None)

    @staticmethod
    def _pandas_object_expression(expression: Any) -> Any:
        """Preserve mixed native values in the declared object carrier."""
        from mountainash.core.lazy_imports import import_pandas
        from mountainash.core.transit import BoundaryKey, transit_call
        from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_value import (
            _pandas_elementwise_batches,
        )

        pandas = import_pandas()

        def cast_object(series: Any) -> Any:
            native = series.native
            if native.dtype == object:
                return series
            output = transit_call(
                BoundaryKey.EXPRESSION_NARWHALS_PANDAS_TYPED_CALLBACK,
                pandas.Series,
                native.astype(object),
                index=native.index,
                name=native.name,
                trace_source=series,
            )
            return series._with_native(output)

        return _pandas_elementwise_batches(expression, cast_object, None)

    @staticmethod
    def _pandas_nullable_dtype(resolved: Any) -> Any:
        """Choose Pandas nullable storage without discarding integer width."""
        from mountainash.core.lazy_imports import import_pandas

        pandas = import_pandas()
        if resolved.descriptor.logical_kind == "boolean":
            return pandas.BooleanDtype()

        name = str(resolved.native_dtype).lower()
        for bits in ("8", "16", "32", "64"):
            if name.startswith(f"uint{bits}"):
                return pandas.api.types.pandas_dtype(f"UInt{bits}")
            if name.startswith(f"int{bits}"):
                return pandas.api.types.pandas_dtype(f"Int{bits}")
        return pandas.Int64Dtype()

    def normalize_conditional_result(
        self, expression: Any, result_type: Any, *, requires_null_carrier: bool
    ) -> Any:
        """Materialize the exact Pandas carrier declared for a null branch."""
        if self.dialect != "narwhals-pandas" or not requires_null_carrier:
            return expression
        if result_type.descriptor.storage_kind == "pandas_nullable" or (
            result_type.descriptor.logical_kind == "float"
            and result_type.native_dtype is not None
        ):
            return self._pandas_nullable_expression(
                expression, result_type.native_dtype
            )
        if result_type.descriptor.storage_kind == "pandas_object":
            return self._pandas_object_expression(expression)
        return expression

    def infer_expression_operand_type(self, input_data: Any, expression: Any) -> Any:
        """Use Narwhals-Polars lazy schema inference; Pandas has no safe path."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.core.transit import BoundaryKey, transit_call
        from mountainash.core.types import (
            BackendCapabilityError,
            is_pandas_dataframe,
            is_polars_dataframe,
            is_polars_lazyframe,
        )
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        native = (
            input_data
            if is_pandas_dataframe(input_data)
            else transit_call(
                BoundaryKey.EXPRESSION_NARWHALS_SCHEMA_UNWRAP, input_data.to_native
            )
        )
        if is_pandas_dataframe(native) or not (
            is_polars_dataframe(native) or is_polars_lazyframe(native)
        ):
            raise BackendCapabilityError(
                "operand metadata is unresolved for computed Narwhals-Pandas expression",
                backend=self.BACKEND_NAME,
                function_key=None,
            )
        name = "__mountainash_operand_metadata__"
        lazy = input_data if type(input_data).__name__ == "LazyFrame" else input_data.lazy()
        dtype = lazy.select(expression.alias(name)).collect_schema()[name]
        dtype_name = type(dtype).__name__
        if dtype_name == "Object":
            descriptor = OperandType("unknown", "polars_object", None)
        elif dtype_name == "Boolean":
            descriptor = OperandType("boolean", "native", None)
        elif dtype_name.startswith(("Int", "UInt")):
            descriptor = OperandType("integer", "native", None)
        elif dtype_name.startswith("Float"):
            descriptor = OperandType("float", "native", None)
        elif dtype_name == "String":
            descriptor = OperandType("text", "native", None)
        elif dtype_name == "Null":
            descriptor = OperandType("null", "native", True)
        else:
            descriptor = OperandType("other", "native", None)
        return ResolvedOperand(descriptor, dtype)

    @staticmethod
    def _pandas_descriptor(dtype: Any) -> Any:
        """Keep Pandas' NumPy, extension, Arrow, and object storage distinct."""
        from mountainash.core.dtypes.metadata import OperandType

        if str(dtype) == "object":
            return OperandType("unknown", "pandas_object", None)
        arrow_dtype = getattr(dtype, "pyarrow_dtype", None)
        pandas_storage = getattr(dtype, "storage", None)
        storage: StorageKind = (
            "pandas_arrow"
            if arrow_dtype is not None or pandas_storage == "pyarrow"
            else "pandas_nullable"
            if type(dtype).__module__.startswith("pandas")
            else "pandas_numpy"
        )
        lower = str(arrow_dtype if arrow_dtype is not None else dtype).lower()
        logical: LogicalKind
        if lower in {"bool", "boolean"}:
            logical = "boolean"
        elif lower.startswith(("int", "uint")):
            logical = "integer"
        elif lower.startswith(("float", "double")):
            logical = "float"
        elif lower.startswith(("string", "str", "large_string")):
            logical = "text"
        elif lower == "null":
            logical = "null"
        else:
            logical = "other"
        return OperandType(logical, storage, None)
