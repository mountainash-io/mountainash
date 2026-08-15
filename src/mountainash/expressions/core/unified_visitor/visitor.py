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
from typing import Any, TYPE_CHECKING
from functools import lru_cache
import inspect

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
from ..expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW, FKEY_MOUNTAINASH_WINDOW

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
    return tuple(
        p for p in inspect.signature(protocol_method).parameters.values()
        if p.name != "self"
    )

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

    def __init__(self, expression_system: Any, enforce_capabilities: bool = True) -> None:
        """Initialize the visitor with a backend expression system.

        Args:
            expression_system: Backend ExpressionSystem instance
                              (e.g., PolarsExpressionSystem, IbisExpressionSystem)
            enforce_capabilities: When False, skip the compile-time capability gate.
        """
        self.backend = expression_system
        self.enforce_capabilities = enforce_capabilities
        if enforce_capabilities:
            # A gating consumer must ensure the capability declaration modules
            # are imported before querying the registry (bootstrap.py contract):
            # otherwise a gate silently no-ops on a cold path where nothing has
            # imported the declaration module. Query-path autoload — a no-op
            # in LOADED and ISOLATED states, so test fixtures that reset()
            # into ISOLATED do not break the visitor.
            from mountainash.core.capabilities.registry import CapabilityRegistry
            CapabilityRegistry.ensure_loaded()

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
        if type_name == 'Expr':
            return True

        # Check module paths for known backends
        module = type(value).__module__
        if module and any(backend in module for backend in ('polars', 'narwhals', 'ibis')):
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

        if 'polars' in module:
            return 'polars'
        elif 'ibis' in module:
            return 'ibis'
        elif 'narwhals' in module:
            return 'narwhals'
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
                    f"Backend mismatch: {source_backend} expression cannot be used "
                    f"with {target_backend} backend"
                )
            return node.value

        return self.backend.lit(node.value)

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

    def _gate_and_resolve_args(self, function_key, arguments, protocol_method):
        """Per-argument capability gate (spec Section 2).

        LITERAL_ONLY + LiteralNode -> raw value; LITERAL_ONLY + dynamic ->
        compile-time BackendCapabilityError; UNSUPPORTED -> immediate error;
        POLYMORPHIC -> LiteralNode unwraps, expressions compile; default ->
        visit normally. Only GATE facts gate here — ROUTER_METADATA is
        consumed by a backend router and MATERIALIZE_RESIDUE enriches an
        error raised after this returns.
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
                CapabilityRegistry.capability_for(
                    function_key, param_name, backend_family, dialect
                )
                if param_name is not None
                else None
            )
            if fact is not None and fact.enforcement is not Enforcement.GATE:
                fact = None  # router metadata / materialize residue never gate here

            level = fact.level if fact is not None else CapabilityLevel.EXPR_CAPABLE

            if self.enforce_capabilities and level is CapabilityLevel.UNSUPPORTED:
                raise BackendCapabilityError(
                    fact.message,
                    backend=self.backend.BACKEND_NAME,
                    function_key=function_key,
                    limitation=fact,
                )
            if level is CapabilityLevel.LITERAL_ONLY:
                if isinstance(arg, LiteralNode):
                    resolved.append(arg.value)
                elif isinstance(arg, ExpressionNode):
                    if self.enforce_capabilities:
                        raise BackendCapabilityError(
                            fact.message,
                            backend=self.backend.BACKEND_NAME,
                            function_key=function_key,
                            limitation=fact,
                        )
                    resolved.append(self.visit(arg))
                else:
                    resolved.append(arg)  # already a raw value
            elif level is CapabilityLevel.POLYMORPHIC:
                if isinstance(arg, LiteralNode):
                    resolved.append(arg.value)
                elif isinstance(arg, ExpressionNode):
                    resolved.append(self.visit(arg))
                else:
                    resolved.append(arg)
            else:
                resolved.append(
                    self.visit(arg) if isinstance(arg, ExpressionNode) else arg
                )
        return resolved

    def _gate_predicate_violations(self, function_key, protocol_method, arguments, options) -> None:
        """Collecting call-level gate (§3): predicate facts, once per call."""
        if not self.enforce_capabilities:
            return
        from mountainash.core.capabilities import CapabilityRegistry
        from mountainash.core.capabilities.predicates import bind_expression_call
        from mountainash.core.types import BackendCapabilityError
        bound = bind_expression_call(
            operation_key=function_key, backend=self.backend.backend_type,
            dialect=getattr(self.backend, "dialect", None),
            protocol_method=protocol_method, arguments=arguments, options=options,
        )
        violations = CapabilityRegistry.violations_for(bound)
        if violations:
            ordered = sorted(violations, key=lambda f: (f.param, f.message))
            combined = "; ".join(f.message for f in ordered)
            raise BackendCapabilityError(
                combined, backend=self.backend.BACKEND_NAME,
                function_key=function_key, limitation=ordered[0],
            )


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
            raise ValueError(
                f"Function {node.function_key} has no protocol_method defined"
            )

        # Get method name from protocol method
        method_name = protocol_method.__name__

        self._gate_predicate_violations(
            node.function_key, protocol_method, node.arguments, node.options
        )


        if self.enforce_capabilities:
            from mountainash.core.capabilities import (
                CapabilityLevel, CapabilityRegistry, Enforcement, WILDCARD_PARAM,
            )
            from mountainash.core.types import BackendCapabilityError

            op_fact = CapabilityRegistry.capability_for(
                node.function_key, WILDCARD_PARAM,
                self.backend.backend_type, getattr(self.backend, "dialect", None),
            )
            if (
                op_fact is not None
                and op_fact.enforcement is Enforcement.GATE
                and op_fact.level is CapabilityLevel.UNSUPPORTED
            ):
                raise BackendCapabilityError(
                    op_fact.message, backend=self.backend.BACKEND_NAME,
                    function_key=node.function_key, limitation=op_fact,
                )

        args = self._gate_and_resolve_args(
            node.function_key, node.arguments, protocol_method
        )

        # Get the backend method
        if not hasattr(self.backend, method_name):
            raise AttributeError(
                f"Backend {type(self.backend).__name__} has no method '{method_name}' "
                f"for function {node.function_key}"
            )
        method = getattr(self.backend, method_name)

        # Call the method with resolved arguments and options
        options = node.options or {}
        if options and self.enforce_capabilities:
            from mountainash.core.capabilities import (
                CapabilityLevel,
                CapabilityRegistry,
                Enforcement,
            )
            from mountainash.core.types import BackendCapabilityError

            dialect = getattr(self.backend, "dialect", None)
            for option_name, option_value in options.items():
                fact = CapabilityRegistry.capability_for(
                    node.function_key,
                    option_name,
                    self.backend.backend_type,
                    dialect,
                    option_value=str(option_value),
                )
                blocks_option = (
                    fact is not None
                    and fact.enforcement is Enforcement.GATE
                    and (
                        fact.level is CapabilityLevel.UNSUPPORTED
                        or (
                            fact.level is CapabilityLevel.LITERAL_ONLY
                            and isinstance(option_value, ExpressionNode)
                        )
                    )
                )
                if blocks_option:
                    raise BackendCapabilityError(
                        fact.message,
                        backend=self.backend.BACKEND_NAME,
                        function_key=node.function_key,
                        limitation=fact,
                    )
        if options:
            return method(*args, **options)
        else:
            return method(*args)

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
        # Build the conditional chain
        # Start with first condition
        if not node.conditions:
            # No conditions, just return else clause
            return self.visit(node.else_clause)

        # Compile first condition
        first_cond, first_result = node.conditions[0]
        cond_expr = self.visit(first_cond)
        result_expr = self.visit(first_result)

        # Use backend's if_then_else for the final else
        else_expr = self.visit(node.else_clause)

        if len(node.conditions) == 1:
            # Simple case: one condition
            return self.backend.if_then_else(cond_expr, result_expr, else_expr)

        # Multiple conditions: chain them together
        # Start from the end and work backwards
        # if c1 then r1 elif c2 then r2 else e
        # becomes: if c1 then r1 else (if c2 then r2 else e)

        # Build from innermost (last condition + else)
        current = else_expr
        for condition, result in reversed(node.conditions):
            cond_expr = self.visit(condition)
            result_expr = self.visit(result)
            current = self.backend.if_then_else(cond_expr, result_expr, current)

        return current

    def visit_cast(self, node: CastNode) -> SupportedExpressions:
        """Compile a type cast to backend expression.

        Args:
            node: CastNode with input expression and target type

        Returns:
            Backend cast expression
        """
        input_expr = self.visit(node.input)
        if self.enforce_capabilities:
            from mountainash.core.capabilities import (
                CapabilityLevel, CapabilityRegistry, Enforcement, WILDCARD_PARAM,
            )
            from mountainash.core.types import BackendCapabilityError
            from ..expression_system.function_keys.enums import FKEY_SUBSTRAIT_CAST

            fact = CapabilityRegistry.capability_for(
                FKEY_SUBSTRAIT_CAST.CAST, WILDCARD_PARAM,
                self.backend.backend_type, getattr(self.backend, "dialect", None),
            )
            if fact is not None and fact.enforcement is Enforcement.GATE \
                    and fact.level is CapabilityLevel.UNSUPPORTED:
                raise BackendCapabilityError(
                    fact.message, backend=self.backend.BACKEND_NAME,
                    function_key=FKEY_SUBSTRAIT_CAST.CAST, limitation=fact,
                )
        return self.backend.cast(
            input_expr, node.target_type, failure_behavior=node.failure_behavior
        )

    def visit_singular_or_list(self, node: SingularOrListNode) -> SupportedExpressions:
        """Compile a membership test (IN operator) to backend expression."""
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_SCALAR_SET,
        )
        from mountainash.expressions.core.expression_system.function_mapping.registry import (
            ExpressionFunctionRegistry,
        )

        protocol_method = ExpressionFunctionRegistry.get_protocol_method(
            FKEY_MOUNTAINASH_SCALAR_SET.IS_IN
        )
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
            raise ValueError(
                f"Window function {node.function_key} has no protocol_method defined"
            )
        method_name = protocol_method.__name__

        # Resolve arguments
        compiled_args = self._gate_and_resolve_args(
            node.function_key, node.arguments, protocol_method
        )

        # Call backend method
        method = getattr(self.backend, method_name)
        options = dict(node.options) if node.options else {}

        # Inject order_by_col and descending for ranking functions so backends
        # can use native rank implementations instead of sequential numbering.
        _RANKING_KEYS = {
            SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
            SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
            SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
            FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE,
            FKEY_MOUNTAINASH_WINDOW.RANK_MAX,
        }
        if node.function_key in _RANKING_KEYS and node.window_spec and node.window_spec.order_by:
            first_sort = node.window_spec.order_by[0]
            order_col = self.visit(FieldReferenceNode(field=first_sort.column))
            options["order_by_col"] = order_col
            options["descending"] = first_sort.descending

        if options:
            result = method(*compiled_args, **options)
        else:
            result = method(*compiled_args)

        # Apply window context
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
