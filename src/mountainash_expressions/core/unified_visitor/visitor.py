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
from typing import Any, Dict, Optional, TYPE_CHECKING
import inspect
from enum import Enum

from ..expression_nodes import (
    ExpressionNode,
    LiteralNode,
    FieldReferenceNode,
    ScalarFunctionNode,
    IfThenNode,
    CastNode,
    SingularOrListNode,
)
from ..expression_system.function_mapping.registry import ExpressionFunctionRegistry as FunctionRegistry
from ..expression_system.function_keys.enums import MOUNTAINASH_TERNARY

# Alias for compatibility
SubstraitNode = ExpressionNode

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

    def __init__(self, expression_system: Any) -> None:
        """Initialize the visitor with a backend expression system.

        Args:
            expression_system: Backend ExpressionSystem instance
                              (e.g., PolarsExpressionSystem, IbisExpressionSystem)
        """
        self.backend = expression_system

    def _resolve_argument(
        self,
        arg: Any,
        param: Optional[inspect.Parameter] = None,
    ) -> Any:
        """Resolve an argument using protocol type hints.

        This method determines how to process an argument based on:
        1. Whether it's a SubstraitNode (needs recursive visiting)
        2. Whether it's already a backend expression (pass through)
        3. The protocol signature type hint (determines wrapping behavior)
        4. The raw value type (primitives may need lit() wrapping)

        Args:
            arg: The argument to resolve (SubstraitNode or raw value)
            param: Optional protocol parameter for type introspection

        Returns:
            Resolved argument ready for backend method call.

        Type Hint Behavior:
            - SupportedExpressions: Visit the node or wrap in lit()
            - str, int, float, bool: Pass through as-is (primitive kwarg)
            - Any/no hint: Visit if node, pass through otherwise
        """
        # If it's a SubstraitNode, always visit recursively
        if isinstance(arg, SubstraitNode):
            return self.visit(arg)

        # Check if arg is already a backend expression (native passthrough)
        # This handles cases where a native expression was wrapped in LiteralNode
        # without dtype="native", or when expressions are passed directly
        if self._is_backend_expression(arg):
            return arg

        # If no parameter info, treat primitives as needing lit() wrapping
        # This maintains backward compatibility
        if param is None:
            # Raw value that isn't a node - likely needs wrapping
            # But we can't wrap here without context; return as-is
            return arg

        # Check the type annotation for guidance
        annotation = param.annotation
        if annotation == inspect.Parameter.empty:
            # No type hint - return as-is
            return arg

        # Get the string representation of the annotation
        # Handle both string annotations and actual types
        annotation_str = str(annotation) if not isinstance(annotation, str) else annotation

        # If annotation indicates expression type, the caller should have
        # passed a node. If they passed a raw value, wrap in lit()
        if "SupportedExpressions" in annotation_str or "Expr" in annotation_str:
            # This should be an expression - wrap raw values
            return self.backend.lit(arg)

        # Primitive types (str, int, float, bool) - pass through as-is
        # These are typically keyword arguments or configuration values
        return arg

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

    def _resolve_options(
        self,
        options: Optional[Dict[str, Any]],
        signature: Optional[inspect.Signature],
    ) -> Dict[str, Any]:
        """Resolve options (keyword arguments) using protocol type hints.

        Args:
            options: Options dict from ScalarFunctionNode
            signature: Protocol method signature for type introspection

        Returns:
            Dict of resolved keyword arguments.

        Example:
            >>> opts = {"precision": 0.01, "ignore_case": True}
            >>> resolved = visitor._resolve_options(opts, sig)
        """
        if not options:
            return {}

        if signature is None:
            # No signature available - pass through as-is
            return dict(options)

        resolved = {}
        for key, value in options.items():
            # Look up parameter in signature
            param = signature.parameters.get(key)
            resolved[key] = self._resolve_argument(value, param)

        return resolved

    def _resolve_args_with_signature(
        self,
        func_name: str,
        args: list,
        options: Optional[Dict[str, Any]],
    ) -> tuple[list, Dict[str, Any]]:
        """Resolve positional and keyword arguments using protocol signature.

        This is the main entry point for protocol-informed argument resolution.

        Args:
            func_name: Function name for signature lookup
            args: List of SubstraitNode arguments
            options: Optional options dict

        Returns:
            Tuple of (resolved_args, resolved_options)
        """
        # Get protocol signature (cached)
        signature = self._get_signature(func_name)

        if signature is None:
            # No protocol signature - fall back to simple resolution
            resolved_args = [self.visit(arg) for arg in args]
            resolved_opts = dict(options) if options else {}
            return resolved_args, resolved_opts

        # Get positional parameters (excluding 'self')
        params = list(signature.parameters.values())
        pos_params = [p for p in params if p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ) and p.name != 'self']

        # Resolve positional arguments with type hints
        resolved_args = []
        for i, arg in enumerate(args):
            param = pos_params[i] if i < len(pos_params) else None
            resolved_args.append(self._resolve_argument(arg, param))

        # Resolve keyword arguments
        resolved_opts = self._resolve_options(options, signature)

        return resolved_args, resolved_opts

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
        if node.dtype == "native" or self._is_backend_expression(node.value):
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

        # Special handling for LIST function - extract raw values from LiteralNodes
        # instead of visiting them as expressions (which would convert them to
        # backend literals like pl.lit("A") instead of raw values like "A")
        if node.function_key == MOUNTAINASH_TERNARY.LIST:
            args = []
            for arg in node.arguments:
                if isinstance(arg, LiteralNode):
                    args.append(arg.value)
                elif isinstance(arg, ExpressionNode):
                    args.append(self.visit(arg))
                else:
                    args.append(arg)
        else:
            # Resolve arguments by visiting child nodes
            args = [self.visit(arg) if isinstance(arg, ExpressionNode) else arg
                    for arg in node.arguments]

        # Get the backend method
        if not hasattr(self.backend, method_name):
            raise AttributeError(
                f"Backend {type(self.backend).__name__} has no method '{method_name}' "
                f"for function {node.function_key}"
            )
        method = getattr(self.backend, method_name)

        # Call the method with resolved arguments and options
        options = node.options or {}
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
        return self.backend.cast(input_expr, node.target_type)

    def visit_singular_or_list(self, node: SingularOrListNode) -> SupportedExpressions:
        """Compile a membership test (IN operator) to backend expression.

        Args:
            node: SingularOrListNode with value and options list

        Returns:
            Backend is_in expression
        """
        value_expr = self.visit(node.value)

        # Options can be nodes or literal values
        # For is_in, we typically pass the literal values directly
        options = []
        for opt in node.options:
            if isinstance(opt, LiteralNode):
                # Extract literal value for the list
                options.append(opt.value)
            elif isinstance(opt, SubstraitNode):
                # Compile and add (for expression-based membership)
                options.append(self.visit(opt))
            else:
                # Already a value
                options.append(opt)

        return self.backend.is_in(value_expr, *options)
