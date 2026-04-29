"""Mountainash string extension protocol.

Mountainash Extension: String
URI: file://extensions/functions_string.yaml

Extensions beyond Substrait standard:
- Short aliases: length, len
- Polars-compatible: to_uppercase, to_lowercase, strip_chars, strip_chars_start, strip_chars_end, len_chars
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class MountainAshScalarStringAPIBuilderProtocol(Protocol):
    """Builder protocol for Mountainash string extensions.

    These operations extend beyond the Substrait standard string
    functions to provide short aliases and Polars-compatible naming.
    """

    # Short aliases
    def length(self) -> BaseExpressionAPI:
        """Alias for char_length()."""
        ...

    def len(self) -> BaseExpressionAPI:
        """Alias for char_length()."""
        ...

    # Polars-compatible aliases
    def to_uppercase(self) -> BaseExpressionAPI:
        """Alias for upper() — Polars compatibility."""
        ...

    def to_lowercase(self) -> BaseExpressionAPI:
        """Alias for lower() — Polars compatibility."""
        ...

    def strip_chars(self, characters: Optional[str] = None) -> BaseExpressionAPI:
        """Alias for trim() — Polars compatibility."""
        ...

    def strip_chars_start(self, characters: Optional[str] = None) -> BaseExpressionAPI:
        """Alias for ltrim() — Polars compatibility."""
        ...

    def strip_chars_end(self, characters: Optional[str] = None) -> BaseExpressionAPI:
        """Alias for rtrim() — Polars compatibility."""
        ...

    def len_chars(self) -> BaseExpressionAPI:
        """Alias for char_length() — Polars compatibility."""
        ...

    # Convenience methods (AST-level composition)
    def zfill(self, length: int) -> BaseExpressionAPI:
        """Left-pad with zeros."""
        ...

    def strip_prefix(self, prefix: str) -> BaseExpressionAPI:
        """Remove prefix from string if present."""
        ...

    def strip_suffix(self, suffix: str) -> BaseExpressionAPI:
        """Remove suffix from string if present."""
        ...

    def to_date(self, format: str) -> BaseExpressionAPI:
        """Parse string to date using format string."""
        ...

    def to_datetime(self, format: str) -> BaseExpressionAPI:
        """Parse string to datetime using format string."""
        ...

    def to_time(self, format: str) -> BaseExpressionAPI:
        """Parse string to time using format string."""
        ...

    def to_integer(self, base: int = 10) -> BaseExpressionAPI:
        """Parse string to integer with given base."""
        ...

    def json_decode(self, dtype: Any = None) -> BaseExpressionAPI:
        """Parse JSON string into structured data."""
        ...

    def json_path_match(self, json_path: str) -> BaseExpressionAPI:
        """Extract value from JSON string via JSONPath."""
        ...

    def encode(self, encoding: str) -> BaseExpressionAPI:
        """Encode string to hex or base64."""
        ...

    def decode(self, encoding: str, *, strict: bool = True) -> BaseExpressionAPI:
        """Decode hex or base64 string to binary."""
        ...

    def extract_groups(self, pattern: str) -> BaseExpressionAPI:
        """Extract named capture groups into struct column."""
        ...
