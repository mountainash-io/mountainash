"""String operations namespace (explicit .str accessor).

Substrait-aligned implementation using ScalarFunctionNode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .ns_base import BaseExpressionNamespace
from ...expression_nodes import ScalarFunctionNode
from ...expression_system.function_keys.enums import KEY_SCALAR_STRING

if TYPE_CHECKING:
    from ..api_base import BaseExpressionAPI
    from ...expression_nodes import ExpressionNode


class ScalarStringNamespace(BaseExpressionNamespace):
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
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.UPPER,
            arguments=[self._node],
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
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.LOWER,
            arguments=[self._node],
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
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.TRIM,
            arguments=[self._node],
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
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.LTRIM,
            arguments=[self._node],
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
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.RTRIM,
            arguments=[self._node],
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
        options = {"start": start}
        if length is not None:
            options["length"] = length

        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.SUBSTRING,
            arguments=[self._node],
            options=options,
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
        old_node = self._to_substrait_node(old)
        new_node = self._to_substrait_node(new)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.REPLACE,
            arguments=[self._node, old_node, new_node],
        )
        return self._build(node)

    def concat(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
        separator: str = "",
    ) -> BaseExpressionAPI:
        """
        Concatenate strings.

        Args:
            *others: Additional strings to concatenate.
            separator: Separator between strings (default: empty string).

        Returns:
            New ExpressionAPI with concat node.

        Example:
            >>> col("first").str.concat(" ", col("last"))
        """
        operands = [self._node] + [self._to_substrait_node(other) for other in others]
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.CONCAT,
            arguments=operands,
            options={"separator": separator} if separator else {},
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
        separator_node = self._to_substrait_node(separator)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.SPLIT,
            arguments=[self._node, separator_node],
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
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.CHAR_LENGTH,
            arguments=[self._node],
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
        substring_node = self._to_substrait_node(substring)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.CONTAINS,
            arguments=[self._node, substring_node],
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
        prefix_node = self._to_substrait_node(prefix)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.STARTS_WITH,
            arguments=[self._node, prefix_node],
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
        suffix_node = self._to_substrait_node(suffix)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.ENDS_WITH,
            arguments=[self._node, suffix_node],
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
        pattern_node = self._to_substrait_node(pattern)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.LIKE,
            arguments=[self._node, pattern_node],
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
        pattern_node = self._to_substrait_node(pattern)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.REGEXP_MATCH,
            arguments=[self._node, pattern_node],
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
        pattern_node = self._to_substrait_node(pattern)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.REGEXP_CONTAINS,
            arguments=[self._node, pattern_node],
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
        pattern_node = self._to_substrait_node(pattern)
        replacement_node = self._to_substrait_node(replacement)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_STRING.REGEXP_REPLACE,
            arguments=[self._node, pattern_node, replacement_node],
        )
        return self._build(node)
