"""Scope-bound, metadata-only operand resolution for expression compilation."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterator, TYPE_CHECKING

from mountainash.core.dtypes.metadata import FixedResultType, OperandType, PreserveResultType
from mountainash.core.types import BackendCapabilityError

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class ResolvedOperand:
    """An operand descriptor paired with backend-owned native dtype evidence."""

    descriptor: OperandType
    native_dtype: Any = None


@dataclass
class _Scope:
    input_data: Any
    semantic_types: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
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

    @property
    def has_lexical_inputs(self) -> bool:
        return bool(self._scopes) and any(
            self.has_lexical_evidence(shape)
            for shape in self._scopes[-1].semantic_types.values()
        )

    @contextmanager
    def input_scope(
        self, input_data: Any, semantic_types: Mapping[str, Any] | None = None,
    ) -> Iterator[None]:
        self._scopes.append(_Scope(input_data, MappingProxyType(dict(semantic_types or {}))))
        try:
            yield
        finally:
            self._scopes.pop()

    def semantic_shape(
        self, node: Any, *, input_names: tuple[str, ...] | None = None,
        output_index: int = 0,
    ) -> Any:
        """Return semantic evidence carried by an expression without evaluating it."""
        from mountainash.core.dtypes import DecimalDtype, MountainashDtype, NativeDtype, parse_cast_target
        from mountainash.expressions.core.expression_nodes import (
            CastNode, FieldReferenceNode, IfThenNode, LiteralNode, OverNode, ScalarFunctionNode,
        )
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_VALUE,
            FKEY_MOUNTAINASH_NAME,
            FKEY_MOUNTAINASH_SCALAR_STRUCT,
            FKEY_MOUNTAINASH_SCALAR_LIST,
            FKEY_SUBSTRAIT_SCALAR_COMPARISON,
        )
        from mountainash.typespec.source_shape import SourceShape, declared_field_shape
        from mountainash.expressions.core.output_names import resolve_output_names

        if not self._scopes:
            return None
        scope = self._scopes[-1]
        if isinstance(node, FieldReferenceNode):
            output = resolve_output_names(node, input_names=input_names)
            names = output.names or ()
            if not names and node.field in scope.semantic_types:
                names = (node.field,)
            index = 0 if len(names) == 1 else output_index
            return scope.semantic_types.get(names[index]) if index < len(names) else None
        if isinstance(node, OverNode):
            return self.semantic_shape(
                node.expression, input_names=input_names, output_index=output_index,
            )
        if isinstance(node, LiteralNode):
            return None
        if isinstance(node, CastNode):
            if isinstance(node.target_type, NativeDtype):
                # Native targets retain backend-owned parameters and do not
                # establish portable numeric evidence.
                return None
            target = parse_cast_target(node.target_type)
            if target is MountainashDtype.STRING:
                return None
            if isinstance(target, DecimalDtype) or target in (MountainashDtype.LEXICAL_INTEGER, MountainashDtype.LEXICAL_DECIMAL):
                return SourceShape(target)
            source = self.semantic_shape(node.input, input_names=input_names, output_index=output_index)
            if self.has_lexical_evidence(source):
                return SourceShape(target)
            return None
        if isinstance(node, IfThenNode):
            branches = [result for _, result in node.conditions] + [node.else_clause]
            shapes = [self.semantic_shape(branch, input_names=input_names, output_index=output_index) for branch in branches]
            concrete = [shape for shape, branch in zip(shapes, branches)
                        if shape is not None or not self.is_null_scalar(branch)]
            if not concrete:
                return None
            if all(shape == concrete[0] for shape in concrete) and self.has_lexical_evidence(concrete[0]):
                return concrete[0]
            if any(self.has_lexical_evidence(shape) for shape in concrete):
                from mountainash.core.dtypes.errors import LexicalNumericUseError
                raise LexicalNumericUseError("conditional branches have incompatible lexical numeric domains")
            return None
        if isinstance(node, ScalarFunctionNode):
            key = node.function_key
            if key is FKEY_MOUNTAINASH_SCALAR_VALUE.NUMERIC_CAST:
                target = parse_cast_target(node.options.get("dtype"))
                if target is MountainashDtype.STRING:
                    return None
                if isinstance(target, DecimalDtype) or target in (MountainashDtype.LEXICAL_INTEGER, MountainashDtype.LEXICAL_DECIMAL):
                    return SourceShape(target)
                source = self.semantic_shape(node.arguments[0], input_names=input_names, output_index=output_index)
                return SourceShape(target) if self.has_lexical_evidence(source) else None
            if key in set(FKEY_MOUNTAINASH_NAME):
                return self.semantic_shape(node.arguments[0], input_names=input_names, output_index=output_index)
            if key is FKEY_SUBSTRAIT_SCALAR_COMPARISON.COALESCE:
                shapes = [self.semantic_shape(arg, input_names=input_names, output_index=output_index) for arg in node.arguments]
                concrete = [shape for shape, arg in zip(shapes, node.arguments)
                            if shape is not None or not self.is_null_scalar(arg)]
                if concrete and all(shape == concrete[0] for shape in concrete):
                    return concrete[0] if self.has_lexical_evidence(concrete[0]) else None
                if any(self.has_lexical_evidence(shape) for shape in concrete):
                    from mountainash.core.dtypes.errors import LexicalNumericUseError
                    raise LexicalNumericUseError("coalesce branches have incompatible lexical numeric domains")
                return None
            if key is FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST:
                return SourceShape(
                    MountainashDtype.STRUCT,
                    struct_fields=tuple(
                        (field.name, declared_field_shape(field) or SourceShape(None))
                        for field in node.options["fields"]
                    ),
                )
            if key is FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS and node.options.get("item_object_fields"):
                return SourceShape(
                    MountainashDtype.LIST,
                    SourceShape(
                        MountainashDtype.STRUCT,
                        struct_fields=tuple(
                            (field.name, declared_field_shape(field) or SourceShape(None))
                            for field in node.options["item_object_fields"]
                        ),
                    ),
                )
            if key in {FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD, FKEY_MOUNTAINASH_SCALAR_LIST.GET}:
                source = self.semantic_shape(
                    node.arguments[0], input_names=input_names, output_index=output_index,
                )
                if source is not None:
                    if key is FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD:
                        return dict(source.struct_fields).get(node.options["field_name"])
                    return source.item_shape
        return None

    @staticmethod
    def has_lexical_evidence(shape: Any) -> bool:
        from mountainash.core.dtypes import MountainashDtype
        if shape is None:
            return False
        if shape.canonical_type in (
            MountainashDtype.LEXICAL_INTEGER, MountainashDtype.LEXICAL_DECIMAL,
        ):
            return True
        if shape.item_shape is not None and TypeContext.has_lexical_evidence(shape.item_shape):
            return True
        return any(TypeContext.has_lexical_evidence(child) for _, child in shape.struct_fields)
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

    def _numeric_cast_input_type(self, argument: Any) -> ResolvedOperand:
        from mountainash.expressions.core.expression_nodes import LiteralNode

        if (
            isinstance(argument, LiteralNode)
            and not argument.is_native
            and not self.backend.is_native_expression(argument.value)
        ):
            from mountainash.expressions.core.numeric_cast import prepare_numeric_cast_literal

            carrier = prepare_numeric_cast_literal(argument.value)
            return self.backend.literal_operand_type(carrier, argument.dtype)
        return self.resolve_native(argument)

    def _scalar_result_type(self, node: Any, input_data: Any) -> ResolvedOperand:
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_VALUE,
            FKEY_SUBSTRAIT_SCALAR_COMPARISON,
        )
        from mountainash.expressions.core.expression_system.function_mapping.registry import (
            ExpressionFunctionRegistry,
        )

        if node.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.NUMERIC_CAST:
            argument = self._argument_by_name(
                ExpressionFunctionRegistry.get(node.function_key).protocol_method,
                node.arguments,
                "x",
            )
            input_type = self._numeric_cast_input_type(argument)
            return self.backend.cast_operand_type(
                node.options["dtype"], input_type.descriptor
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
            FKEY_MOUNTAINASH_SCALAR_VALUE,
            FKEY_SUBSTRAIT_SCALAR_COMPARISON,
        )
        from mountainash.expressions.core.expression_system.function_mapping.registry import (
            ExpressionFunctionRegistry,
        )

        if node.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.NUMERIC_CAST:
            definition = ExpressionFunctionRegistry.get(node.function_key)
            argument = self._argument_by_name(
                definition.protocol_method, node.arguments, "x"
            )
            input_type = self._numeric_cast_input_type(argument)
            if input_type is None:
                return None
            return self.backend.cast_operand_type(
                node.options["dtype"], input_type.descriptor
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
