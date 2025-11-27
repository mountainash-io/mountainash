"""Polars string and pattern operations implementation."""

from typing import Any
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import StringExpressionProtocol


class PolarsStringExpressionSystem(PolarsBaseExpressionSystem, StringExpressionProtocol):
    """
    Polars implementation of string and pattern operations.

    Implements StringExpressionProtocol methods.
    Pattern methods use pat_ prefix as specified in protocol.
    """

    # ========================================
    # String Transformation Operations
    # ========================================

    def str_upper(self, operand: Any) -> pl.Expr:
        """Convert string to uppercase using Polars str.to_uppercase()."""
        return operand.str.to_uppercase()

    def str_lower(self, operand: Any) -> pl.Expr:
        """Convert string to lowercase using Polars str.to_lowercase()."""
        return operand.str.to_lowercase()

    def str_trim(self, operand: Any) -> pl.Expr:
        """Trim whitespace from both sides using Polars str.strip_chars()."""
        return operand.str.strip_chars()

    def str_ltrim(self, operand: Any) -> pl.Expr:
        """Trim whitespace from left side using Polars str.strip_chars_start()."""
        return operand.str.strip_chars_start()

    def str_rtrim(self, operand: Any) -> pl.Expr:
        """Trim whitespace from right side using Polars str.strip_chars_end()."""
        return operand.str.strip_chars_end()

    def str_substring(self, operand: Any, start: int, length: int = None) -> pl.Expr:
        """
        Extract substring using Polars str.slice().

        Args:
            operand: String expression (pl.Expr)
            start: Starting index
            length: Length of substring (None for rest of string)

        Returns:
            pl.Expr representing substring
        """
        if length is None:
            # From start to end
            return operand.str.slice(start)
        else:
            # From start with specific length
            return operand.str.slice(start, length)

    def str_length(self, operand: Any) -> pl.Expr:
        """Get string length using Polars str.len_chars()."""
        return operand.str.len_chars()

    def str_replace(self, operand: Any, substring: Any, replacement: Any) -> pl.Expr:
        """
        Replace substring using Polars str.replace().

        Args:
            operand: String expression (pl.Expr)
            substring: Substring to replace
            replacement: Replacement string

        Returns:
            pl.Expr with replacements applied

        Note:
            Protocol parameter names differ from deprecated (old/new vs substring/replacement).
            Using protocol names for consistency.
        """
        return operand.str.replace(substring, replacement, literal=True)

    def str_split(self, operand: Any, separator: Any) -> pl.Expr:
        """
        Split string using Polars str.split().

        Args:
            operand: String expression (pl.Expr)
            separator: Separator string

        Returns:
            pl.Expr containing list of split strings
        """
        return operand.str.split(separator)

    def str_concat(self, operand: Any, *others: Any, **kwargs) -> pl.Expr:
        """
        Concatenate strings using Polars + operator.

        Args:
            operand: First string expression (pl.Expr)
            *others: Additional string expressions to concatenate
            **kwargs: Optional separator keyword argument

        Returns:
            pl.Expr representing concatenated string

        Note:
            Protocol signature uses **kwargs to match visitor usage.
            Deprecated used explicit separator parameter.
        """
        separator = kwargs.get('separator', '')

        result = operand
        for other in others:
            if separator:
                result = result + pl.lit(separator) + other
            else:
                result = result + other
        return result

    # ========================================
    # String Check Operations (Return Boolean)
    # ========================================

    def str_contains(self, operand: Any, substring: str, **kwargs) -> pl.Expr:
        """
        Check if string contains substring using Polars str.contains().

        Args:
            operand: String expression (pl.Expr)
            substring: Substring to search for
            **kwargs: Additional options for str.contains()

        Returns:
            pl.Expr boolean indicating if substring is present
        """
        return operand.str.contains(substring, literal=True, **kwargs)

    def str_starts_with(self, operand: Any, prefix: str, **kwargs) -> pl.Expr:
        """
        Check if string starts with prefix using Polars str.starts_with().

        Args:
            operand: String expression (pl.Expr)
            prefix: Prefix to check for
            **kwargs: Additional options

        Returns:
            pl.Expr boolean indicating if string starts with prefix
        """
        return operand.str.starts_with(prefix, **kwargs)

    def str_ends_with(self, operand: Any, suffix: str, **kwargs) -> pl.Expr:
        """
        Check if string ends with suffix using Polars str.ends_with().

        Args:
            operand: String expression (pl.Expr)
            suffix: Suffix to check for
            **kwargs: Additional options

        Returns:
            pl.Expr boolean indicating if string ends with suffix
        """
        return operand.str.ends_with(suffix, **kwargs)

    # ========================================
    # Pattern Matching Operations
    # ========================================

    def pat_like(self, operand: Any, pattern: str, **kwargs) -> pl.Expr:
        """
        SQL LIKE pattern matching (% and _ wildcards).
        Convert SQL LIKE syntax to regex for Polars.

        Args:
            operand: String expression (pl.Expr)
            pattern: SQL LIKE pattern
            **kwargs: Additional options

        Returns:
            pl.Expr boolean indicating if pattern matches

        Note:
            RENAMED: Deprecated had pattern_like(), protocol expects pat_like().
        """
        # Convert SQL LIKE pattern to regex
        import re
        # Use placeholders for SQL wildcards before escaping (use unique strings without _ or %)
        pattern = pattern.replace('%', '\x00PERCENT\x00').replace('_', '\x00UNDERSCORE\x00')
        # Escape all regex special characters
        regex_pattern = re.escape(pattern)
        # Replace placeholders with regex equivalents
        regex_pattern = regex_pattern.replace('\x00PERCENT\x00', '.*').replace('\x00UNDERSCORE\x00', '.')
        # Anchor the pattern for full match
        regex_pattern = f'^{regex_pattern}$'
        return operand.str.contains(regex_pattern, literal=False, **kwargs)

    def pat_regex_match(self, operand: Any, pattern: str, **kwargs) -> pl.Expr:
        """Check if string fully matches regex pattern."""
        # Anchor pattern for full match if not already anchored
        if not pattern.startswith('^'):
            pattern = '^' + pattern
        if not pattern.endswith('$'):
            pattern = pattern + '$'
        return operand.str.contains(pattern, literal=False, **kwargs)

    def pat_regex_contains(self, operand: Any, pattern: str, **kwargs) -> pl.Expr:
        """Check if string contains regex pattern."""
        return operand.str.contains(pattern, literal=False, **kwargs)

    def pat_regex_replace(self, operand: Any, pattern: str, replacement: str, **kwargs) -> pl.Expr:
        """Replace text matching regex pattern."""
        return operand.str.replace(pattern, replacement, literal=False, **kwargs)
