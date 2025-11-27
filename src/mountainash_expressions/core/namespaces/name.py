"""Name/alias operations namespace (explicit .name accessor)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseNamespace
from ..protocols import ENUM_NAME_OPERATORS, NameBuilderProtocol
from ..expression_nodes import (
    NameExpressionNode,
    NameAliasExpressionNode,
    NamePrefixExpressionNode,
    NameSuffixExpressionNode,
)

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


class NameNamespace(BaseNamespace, NameBuilderProtocol):
    """
    Name/alias operations namespace accessed via .name accessor.

    Provides column naming and renaming operations.

    Usage:
        col("x").name.alias("y")      # Instead of alias("y")
        col("x").name.prefix("pre_")  # Instead of prefix("pre_")

    Operations:
        alias: Rename the expression/column
        prefix: Add prefix to column name
        suffix: Add suffix to column name
        to_upper: Convert column name to uppercase
        to_lower: Convert column name to lowercase
    """

    def alias(
        self,
        name: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Rename the expression/column.

        Args:
            name: New name for the expression.

        Returns:
            New ExpressionAPI with alias node.

        Example:
            >>> col("customer_id").name.alias("id")
            >>> col("price").mul(col("quantity")).name.alias("total")
        """
        name_node = self._to_node_or_value(name)
        node = NameAliasExpressionNode(
            ENUM_NAME_OPERATORS.ALIAS,
            self._node,
            name_node,
        )
        return self._build(node)

    def prefix(
        self,
        prefix_str: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Add prefix to column name.

        Args:
            prefix_str: Prefix to add.

        Returns:
            New ExpressionAPI with prefix node.

        Example:
            >>> col("id").name.prefix("customer_")  # -> "customer_id"
        """
        prefix_node = self._to_node_or_value(prefix_str)
        node = NamePrefixExpressionNode(
            ENUM_NAME_OPERATORS.NAME_PREFIX,
            self._node,
            prefix_node,
        )
        return self._build(node)

    def suffix(
        self,
        suffix_str: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Add suffix to column name.

        Args:
            suffix_str: Suffix to add.

        Returns:
            New ExpressionAPI with suffix node.

        Example:
            >>> col("price").name.suffix("_usd")  # -> "price_usd"
        """
        suffix_node = self._to_node_or_value(suffix_str)
        node = NameSuffixExpressionNode(
            ENUM_NAME_OPERATORS.NAME_SUFFIX,
            self._node,
            suffix_node,
        )
        return self._build(node)

    def to_upper(self) -> BaseExpressionAPI:
        """
        Convert column name to uppercase.

        Returns:
            New ExpressionAPI with to_upper node.

        Example:
            >>> col("name").name.to_upper()  # -> "NAME"
        """
        node = NameExpressionNode(
            ENUM_NAME_OPERATORS.NAME_TO_UPPER,
            self._node,
        )
        return self._build(node)

    def to_lower(self) -> BaseExpressionAPI:
        """
        Convert column name to lowercase.

        Returns:
            New ExpressionAPI with to_lower node.

        Example:
            >>> col("ID").name.to_lower()  # -> "id"
        """
        node = NameExpressionNode(
            ENUM_NAME_OPERATORS.NAME_TO_LOWER,
            self._node,
        )
        return self._build(node)
