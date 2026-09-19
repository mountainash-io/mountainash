"""Scope-bound, metadata-only operand resolution for expression compilation."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

from mountainash.core.dtypes.metadata import FixedResultType, OperandType, PreserveResultType
from mountainash.core.types import BackendCapabilityError


@dataclass(frozen=True)
class ResolvedOperand:
    """An operand descriptor paired with backend-owned native dtype evidence."""

    descriptor: OperandType
    native_dtype: Any = None


@dataclass
class _Scope:
    input_data: Any
    resolved: dict[int, tuple[Any, ResolvedOperand]] = field(default_factory=dict)


class TypeContext:
    """Lazily resolve AST identity metadata in one native input scope."""

    def __init__(self, backend: Any, native_expression: Any = None) -> None:
        self.backend = backend
        self._native_expression = native_expression
        self._scopes: list[_Scope] = []

    @property
    def active(self) -> bool:
        """Whether resolution currently has a native input scope."""
        return bool(self._scopes)

    @contextmanager
    def input_scope(self, input_data: Any) -> Iterator[None]:
        self._scopes.append(_Scope(input_data))
        try:
            yield
        finally:
            self._scopes.pop()

    def resolve(self, node: Any) -> OperandType:
        return self.resolve_native(node).descriptor

    def native_dtype(self, node: Any) -> Any:
        return self.resolve_native(node).native_dtype

    def cached_native(self, node: Any) -> ResolvedOperand | None:
        """Return already-required metadata without starting a resolution pass."""
        if not self._scopes:
            return None
        cached = self._scopes[-1].resolved.get(id(node))
        if cached is not None and cached[0] is node:
            return cached[1]
        return None

    def resolve_native(self, node: Any) -> ResolvedOperand:
        scope = self._scope_for(node)
        cached = scope.resolved.get(id(node))
        if cached is not None and cached[0] is node:
            return cached[1]
        resolved = self._resolve_uncached(node, scope.input_data)
        scope.resolved[id(node)] = (node, resolved)
        return resolved

    def _scope_for(self, node: Any) -> _Scope:
        if self._scopes and self._scopes[-1].input_data is not None:
            return self._scopes[-1]
        raise self._unresolved(node, "no native input scope is bound")

    def resolve_declared_native(self, node: Any) -> ResolvedOperand | None:
        """Resolve only metadata declared by the AST without native inference."""
        if not self._scopes:
            return None
        scope = self._scopes[-1]
        if scope.input_data is None:
            return None
        cached = scope.resolved.get(id(node))
        if cached is not None and cached[0] is node:
            return cached[1]
        resolved = self._resolve_declared_uncached(node, scope.input_data)
        if resolved is not None:
            scope.resolved[id(node)] = (node, resolved)
        return resolved

    def _resolve_declared_uncached(
        self, node: Any, input_data: Any
    ) -> ResolvedOperand | None:
        from mountainash.expressions.core.expression_nodes import (
            CastNode,
            FieldReferenceNode,
            IfThenNode,
            LiteralNode,
            ScalarFunctionNode,
        )

        if isinstance(node, FieldReferenceNode):
            return self.backend.field_operand_type(input_data, node.field)
        if isinstance(node, LiteralNode):
            return self.backend.literal_operand_type(node.value, node.dtype)
        if isinstance(node, CastNode):
            resolved = self.resolve_declared_native(node.input)
            if resolved is None:
                return None
            return self.backend.cast_operand_type(node.target_type, resolved.descriptor)
        if isinstance(node, IfThenNode):
            branches = [result for _, result in node.conditions] + [node.else_clause]
            resolved = [self.resolve_declared_native(branch) for branch in branches]
            if any(item is None for item in resolved):
                return None
            concrete = [
                item
                for item in resolved
                if item.descriptor.logical_kind != "null"
            ]
            if concrete and any(
                item.descriptor.logical_kind != concrete[0].descriptor.logical_kind
                for item in concrete[1:]
            ):
                return None
            return self._common_result_type(branches, conditional=True)
        if isinstance(node, ScalarFunctionNode):
            return self._declared_scalar_result_type(node)
        return None

    def _resolve_uncached(self, node: Any, input_data: Any) -> ResolvedOperand:
        from mountainash.expressions.core.expression_nodes import (
            CastNode,
            FieldReferenceNode,
            IfThenNode,
            LiteralNode,
            ScalarFunctionNode,
        )

        if isinstance(node, FieldReferenceNode):
            return self.backend.field_operand_type(input_data, node.field)
        if isinstance(node, LiteralNode):
            return self.backend.literal_operand_type(node.value, node.dtype)
        if isinstance(node, CastNode):
            return self.backend.cast_operand_type(
                node.target_type, self.resolve_native(node.input).descriptor
            )
        if isinstance(node, IfThenNode):
            return self._common_result_type(
                [result for _, result in node.conditions] + [node.else_clause],
                conditional=True,
            )
        if isinstance(node, ScalarFunctionNode):
            return self._scalar_result_type(node, input_data)
        if self._native_expression is not None:
            return self.backend.infer_expression_operand_type(
                input_data, self._native_expression(node)
            )
        raise self._unresolved(node, f"no metadata-only resolver for {type(node).__name__}")

    def _scalar_result_type(self, node: Any, input_data: Any) -> ResolvedOperand:
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_COMPARISON,
        )
        from mountainash.expressions.core.expression_system.function_mapping.registry import (
            ExpressionFunctionRegistry,
        )

        if node.function_key is FKEY_SUBSTRAIT_SCALAR_COMPARISON.COALESCE:
            return self._common_result_type(node.arguments, conditional=False)

        definition = ExpressionFunctionRegistry.get(node.function_key)
        rule = definition.result_type
        if isinstance(rule, FixedResultType):
            input_type = None
            if definition.type_arguments:
                argument = self._argument_by_name(
                    definition.protocol_method,
                    node.arguments,
                    definition.type_arguments[0],
                )
                input_type = self.resolve_native(argument)
            return self.backend.fixed_result_type(
                rule.logical_kind, rule.nullable, input_type, node
            )
        if isinstance(rule, PreserveResultType):
            argument = self._argument_by_name(
                definition.protocol_method, node.arguments, rule.argument
            )
            resolved = self.resolve_native(argument)
            if (
                rule.require_kind is not None
                and resolved.descriptor.logical_kind != rule.require_kind
            ):
                raise self._unresolved(
                    node,
                    f"{node.function_key} preserves only {rule.require_kind!r} operands",
                )
            return self.backend.preserve_result_type(resolved)
        if self._native_expression is not None:
            return self.backend.infer_expression_operand_type(
                input_data, self._native_expression(node)
            )
        raise self._unresolved(node, f"{node.function_key} has no metadata-only result rule")

    def _declared_scalar_result_type(
        self, node: Any
    ) -> ResolvedOperand | None:
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_COMPARISON,
        )
        from mountainash.expressions.core.expression_system.function_mapping.registry import (
            ExpressionFunctionRegistry,
        )

        if node.function_key is FKEY_SUBSTRAIT_SCALAR_COMPARISON.COALESCE:
            if any(
                self.resolve_declared_native(argument) is None
                for argument in node.arguments
            ):
                return None
            return self._common_result_type(node.arguments, conditional=False)

        definition = ExpressionFunctionRegistry.get(node.function_key)
        rule = definition.result_type
        if isinstance(rule, FixedResultType):
            input_type = None
            if definition.type_arguments:
                argument = self._argument_by_name(
                    definition.protocol_method,
                    node.arguments,
                    definition.type_arguments[0],
                )
                input_type = self.resolve_declared_native(argument)
                if input_type is None:
                    return None
            return self.backend.fixed_result_type(
                rule.logical_kind, rule.nullable, input_type, node
            )
        if isinstance(rule, PreserveResultType):
            argument = self._argument_by_name(
                definition.protocol_method, node.arguments, rule.argument
            )
            resolved = self.resolve_declared_native(argument)
            if resolved is None:
                return None
            if (
                rule.require_kind is not None
                and resolved.descriptor.logical_kind != rule.require_kind
            ):
                raise self._unresolved(
                    node,
                    f"{node.function_key} preserves only {rule.require_kind!r} operands",
                )
            return self.backend.preserve_result_type(resolved)
        return None

    def _argument_by_name(self, method: Any, arguments: list[Any], name: str) -> Any:
        from mountainash.expressions.core.unified_visitor.visitor import (
            _param_name_for,
            _protocol_sig_params,
        )

        for index, argument in enumerate(arguments):
            if _param_name_for(_protocol_sig_params(method), index) == name:
                return argument
        raise self._unresolved(method, f"required operand {name!r} is not bound")

    def _common_result_type(
        self, nodes: list[Any], *, conditional: bool
    ) -> ResolvedOperand:
        resolved = [self.resolve_native(node) for node in nodes]
        concrete_pairs = [
            (node, item)
            for node, item in zip(nodes, resolved, strict=True)
            if item.descriptor.logical_kind != "null"
        ]
        if not concrete_pairs:
            return self.backend.fixed_result_type("null", True)
        concrete_nodes = [node for node, _ in concrete_pairs]
        concrete = [item for _, item in concrete_pairs]
        kind = concrete[0].descriptor.logical_kind
        if any(item.descriptor.logical_kind != kind for item in concrete[1:]):
            raise self._unresolved(nodes[0], "branches have no common concrete logical kind")
        nullable = any(item.descriptor.nullable is not False for item in resolved)
        has_literal_null = any(
            item.descriptor.logical_kind == "null" for item in resolved
        )
        has_nullable_storage = any(
            item.descriptor.storage_kind in {"pandas_nullable", "pandas_arrow"}
            for item in resolved
        )
        return self.backend.common_result_type(
            concrete,
            nullable,
            composition="conditional" if conditional else "coalesce",
            concrete_nodes=concrete_nodes,
            has_literal_null=has_literal_null,
            has_nullable_storage=has_nullable_storage,
        )

    @staticmethod
    def is_null_scalar(node: Any) -> bool:
        """Recognize literal absence through preserve wrappers without inference."""
        from mountainash.core.value_classification import ValueKind, value_kind
        from mountainash.expressions.core.expression_nodes import LiteralNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_mapping.registry import (
            ExpressionFunctionRegistry,
        )

        if isinstance(node, LiteralNode):
            return not node.is_native and value_kind(node.value) is ValueKind.ABSENT
        if (
            isinstance(node, ScalarFunctionNode)
            and node.function_key is not None
            and len(node.arguments) == 1
        ):
            rule = ExpressionFunctionRegistry.get(node.function_key).result_type
            return (
                isinstance(rule, PreserveResultType)
                and rule.require_kind is None
                and TypeContext.is_null_scalar(node.arguments[0])
            )
        return False

    def _unresolved(self, node: Any, detail: str) -> BackendCapabilityError:
        return BackendCapabilityError(
            f"operand metadata is unresolved: {detail}",
            backend=self.backend.BACKEND_NAME,
            function_key=getattr(node, "function_key", None),
        )
