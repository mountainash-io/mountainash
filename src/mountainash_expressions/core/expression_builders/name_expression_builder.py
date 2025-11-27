"""Name/alias operations mixin for ExpressionBuilder."""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

from ..protocols import NameBuilderProtocol, ENUM_NAME_OPERATORS
from ..expression_nodes import (
    NameExpressionNode,
    NameAliasExpressionNode,
    NamePrefixExpressionNode,
    NameSuffixExpressionNode,
)


class NameExpressionBuilder(BaseExpressionBuilder, NameBuilderProtocol):
    """
    Mixin providing name/alias operations for ExpressionBuilder.

    Implements methods for column naming:
    - alias(): Rename the expression
    - prefix(): Add prefix to column name
    - suffix(): Add suffix to column name
    - to_upper(): Convert column name to uppercase
    - to_lower(): Convert column name to lowercase
    """

    def alias(self, name: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Rename the expression/column.

        Args:
            name: New name for the expression

        Returns:
            New ExpressionBuilder with alias node

        Example:
            >>> col("customer_id").alias("id")
            >>> col("price").mul(col("quantity")).alias("total")
        """

        name_node = self._to_node_or_value(name)
        node = NameAliasExpressionNode(
            ENUM_NAME_OPERATORS.ALIAS,
            self._node,
            name_node
        )
        return self.create(node)

    def prefix(self, prefix_str: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Add prefix to column name.

        Args:
            prefix_str: Prefix to add

        Returns:
            New ExpressionBuilder with prefix node

        Example:
            >>> col("id").prefix("customer_")  # -> "customer_id"
        """

        prefix_node = self._to_node_or_value(prefix_str)
        node = NamePrefixExpressionNode(
            ENUM_NAME_OPERATORS.NAME_PREFIX,
            self._node,
            prefix_node
        )
        return self.create(node)

    def suffix(self, suffix_str: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Add suffix to column name.

        Args:
            suffix_str: Suffix to add

        Returns:
            New ExpressionBuilder with suffix node

        Example:
            >>> col("price").suffix("_usd")  # -> "price_usd"
        """

        suffix_node = self._to_node_or_value(suffix_str)
        node = NameSuffixExpressionNode(
            ENUM_NAME_OPERATORS.NAME_SUFFIX,
            self._node,
            suffix_node
        )
        return self.create(node)

    def to_upper(self) -> BaseExpressionBuilder:
        """
        Convert column name to uppercase.

        Returns:
            New ExpressionBuilder with to_upper node

        Example:
            >>> col("name").to_upper()  # -> "NAME"
        """

        node = NameExpressionNode(
            ENUM_NAME_OPERATORS.NAME_TO_UPPER
        )
        return self.create(node)

    def to_lower(self) -> BaseExpressionBuilder:
        """
        Convert column name to lowercase.

        Returns:
            New ExpressionBuilder with to_lower node

        Example:
            >>> col("ID").to_lower()  # -> "id"
        """

        node = NameExpressionNode(
            ENUM_NAME_OPERATORS.NAME_TO_LOWER
        )
        return self.create(node)
