"""Mountainash extension string operations APIBuilder.

Polars-compatible aliases for standard string operations.
Standard string operations are handled by SubstraitScalarStringAPIBuilder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
    FKEY_MOUNTAINASH_SCALAR_STRING,
)
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

    def zfill(self, length: int) -> BaseExpressionAPI:
        """Left-pad with zeros. Equivalent to lpad(length, "0")."""
        length_node = LiteralNode(value=length)
        zero_node = LiteralNode(value="0")
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,
            arguments=[self._node, length_node, zero_node],
        )
        return self._build(node)

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
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.STRIP_SUFFIX,
            arguments=[self._node],
            options={"suffix": suffix},
        )
        return self._build(node)

    def to_date(self, format: str) -> BaseExpressionAPI:
        """Parse string to date using format string."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.TO_DATE,
            arguments=[self._node],
            options={"format": format},
        )
        return self._build(node)

    def to_datetime(self, format: str) -> BaseExpressionAPI:
        """Parse string to datetime using format string."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.TO_DATETIME,
            arguments=[self._node],
            options={"format": format},
        )
        return self._build(node)

    def to_time(self, format: str) -> "BaseExpressionAPI":
        """Parse string to time using format string."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME,
            arguments=[self._node],
            options={"format": format},
        )
        return self._build(node)

    def to_integer(self, base: int = 10) -> "BaseExpressionAPI":
        """Parse string to integer with given base."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.TO_INTEGER,
            arguments=[self._node],
            options={"base": base},
        )
        return self._build(node)

    def json_decode(self, dtype: Any = None) -> "BaseExpressionAPI":
        """Parse JSON string into structured data."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE,
            arguments=[self._node],
            options={"dtype": dtype},
        )
        return self._build(node)

    def json_path_match(self, json_path: str) -> "BaseExpressionAPI":
        """Extract value from JSON string via JSONPath."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH,
            arguments=[self._node],
            options={"json_path": json_path},
        )
        return self._build(node)

    def encode(self, encoding: str) -> "BaseExpressionAPI":
        """Encode string to hex or base64."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE,
            arguments=[self._node],
            options={"encoding": encoding},
        )
        return self._build(node)

    def decode(self, encoding: str, *, strict: bool = True) -> "BaseExpressionAPI":
        """Decode hex or base64 string to binary."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.DECODE,
            arguments=[self._node],
            options={"encoding": encoding, "strict": strict},
        )
        return self._build(node)

    def extract_groups(self, pattern: str) -> "BaseExpressionAPI":
        """Extract named capture groups into struct column."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS,
            arguments=[self._node],
            options={"pattern": pattern},
        )
        return self._build(node)
