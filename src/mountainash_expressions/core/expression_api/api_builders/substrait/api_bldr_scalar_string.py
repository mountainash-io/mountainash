"""String operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarStringBuilderProtocol for string operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..api_builder_base import BaseExpressionAPIBuilder
from ...api_base import BaseExpressionAPI

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.substrait import SubstraitScalarStringAPIBuilderProtocol


if TYPE_CHECKING:
    from mountainash_expressions.core.expression_nodes import ExpressionNode, ScalarFunctionNode


class SubstraitScalarStringAPIBuilder(BaseExpressionAPIBuilder, SubstraitScalarStringAPIBuilderProtocol):
    """
    String operations APIBuilder (Substrait-aligned).

    Provides string manipulation operations.

    Case Conversion:
        lower, upper: Basic case conversion
        swapcase: Swap upper/lower
        capitalize: Capitalize first character
        title: Title case (except articles)
        initcap: Capitalize each word

    Trimming:
        ltrim, rtrim, trim: Remove characters from sides

    Padding:
        lpad, rpad: Pad to length
        center: Center with padding

    Extraction:
        substring: Extract substring by position
        left, right: Extract from start/end
        replace_slice: Replace portion of string

    Search:
        contains: Check if substring exists
        starts_with, ends_with: Check prefix/suffix
        strpos: Find position of substring
        count_substring: Count occurrences

    Pattern Matching:
        like: SQL LIKE pattern
        regexp_match_substring: Extract regex match
        regexp_replace: Replace regex matches
        regexp_string_split: Split by regex pattern

    Manipulation:
        concat: Concatenate strings
        concat_ws: Concatenate with separator
        replace: Replace all occurrences
        repeat: Repeat string
        reverse: Reverse string
        string_split: Split by separator

    Info:
        char_length: Character count
        bit_length: Bit count
        octet_length: Byte count
    """

    # ========================================
    # Case Conversion
    # ========================================

    def lower(self) -> BaseExpressionAPI:
        """
        Convert to lowercase.

        Substrait: lower

        Returns:
            New ExpressionAPI with lower node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
            arguments=[self._node],
        )
        return self._build(node)

    def upper(self) -> BaseExpressionAPI:
        """
        Convert to uppercase.

        Substrait: upper

        Returns:
            New ExpressionAPI with upper node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
            arguments=[self._node],
        )
        return self._build(node)

    def swapcase(self) -> BaseExpressionAPI:
        """
        Swap case of characters (upper to lower and vice versa).

        Substrait: swapcase

        Returns:
            New ExpressionAPI with swapcase node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE,
            arguments=[self._node],
        )
        return self._build(node)

    def capitalize(self) -> BaseExpressionAPI:
        """
        Capitalize first character.

        Substrait: capitalize

        Returns:
            New ExpressionAPI with capitalize node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE,
            arguments=[self._node],
        )
        return self._build(node)

    def title(self) -> BaseExpressionAPI:
        """
        Convert to title case (except articles).

        Substrait: title

        Returns:
            New ExpressionAPI with title node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE,
            arguments=[self._node],
        )
        return self._build(node)

    def initcap(self) -> BaseExpressionAPI:
        """
        Capitalize first character of each word.

        Substrait: initcap

        Returns:
            New ExpressionAPI with initcap node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Trimming
    # ========================================

    def ltrim(
        self,
        characters: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any]] = None,
    ) -> BaseExpressionAPI:
        """
        Remove characters from left side.

        Substrait: ltrim

        Args:
            characters: Characters to remove (default: spaces).

        Returns:
            New ExpressionAPI with ltrim node.
        """
        if characters is None:
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM,
                arguments=[self._node],
            )
        else:
            char_node = self._to_substrait_node(characters)
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM,
                arguments=[self._node, char_node],
            )
        return self._build(node)

    def rtrim(
        self,
        characters: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any]] = None,
    ) -> BaseExpressionAPI:
        """
        Remove characters from right side.

        Substrait: rtrim

        Args:
            characters: Characters to remove (default: spaces).

        Returns:
            New ExpressionAPI with rtrim node.
        """
        if characters is None:
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM,
                arguments=[self._node],
            )
        else:
            char_node = self._to_substrait_node(characters)
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM,
                arguments=[self._node, char_node],
            )
        return self._build(node)

    def trim(
        self,
        characters: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any]] = None,
    ) -> BaseExpressionAPI:
        """
        Remove characters from both sides.

        Substrait: trim

        Args:
            characters: Characters to remove (default: spaces).

        Returns:
            New ExpressionAPI with trim node.
        """
        if characters is None:
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TRIM,
                arguments=[self._node],
            )
        else:
            char_node = self._to_substrait_node(characters)
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TRIM,
                arguments=[self._node, char_node],
            )
        return self._build(node)

    # ========================================
    # Padding
    # ========================================

    def lpad(
        self,
        length: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
        characters: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any]] = None,
    ) -> BaseExpressionAPI:
        """
        Left-pad to specified length.

        Substrait: lpad

        Args:
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            New ExpressionAPI with lpad node.
        """
        length_node = self._to_substrait_node(length)
        if characters is None:
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,
                arguments=[self._node, length_node],
            )
        else:
            char_node = self._to_substrait_node(characters)
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,
                arguments=[self._node, length_node, char_node],
            )
        return self._build(node)

    def rpad(
        self,
        length: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
        characters: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any]] = None,
    ) -> BaseExpressionAPI:
        """
        Right-pad to specified length.

        Substrait: rpad

        Args:
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            New ExpressionAPI with rpad node.
        """
        length_node = self._to_substrait_node(length)
        if characters is None:
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RPAD,
                arguments=[self._node, length_node],
            )
        else:
            char_node = self._to_substrait_node(characters)
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RPAD,
                arguments=[self._node, length_node, char_node],
            )
        return self._build(node)

    def center(
        self,
        length: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
        character: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any]] = None,
    ) -> BaseExpressionAPI:
        """
        Center string by padding both sides.

        Substrait: center

        Args:
            length: Target length.
            character: Padding character (default: space).

        Returns:
            New ExpressionAPI with center node.
        """
        length_node = self._to_substrait_node(length)
        if character is None:
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
                arguments=[self._node, length_node],
            )
        else:
            char_node = self._to_substrait_node(character)
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
                arguments=[self._node, length_node, char_node],
            )
        return self._build(node)

    # ========================================
    # Extraction
    # ========================================

    def substring(
        self,
        start: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
        length: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any, int]] = None,
    ) -> BaseExpressionAPI:
        """
        Extract a substring.

        Substrait: substring

        Args:
            start: Start position (1-indexed).
            length: Number of characters (optional).

        Returns:
            New ExpressionAPI with substring node.
        """
        start_node = self._to_substrait_node(start)
        if length is None:
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
                arguments=[self._node, start_node],
            )
        else:
            length_node = self._to_substrait_node(length)
            node = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
                arguments=[self._node, start_node, length_node],
            )
        return self._build(node)

    def left(
        self,
        count: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Extract count characters from left.

        Substrait: left

        Args:
            count: Number of characters.

        Returns:
            New ExpressionAPI with left node.
        """
        count_node = self._to_substrait_node(count)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LEFT,
            arguments=[self._node, count_node],
        )
        return self._build(node)

    def right(
        self,
        count: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Extract count characters from right.

        Substrait: right

        Args:
            count: Number of characters.

        Returns:
            New ExpressionAPI with right node.
        """
        count_node = self._to_substrait_node(count)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RIGHT,
            arguments=[self._node, count_node],
        )
        return self._build(node)

    def replace_slice(
        self,
        start: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
        length: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
        replacement: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Replace a slice of the string.

        Substrait: replace_slice

        Args:
            start: Start position (1-indexed).
            length: Number of characters to replace.
            replacement: Replacement string.

        Returns:
            New ExpressionAPI with replace_slice node.
        """
        start_node = self._to_substrait_node(start)
        length_node = self._to_substrait_node(length)
        replacement_node = self._to_substrait_node(replacement)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE,
            arguments=[self._node, start_node, length_node, replacement_node],
        )
        return self._build(node)

    # ========================================
    # Search
    # ========================================

    def contains(
        self,
        substring: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Whether string contains substring.

        Substrait: contains

        Args:
            substring: Substring to search for.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with contains node.
        """
        substring_node = self._to_substrait_node(substring)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            arguments=[self._node, substring_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)

    def starts_with(
        self,
        prefix: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Whether string starts with prefix.

        Substrait: starts_with

        Args:
            prefix: Prefix to check.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with starts_with node.
        """
        prefix_node = self._to_substrait_node(prefix)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
            arguments=[self._node, prefix_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)

    def ends_with(
        self,
        suffix: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Whether string ends with suffix.

        Substrait: ends_with

        Args:
            suffix: Suffix to check.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with ends_with node.
        """
        suffix_node = self._to_substrait_node(suffix)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
            arguments=[self._node, suffix_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)

    def strpos(
        self,
        substring: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Position of first occurrence of substring (1-indexed, 0 if not found).

        Substrait: strpos

        Args:
            substring: Substring to find.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with strpos node.
        """
        substring_node = self._to_substrait_node(substring)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
            arguments=[self._node, substring_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)

    def count_substring(
        self,
        substring: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Count non-overlapping occurrences of substring.

        Substrait: count_substring

        Args:
            substring: Substring to count.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with count_substring node.
        """
        substring_node = self._to_substrait_node(substring)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
            arguments=[self._node, substring_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)


    # ========================================
    # Info
    # ========================================

    def char_length(self) -> BaseExpressionAPI:
        """
        Return number of characters.

        Substrait: char_length

        Returns:
            New ExpressionAPI with char_length node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CHAR_LENGTH,
            arguments=[self._node],
        )
        return self._build(node)


    def bit_length(self) -> BaseExpressionAPI:
        """
        Return number of bits.

        Substrait: bit_length

        Returns:
            New ExpressionAPI with bit_length node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.BIT_LENGTH,
            arguments=[self._node],
        )
        return self._build(node)

    def octet_length(self) -> BaseExpressionAPI:
        """
        Return number of bytes.

        Substrait: octet_length

        Returns:
            New ExpressionAPI with octet_length node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.OCTET_LENGTH,
            arguments=[self._node],
        )
        return self._build(node)


    # ========================================
    # Manipulation
    # ========================================

    def concat(
        self,
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Concatenate strings.

        Substrait: concat

        Args:
            *others: Strings to concatenate with this one.

        Returns:
            New ExpressionAPI with concat node.
        """
        operands = [self._node] + [self._to_substrait_node(o) for o in others]
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT,
            arguments=operands,
        )
        return self._build(node)

    def concat_ws(
        self,
        separator: Union[BaseExpressionAPI, "ExpressionNode", Any],
        *others: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Concatenate strings with separator.

        Substrait: concat_ws

        Args:
            separator: String to insert between values.
            *others: Additional strings to concatenate.

        Returns:
            New ExpressionAPI with concat_ws node.
        """
        separator_node = self._to_substrait_node(separator)
        operands = [self._node] + [self._to_substrait_node(o) for o in others]
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT_WS,
            arguments=[separator_node] + operands,
        )
        return self._build(node)

    def replace(
        self,
        old: Union[BaseExpressionAPI, "ExpressionNode", Any],
        new: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Replace all occurrences of substring.

        Substrait: replace

        Args:
            old: Substring to find.
            new: Replacement string.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with replace node.
        """
        old_node = self._to_substrait_node(old)
        new_node = self._to_substrait_node(new)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
            arguments=[self._node, old_node, new_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)

    def repeat(
        self,
        count: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Repeat string count times.

        Substrait: repeat

        Args:
            count: Number of repetitions.

        Returns:
            New ExpressionAPI with repeat node.
        """
        count_node = self._to_substrait_node(count)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT,
            arguments=[self._node, count_node],
        )
        return self._build(node)

    def reverse(self) -> BaseExpressionAPI:
        """
        Reverse the string.

        Substrait: reverse

        Returns:
            New ExpressionAPI with reverse node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REVERSE,
            arguments=[self._node],
        )
        return self._build(node)


    # ========================================
    # Pattern Matching
    # ========================================

    def like(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Match against a SQL LIKE pattern.

        Substrait: like

        Args:
            pattern: LIKE pattern (% for any chars, _ for single char).
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with like node.
        """
        pattern_node = self._to_substrait_node(pattern)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
            arguments=[self._node, pattern_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)

    def regexp_match_substring(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        position: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any, int]] = None,
        occurrence: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any, int]] = None,
        group: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any, int]] = None,
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Extract substring matching regex pattern.

        Substrait: regexp_match_substring

        Args:
            pattern: Regular expression pattern.
            position: Start position for search (1-indexed).
            occurrence: Which occurrence to extract.
            group: Capture group to extract.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with regexp_match_substring node.
        """
        pattern_node = self._to_substrait_node(pattern)
        args = [self._node, pattern_node]

        if position is not None:
            args.append(self._to_substrait_node(position))
        if occurrence is not None:
            args.append(self._to_substrait_node(occurrence))
        if group is not None:
            args.append(self._to_substrait_node(group))

        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_SUBSTRING,
            arguments=args,
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)



    def regexp_match_substring_all(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        position: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        group: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        *,
        case_sensitive: bool = True,
        multiline: bool = None,
        dotall: bool = None,
    ) -> BaseExpressionAPI:
        """Extract all substrings that match the given regular expression pattern

        Substrait: regexp_match_substring_all
        """
        ...

    def regexp_strpos(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        position: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        occurrence: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        *,
        case_sensitive: bool = True,
        multiline: bool = None,
        dotall: bool = None,
    ) -> BaseExpressionAPI:
        """"Return the position of an occurrence of the given regular expression pattern in a string.

        Substrait: regexp_strpos
        """
        ...

    def regexp_count_substring(
        self,
        pattern: Union[BaseExpressionAPI, ExpressionNode, Any],
        position: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None,
        *,
        case_sensitive: bool = True,
        multiline: bool = None,
        dotall: bool = None,
    ) -> BaseExpressionAPI:
        """"Return the number of non-overlapping occurrences of a regular expression pattern in an input string
        Substrait: regexp_count_substring
        """
        ...



    def regexp_replace(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        replacement: Union[BaseExpressionAPI, "ExpressionNode", Any],
        position: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any, int]] = None,
        occurrence: Optional[Union[BaseExpressionAPI, "ExpressionNode", Any, int]] = None,
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Replace occurrences matching regex pattern.

        Substrait: regexp_replace

        Args:
            pattern: Regular expression pattern.
            replacement: Replacement string.
            position: Start position for search (1-indexed).
            occurrence: Which occurrence to replace (0 = all).
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with regexp_replace node.
        """
        pattern_node = self._to_substrait_node(pattern)
        replacement_node = self._to_substrait_node(replacement)
        args = [self._node, pattern_node, replacement_node]

        if position is not None:
            args.append(self._to_substrait_node(position))
        if occurrence is not None:
            args.append(self._to_substrait_node(occurrence))

        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            arguments=args,
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)


    # ========================================
    # Pattern Matching Aliases (User-Friendly)
    # ========================================

    def regex_replace(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        replacement: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Replace all occurrences matching regex pattern.

        Alias for regexp_replace() with simpler interface.

        Args:
            pattern: Regular expression pattern.
            replacement: Replacement string.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with replaced string.
        """
        return self.regexp_replace(pattern, replacement, case_sensitive=case_sensitive)


    def string_split(
        self,
        separator: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Split string by separator.

        Substrait: string_split

        Args:
            separator: Separator string.

        Returns:
            New ExpressionAPI with string_split node.
        """
        separator_node = self._to_substrait_node(separator)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STRING_SPLIT,
            arguments=[self._node, separator_node],
        )
        return self._build(node)

    def regexp_string_split(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Split string by regex pattern.

        Substrait: regexp_string_split

        Args:
            pattern: Regular expression pattern for separator.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with regexp_string_split node.
        """
        pattern_node = self._to_substrait_node(pattern)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRING_SPLIT,
            arguments=[self._node, pattern_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)




    def length(self) -> BaseExpressionAPI:
        """
        Return number of characters.

        Alias for char_length() for convenience.

        Returns:
            New ExpressionAPI with char_length node.
        """
        return self.char_length()



    def regex_match(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Check if entire string matches regex pattern.

        This anchors the pattern with ^ and $ to match the full string.
        For partial matching, use regex_contains().

        Args:
            pattern: Regular expression pattern.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with boolean result.
        """
        # Anchor pattern to match entire string
        if isinstance(pattern, str):
            anchored_pattern = f"^{pattern}$"
        else:
            # If pattern is an expression, we can't easily anchor it
            # Fall back to using the pattern as-is
            anchored_pattern = pattern

        return self.regex_contains(anchored_pattern, case_sensitive=case_sensitive)

    def regex_contains(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """
        Check if string contains a match for regex pattern.

        Args:
            pattern: Regular expression pattern.
            case_sensitive: Case sensitivity (default: True).

        Returns:
            New ExpressionAPI with boolean result.
        """
        # Use contains with regex pattern - backends interpret patterns as regex
        return self.contains(pattern, case_sensitive=case_sensitive)
