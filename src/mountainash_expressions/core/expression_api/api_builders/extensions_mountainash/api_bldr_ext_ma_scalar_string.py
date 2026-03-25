"""Mountainash extension string operations APIBuilder.

Polars-compatible aliases for standard string operations.
Standard string operations are handled by SubstraitScalarStringAPIBuilder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode


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
