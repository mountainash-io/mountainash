"""Column naming operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Provides column renaming and name transformation operations.
"""

from __future__ import annotations


from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshNameAPIBuilderProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI



class MountainAshNameAPIBuilder(BaseExpressionAPIBuilder, MountainAshNameAPIBuilderProtocol):
    """
    Column naming operations APIBuilder.

    Provides operations for renaming and transforming column names.
    Accessed via the .name accessor on ExpressionAPI.

    Methods:
        alias: Rename the column
        prefix: Add a prefix to the column name
        suffix: Add a suffix to the column name
        name_to_upper: Convert column name to uppercase
        name_to_lower: Convert column name to lowercase
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
        if not isinstance(name, str):
            raise TypeError(
                f"name.alias(name=...) requires a literal str, got {type(name).__name__}. "
                f"Options must be raw Python values (see principle: arguments-vs-options.md)."
            )
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
            arguments=[self._node],
            options={"name": name},
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
        if not isinstance(prefix, str):
            raise TypeError(
                f"name.prefix(prefix=...) requires a literal str, got {type(prefix).__name__}. "
                f"Options must be raw Python values (see principle: arguments-vs-options.md)."
            )
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.PREFIX,
            arguments=[self._node],
            options={"prefix": prefix},
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
        if not isinstance(suffix, str):
            raise TypeError(
                f"name.suffix(suffix=...) requires a literal str, got {type(suffix).__name__}. "
                f"Options must be raw Python values (see principle: arguments-vs-options.md)."
            )
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.SUFFIX,
            arguments=[self._node],
            options={"suffix": suffix},
        )
        return self._build(node)

    def name_to_upper(self) -> BaseExpressionAPI:
        """
        Convert column name to uppercase.

        Returns:
            New ExpressionAPI with name_to_upper node.

        Example:
            >>> expr = col("user_id").name.name_to_upper()
            >>> # Column name becomes "USER_ID"
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.NAME_TO_UPPER,
            arguments=[self._node],
        )
        return self._build(node)

    def name_to_lower(self) -> BaseExpressionAPI:
        """
        Convert column name to lowercase.

        Returns:
            New ExpressionAPI with name_to_lower node.

        Example:
            >>> expr = col("USER_ID").name.name_to_lower()
            >>> # Column name becomes "user_id"
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.NAME_TO_LOWER,
            arguments=[self._node],
        )
        return self._build(node)

    # Polars-compatible aliases
    to_lowercase = name_to_lower
    to_uppercase = name_to_upper
