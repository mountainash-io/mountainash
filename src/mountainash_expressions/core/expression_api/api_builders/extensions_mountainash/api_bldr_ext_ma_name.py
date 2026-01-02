"""Column naming operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Provides column renaming and name transformation operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder
from ...api_base import BaseExpressionAPI

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, LiteralNode
from mountainash_expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshNameAPIBuilderProtocol



class MountainAshNameAPIBuilder(BaseExpressionAPIBuilder):
    """
    Column naming operations APIBuilder.

    Provides operations for renaming and transforming column names.
    Accessed via the .name accessor on ExpressionAPI.

    Methods:
        alias: Rename the column
        prefix: Add a prefix to the column name
        suffix: Add a suffix to the column name
        to_upper: Convert column name to uppercase
        to_lower: Convert column name to lowercase
    """

    def alias(self, name: str) -> BaseExpressionAPI:
        """
        Rename the column.

        Args:
            name: New name for the column.

        Returns:
            New ExpressionAPI with alias node.

        Example:
            >>> expr = col("user_id").name.alias("id")
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
            arguments=[self._node, LiteralNode(value=name)],
        )
        return self._build(node)

    def prefix(self, prefix: str) -> BaseExpressionAPI:
        """
        Add a prefix to the column name.

        Args:
            prefix: Prefix to add.

        Returns:
            New ExpressionAPI with prefix node.

        Example:
            >>> expr = col("score").name.prefix("raw_")
            >>> # Column name becomes "raw_score"
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.PREFIX,
            arguments=[self._node, LiteralNode(value=prefix)],
        )
        return self._build(node)

    def suffix(self, suffix: str) -> BaseExpressionAPI:
        """
        Add a suffix to the column name.

        Args:
            suffix: Suffix to add.

        Returns:
            New ExpressionAPI with suffix node.

        Example:
            >>> expr = col("score").name.suffix("_normalized")
            >>> # Column name becomes "score_normalized"
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.SUFFIX,
            arguments=[self._node, LiteralNode(value=suffix)],
        )
        return self._build(node)

    def to_upper(self) -> BaseExpressionAPI:
        """
        Convert column name to uppercase.

        Returns:
            New ExpressionAPI with name_to_upper node.

        Example:
            >>> expr = col("user_id").name.to_upper()
            >>> # Column name becomes "USER_ID"
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.NAME_TO_UPPER,
            arguments=[self._node],
        )
        return self._build(node)

    def to_lower(self) -> BaseExpressionAPI:
        """
        Convert column name to lowercase.

        Returns:
            New ExpressionAPI with name_to_lower node.

        Example:
            >>> expr = col("USER_ID").name.to_lower()
            >>> # Column name becomes "user_id"
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.NAME_TO_LOWER,
            arguments=[self._node],
        )
        return self._build(node)
