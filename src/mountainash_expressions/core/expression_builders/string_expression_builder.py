"""String and pattern operations mixin for ExpressionBuilder."""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

from ..protocols import StringBuilderProtocol, ENUM_STRING_OPERATORS
from ..expression_nodes import (
    StringExpressionNode,
    StringIterableExpressionNode,
    StringSuffixExpressionNode,
    StringPrefixExpressionNode,
    StringSubstringExpressionNode,
    StringPatternExpressionNode,
    StringReplaceExpressionNode,
    StringPatternReplaceExpressionNode,
    StringSplitExpressionNode,
)


class StringExpressionBuilder(BaseExpressionBuilder, StringBuilderProtocol):
    """
    Mixin providing string and pattern operations for ExpressionBuilder.

    Implements all methods from StringBuilderProtocol:
    - String case: str_upper(), str_lower()
    - String trimming: str_trim(), str_ltrim(), str_rtrim()
    - String manipulation: str_substring(), str_replace(), str_concat(), str_split()
    - String properties: str_length()
    - String checks: str_contains(), str_starts_with(), str_ends_with()
    - Pattern matching: pat_like(), pat_regex_match(), pat_regex_contains(), pat_regex_replace()
    """

    # ========================================
    # String Case Operations
    # ========================================

    def str_upper(self) -> BaseExpressionBuilder:
        """
        Convert string to uppercase.

        Returns:
            New ExpressionBuilder with uppercase node

        Example:
            >>> col("name").str_upper()  # "hello" -> "HELLO"
        """

        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_UPPER,
            self._node
        )
        return self.create(node)

    def str_lower(self) -> BaseExpressionBuilder:
        """
        Convert string to lowercase.

        Returns:
            New ExpressionBuilder with lowercase node

        Example:
            >>> col("name").str_lower()  # "HELLO" -> "hello"
        """

        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_LOWER,
            self._node
        )
        return self.create(node)

    # ========================================
    # String Trimming Operations
    # ========================================

    def str_trim(self) -> BaseExpressionBuilder:
        """
        Trim whitespace from both sides of string.

        Returns:
            New ExpressionBuilder with trim node

        Example:
            >>> col("text").str_trim()  # "  hello  " -> "hello"
        """

        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_TRIM,
            self._node
        )
        return self.create(node)

    def str_ltrim(self) -> BaseExpressionBuilder:
        """
        Trim whitespace from left side of string.

        Returns:
            New ExpressionBuilder with ltrim node

        Example:
            >>> col("text").str_ltrim()  # "  hello" -> "hello"
        """

        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_LTRIM,
            self._node
        )
        return self.create(node)

    def str_rtrim(self) -> BaseExpressionBuilder:
        """
        Trim whitespace from right side of string.

        Returns:
            New ExpressionBuilder with rtrim node

        Example:
            >>> col("text").str_rtrim()  # "hello  " -> "hello"
        """

        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_RTRIM,
            self._node
        )
        return self.create(node)

    # ========================================
    # String Manipulation Operations
    # ========================================

    def str_substring(self,
                      start: Union[BaseExpressionBuilder, ExpressionNode, Any],
                      length: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Extract substring.

        Args:
            start: Starting position (0-indexed)
            length: Number of characters to extract

        Returns:
            New ExpressionBuilder with substring node

        Example:
            >>> col("text").str_substring(0, 5)  # "hello world" -> "hello"
        """

        start_node = self._to_node_or_value(start)
        length_node = self._to_node_or_value(length)
        node = StringSubstringExpressionNode(
            ENUM_STRING_OPERATORS.STR_SUBSTRING,
            self._node,
            start_node,
            length_node
        )
        return self.create(node)

    def str_replace(self, old: Union[BaseExpressionBuilder, ExpressionNode, Any],
                    new: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Replace substring with another string.

        Args:
            old: Substring to find
            new: Replacement string

        Returns:
            New ExpressionBuilder with replace node

        Example:
            >>> col("text").str_replace("old", "new")  # "old text" -> "new text"
        """

        old_node = self._to_node_or_value(old)
        new_node = self._to_node_or_value(new)
        node = StringReplaceExpressionNode(
            ENUM_STRING_OPERATORS.STR_REPLACE,
            self._node,
            old_node,
            new_node
        )
        return self.create(node)

    def str_concat(self, *others: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Concatenate strings.

        Args:
            *others: Additional strings to concatenate

        Returns:
            New ExpressionBuilder with concat node

        Example:
            >>> col("first").str_concat(" ", col("last"))  # "John" + " " + "Doe" -> "John Doe"
        """

        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = StringIterableExpressionNode(
            ENUM_STRING_OPERATORS.STR_CONCAT,
            *operands
        )
        return self.create(node)

    def str_split(self, separator: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Split string by separator.

        Args:
            separator: Separator string

        Returns:
            New ExpressionBuilder with split node

        Example:
            >>> col("text").str_split(",")  # "a,b,c" -> ["a", "b", "c"]
        """

        separator_node = self._to_node_or_value(separator)
        node = StringSplitExpressionNode(
            ENUM_STRING_OPERATORS.STR_SUBSTRING,  # TODO: Verify this operator
            self._node,
            separator_node
        )
        return self.create(node)

    # ========================================
    # String Property Operations
    # ========================================

    def str_length(self) -> BaseExpressionBuilder:
        """
        Get string length.

        Returns:
            New ExpressionBuilder with length node

        Example:
            >>> col("text").str_length()  # "hello" -> 5
        """

        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_LENGTH,
            self._node
        )
        return self.create(node)

    # ========================================
    # String Check Operations
    # ========================================

    def str_contains(self, substring: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Check if string contains substring.

        Args:
            substring: Substring to search for

        Returns:
            New ExpressionBuilder with contains node

        Example:
            >>> col("text").str_contains("hello")
        """

        substring_node = self._to_node_or_value(substring)
        node = StringPatternExpressionNode(
            ENUM_STRING_OPERATORS.STR_CONTAINS,
            self._node,
            substring_node
        )
        return self.create(node)

    def str_starts_with(self, prefix: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Check if string starts with prefix.

        Args:
            prefix: Prefix to check for

        Returns:
            New ExpressionBuilder with starts_with node

        Example:
            >>> col("text").str_starts_with("hello")
        """

        prefix_node = self._to_node_or_value(prefix)
        node = StringPrefixExpressionNode(
            ENUM_STRING_OPERATORS.STR_STARTS_WITH,
            self._node,
            prefix_node
        )
        return self.create(node)

    def str_ends_with(self, suffix: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Check if string ends with suffix.

        Args:
            suffix: Suffix to check for

        Returns:
            New ExpressionBuilder with ends_with node

        Example:
            >>> col("text").str_ends_with("world")
        """

        suffix_node = self._to_node_or_value(suffix)
        node = StringSuffixExpressionNode(
            ENUM_STRING_OPERATORS.STR_ENDS_WITH,
            self._node,
            suffix_node
        )
        return self.create(node)

    # ========================================
    # Pattern Matching Operations
    # ========================================

    def pat_like(self, pattern: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        SQL LIKE pattern matching.

        Args:
            pattern: SQL LIKE pattern (% for wildcard, _ for single char)

        Returns:
            New ExpressionBuilder with like node

        Example:
            >>> col("text").pat_like("%hello%")  # Contains "hello"
            >>> col("text").pat_like("hello%")   # Starts with "hello"
        """

        pattern_node = self._to_node_or_value(pattern)
        node = StringPatternExpressionNode(
            ENUM_STRING_OPERATORS.PAT_LIKE,
            self._node,
            pattern_node
        )
        return self.create(node)

    def pat_regex_match(self, pattern: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Check if string matches regex pattern (full match).

        Args:
            pattern: Regular expression pattern

        Returns:
            New ExpressionBuilder with regex_match node

        Example:
            >>> col("text").pat_regex_match(r"^\d{3}-\d{4}$")  # Phone number format
        """

        pattern_node = self._to_node_or_value(pattern)
        node = StringPatternExpressionNode(
            ENUM_STRING_OPERATORS.PAT_REGEX_MATCH,
            self._node,
            pattern_node
        )
        return self.create(node)

    def pat_regex_contains(self, pattern: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Check if string contains regex pattern.

        Args:
            pattern: Regular expression pattern

        Returns:
            New ExpressionBuilder with regex_contains node

        Example:
            >>> col("text").pat_regex_contains(r"\d+")  # Contains digits
        """

        pattern_node = self._to_node_or_value(pattern)
        node = StringPatternExpressionNode(
            ENUM_STRING_OPERATORS.PAT_REGEX_CONTAINS,
            self._node,
            pattern_node
        )
        return self.create(node)

    def pat_regex_replace(self, pattern: Union[BaseExpressionBuilder, ExpressionNode, Any],
                          replacement: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Replace regex pattern with replacement string.

        Args:
            pattern: Regular expression pattern
            replacement: Replacement string

        Returns:
            New ExpressionBuilder with regex_replace node

        Example:
            >>> col("text").pat_regex_replace(r"\d+", "XXX")  # Replace all digits with "XXX"
        """

        pattern_node = self._to_node_or_value(pattern)
        replacement_node = self._to_node_or_value(replacement)
        node = StringPatternReplaceExpressionNode(
            ENUM_STRING_OPERATORS.PAT_REGEX_REPLACE,
            self._node,
            pattern_node,
            replacement_node
        )
        return self.create(node)
