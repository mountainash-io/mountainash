"""String operations namespace (explicit .str accessor)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseNamespace
from ..protocols import ENUM_STRING_OPERATORS
from ..expression_nodes import (
    StringExpressionNode,
    StringIterableExpressionNode,
    StringSuffixExpressionNode,
    StringPrefixExpressionNode,
    StringSubstringExpressionNode,
    StringPatternExpressionNode,
    StringSearchExpressionNode,
    StringReplaceExpressionNode,
    StringPatternReplaceExpressionNode,
    StringSplitExpressionNode,
)

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


class StringNamespace(BaseNamespace):
    """
    String operations namespace accessed via .str accessor.

    Provides string manipulation and pattern matching operations.
    Method names omit the 'str_' and 'pat_' prefixes since the
    namespace provides that context.

    Usage:
        col("text").str.upper()      # Instead of str_upper()
        col("text").str.contains()   # Instead of str_contains()
        col("text").str.like()       # Instead of pat_like()

    Case Operations:
        upper, lower

    Trimming Operations:
        trim, ltrim, rtrim

    Manipulation Operations:
        substring, replace, concat, split

    Property Operations:
        length

    Check Operations:
        contains, starts_with, ends_with

    Pattern Operations:
        like, regex_match, regex_contains, regex_replace
    """

    # ========================================
    # Case Operations
    # ========================================

    def upper(self) -> BaseExpressionAPI:
        """
        Convert string to uppercase.

        Returns:
            New ExpressionAPI with uppercase node.

        Example:
            >>> col("name").str.upper()  # "hello" -> "HELLO"
        """
        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_UPPER,
            self._node,
        )
        return self._build(node)

    def lower(self) -> BaseExpressionAPI:
        """
        Convert string to lowercase.

        Returns:
            New ExpressionAPI with lowercase node.

        Example:
            >>> col("name").str.lower()  # "HELLO" -> "hello"
        """
        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_LOWER,
            self._node,
        )
        return self._build(node)

    # ========================================
    # Trimming Operations
    # ========================================

    def trim(self) -> BaseExpressionAPI:
        """
        Trim whitespace from both sides of string.

        Returns:
            New ExpressionAPI with trim node.

        Example:
            >>> col("text").str.trim()  # "  hello  " -> "hello"
        """
        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_TRIM,
            self._node,
        )
        return self._build(node)

    def ltrim(self) -> BaseExpressionAPI:
        """
        Trim whitespace from left side of string.

        Returns:
            New ExpressionAPI with ltrim node.

        Example:
            >>> col("text").str.ltrim()  # "  hello" -> "hello"
        """
        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_LTRIM,
            self._node,
        )
        return self._build(node)

    def rtrim(self) -> BaseExpressionAPI:
        """
        Trim whitespace from right side of string.

        Returns:
            New ExpressionAPI with rtrim node.

        Example:
            >>> col("text").str.rtrim()  # "hello  " -> "hello"
        """
        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_RTRIM,
            self._node,
        )
        return self._build(node)

    # ========================================
    # Manipulation Operations
    # ========================================

    def substring(
        self,
        start: Union[BaseExpressionAPI, ExpressionNode, Any],
        length: Union[BaseExpressionAPI, ExpressionNode, Any, None] = None,
    ) -> BaseExpressionAPI:
        """
        Extract substring.

        Args:
            start: Starting position (0-indexed).
            length: Number of characters to extract. If None, extracts to end.

        Returns:
            New ExpressionAPI with substring node.

        Example:
            >>> col("text").str.substring(0, 5)  # "hello world" -> "hello"
            >>> col("text").str.substring(6)     # "hello world" -> "world"
        """
        start_node = self._to_node_or_value(start)
        length_node = self._to_node_or_value(length) if length is not None else None
        node = StringSubstringExpressionNode(
            ENUM_STRING_OPERATORS.STR_SUBSTRING,
            self._node,
            start_node,
            length_node,
        )
        return self._build(node)

    def replace(
        self,
        old: Union[BaseExpressionAPI, ExpressionNode, Any],
        new: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Replace substring with another string.

        Args:
            old: Substring to find.
            new: Replacement string.

        Returns:
            New ExpressionAPI with replace node.

        Example:
            >>> col("text").str.replace("old", "new")
        """
        old_node = self._to_node_or_value(old)
        new_node = self._to_node_or_value(new)
        node = StringReplaceExpressionNode(
            ENUM_STRING_OPERATORS.STR_REPLACE,
            self._node,
            old_node,
            new_node,
        )
        return self._build(node)

    def concat(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Concatenate strings.

        Args:
            *others: Additional strings to concatenate.

        Returns:
            New ExpressionAPI with concat node.

        Example:
            >>> col("first").str.concat(" ", col("last"))
        """
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = StringIterableExpressionNode(
            ENUM_STRING_OPERATORS.STR_CONCAT,
            *operands,
        )
        return self._build(node)

    def split(
        self,
        separator: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Split string by separator.

        Args:
            separator: Separator string.

        Returns:
            New ExpressionAPI with split node.

        Example:
            >>> col("text").str.split(",")  # "a,b,c" -> ["a", "b", "c"]
        """
        separator_node = self._to_node_or_value(separator)
        node = StringSplitExpressionNode(
            ENUM_STRING_OPERATORS.STR_SUBSTRING,  # TODO: Verify this operator
            self._node,
            separator_node,
        )
        return self._build(node)

    # ========================================
    # Property Operations
    # ========================================

    def length(self) -> BaseExpressionAPI:
        """
        Get string length.

        Returns:
            New ExpressionAPI with length node.

        Example:
            >>> col("text").str.length()  # "hello" -> 5
        """
        node = StringExpressionNode(
            ENUM_STRING_OPERATORS.STR_LENGTH,
            self._node,
        )
        return self._build(node)

    # ========================================
    # Check Operations
    # ========================================

    def contains(
        self,
        substring: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if string contains substring.

        Args:
            substring: Substring to search for.

        Returns:
            New ExpressionAPI with contains node.

        Example:
            >>> col("text").str.contains("hello")
        """
        substring_node = self._to_node_or_value(substring)
        node = StringSearchExpressionNode(
            ENUM_STRING_OPERATORS.STR_CONTAINS,
            self._node,
            substring_node,
        )
        return self._build(node)

    def starts_with(
        self,
        prefix: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if string starts with prefix.

        Args:
            prefix: Prefix to check for.

        Returns:
            New ExpressionAPI with starts_with node.

        Example:
            >>> col("text").str.starts_with("hello")
        """
        prefix_node = self._to_node_or_value(prefix)
        node = StringPrefixExpressionNode(
            ENUM_STRING_OPERATORS.STR_STARTS_WITH,
            self._node,
            prefix_node,
        )
        return self._build(node)

    def ends_with(
        self,
        suffix: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if string ends with suffix.

        Args:
            suffix: Suffix to check for.

        Returns:
            New ExpressionAPI with ends_with node.

        Example:
            >>> col("text").str.ends_with("world")
        """
        suffix_node = self._to_node_or_value(suffix)
        node = StringSuffixExpressionNode(
            ENUM_STRING_OPERATORS.STR_ENDS_WITH,
            self._node,
            suffix_node,
        )
        return self._build(node)

    # ========================================
    # Pattern Operations
    # ========================================

    def like(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        SQL LIKE pattern matching.

        Args:
            pattern: SQL LIKE pattern (% for wildcard, _ for single char).

        Returns:
            New ExpressionAPI with like node.

        Example:
            >>> col("text").str.like("%hello%")  # Contains "hello"
            >>> col("text").str.like("hello%")   # Starts with "hello"
        """
        pattern_node = self._to_node_or_value(pattern)
        node = StringPatternExpressionNode(
            ENUM_STRING_OPERATORS.PAT_LIKE,
            self._node,
            pattern_node,
        )
        return self._build(node)

    def regex_match(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if string matches regex pattern (full match).

        Args:
            pattern: Regular expression pattern.

        Returns:
            New ExpressionAPI with regex_match node.

        Example:
            >>> col("text").str.regex_match(r"^\\d{3}-\\d{4}$")
        """
        pattern_node = self._to_node_or_value(pattern)
        node = StringPatternExpressionNode(
            ENUM_STRING_OPERATORS.PAT_REGEX_MATCH,
            self._node,
            pattern_node,
        )
        return self._build(node)

    def regex_contains(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Check if string contains regex pattern.

        Args:
            pattern: Regular expression pattern.

        Returns:
            New ExpressionAPI with regex_contains node.

        Example:
            >>> col("text").str.regex_contains(r"\\d+")  # Contains digits
        """
        pattern_node = self._to_node_or_value(pattern)
        node = StringPatternExpressionNode(
            ENUM_STRING_OPERATORS.PAT_REGEX_CONTAINS,
            self._node,
            pattern_node,
        )
        return self._build(node)

    def regex_replace(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        replacement: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Replace regex pattern with replacement string.

        Args:
            pattern: Regular expression pattern.
            replacement: Replacement string.

        Returns:
            New ExpressionAPI with regex_replace node.

        Example:
            >>> col("text").str.regex_replace(r"\\d+", "XXX")
        """
        pattern_node = self._to_node_or_value(pattern)
        replacement_node = self._to_node_or_value(replacement)
        node = StringPatternReplaceExpressionNode(
            ENUM_STRING_OPERATORS.PAT_REGEX_REPLACE,
            self._node,
            pattern_node,
            replacement_node,
        )
        return self._build(node)
