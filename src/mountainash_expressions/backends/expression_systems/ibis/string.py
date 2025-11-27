"""Ibis string and pattern operations implementation."""

from typing import Any
from .base import IbisBaseExpressionSystem
from ....core.protocols import StringExpressionProtocol


class IbisStringExpressionSystem(IbisBaseExpressionSystem, StringExpressionProtocol):
    """
    Ibis implementation of string and pattern operations.

    Note: Pattern methods use pat_ prefix as specified in protocol.
    """

    # String Transformation
    def str_upper(self, operand: Any) -> Any:
        return operand.upper()

    def str_lower(self, operand: Any) -> Any:
        return operand.lower()

    def str_trim(self, operand: Any) -> Any:
        return operand.strip()

    def str_ltrim(self, operand: Any) -> Any:
        return operand.lstrip()

    def str_rtrim(self, operand: Any) -> Any:
        return operand.rstrip()

    def str_substring(self, operand: Any, start: int, length: int = None) -> Any:
        if length is None:
            return operand.substr(start)
        else:
            return operand.substr(start, length)

    def str_length(self, operand: Any) -> Any:
        return operand.length()

    def str_replace(self, operand: Any, substring: Any, replacement: Any) -> Any:
        return operand.replace(substring, replacement)

    def str_split(self, operand: Any, separator: Any) -> Any:
        """
        Note:
            ISSUE: Ibis str.split() may not exist in all versions.
            Using fallback approach.
        """
        return operand.split(separator)

    def str_concat(self, operand: Any, *others: Any, **kwargs) -> Any:
        separator = kwargs.get('separator', '')
        result = operand
        for other in others:
            if separator:
                import ibis
                result = result + ibis.literal(separator) + other
            else:
                result = result + other
        return result

    # String Checks
    def str_contains(self, operand: Any, substring: str, **kwargs) -> Any:
        return operand.contains(substring)

    def str_starts_with(self, operand: Any, prefix: str, **kwargs) -> Any:
        return operand.startswith(prefix)

    def str_ends_with(self, operand: Any, suffix: str, **kwargs) -> Any:
        return operand.endswith(suffix)

    # Pattern Matching
    def pat_like(self, operand: Any, pattern: str, **kwargs) -> Any:
        """SQL LIKE pattern matching using Ibis .like() method."""
        return operand.like(pattern)

    def pat_regex_match(self, operand: Any, pattern: str, **kwargs) -> Any:
        """Check if string fully matches regex pattern."""
        if not pattern.startswith('^'):
            pattern = '^' + pattern
        if not pattern.endswith('$'):
            pattern = pattern + '$'
        return operand.re_search(pattern)

    def pat_regex_contains(self, operand: Any, pattern: str, **kwargs) -> Any:
        """Check if string contains regex pattern."""
        return operand.re_search(pattern)

    def pat_regex_replace(self, operand: Any, pattern: str, replacement: str, **kwargs) -> Any:
        """Replace text matching regex pattern."""
        return operand.re_replace(pattern, replacement)
