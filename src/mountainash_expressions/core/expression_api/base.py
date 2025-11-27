"""Base class for expression API facades."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar, Self, Union

if TYPE_CHECKING:
    from ..expression_nodes.base_expression_node import ExpressionNode
    from ..namespaces.base import BaseNamespace


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
    _FLAT_NAMESPACES: ClassVar[tuple[type[BaseNamespace], ...]] = ()

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
        - ExpressionNode instances: returns as-is
        - Other values: returns as-is (visitor will handle them)

        Args:
            other: The value to convert.

        Returns:
            An ExpressionNode or raw value representing the input.
        """
        if isinstance(other, BaseExpressionAPI):
            return other._node

        # Import here to avoid circular dependency
        from ..expression_nodes.base_expression_node import ExpressionNode

        if isinstance(other, ExpressionNode):
            return other

        # Keep raw values as-is (visitor/ExpressionParameter will handle them)
        return other

    @property
    def node(self) -> Union[ExpressionNode, Any]:
        """Get the underlying expression node or raw value."""
        return self._node

    def compile(self, dataframe: Any) -> Any:
        """
        Compile expression to backend-native expression.

        This is the main entry point for converting a backend-agnostic
        ExpressionBuilder to a backend-specific expression (pl.Expr, nw.Expr, ir.Expr).

        Args:
            dataframe: DataFrame to detect backend from (pl.DataFrame, nw.DataFrame, ir.Table, etc.)
            logic_type: Logic system (defaults to BOOLEAN)

        Returns:
            Backend-native expression (pl.Expr | nw.Expr | ir.Expr)

        Example:
            >>> import mountainash_expressions as ma
            >>> expr = ma.col("age").gt(30)
            >>> backend_expr = expr.compile(df)  # df is Polars DataFrame
            >>> result = df.filter(backend_expr)
        """
        from ..expression_visitors import ExpressionVisitorFactory
        from ...constants import CONST_LOGIC_TYPES
        from ..expression_nodes.base_expression_node import ExpressionNode

        # logic = logic_type or CONST_LOGIC_TYPES.BOOLEAN

        # Detect backend and get ExpressionSystem
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system_class = ExpressionVisitorFactory._expression_systems_registry[backend_type]
        expression_system = expression_system_class()

        # Get appropriate visitor for the top-level node
        if isinstance(self._node, ExpressionNode):
            visitor = ExpressionVisitorFactory.get_visitor_for_node(
                self._node,
                expression_system,
                # logic
            )
            return self._node.accept(visitor)
        else:
            # Handle raw values
            from ..expression_parameters import ExpressionParameter
            return ExpressionParameter(
                self._node,
                expression_system=expression_system
            ).to_native_expression()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._node!r})"
