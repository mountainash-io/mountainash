"""Base class for expression namespaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


class BaseNamespace:
    """
    Base class for all expression namespaces.

    Provides shared utilities for node access, value conversion, and building
    new API instances. Subclasses implement domain-specific operations.

    Attributes:
        _api: The parent ExpressionAPI instance this namespace is bound to.
    """

    __slots__ = ("_api",)

    def __init__(self, api: BaseExpressionAPI) -> None:
        """
        Initialise the namespace.

        Args:
            api: The parent ExpressionAPI instance.
        """
        self._api = api

    @property
    def _node(self) -> ExpressionNode:
        """Access the current expression node from the parent API."""
        return self._api._node

    def _to_node_or_value(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> Union[ExpressionNode, Any]:
        """
        Convert input to an ExpressionNode or pass through raw values.

        Delegates to the parent API's conversion method, then applies
        any namespace-specific coercion.

        Args:
            other: Value, node, or API instance to convert.

        Returns:
            ExpressionNode or raw value representing the input.
        """
        node_or_value = self._api._to_node_or_value(other)
        return self._coerce_if_needed(node_or_value)

    def _coerce_if_needed(
        self,
        node_or_value: Union[ExpressionNode, Any],
    ) -> Union[ExpressionNode, Any]:
        """
        Apply type coercion to a node if required by this namespace.

        Override in subclasses that require specific input types.
        Default implementation returns the input unchanged.

        Args:
            node_or_value: The node or value to potentially coerce.

        Returns:
            The original input or a wrapped coercion node.
        """
        return node_or_value

    def _build(self, node: ExpressionNode) -> BaseExpressionAPI:
        """
        Return a new API instance with the given node.

        Uses the parent API's create() factory to preserve the concrete type.

        Args:
            node: The new expression node.

        Returns:
            New ExpressionAPI instance of the same type as the parent.
        """
        return self._api.create(node)
