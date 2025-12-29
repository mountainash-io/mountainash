"""Name/alias operations namespace (explicit .name accessor).

Substrait-aligned implementation using ScalarFunctionNode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseExpressionNamespace
from ...expression_nodes import ScalarFunctionNode, MOUNTAINASH_NAME

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ...expression_nodes import SubstraitNode


class NameNamespace(BaseExpressionNamespace):
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
        name: str,
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
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_NAME.ALIAS,
            arguments=[self._node],
            options={"name": name},
        )
        return self._build(node)

    def prefix(
        self,
        prefix_str: str,
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
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_NAME.PREFIX,
            arguments=[self._node],
            options={"prefix": prefix_str},
        )
        return self._build(node)

    def suffix(
        self,
        suffix_str: str,
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
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_NAME.SUFFIX,
            arguments=[self._node],
            options={"suffix": suffix_str},
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
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_NAME.NAME_TO_UPPER,
            arguments=[self._node],
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
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_NAME.NAME_TO_LOWER,
            arguments=[self._node],
        )
        return self._build(node)
