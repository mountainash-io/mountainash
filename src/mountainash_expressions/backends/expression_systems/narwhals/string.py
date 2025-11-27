"""Narwhals string and pattern operations implementation."""

from typing import Any
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import StringExpressionProtocol


class NarwhalsStringExpressionSystem(NarwhalsBaseExpressionSystem, StringExpressionProtocol):
    """
    Narwhals implementation of string and pattern operations.

    Implements StringExpressionProtocol methods.
    Pattern methods use pat_ prefix as specified in protocol.
    """

    # ========================================
    # String Transformation Operations
    # ========================================

    def str_upper(self, operand: Any) -> nw.Expr:
        """Convert string to uppercase using Narwhals str.to_uppercase()."""
        return operand.str.to_uppercase()

    def str_lower(self, operand: Any) -> nw.Expr:
        """Convert string to lowercase using Narwhals str.to_lowercase()."""
        return operand.str.to_lowercase()

    def str_trim(self, operand: Any) -> nw.Expr:
        """Trim whitespace from both sides using Narwhals str.strip_chars()."""
        return operand.str.strip_chars()

    def str_ltrim(self, operand: Any) -> nw.Expr:
        """Trim whitespace from left side using Narwhals str.strip_chars_start()."""
        return operand.str.strip_chars_start()

    def str_rtrim(self, operand: Any) -> nw.Expr:
        """Trim whitespace from right side using Narwhals str.strip_chars_end()."""
        return operand.str.strip_chars_end()

    def str_substring(self, operand: Any, start: int, length: int = None) -> nw.Expr:
        """Extract substring using Narwhals str.slice()."""
        if length is None:
            return operand.str.slice(start)
        else:
            return operand.str.slice(start, length)

    def str_length(self, operand: Any) -> nw.Expr:
        """Get string length using Narwhals str.len_chars()."""
        return operand.str.len_chars()

    def str_replace(self, operand: Any, substring: Any, replacement: Any) -> nw.Expr:
        """Replace substring using Narwhals str.replace()."""
        return operand.str.replace(substring, replacement, literal=True)

    def str_split(self, operand: Any, separator: Any) -> nw.Expr:
        """Split string using Narwhals str.split()."""
        return operand.str.split(separator)

    def str_concat(self, operand: Any, *others: Any, **kwargs) -> nw.Expr:
        """Concatenate strings using Narwhals + operator."""
        separator = kwargs.get('separator', '')
        result = operand
        for other in others:
            if separator:
                result = result + nw.lit(separator) + other
            else:
                result = result + other
        return result

    # ========================================
    # String Check Operations (Return Boolean)
    # ========================================

    def str_contains(self, operand: Any, substring: str, **kwargs) -> nw.Expr:
        """Check if string contains substring using Narwhals str.contains()."""
        return operand.str.contains(substring, literal=True, **kwargs)

    def str_starts_with(self, operand: Any, prefix: str, **kwargs) -> nw.Expr:
        """Check if string starts with prefix using Narwhals str.starts_with()."""
        return operand.str.starts_with(prefix, **kwargs)

    def str_ends_with(self, operand: Any, suffix: str, **kwargs) -> nw.Expr:
        """Check if string ends with suffix using Narwhals str.ends_with()."""
        return operand.str.ends_with(suffix, **kwargs)

    # ========================================
    # Pattern Matching Operations
    # ========================================

    def pat_like(self, operand: Any, pattern: str, **kwargs) -> nw.Expr:
        """
        SQL LIKE pattern matching (% and _ wildcards).
        """
        import re
        pattern = pattern.replace('%', '\x00PERCENT\x00').replace('_', '\x00UNDERSCORE\x00')
        regex_pattern = re.escape(pattern)
        regex_pattern = regex_pattern.replace('\x00PERCENT\x00', '.*').replace('\x00UNDERSCORE\x00', '.')
        regex_pattern = f'^{regex_pattern}$'
        return operand.str.contains(regex_pattern, literal=False, **kwargs)

    def pat_regex_match(self, operand: Any, pattern: str, **kwargs) -> nw.Expr:
        """
        Check if string fully matches regex pattern.
        """
        if not pattern.startswith('^'):
            pattern = '^' + pattern
        if not pattern.endswith('$'):
            pattern = pattern + '$'
        return operand.str.contains(pattern, literal=False, **kwargs)

    def pat_regex_contains(self, operand: Any, pattern: str, **kwargs) -> nw.Expr:
        """
        Check if string contains regex pattern.
        """
        return operand.str.contains(pattern, literal=False, **kwargs)

    def pat_regex_replace(self, operand: Any, pattern: str, replacement: str, **kwargs) -> nw.Expr:
        """
        Replace text matching regex pattern.
        """
        return operand.str.replace(pattern, replacement, literal=False, **kwargs)
