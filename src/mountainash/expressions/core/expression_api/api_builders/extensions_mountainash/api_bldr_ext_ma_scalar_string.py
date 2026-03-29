"""Mountainash extension string operations APIBuilder.

Polars-compatible aliases for standard string operations.
Standard string operations are handled by SubstraitScalarStringAPIBuilder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, IfThenNode, LiteralNode


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarStringAPIBuilder(BaseExpressionAPIBuilder):
    """Mountainash extension string operations.

    Provides Polars-compatible aliases for standard string operations.
    Standard string operations live in SubstraitScalarStringAPIBuilder.
    """

    # Polars-compatible aliases (direct AST construction)

    def to_uppercase(self) -> BaseExpressionAPI:
        """Alias for upper() — Polars compatibility."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
            arguments=[self._node],
        )
        return self._build(node)

    def to_lowercase(self) -> BaseExpressionAPI:
        """Alias for lower() — Polars compatibility."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
            arguments=[self._node],
        )
        return self._build(node)

    def strip_chars(self, characters: Optional[str] = None) -> BaseExpressionAPI:
        """Alias for trim() — Polars compatibility."""
        options = {"characters": characters} if characters is not None else {}
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TRIM,
            arguments=[self._node],
            options=options,
        )
        return self._build(node)

    def strip_chars_start(self, characters: Optional[str] = None) -> BaseExpressionAPI:
        """Alias for ltrim() — Polars compatibility."""
        options = {"characters": characters} if characters is not None else {}
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM,
            arguments=[self._node],
            options=options,
        )
        return self._build(node)

    def strip_chars_end(self, characters: Optional[str] = None) -> BaseExpressionAPI:
        """Alias for rtrim() — Polars compatibility."""
        options = {"characters": characters} if characters is not None else {}
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM,
            arguments=[self._node],
            options=options,
        )
        return self._build(node)

    def len_chars(self) -> BaseExpressionAPI:
        """Alias for char_length() — Polars compatibility."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CHAR_LENGTH,
            arguments=[self._node],
        )
        return self._build(node)

    # Short aliases for Substrait string operations

    def length(self) -> BaseExpressionAPI:
        """Alias for char_length()."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CHAR_LENGTH,
            arguments=[self._node],
        )
        return self._build(node)

    def len(self) -> BaseExpressionAPI:
        """Alias for char_length()."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CHAR_LENGTH,
            arguments=[self._node],
        )
        return self._build(node)

    # Convenience methods (AST-level composition)

    def strip_prefix(self, prefix: str) -> BaseExpressionAPI:
        """Remove prefix from string if present.

        Args:
            prefix: The prefix string to remove.
        """
        prefix_node = LiteralNode(value=prefix)
        starts_cond = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
            arguments=[self._node, prefix_node],
        )
        start_node = LiteralNode(value=len(prefix))
        stripped = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
            arguments=[self._node, start_node],
        )
        node = IfThenNode(
            conditions=[(starts_cond, stripped)],
            else_clause=self._node,
        )
        return self._build(node)

    def strip_suffix(self, suffix: str) -> BaseExpressionAPI:
        """Remove suffix from string if present.

        Args:
            suffix: The suffix string to remove.
        """
        suffix_node = LiteralNode(value=suffix)
        ends_cond = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
            arguments=[self._node, suffix_node],
        )
        # Use negative offset to slice from end: substring(0, char_length - suffix_len)
        # Since char_length varies per row, we need to compute it dynamically.
        # Use REPLACE to remove the suffix (replace last occurrence).
        # Simpler: use substring with computed length.
        str_len = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CHAR_LENGTH,
            arguments=[self._node],
        )
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        new_len = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            arguments=[str_len, LiteralNode(value=len(suffix))],
        )
        start_node = LiteralNode(value=0)
        stripped = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
            arguments=[self._node, start_node, new_len],
        )
        node = IfThenNode(
            conditions=[(ends_cond, stripped)],
            else_clause=self._node,
        )
        return self._build(node)
