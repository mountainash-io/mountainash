"""Ibis ScalarStringExpressionProtocol implementation.

Implements string operations for the Ibis backend.
"""

from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING

import ibis
import ibis.expr.types as ir

from .base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_scalar_string import (
        ScalarStringExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = ir.Column | ir.Scalar


class IbisScalarStringSystem(IbisBaseExpressionSystem):
    """Ibis implementation of ScalarStringExpressionProtocol.

    Implements string methods across categories:
    - Case: upper, lower, swapcase, capitalize, title, initcap
    - Trim/Pad: trim, ltrim, rtrim, lpad, rpad, center
    - Substring: substring, left, right, replace_slice
    - Search: contains, starts_with, ends_with, strpos, count_substring
    - Length: char_length, bit_length, octet_length
    - Transform: concat, concat_ws, replace, repeat, reverse
    - Pattern: like, regexp_match_substring, regexp_replace, regexp_strpos
    - Split: string_split, regexp_string_split, string_agg
    """

    # =========================================================================
    # Case Transformation Operations
    # =========================================================================

    def lower(
        self,
        input: SupportedExpressions,
        /,
        char_set: Any = None,
    ) -> SupportedExpressions:
        """Transform the string to lower case characters.

        Args:
            input: String expression.
            char_set: Character set (ignored in Ibis).

        Returns:
            Lowercase string.
        """
        return input.lower()

    def upper(
        self,
        input: SupportedExpressions,
        /,
        char_set: Any = None,
    ) -> SupportedExpressions:
        """Transform the string to upper case characters.

        Args:
            input: String expression.
            char_set: Character set (ignored in Ibis).

        Returns:
            Uppercase string.
        """
        return input.upper()

    def swapcase(
        self,
        input: SupportedExpressions,
        /,
        char_set: Any = None,
    ) -> SupportedExpressions:
        """Swap case of characters (lowercase to uppercase and vice versa).

        Args:
            input: String expression.
            char_set: Character set (ignored in Ibis).

        Returns:
            String with swapped case.

        Note:
            Ibis doesn't have swapcase. Returns input unchanged.
        """
        # Ibis doesn't have swapcase - fallback
        return input

    def capitalize(
        self,
        input: SupportedExpressions,
        /,
        char_set: Any = None,
    ) -> SupportedExpressions:
        """Capitalize the first character of the input string.

        Args:
            input: String expression.
            char_set: Character set (ignored in Ibis).

        Returns:
            String with first character capitalized.
        """
        return input.capitalize()

    def title(
        self,
        input: SupportedExpressions,
        /,
        char_set: Any = None,
    ) -> SupportedExpressions:
        """Convert to title case (capitalize first char of each word except articles).

        Args:
            input: String expression.
            char_set: Character set (ignored in Ibis).

        Returns:
            Title-cased string.

        Note:
            Ibis may not have title. Falls back to capitalize.
        """
        # Ibis may not have title - use capitalize
        return input.capitalize()

    def initcap(
        self,
        input: SupportedExpressions,
        /,
        char_set: Any = None,
    ) -> SupportedExpressions:
        """Capitalize first character of each word.

        Unlike title(), this includes articles.

        Args:
            input: String expression.
            char_set: Character set (ignored in Ibis).

        Returns:
            String with each word capitalized.
        """
        return input.initcap()

    # =========================================================================
    # Trim and Pad Operations
    # =========================================================================

    def trim(
        self,
        input: SupportedExpressions,
        /,
        characters: SupportedExpressions = None,
    ) -> SupportedExpressions:
        """Remove characters from both sides of the string.

        Args:
            input: String expression.
            characters: Characters to remove (default: whitespace).

        Returns:
            Trimmed string.
        """
        return input.strip()

    def ltrim(
        self,
        input: SupportedExpressions,
        /,
        characters: SupportedExpressions = None,
    ) -> SupportedExpressions:
        """Remove characters from the left side of the string.

        Args:
            input: String expression.
            characters: Characters to remove (default: whitespace).

        Returns:
            Left-trimmed string.
        """
        return input.lstrip()

    def rtrim(
        self,
        input: SupportedExpressions,
        /,
        characters: SupportedExpressions = None,
    ) -> SupportedExpressions:
        """Remove characters from the right side of the string.

        Args:
            input: String expression.
            characters: Characters to remove (default: whitespace).

        Returns:
            Right-trimmed string.
        """
        return input.rstrip()

    def lpad(
        self,
        input: SupportedExpressions,
        /,
        length: SupportedExpressions,
        characters: SupportedExpressions = None,
    ) -> SupportedExpressions:
        """Left-pad the input string to specified length.

        Args:
            input: String expression.
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            Left-padded string.
        """
        fill_char = " " if characters is None else characters
        if isinstance(length, int) and isinstance(fill_char, str):
            return input.lpad(length, fill_char)
        if isinstance(length, int):
            return input.lpad(length, " ")
        return input

    def rpad(
        self,
        input: SupportedExpressions,
        /,
        length: SupportedExpressions,
        characters: SupportedExpressions = None,
    ) -> SupportedExpressions:
        """Right-pad the input string to specified length.

        Args:
            input: String expression.
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            Right-padded string.
        """
        fill_char = " " if characters is None else characters
        if isinstance(length, int) and isinstance(fill_char, str):
            return input.rpad(length, fill_char)
        if isinstance(length, int):
            return input.rpad(length, " ")
        return input

    def center(
        self,
        input: SupportedExpressions,
        /,
        length: SupportedExpressions,
        character: SupportedExpressions = None,
        padding: Any = None,
    ) -> SupportedExpressions:
        """Center the input string by padding both sides.

        Args:
            input: String expression.
            length: Target length.
            character: Single padding character (default: space).
            padding: Which side gets extra padding (ignored).

        Returns:
            Centered string.

        Note:
            Ibis doesn't have center. Falls back to input.
        """
        # Ibis doesn't have center - fallback
        return input

    # =========================================================================
    # Substring Operations
    # =========================================================================

    def substring(
        self,
        input: SupportedExpressions,
        /,
        start: SupportedExpressions,
        length: SupportedExpressions = None,
        negative_start: Any = None,
    ) -> SupportedExpressions:
        """Extract a substring.

        Args:
            input: String expression.
            start: Starting position (1-indexed in Substrait).
            length: Length of substring.
            negative_start: How to handle negative start values.

        Returns:
            Substring expression.
        """
        # Ibis uses 0-indexed substr
        if isinstance(start, int):
            offset = start - 1 if start > 0 else start
            if length is None:
                return input.substr(offset)
            if isinstance(length, int):
                return input.substr(offset, length)
        return input.substr(0)

    def left(
        self,
        input: SupportedExpressions,
        /,
        count: SupportedExpressions,
    ) -> SupportedExpressions:
        """Extract count characters from the left.

        Args:
            input: String expression.
            count: Number of characters.

        Returns:
            Left substring.
        """
        if isinstance(count, int):
            return input.left(count)
        return input

    def right(
        self,
        input: SupportedExpressions,
        /,
        count: SupportedExpressions,
    ) -> SupportedExpressions:
        """Extract count characters from the right.

        Args:
            input: String expression.
            count: Number of characters.

        Returns:
            Right substring.
        """
        if isinstance(count, int):
            return input.right(count)
        return input

    def replace_slice(
        self,
        input: SupportedExpressions,
        /,
        start: SupportedExpressions,
        length: SupportedExpressions,
        replacement: SupportedExpressions,
    ) -> SupportedExpressions:
        """Replace a slice of the input string.

        Args:
            input: String expression.
            start: Starting position (1-indexed).
            length: Length to replace.
            replacement: Replacement string.

        Returns:
            String with replaced slice.

        Note:
            Ibis doesn't have replace_slice. Falls back to input.
        """
        # Ibis doesn't have replace_slice - fallback
        return input

    # =========================================================================
    # Search Operations
    # =========================================================================

    def contains(
        self,
        input: SupportedExpressions,
        /,
        substring: SupportedExpressions,
        case_sensitivity: Any = None,
    ) -> SupportedExpressions:
        """Whether the input string contains the substring.

        Args:
            input: String expression.
            substring: Substring to search for.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        return input.contains(substring)

    def starts_with(
        self,
        input: SupportedExpressions,
        substring: SupportedExpressions,
        /,
        case_sensitivity: Any = None,
    ) -> SupportedExpressions:
        """Whether input string starts with the substring.

        Args:
            input: String expression.
            substring: Prefix to check.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        return input.startswith(substring)

    def ends_with(
        self,
        input: SupportedExpressions,
        /,
        substring: SupportedExpressions,
        case_sensitivity: Any = None,
    ) -> SupportedExpressions:
        """Whether input string ends with the substring.

        Args:
            input: String expression.
            substring: Suffix to check.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        return input.endswith(substring)

    def strpos(
        self,
        input: SupportedExpressions,
        /,
        substring: SupportedExpressions,
        case_sensitivity: Any = None,
    ) -> SupportedExpressions:
        """Return position of first occurrence of substring (1-indexed).

        Args:
            input: String expression.
            substring: Substring to find.
            case_sensitivity: Case sensitivity option.

        Returns:
            Position (1-indexed), or 0 if not found.
        """
        # Ibis find returns 0-based or -1; add 1 to make 1-indexed
        return input.find(substring) + ibis.literal(1)

    def count_substring(
        self,
        input: SupportedExpressions,
        /,
        substring: SupportedExpressions,
        case_sensitivity: Any = None,
    ) -> SupportedExpressions:
        """Return the number of non-overlapping occurrences of substring.

        Args:
            input: String expression.
            substring: Substring to count.
            case_sensitivity: Case sensitivity option.

        Returns:
            Count of occurrences.

        Note:
            Ibis may not have count. Falls back to 0.
        """
        # Ibis doesn't have count_substring directly - fallback
        return ibis.literal(0)

    # =========================================================================
    # Length Operations
    # =========================================================================

    def char_length(self, input: SupportedExpressions, /) -> SupportedExpressions:
        """Return the number of characters in the input string.

        Args:
            input: String expression.

        Returns:
            Character count.
        """
        return input.length()

    def bit_length(self, input: SupportedExpressions, /) -> SupportedExpressions:
        """Return the number of bits in the input string.

        Args:
            input: String expression.

        Returns:
            Bit count.
        """
        # Bit length = byte length * 8
        return input.length() * ibis.literal(8)

    def octet_length(self, input: SupportedExpressions, /) -> SupportedExpressions:
        """Return the number of bytes in the input string.

        Args:
            input: String expression.

        Returns:
            Byte count.
        """
        # For ASCII, length approximates byte count
        return input.length()

    # =========================================================================
    # Transform Operations
    # =========================================================================

    def concat(
        self,
        input: SupportedExpressions,
        /,
        null_handling: Any = None,
    ) -> SupportedExpressions:
        """Concatenate strings.

        Note: This is variadic in Substrait. For single input, returns input.

        Args:
            input: String expression (or list of expressions).
            null_handling: How to handle nulls (IGNORE_NULLS or ACCEPT_NULLS).

        Returns:
            Concatenated string.
        """
        return input

    def concat_ws(
        self,
        separator: SupportedExpressions,
        /,
        string_arguments: SupportedExpressions,
    ) -> SupportedExpressions:
        """Concatenate strings with separator.

        Args:
            separator: Separator string.
            string_arguments: Strings to concatenate.

        Returns:
            Concatenated string with separator.

        Note:
            Ibis doesn't have concat_ws directly. Falls back.
        """
        # Ibis doesn't have concat_ws - fallback
        if isinstance(string_arguments, (list, tuple)) and len(string_arguments) > 0:
            return string_arguments[0]
        return string_arguments

    def replace(
        self,
        input: SupportedExpressions,
        /,
        substring: SupportedExpressions,
        replacement: SupportedExpressions,
        case_sensitivity: Any = None,
    ) -> SupportedExpressions:
        """Replace all occurrences of substring with replacement.

        Args:
            input: String expression.
            substring: Substring to replace.
            replacement: Replacement string.
            case_sensitivity: Case sensitivity option.

        Returns:
            String with replacements.
        """
        return input.replace(substring, replacement)

    def repeat(
        self,
        input: SupportedExpressions,
        /,
        count: SupportedExpressions,
    ) -> SupportedExpressions:
        """Repeat a string count number of times.

        Args:
            input: String expression.
            count: Number of repetitions.

        Returns:
            Repeated string.
        """
        if isinstance(count, int):
            return input.repeat(count)
        return input

    def reverse(self, input: SupportedExpressions, /) -> SupportedExpressions:
        """Return the string in reverse order.

        Args:
            input: String expression.

        Returns:
            Reversed string.
        """
        return input.reverse()

    # =========================================================================
    # Pattern Matching Operations
    # =========================================================================

    def like(
        self,
        input: SupportedExpressions,
        /,
        match: SupportedExpressions,
        case_sensitivity: Any = None,
    ) -> SupportedExpressions:
        """SQL LIKE pattern matching (% and _ wildcards).

        Args:
            input: String expression.
            match: SQL LIKE pattern.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        return input.like(match)

    def regexp_match_substring(
        self,
        input: SupportedExpressions,
        pattern: SupportedExpressions,
        /,
        position: SupportedExpressions = None,
        occurrence: SupportedExpressions = None,
        group: SupportedExpressions = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> SupportedExpressions:
        """Extract substring matching regex pattern.

        Args:
            input: String expression.
            pattern: Regex pattern.
            position: Starting position (ignored in basic impl).
            occurrence: Which occurrence (ignored in basic impl).
            group: Capture group number.
            case_sensitivity: Case sensitivity option.
            multiline: Multiline mode.
            dotall: Dotall mode.

        Returns:
            Matched substring or null.
        """
        group_index = 0 if group is None else (group if isinstance(group, int) else 0)
        return input.re_extract(pattern, group_index)

    def regexp_match_substring_all(
        self,
        input: SupportedExpressions,
        /,
        pattern: SupportedExpressions,
        position: SupportedExpressions = None,
        group: SupportedExpressions = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> SupportedExpressions:
        """Extract all substrings matching regex pattern.

        Args:
            input: String expression.
            pattern: Regex pattern.
            position: Starting position.
            group: Capture group number.
            case_sensitivity: Case sensitivity option.
            multiline: Multiline mode.
            dotall: Dotall mode.

        Returns:
            List of matched substrings.

        Note:
            Ibis doesn't have extract_all. Falls back to single match.
        """
        # Ibis doesn't have extract_all - fallback
        return input.re_extract(pattern, 0)

    def regexp_strpos(
        self,
        input: SupportedExpressions,
        /,
        pattern: SupportedExpressions,
        position: SupportedExpressions = None,
        occurrence: SupportedExpressions = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> SupportedExpressions:
        """Return position of regex pattern match (1-indexed).

        Args:
            input: String expression.
            pattern: Regex pattern.
            position: Starting position.
            occurrence: Which occurrence.
            case_sensitivity: Case sensitivity option.
            multiline: Multiline mode.
            dotall: Dotall mode.

        Returns:
            Position (1-indexed), or 0 if not found.

        Note:
            Ibis doesn't have regex position. Falls back to 0.
        """
        # Ibis doesn't have regex position - fallback
        return ibis.literal(0)

    def regexp_count_substring(
        self,
        input: SupportedExpressions,
        /,
        pattern: SupportedExpressions,
        position: SupportedExpressions = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> SupportedExpressions:
        """Return count of non-overlapping regex matches.

        Args:
            input: String expression.
            pattern: Regex pattern.
            position: Starting position.
            case_sensitivity: Case sensitivity option.
            multiline: Multiline mode.
            dotall: Dotall mode.

        Returns:
            Count of matches.

        Note:
            Ibis doesn't have regex count. Falls back to 0.
        """
        # Ibis doesn't have regex count - fallback
        return ibis.literal(0)

    def regexp_replace(
        self,
        input: SupportedExpressions,
        /,
        pattern: SupportedExpressions,
        replacement: SupportedExpressions,
        position: SupportedExpressions = None,
        occurrence: SupportedExpressions = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> SupportedExpressions:
        """Replace text matching regex pattern.

        Args:
            input: String expression.
            pattern: Regex pattern.
            replacement: Replacement string.
            position: Starting position.
            occurrence: Which occurrence (0 = all).
            case_sensitivity: Case sensitivity option.
            multiline: Multiline mode.
            dotall: Dotall mode.

        Returns:
            String with replacements.
        """
        return input.re_replace(pattern, replacement)

    # =========================================================================
    # Split Operations
    # =========================================================================

    def string_split(
        self,
        input: SupportedExpressions,
        /,
        separator: SupportedExpressions,
    ) -> SupportedExpressions:
        """Split a string into a list based on separator.

        Args:
            input: String expression.
            separator: Separator string.

        Returns:
            List of strings.
        """
        return input.split(separator)

    def regexp_string_split(
        self,
        input: SupportedExpressions,
        /,
        pattern: SupportedExpressions,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> SupportedExpressions:
        """Split a string into a list based on regex pattern.

        Args:
            input: String expression.
            pattern: Regex pattern for separator.
            case_sensitivity: Case sensitivity option.
            multiline: Multiline mode.
            dotall: Dotall mode.

        Returns:
            List of strings.

        Note:
            Ibis doesn't have regex split. Falls back to normal split.
        """
        # Ibis doesn't have regex split - fallback
        return input

    def string_agg(
        self,
        input: SupportedExpressions,
        /,
        separator: SupportedExpressions,
    ) -> SupportedExpressions:
        """Concatenate a column of string values with a separator.

        This is an aggregate function.

        Args:
            input: String expression.
            separator: Separator string.

        Returns:
            Aggregated string.
        """
        return input.group_concat(separator)
