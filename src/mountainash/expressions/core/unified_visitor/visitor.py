"""Unified expression visitor for Substrait-aligned nodes.

This module provides a single visitor that handles all node types,
replacing the previous category-specific visitors (BooleanExpressionVisitor,
ArithmeticExpressionVisitor, etc.).

The visitor:
1. Traverses the expression tree
2. Resolves function definitions from the registry
3. Calls the appropriate backend method for each operation
"""

from __future__ import annotations
from contextlib import contextmanager
from dataclasses import replace
from enum import Enum
from functools import lru_cache
import inspect
from typing import Any, TYPE_CHECKING, Iterator

from ..expression_nodes import (
    ExpressionNode,
    LiteralNode,
    FieldReferenceNode,
    ScalarFunctionNode,
    IfThenNode,
    CastNode,
    SingularOrListNode,
    WindowFunctionNode,
    OverNode,
)
from ..expression_system.function_mapping.registry import ExpressionFunctionRegistry as FunctionRegistry
from .type_context import TypeContext

# Alias for compatibility
SubstraitNode = ExpressionNode


@lru_cache(maxsize=None)
def _protocol_sig_params(protocol_method: Any) -> tuple:
    """Protocol parameters (minus ``self``) for a protocol method.

    ``protocol_method`` is the stable per-operation object stored on the
    registry's function def, so it is a sound cache key: the same operation
    resolves the same method object on every dispatch. Caching here avoids
    re-running ``inspect.signature`` on every ``_gate_and_resolve_args`` call.
    """
    return tuple(p for p in inspect.signature(protocol_method).parameters.values() if p.name != "self")


def _param_name_for(sig_params: tuple, index: int) -> str | None:
    """Map an emitted argument's position to its protocol parameter name.

    Every index at or after the VAR_POSITIONAL parameter (if any) maps to
    that parameter's name — not just an exact index match — so a variadic
    parameter followed by trailing named parameters (``is_in``'s
    ``(needle, /, *haystack, unknown_values=None, member_unknown_values=None)``,
    ``concat``'s ``(*input, null_handling=None)``) correctly maps every
    variadic member, however many there are, instead of silently drifting
    into the trailing parameter names once the index exceeds
    ``len(sig_params)``.
    """
    var_positional_idx = next(
        (i for i, p in enumerate(sig_params) if p.kind is inspect.Parameter.VAR_POSITIONAL),
        None,
    )
    if var_positional_idx is not None and index >= var_positional_idx:
        return sig_params[var_positional_idx].name
    if index < len(sig_params):
        return sig_params[index].name
    return None


if TYPE_CHECKING:
    from ...types import SupportedExpressions


class UnifiedExpressionVisitor:
    """Single visitor that compiles all Substrait-aligned nodes to backend expressions.

    This visitor replaces the 12+ category-specific visitors with a single
    implementation that:
    - Derives method names from function_key enum values
    - Recursively visits child nodes
    - Calls backend methods with resolved arguments

    Example:
        >>> visitor = UnifiedExpressionVisitor(polars_expression_system)
        >>> backend_expr = visitor.visit(node)
    """

    def __init__(
        self,
        expression_system: Any,
        enforce_capabilities: bool = True,
        *,
        diagnostic_trace: Any = None,
        conform_node_id: str | None = None,
        input_data: Any = None,
    ) -> None:
        """Initialize the visitor with a backend expression system.

        ``diagnostic_trace`` is supplied only by relation conform
        compilation. Keeping it optional preserves standalone expression
        compilation exactly as before.
        """
        self.backend = expression_system
        self.enforce_capabilities = enforce_capabilities
        self.diagnostic_trace = diagnostic_trace
        self.conform_node_id = conform_node_id
        self.raising_diagnostic = None
        self._input_data = input_data
        self.type_context = TypeContext(expression_system, self.visit)
        if enforce_capabilities:
            # A gating consumer must ensure the capability declaration modules
            # are imported before querying the registry (bootstrap.py contract):
            # otherwise a gate silently no-ops on a cold path where nothing has
            # imported the declaration module. Query-path autoload — a no-op
            # in LOADED and ISOLATED states, so test fixtures that reset()
            # into ISOLATED do not break the visitor.
            from mountainash.core.capabilities.registry import CapabilityRegistry

            CapabilityRegistry.ensure_loaded()

    @contextmanager
    def input_scope(self, native_input: Any) -> Iterator[None]:
        """Bind one native relation/frame as metadata-only compilation context."""
        with self.type_context.input_scope(native_input):
            yield

    def resolve_operand_type(self, node: ExpressionNode) -> Any:
        """Resolve a node descriptor from the current scope for compiler use."""
        return self.type_context.resolve(node)

    def _is_backend_expression(self, value: Any) -> bool:
        """Check if a value is already a backend expression.

        This detects native expressions that should be passed through
        without wrapping in lit().

        Args:
            value: Value to check

        Returns:
            True if value is a backend expression (pl.Expr, nw.Expr, ir.Expr, etc.)
        """
        # Check common expression type names
        type_name = type(value).__name__
        if type_name == "Expr":
            return True

        # Check module paths for known backends
        module = type(value).__module__
        if module and any(backend in module for backend in ("polars", "narwhals", "ibis")):
            return True

        return False

    def _detect_expression_backend(self, value: Any) -> str:
        """Detect what backend a native expression belongs to.

        Args:
            value: A native expression object

        Returns:
            The backend name as a string (e.g., 'polars', 'ibis', 'narwhals')
        """
        module = type(value).__module__

        if "polars" in module:
            return "polars"
        elif "ibis" in module:
            return "ibis"
        elif "narwhals" in module:
            return "narwhals"
        else:
            return type(value).__name__

    def visit(self, node: SubstraitNode) -> SupportedExpressions:
        """Visit a node and return the compiled backend expression.

        This is the main entry point. Uses double-dispatch via node.accept().

        Args:
            node: Any SubstraitNode to compile

        Returns:
            Backend-native expression (pl.Expr, nw.Expr, ir.Expr, etc.)

        Raises:
            ValueError: If node type is unknown
        """
        if self._input_data is not None and not self.type_context.active:
            with self.input_scope(self._input_data):
                return node.accept(self)
        return node.accept(self)

    def visit_literal(self, node: LiteralNode) -> SupportedExpressions:
        """Compile a literal value to backend expression.

        Args:
            node: LiteralNode with value and optional dtype

        Returns:
            Backend literal expression

        Raises:
            TypeError: If native expression doesn't match target backend
        """
        # Handle native expression passthrough (explicit dtype or auto-detected)
        if node.is_native or self._is_backend_expression(node.value):
            # Validate the native expression matches the target backend
            if not self.backend.is_native_expression(node.value):
                source_backend = self._detect_expression_backend(node.value)
                target_backend = self.backend.backend_type.value
                raise TypeError(
                    f"Backend mismatch: {source_backend} expression cannot be used " f"with {target_backend} backend"
                )
            return node.value

        return self.backend.lit(node.value, dtype=node.dtype)

    def visit_field_reference(self, node: FieldReferenceNode) -> SupportedExpressions:
        """Compile a column reference to backend expression.

        Args:
            node: FieldReferenceNode with column name

        Returns:
            Backend column expression
        """
        # Handle unknown_values for ternary logic (t_col semantics)
        # When unknown_values are specified, the column reference should
        # be wrapped to treat those values as UNKNOWN (0)
        if node.unknown_values is not None and len(node.unknown_values) > 0:
            # Build: when(col.is_in(unknown_values)).then(0).otherwise(col)
            # This is handled at compilation time, not at node creation
            # For now, just return the column - the ternary comparison
            # operators will handle the unknown_values
            pass

        return self.backend.col(node.field)

    def _gate_and_resolve_args(self, function_key, arguments, protocol_method, *, compiled_arguments=None):
        """Per-argument capability gate (spec Section 2).

        LITERAL_ONLY + LiteralNode -> raw value; LITERAL_ONLY + dynamic ->
        compile-time BackendCapabilityError; UNSUPPORTED -> immediate error;
        POLYMORPHIC -> LiteralNode unwraps, expressions compile; default ->
        visit normally. Only GATE facts gate here — ROUTER_METADATA is
        consumed by a backend router and MATERIALIZE_RESIDUE enriches an
        error raised after this returns. Precompiled operands still use their
        original AST for capability checks without a second compilation walk.
        """
        from mountainash.core.capabilities import (
            CapabilityLevel,
            CapabilityRegistry,
            Enforcement,
        )
        from mountainash.core.types import BackendCapabilityError

        backend_family = self.backend.backend_type
        dialect = getattr(self.backend, "dialect", None)

        # Map node.arguments positions to protocol param names.
        # Signature shape: (self, input, /, a, b=None, *varargs) — skip self;
        # every index at/after a VAR_POSITIONAL param maps to its name (see
        # module-level _param_name_for). Cached per protocol_method (stable
        # registry object).
        sig_params = _protocol_sig_params(protocol_method)

        resolved = []
        for i, arg in enumerate(arguments):
            param_name = _param_name_for(sig_params, i)
            fact = (
                CapabilityRegistry.capability_for(function_key, param_name, backend_family, dialect)
                if param_name is not None
                else None
            )
            if fact is not None and (fact.enforcement is not Enforcement.GATE or fact.predicate is not None):
                fact = None  # conditional facts gate only through the collecting path

            level = fact.level if fact is not None else CapabilityLevel.EXPR_CAPABLE

            if self.enforce_capabilities and level is CapabilityLevel.UNSUPPORTED:
                raise BackendCapabilityError(
                    fact.message,
                    backend=self.backend.BACKEND_NAME,
                    function_key=function_key,
                    limitation=fact,
                )
            if (
                level is CapabilityLevel.LITERAL_ONLY
                and isinstance(arg, ExpressionNode)
                and not isinstance(arg, LiteralNode)
                and self.enforce_capabilities
            ):
                raise BackendCapabilityError(
                    fact.message,
                    backend=self.backend.BACKEND_NAME,
                    function_key=function_key,
                    limitation=fact,
                )
            if (
                (level is CapabilityLevel.LITERAL_ONLY or level is CapabilityLevel.POLYMORPHIC)
                and isinstance(arg, LiteralNode)
            ):
                resolved.append(arg.value)
            elif compiled_arguments is not None and i in compiled_arguments:
                resolved.append(compiled_arguments[i])
            else:
                resolved.append(self.visit(arg) if isinstance(arg, ExpressionNode) else arg)
        return resolved

    def _bound_call(self, function_key, protocol_method, arguments, options):
        from mountainash.core.capabilities.predicates import bind_expression_call

        return bind_expression_call(
            operation_key=function_key,
            backend=self.backend.backend_type,
            dialect=getattr(self.backend, "dialect", None),
            protocol_method=protocol_method,
            arguments=arguments,
            options=options,
        )

    def _gate_predicate_violations(self, bound, *, phase: str) -> None:
        """Collect capability blockers in the requested metadata-resolution phase."""
        if not self.enforce_capabilities:
            return
        from mountainash.core.capabilities import CapabilityRegistry
        from mountainash.core.types import BackendCapabilityError

        violations = CapabilityRegistry.violations_for(bound, phase=phase)
        if violations:
            ordered = sorted(violations, key=lambda f: (f.param, f.message))
            combined = "; ".join(f.message for f in ordered)
            raise BackendCapabilityError(
                combined,
                backend=self.backend.BACKEND_NAME,
                function_key=bound.operation_key,
                limitation=ordered[0],
            )

    def _gate_operation(self, function_key) -> None:
        if not self.enforce_capabilities:
            return
        from mountainash.core.capabilities import (
            CapabilityLevel, CapabilityRegistry, Enforcement, WILDCARD_PARAM,
        )
        from mountainash.core.types import BackendCapabilityError

        fact = CapabilityRegistry.capability_for(
            function_key, WILDCARD_PARAM, self.backend.backend_type,
            getattr(self.backend, "dialect", None),
        )
        if (
            fact is not None
            and fact.predicate is None
            and fact.enforcement is Enforcement.GATE
            and fact.level is CapabilityLevel.UNSUPPORTED
        ):
            raise BackendCapabilityError(
                fact.message, backend=self.backend.BACKEND_NAME,
                function_key=function_key, limitation=fact,
            )

    def _gate_options(self, function_key, options) -> None:
        if not options or not self.enforce_capabilities:
            return
        from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry, Enforcement
        from mountainash.core.types import BackendCapabilityError

        dialect = getattr(self.backend, "dialect", None)
        for name, value in options.items():
            fact = CapabilityRegistry.capability_for(
                function_key, name, self.backend.backend_type, dialect,
                option_value=str(value.value if isinstance(value, Enum) else value),
            )
            if (
                fact is not None
                and fact.predicate is None
                and fact.enforcement is Enforcement.GATE
                and (
                    fact.level is CapabilityLevel.UNSUPPORTED
                    or (fact.level is CapabilityLevel.LITERAL_ONLY and isinstance(value, ExpressionNode))
                )
            ):
                raise BackendCapabilityError(
                    fact.message, backend=self.backend.BACKEND_NAME,
                    function_key=function_key, limitation=fact,
                )

    def _required_operand_types(self, func_def, protocol_method, arguments, options=None) -> dict[str, Any]:
        """Resolve function-declared and capability metadata operands."""
        required = func_def.type_arguments
        if self.enforce_capabilities:
            from mountainash.core.capabilities import CapabilityRegistry

            capability_names = CapabilityRegistry.metadata_operand_names(
                func_def.function_key,
                self.backend.backend_type,
                getattr(self.backend, "dialect", None),
            )
            if capability_names:
                required = capability_names if not required else capability_names.union(required)
        if not required:
            return {}

        resolved: dict[str, Any] = {}
        for index, argument in enumerate(arguments):
            name = _param_name_for(_protocol_sig_params(protocol_method), index)
            if name is not None and name in required and isinstance(argument, ExpressionNode):
                resolved[name] = self.type_context.resolve(argument)
        if options:
            for name in required:
                argument = options.get(name)
                if name not in resolved and isinstance(argument, ExpressionNode):
                    resolved[name] = self.type_context.resolve(argument)
        missing = set(required).difference(resolved)
        if missing:
            raise self.type_context._unresolved(
                func_def.function_key,
                f"required operands are not bound: {', '.join(sorted(missing))}",
            )
        return resolved

    def visit_scalar_function(self, node: ScalarFunctionNode) -> SupportedExpressions:
        """Compile a scalar function call to backend expression.

        This is the main dispatch method that handles most operations.
        Uses FunctionRegistry to look up the protocol method and call it on the backend.

        Args:
            node: ScalarFunctionNode with function name, arguments, and options

        Returns:
            Backend expression result of calling the function
        """
        # Look up function definition from registry
        func_def = FunctionRegistry.get(node.function_key)

        # Get the protocol method from the function definition
        protocol_method = func_def.protocol_method
        if protocol_method is None:
            raise ValueError(f"Function {node.function_key} has no protocol_method defined")

        # Get method name from protocol method
        method_name = protocol_method.__name__

        bound = self._bound_call(node.function_key, protocol_method, node.arguments, node.options)
        self._gate_predicate_violations(bound, phase="raw")

        self._gate_operation(node.function_key)

        operand_types = self._required_operand_types(func_def, protocol_method, node.arguments)
        args = self._gate_and_resolve_args(node.function_key, node.arguments, protocol_method)
        from ..expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_COMPARISON,
        )

        if node.function_key is FKEY_SUBSTRAIT_SCALAR_COMPARISON.COALESCE:
            args = self.backend.prepare_coalesce_arguments(
                args,
                [self.type_context.is_null_scalar(argument) for argument in node.arguments],
                self.type_context.cached_native(node),
            )
        self._gate_predicate_violations(replace(bound, operand_types=operand_types), phase="complete")

        # Get the backend method
        if not hasattr(self.backend, method_name):
            raise AttributeError(
                f"Backend {type(self.backend).__name__} has no method '{method_name}' "
                f"for function {node.function_key}"
            )
        method = getattr(self.backend, method_name)

        options = node.options or {}
        self._gate_options(node.function_key, options)
        diagnostic = None
        if self.diagnostic_trace is not None:
            diagnostic = self.diagnostic_trace.record(
                node,
                backend_family=self.backend.backend_type,
                dialect=getattr(self.backend, "dialect", None),
                conform_node_id=self.conform_node_id,
            )
        try:
            with self.backend.operand_types(operand_types):
                if options:
                    return method(*args, **options)
                return method(*args)
        except Exception:
            self.raising_diagnostic = diagnostic
            raise

    def visit_if_then(self, node: IfThenNode) -> SupportedExpressions:
        """Compile a conditional expression to backend expression.

        Handles when/then/otherwise chains. This is used for:
        - Direct when().then().otherwise() expressions
        - Ternary logic lowering (t_eq, t_gt, etc.)

        Args:
            node: IfThenNode with conditions list and else_clause

        Returns:
            Backend conditional expression
        """
        if not node.conditions:
            return self.visit(node.else_clause)

        from ..expression_system.function_keys.enums import FKEY_SUBSTRAIT_CONDITIONAL

        function_key = FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE
        func_def = FunctionRegistry.get(function_key)
        protocol_method = func_def.protocol_method
        needs_binding = self.enforce_capabilities or bool(func_def.type_arguments)
        result_type, requires_null_carrier = self._conditional_result_metadata(node)
        logical_else = node.else_clause
        last_index = len(node.conditions) - 1
        compiled_arguments: dict[int, SupportedExpressions] | None = None
        for index in range(last_index, -1, -1):
            condition, branch = node.conditions[index]
            arguments = (condition, branch, logical_else)
            operand_types = {}
            if needs_binding:
                bound = self._bound_call(function_key, protocol_method, arguments, None)
                self._gate_predicate_violations(bound, phase="raw")
                self._gate_operation(function_key)
                operand_types = self._required_operand_types(func_def, protocol_method, arguments)
            args = self._gate_and_resolve_args(
                function_key, arguments, protocol_method,
                compiled_arguments=compiled_arguments,
            )
            if needs_binding:
                self._gate_predicate_violations(replace(bound, operand_types=operand_types), phase="complete")
            args[1] = self._normalize_conditional_branch(
                branch, args[1], result_type, requires_null_carrier
            )
            if index == last_index:
                args[2] = self._normalize_conditional_branch(
                    node.else_clause, args[2], result_type, requires_null_carrier
                )
            with self.backend.operand_types(operand_types):
                current = self.backend.if_then_else(*args)
            if index:
                if needs_binding:
                    compiled_arguments = {2: current}
                logical_else = (
                    IfThenNode(conditions=[(condition, branch)], else_clause=logical_else)
                    if needs_binding else current
                )
        return self._normalize_if_then_result(current, result_type, requires_null_carrier)

    def _conditional_result_metadata(self, node: IfThenNode) -> tuple[Any, bool]:
        """Read only metadata an enclosing type-sensitive call already required."""
        result_type = self.type_context.cached_native(node)
        if result_type is None:
            return None, False
        branches = [result for _, result in node.conditions] + [node.else_clause]
        branch_types = [self.type_context.cached_native(branch) for branch in branches]
        has_literal_null = any(
            branch_type is not None and branch_type.descriptor.logical_kind == "null" for branch_type in branch_types
        )
        storages = {branch_type.descriptor.storage_kind for branch_type in branch_types if branch_type is not None}
        has_nullable_storage = bool({"pandas_nullable", "pandas_arrow"}.intersection(storages))
        concrete = [
            branch_type
            for branch_type in branch_types
            if branch_type is not None and branch_type.descriptor.logical_kind != "null"
        ]
        different_dtypes = bool(concrete) and any(
            branch_type.native_dtype != concrete[0].native_dtype for branch_type in concrete[1:]
        )
        requires_null_carrier = has_literal_null or different_dtypes or (has_nullable_storage and len(storages) > 1)
        return result_type, requires_null_carrier

    def _normalize_conditional_branch(
        self,
        node: ExpressionNode,
        expression: SupportedExpressions,
        result_type: Any,
        requires_null_carrier: bool,
    ) -> SupportedExpressions:
        """Prepare a concrete branch only when its result type is already known."""
        if result_type is None:
            return expression
        branch_type = self.type_context.cached_native(node)
        if branch_type is None:
            return expression
        return self.backend.normalize_conditional_branch(
            expression,
            branch_type,
            result_type,
            requires_null_carrier=requires_null_carrier,
        )

    def _normalize_if_then_result(
        self,
        expression: SupportedExpressions,
        result_type: Any,
        requires_null_carrier: bool,
    ) -> SupportedExpressions:
        """Apply the declared backend storage contract without resolving anew."""
        if result_type is None or not requires_null_carrier:
            return expression
        return self.backend.normalize_conditional_result(
            expression,
            result_type,
            requires_null_carrier=requires_null_carrier,
        )

    def visit_cast(self, node: CastNode) -> SupportedExpressions:
        """Compile a type cast to backend expression.

        Args:
            node: CastNode with input expression and target type

        Returns:
            Backend cast expression
        """
        from ..expression_system.function_keys.enums import FKEY_SUBSTRAIT_CAST

        function_key = FKEY_SUBSTRAIT_CAST.CAST
        func_def = FunctionRegistry.get(function_key)
        protocol_method = func_def.protocol_method
        arguments = (node.input,)
        options = {"dtype": node.target_type, "failure_behavior": node.failure_behavior}
        bound = self._bound_call(function_key, protocol_method, arguments, options)
        self._gate_predicate_violations(bound, phase="raw")
        self._gate_operation(function_key)
        operand_types = self._required_operand_types(func_def, protocol_method, arguments)
        args = self._gate_and_resolve_args(function_key, arguments, protocol_method)
        self._gate_predicate_violations(replace(bound, operand_types=operand_types), phase="complete")
        self._gate_options(function_key, options)
        with self.backend.operand_types(operand_types):
            return self.backend.cast(*args, **options)

    def visit_singular_or_list(self, node: SingularOrListNode) -> SupportedExpressions:
        """Compile a membership test (IN operator) to backend expression."""
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_SET,
        )
        from mountainash.expressions.core.expression_system.function_mapping.registry import (
            ExpressionFunctionRegistry,
        )

        protocol_method = ExpressionFunctionRegistry.get_protocol_method(FKEY_MOUNTAINASH_SCALAR_SET.IS_IN)
        # needle maps to param 0; every options member maps to *haystack
        # (VAR_POSITIONAL) via _param_name_for's trailing-varargs rule.
        value_expr, *options = self._gate_and_resolve_args(
            FKEY_MOUNTAINASH_SCALAR_SET.IS_IN,
            (node.value, *node.options),
            protocol_method,
        )
        return self.backend.is_in(value_expr, *options)

    def visit_window_function(self, node: WindowFunctionNode) -> SupportedExpressions:
        """Compile a window function node to backend expression.

        Resolves the function from the registry, calls the backend method,
        then applies the window specification.

        Args:
            node: WindowFunctionNode with function_key, arguments, and window_spec.

        Returns:
            Backend expression with window context applied.

        Raises:
            ValueError: If window_spec is None (i.e., .over() was not called).
        """
        if node.window_spec is None:
            raise ValueError(
                f"Window function '{node.function_key.value}' requires .over() — "
                f"e.g., col('x').{node.function_key.name.lower()}().over('group')"
            )

        # Look up function definition from registry
        func_def = FunctionRegistry.get(node.function_key)
        protocol_method = func_def.protocol_method
        if protocol_method is None:
            raise ValueError(f"Window function {node.function_key} has no protocol_method defined")
        method_name = protocol_method.__name__

        options = dict(node.options) if node.options else {}
        first_sort = node.window_spec.order_by[0] if node.window_spec.order_by else None
        order_node = None
        for parameter in _protocol_sig_params(protocol_method):
            if parameter.name == "descending":
                options["descending"] = (
                    first_sort.descending if first_sort is not None
                    else options.get("descending", parameter.default)
                )
            elif parameter.name == "order_by_col" and first_sort is not None:
                order_node = FieldReferenceNode(field=first_sort.column)
                options["order_by_col"] = order_node

        bound = self._bound_call(node.function_key, protocol_method, node.arguments, options)
        self._gate_predicate_violations(bound, phase="raw")
        self._gate_operation(node.function_key)
        operand_types = self._required_operand_types(func_def, protocol_method, node.arguments, options)
        compiled_args = self._gate_and_resolve_args(node.function_key, node.arguments, protocol_method)
        self._gate_predicate_violations(replace(bound, operand_types=operand_types), phase="complete")
        self._gate_options(node.function_key, options)
        if order_node is not None:
            options["order_by_col"] = self.visit(order_node)

        method = getattr(self.backend, method_name)
        with self.backend.operand_types(operand_types):
            result = method(*compiled_args, **options) if options else method(*compiled_args)
        return self._apply_window_spec(result, node.window_spec)

    def visit_over(self, node: OverNode) -> SupportedExpressions:
        """Compile an OverNode — wraps any expression with window context.

        Visits the inner expression first, then applies the window specification.

        Args:
            node: OverNode with expression and window_spec.

        Returns:
            Backend expression with window context applied.
        """
        inner_result = self.visit(node.expression)
        return self._apply_window_spec(inner_result, node.window_spec)

    def _apply_window_spec(self, expr: Any, window_spec: Any) -> SupportedExpressions:
        """Apply a WindowSpec to a native backend expression.

        Resolves partition_by and order_by columns, then delegates to
        the backend's apply_window method.

        Args:
            expr: Native backend expression to apply window context to.
            window_spec: WindowSpec with partition_by, order_by, and bounds.

        Returns:
            Backend expression with window context applied.
        """
        # Resolve partition_by expressions
        partition_by = []
        for p in window_spec.partition_by:
            if isinstance(p, ExpressionNode):
                partition_by.append(self.visit(p))
            elif isinstance(p, str):
                partition_by.append(self.visit(FieldReferenceNode(field=p)))
            else:
                partition_by.append(p)

        # Resolve order_by expressions
        order_by = []
        for sf in window_spec.order_by:
            col_expr = self.visit(FieldReferenceNode(field=sf.column))
            order_by.append((col_expr, sf.descending))

        return self.backend.apply_window(
            expr,
            partition_by=partition_by,
            order_by=order_by,
            lower_bound=window_spec.lower_bound,
            upper_bound=window_spec.upper_bound,
        )
