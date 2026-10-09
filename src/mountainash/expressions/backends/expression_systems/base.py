"""Base classes for backend expression systems.

This module provides shared base classes and utilities used by all backend
implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from mountainash.expressions.core.constants import CONST_BACKEND
    from mountainash.core.dtypes.metadata import LogicalKind, StorageKind


class BaseExpressionSystem(ABC):
    """Abstract base class for all backend expression systems.

    Each backend (Polars, Narwhals, Ibis) should inherit from this class
    and implement the required abstract methods.
    """

    @property
    @abstractmethod
    def backend_type(self) -> "CONST_BACKEND":
        """Return the backend type identifier."""
        ...

    @abstractmethod
    def is_native_expression(self, expr: Any) -> bool:
        """Check if the given expression is native to this backend.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a native expression type for this backend.
        """
        ...

    BACKEND_NAME: str = "unknown"

    def __init__(self, dialect: str | None = None, *, execution_context: Any) -> None:
        self.dialect = dialect
        self.execution_context = execution_context
        self._operand_type_stack: list[Mapping[str, Any]] = []

    def prepare_call_arguments(
        self, method_name: str, resolver_type: Any, visitor: Any,
        function_key: Any, arguments: Any, compiled_arguments: Any,
    ) -> list[Any] | None:
        """Resolve the category companion before allocating its operand resolver."""
        companion = getattr(self, f"_prepare_call_{method_name}", None)
        if companion is None:
            return None
        return companion(resolver_type(visitor, function_key, arguments, compiled_arguments))

    @contextmanager
    def operand_types(self, named_operands: Mapping[str, Any]) -> Iterator[None]:
        """Expose resolved descriptors to one backend dispatch and restore nesting."""
        self._operand_type_stack.append(named_operands)
        try:
            yield
        finally:
            self._operand_type_stack.pop()

    def operand_type(self, name: str) -> Any:
        """Return the current dispatch operand descriptor by protocol parameter name."""
        from mountainash.core.types import BackendCapabilityError

        if self._operand_type_stack and name in self._operand_type_stack[-1]:
            return self._operand_type_stack[-1][name]
        raise BackendCapabilityError(
            f"operand metadata is unresolved for {name!r}",
            backend=self.BACKEND_NAME,
            function_key=None,
        )

    def field_operand_type(self, input_data: Any, field: str) -> Any:
        """Resolve a direct field through the backend's metadata-only adapter."""
        raise NotImplementedError(
            f"{type(self).__name__} does not provide field metadata resolution"
        )


    def infer_expression_operand_type(self, input_data: Any, expression: Any) -> Any:
        """Infer a computed result only through backend metadata, never data evaluation."""
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "operand metadata is unresolved for this computed expression",
            backend=self.BACKEND_NAME,
            function_key=None,
        )
    def literal_operand_type(self, value: Any, dtype: Any = None) -> Any:
        """Resolve only literals whose representation is explicit or safely known."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand
        if dtype is not None:
            return self.cast_operand_type(dtype, None)

        if value is None:
            return ResolvedOperand(OperandType("null", "native", True))
        from mountainash.core.value_classification import ValueKind, value_kind

        classified = value_kind(value)
        if classified is ValueKind.ABSENT:
            return ResolvedOperand(OperandType("null", "native", True))
        kinds: dict[ValueKind, LogicalKind] = {
            ValueKind.BOOLEAN: "boolean",
            ValueKind.INTEGER: "integer",
            ValueKind.FLOAT: "float",
            ValueKind.TEXT: "text",
        }
        logical_kind = kinds.get(classified)
        if logical_kind is not None:
            return ResolvedOperand(OperandType(logical_kind, "native", False))
        raise self._unresolvable_literal(value)

    def cast_operand_type(self, target_type: Any, input_type: Any) -> Any:
        """Resolve a cast from its declared target without evaluating a sample."""
        from mountainash.core.dtypes import MountainashDtype, NativeDtype, TypeTarget, registry
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand
        native_dtype = (
            target_type.value
            if isinstance(target_type, NativeDtype)
            else registry.to_native_cast(target_type, TypeTarget(self.BACKEND_NAME))
        )
        dtype = getattr(target_type, "value", target_type)
        target = getattr(target_type, "target", None)
        if target is not None:
            dtype = registry.from_native(dtype, target=target)
        if isinstance(dtype, MountainashDtype):
            dtype = dtype.value
        name = str(dtype).split("(", 1)[0]
        kinds: dict[str, LogicalKind] = {
            "bool": "boolean", "boolean": "boolean", "Boolean": "boolean",
            "i8": "integer", "i16": "integer", "i32": "integer", "i64": "integer",
            "u8": "integer", "u16": "integer", "u32": "integer", "u64": "integer",
            "integer": "integer", "Int8": "integer", "Int16": "integer",
            "Int32": "integer", "Int64": "integer", "UInt8": "integer",
            "UInt16": "integer", "UInt32": "integer", "UInt64": "integer",
            "fp32": "float", "fp64": "float", "float": "float", "number": "float",
            "Float32": "float", "Float64": "float",
            "string": "text", "str": "text", "text": "text", "String": "text",
        }
        kind = kinds.get(name)
        storage: StorageKind = (
            input_type.storage_kind
            if input_type is not None and input_type.storage_kind != "native"
            else "native"
        )
        if kind is None:
            return ResolvedOperand(OperandType("other", storage, True), native_dtype)
        return ResolvedOperand(OperandType(kind, storage, True), native_dtype)
    def fixed_result_type(
        self,
        logical_kind: LogicalKind,
        nullable: bool | None,
        input_type: Any = None,
        node: Any = None,
    ) -> Any:
        """Describe a backend result promised by a declarative fixed result rule."""
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        return ResolvedOperand(OperandType(logical_kind, "native", nullable))

    def preserve_result_type(self, resolved: Any) -> Any:
        """Preserving operations retain the input representation exactly."""
        return resolved

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
        """Combine matching logical operands without guessing storage promotion."""
        first = operands[0]
        storages = {operand.descriptor.storage_kind for operand in operands}
        non_native = storages.difference({"native"})
        storage: StorageKind
        if "sql_dynamic" in non_native:
            storage = "sql_dynamic"
        elif len(non_native) == 1:
            storage = next(iter(non_native))
        elif non_native and all(item.startswith("pandas_") for item in non_native):
            storage = first.descriptor.storage_kind
            if storage == "native":
                storage = "pandas_numpy"
        elif not non_native:
            storage = "native"
        else:
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "operand metadata is unresolved: branches have incompatible storage",
                backend=self.BACKEND_NAME,
                function_key=None,
            )
        native = first.native_dtype
        if any(operand.native_dtype != native for operand in operands[1:]):
            # Logical agreement does not establish a native width or precision.
            native = None
        from mountainash.core.dtypes.metadata import OperandType
        from mountainash.expressions.core.unified_visitor.type_context import ResolvedOperand

        return ResolvedOperand(
            OperandType(first.descriptor.logical_kind, storage, nullable), native
        )

    def prepare_coalesce_arguments(
        self,
        arguments: list[Any],
        null_scalars: list[bool],
        result_type: Any = None,
    ) -> list[Any]:
        """Apply a backend-local coalesce lowering adjustment."""
        return arguments

    def normalize_conditional_branch(
        self,
        expression: Any,
        branch_type: Any,
        result_type: Any,
        *,
        requires_null_carrier: bool,
    ) -> Any:
        """Prepare one conditional result branch for its backend storage."""
        return expression

    def normalize_conditional_result(
        self, expression: Any, result_type: Any, *, requires_null_carrier: bool
    ) -> Any:
        """Return a backend-normalized conditional result when required."""
        return expression

    def _unresolvable_literal(self, value: Any) -> Exception:
        from mountainash.core.types import BackendCapabilityError

        return BackendCapabilityError(
            f"operand metadata is unresolved for literal {type(value).__name__}",
            backend=self.BACKEND_NAME,
            function_key=None,
        )

    def _call_with_expr_support(
        self,
        fn: Any,
        *,
        function_key: Any,
        **named_args: Any,
    ) -> Any:
        """Attach explanation only to an identified immediate native failure."""
        from mountainash.core.capabilities import (
            CapabilityRegistry,
            PolicyConsumer,
            WILDCARD_PARAM,
        )
        from mountainash.core.limitations import call_with_limitation_enrichment

        if not self.execution_context.policy.has_demand(PolicyConsumer.IMMEDIATE_ERROR):
            return fn()
        limitations: dict[tuple[Any, str], Any] = {}
        for param in (*named_args, WILDCARD_PARAM):
            fact = CapabilityRegistry.capability_for(
                function_key, param, self.backend_type, self.dialect,
                consumer=PolicyConsumer.IMMEDIATE_ERROR,
                execution_context=self.execution_context,
            )
            if (
                fact is not None
                and fact.consumer is PolicyConsumer.IMMEDIATE_ERROR
            ):
                limitations[(function_key, param)] = fact
        return call_with_limitation_enrichment(
            fn,
            limitations=limitations,
            backend_name=self.BACKEND_NAME,
            operation_key=function_key,
            named_args=named_args,
            identify_issue=getattr(self, "identify_native_issue", None),
            execution_context=self.execution_context,
        )
