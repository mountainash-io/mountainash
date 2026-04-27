"""Base class for expression API facades."""

from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Literal, Self, Union

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode
    from .api_builders.api_builder_base import BaseExpressionAPIBuilder as BaseExpressionNamespace

logger = logging.getLogger(__name__)

# Type alias for booleanizer parameter
Booleanizer = Union[
    Literal["is_true", "is_false", "is_unknown", "is_known", "maybe_true", "maybe_false"],
    Callable[["BaseExpressionAPI"], "BaseExpressionAPI"],
    None,
]


class BaseExpressionAPI(ABC):
    """
    Abstract base class for fluent expression API facades.

    Provides:
    - Explicit namespaces via descriptors (.str, .dt, .name)
    - Flat method dispatch via __getattr__ for _FLAT_NAMESPACES
    - Factory method for creating new instances preserving type

    Subclasses define _FLAT_NAMESPACES to compose their operation set.

    Attributes:
        _node: The current expression node.
    """

    # Subclasses override to define flat namespace composition
    _FLAT_NAMESPACES: ClassVar[tuple[type[BaseExpressionNamespace], ...]] = ()

    __slots__ = ("_node",)

    def __init__(self, node: Union[ExpressionNode, Any]) -> None:
        """
        Initialise the API with an expression node.

        Args:
            node: The root expression node or raw value.
        """
        self._node = node

    @classmethod
    def create(cls, node: ExpressionNode) -> Self:
        """
        Factory method for creating new API instances.

        Preserves the concrete class type when called from subclasses.

        Args:
            node: The expression node for the new instance.

        Returns:
            New instance of the concrete API class.
        """
        return cls(node)

    def __getattr__(self, name: str) -> Any:
        """
        Dispatch attribute access to flat namespaces.

        Searches _FLAT_NAMESPACES in order for the requested attribute.
        Raises AttributeError if not found in any namespace.

        Args:
            name: The attribute name to look up.

        Returns:
            The bound method from the first namespace containing it.

        Raises:
            AttributeError: If no namespace contains the attribute.
        """
        # Avoid infinite recursion for special attributes
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' has no attribute '{name}'"
            )

        for ns_cls in self._FLAT_NAMESPACES:
            ns = ns_cls(self)
            if hasattr(ns_cls, name):
                return getattr(ns, name)

        raise AttributeError(
            f"'{type(self).__name__}' has no attribute '{name}'"
        )

    def _to_node_or_value(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> Union[ExpressionNode, Any]:
        """
        Convert input to an ExpressionNode or pass through raw values.

        Handles:
        - BaseExpressionAPI instances: extracts ._node
        - ExpressionNode instances: returns as-is (legacy)
        - ExpressionNode instances: returns as-is (new)
        - Other values: returns as-is (visitor will handle them)

        Args:
            other: The value to convert.

        Returns:
            An ExpressionNode, ExpressionNode, or raw value representing the input.
        """
        if isinstance(other, BaseExpressionAPI):
            return other._node

        # Check for new Substrait nodes first
        from ..expression_nodes import ExpressionNode
        if isinstance(other, ExpressionNode):
            return other

        # Import here to avoid circular dependency
        from ..expression_nodes import ExpressionNode

        if isinstance(other, ExpressionNode):
            return other

        # Keep raw values as-is (visitor/ExpressionParameter will handle them)
        return other

    @property
    def node(self) -> Union[ExpressionNode, Any]:
        """Get the underlying expression node or raw value."""
        return self._node

    def compile(
        self,
        dataframe: Any,
        *,
        booleanizer: Booleanizer = "is_true",
    ) -> Any:
        """
        Compile expression to backend-native expression.

        This is the main entry point for converting a backend-agnostic
        ExpressionBuilder to a backend-specific expression (pl.Expr, nw.Expr, ir.Expr).

        For ternary expressions (t_eq, t_gt, t_and, etc.), this automatically
        converts the internal sentinel values (-1/0/1) to boolean using the
        specified booleanizer. This prevents users from accidentally
        materializing internal sentinel values.

        Args:
            dataframe: DataFrame to detect backend from (pl.DataFrame, nw.DataFrame, ir.Table, etc.)
            booleanizer: How to convert non-terminal ternary expressions to boolean.
                - "is_true" (default): Only TRUE (1) becomes True - strictest
                - "is_false": Only FALSE (-1) becomes True
                - "is_unknown": Only UNKNOWN (0) becomes True
                - "is_known": TRUE or FALSE becomes True
                - "maybe_true": TRUE or UNKNOWN becomes True - lenient
                - "maybe_false": FALSE or UNKNOWN becomes True
                - Callable: Custom function (api) -> api with booleanizer applied
                - None: Return raw ternary values (-1/0/1) without conversion

        Returns:
            Backend-native expression (pl.Expr | nw.Expr | ir.Expr)

        Example:
            >>> import mountainash.expressions as ma
            >>> expr = ma.col("age").t_gt(30)  # ternary comparison
            >>> # Default: strict is_true() - only definite TRUE passes
            >>> backend_expr = expr.compile(df)
            >>> # Lenient: UNKNOWN also passes
            >>> backend_expr = expr.compile(df, booleanizer="maybe_true")
            >>> # Raw sentinels: for testing/debugging
            >>> backend_expr = expr.compile(df, booleanizer=None)
        """
        from ..expression_system.expsys_base import identify_backend, get_expression_system

        # Auto-booleanize non-terminal ternary expressions
        node_to_compile = self._maybe_booleanize(booleanizer)

        # Detect backend and get ExpressionSystem
        backend_type = identify_backend(dataframe)
        expression_system_class = get_expression_system(backend_type)
        expression_system = expression_system_class()

        # Check if this is an ExpressionNode
        from ..expression_nodes import ExpressionNode
        if isinstance(node_to_compile, ExpressionNode):
            # Use unified visitor for all expression nodes
            from ..unified_visitor import UnifiedExpressionVisitor
            visitor = UnifiedExpressionVisitor(expression_system)
            return visitor.visit(node_to_compile)

        # Handle raw values (should not normally reach here)
        # Wrap in a literal and compile
        from ..expression_nodes import LiteralNode
        lit_node = LiteralNode(value=node_to_compile)
        from ..unified_visitor import UnifiedExpressionVisitor
        visitor = UnifiedExpressionVisitor(expression_system)
        return visitor.visit(lit_node)

    def _maybe_booleanize(
        self,
        booleanizer: Booleanizer,
    ) -> Union[ExpressionNode, Any]:
        """
        Apply booleanizer if this is a non-terminal ternary node.

        Ternary expressions return sentinel values (-1/0/1) which should not
        be materialized directly. This method automatically wraps them with
        a booleanizer (default: is_true) to convert to boolean.

        Args:
            booleanizer: The booleanizer to apply, or None for raw values.

        Returns:
            The node to compile (possibly wrapped with a booleanizer).
        """
        from ..expression_nodes import ScalarFunctionNode
        from ..expression_system.function_keys.enums import (
            MOUNTAINASH_TERNARY_TERMINAL,
            MOUNTAINASH_TERNARY_NON_TERMINAL,
        )

        # Check if this is a ScalarFunctionNode with a ternary function
        if not isinstance(self._node, ScalarFunctionNode):
            return self._node

        function_key = self._node.function_key

        # If already terminal (booleanized), return as-is
        if function_key in MOUNTAINASH_TERNARY_TERMINAL:
            return self._node

        # If not a ternary function at all, return as-is
        if function_key not in MOUNTAINASH_TERNARY_NON_TERMINAL:
            return self._node

        # If booleanizer is None, return raw (user explicitly wants sentinels)
        if booleanizer is None:
            return self._node

        # Apply booleanizer and log info message
        logger.info(
            "Auto-booleanizing ternary expression with '%s'. "
            "Use booleanizer=None to get raw sentinel values, or call "
            ".is_true(), .maybe_true(), etc. explicitly.",
            booleanizer if isinstance(booleanizer, str) else "custom",
        )
        return self._apply_booleanizer(booleanizer)._node

    def _apply_booleanizer(
        self,
        booleanizer: Booleanizer,
    ) -> BaseExpressionAPI:
        """
        Apply the specified booleanizer to this expression.

        Args:
            booleanizer: The booleanizer to apply.

        Returns:
            New API instance with booleanizer applied.

        Raises:
            ValueError: If booleanizer string is not recognized.
        """
        if booleanizer is None:
            return self

        if callable(booleanizer) and not isinstance(booleanizer, str):
            return booleanizer(self)

        # String-based booleanizer lookup
        booleanizer_methods = {
            "is_true": lambda api: api.is_true(),
            "is_false": lambda api: api.is_false(),
            "is_unknown": lambda api: api.is_unknown(),
            "is_known": lambda api: api.is_known(),
            "maybe_true": lambda api: api.maybe_true(),
            "maybe_false": lambda api: api.maybe_false(),
        }

        if booleanizer not in booleanizer_methods:
            raise ValueError(
                f"Unknown booleanizer: {booleanizer!r}. "
                f"Valid options: {list(booleanizer_methods.keys())}"
            )

        return booleanizer_methods[booleanizer](self)

    def over(
        self,
        *partition_by: str,
        order_by: str | list[str] | None = None,
        rows_between: tuple[int | None, int | None] | None = None,
    ) -> BaseExpressionAPI:
        """
        Apply window context to the current expression.

        If the inner node is a WindowFunctionNode with window_spec=None,
        populates the window_spec directly. Otherwise, wraps the inner
        node in an OverNode.

        Args:
            *partition_by: Column names to partition by.
            order_by: Column name(s) to order by within each partition.
            rows_between: Tuple of (lower, upper) frame bounds.
                Use None for unbounded, 0 for current row, negative for preceding,
                positive for following.

        Returns:
            New ExpressionAPI with window context applied.
        """
        # Lazy imports to avoid circular dependencies
        from ..expression_nodes.substrait.exn_window_spec import WindowSpec, WindowBound
        from ..expression_nodes.substrait.exn_window_function import WindowFunctionNode
        from ..expression_nodes.mountainash_extensions.exn_ext_ma_over import OverNode
        from ..expression_nodes import FieldReferenceNode
        from mountainash.core.constants import SortField, WindowBoundType

        # Convert partition_by strings to FieldReferenceNode
        partition_nodes = [
            FieldReferenceNode(field=col_name) for col_name in partition_by
        ]

        # Convert order_by to SortField list
        sort_fields: list[SortField] = []
        if order_by is not None:
            if isinstance(order_by, str):
                order_by = [order_by]
            for col_name in order_by:
                if col_name.startswith("-"):
                    sort_fields.append(SortField(column=col_name[1:], descending=True))
                else:
                    sort_fields.append(SortField(column=col_name))

        # Convert rows_between to WindowBound objects
        lower_bound: WindowBound | None = None
        upper_bound: WindowBound | None = None
        if rows_between is not None:
            lower, upper = rows_between
            if lower is None:
                lower_bound = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
            elif lower == 0:
                lower_bound = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
            elif lower < 0:
                lower_bound = WindowBound(bound_type=WindowBoundType.PRECEDING, offset=abs(lower))
            else:
                lower_bound = WindowBound(bound_type=WindowBoundType.FOLLOWING, offset=lower)

            if upper is None:
                upper_bound = WindowBound(bound_type=WindowBoundType.UNBOUNDED_FOLLOWING)
            elif upper == 0:
                upper_bound = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
            elif upper < 0:
                upper_bound = WindowBound(bound_type=WindowBoundType.PRECEDING, offset=abs(upper))
            else:
                upper_bound = WindowBound(bound_type=WindowBoundType.FOLLOWING, offset=upper)

        # Build the WindowSpec
        spec = WindowSpec(
            partition_by=partition_nodes,
            order_by=sort_fields,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )

        # If inner node is a WindowFunctionNode, either populate or merge
        if isinstance(self._node, WindowFunctionNode):
            if self._node.window_spec is None:
                updated_node = self._node.model_copy(update={"window_spec": spec})
                return self.create(updated_node)
            else:
                # Merge: add partition_by from .over() into existing spec
                # Preserve existing order_by (from rank()) and bounds (from cum_sum())
                existing = self._node.window_spec
                merged_order_by = existing.order_by if existing.order_by else sort_fields
                merged_lower = existing.lower_bound if existing.lower_bound is not None else lower_bound
                merged_upper = existing.upper_bound if existing.upper_bound is not None else upper_bound
                merged_spec = WindowSpec(
                    partition_by=partition_nodes,
                    order_by=merged_order_by,
                    lower_bound=merged_lower,
                    upper_bound=merged_upper,
                )
                updated_node = self._node.model_copy(update={"window_spec": merged_spec})
                return self.create(updated_node)

        # Otherwise, wrap in an OverNode
        over_node = OverNode(expression=self._node, window_spec=spec)
        return self.create(over_node)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._node!r})"
