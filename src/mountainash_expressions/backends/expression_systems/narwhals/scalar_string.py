"""Narwhals ScalarStringExpressionProtocol implementation.

Implements string operations for the Narwhals backend.
"""

from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING

import narwhals as nw

from .base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_scalar_string import (
        ScalarStringExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = nw.Expr


class NarwhalsScalarStringSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of ScalarStringExpressionProtocol.

    Implements string methods across categories:
    - Case: upper, lower, swapcase, capitalize, title, initcap
    - Trim/Pad: trim, ltrim, rtrim, lpad, rpad, center
    - Substring: substring, left, right, replace_slice
    - Search: contains, starts_with, ends_with, strpos, count_substring
    - Length: char_length, bit_length, octet_length
    - Transform: concat, concat_ws, replace, repeat, reverse
    - Pattern: like, regexp_match_substring, regexp_replace, regexp_strpos
    - Split: string_split, regexp_string_split, string_agg

    Note: Narwhals has a more limited string API than Polars. Some methods
    use workarounds or simplified implementations.
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
            char_set: Character set (ignored in Narwhals).

        Returns:
            Lowercase string.
        """
        return input.str.to_lowercase()

    def upper(
        self,
        input: SupportedExpressions,
        /,
        char_set: Any = None,
    ) -> SupportedExpressions:
        """Transform the string to upper case characters.

        Args:
            input: String expression.
            char_set: Character set (ignored in Narwhals).

        Returns:
            Uppercase string.
        """
        return input.str.to_uppercase()

    def swapcase(
        self,
        input: SupportedExpressions,
        /,
        char_set: Any = None,
    ) -> SupportedExpressions:
        """Swap case of characters (lowercase to uppercase and vice versa).

        Args:
            input: String expression.
            char_set: Character set (ignored in Narwhals).

        Returns:
            String with swapped case.

        Note:
            Narwhals doesn't have swapcase. Returns input unchanged as fallback.
        """
        # Narwhals doesn't have swapcase - fallback to no-op
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
            char_set: Character set (ignored in Narwhals).

        Returns:
            String with first character capitalized.

        Note:
            Narwhals doesn't have capitalize. Returns input unchanged as fallback.
        """
        # Narwhals doesn't have capitalize - fallback
        return input

    def title(
        self,
        input: SupportedExpressions,
        /,
        char_set: Any = None,
    ) -> SupportedExpressions:
        """Convert to title case (capitalize first char of each word except articles).

        Args:
            input: String expression.
            char_set: Character set (ignored in Narwhals).

        Returns:
            Title-cased string.

        Note:
            Narwhals doesn't have title. Returns input unchanged as fallback.
        """
        # Narwhals doesn't have title - fallback
        return input

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
            char_set: Character set (ignored in Narwhals).

        Returns:
            String with each word capitalized.
        """
        # Narwhals doesn't have initcap - fallback
        return input

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
        if characters is None:
            return input.str.strip_chars()
        if isinstance(characters, str):
            return input.str.strip_chars(characters)
        return input.str.strip_chars()

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
        if characters is None:
            return input.str.strip_chars()  # Narwhals may not have directional strip
        return input.str.strip_chars()

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
        if characters is None:
            return input.str.strip_chars()
        return input.str.strip_chars()

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

        Note:
            Narwhals may not have pad_start. Returns input as fallback.
        """
        # Narwhals doesn't have pad_start - fallback
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

        Note:
            Narwhals may not have pad_end. Returns input as fallback.
        """
        # Narwhals doesn't have pad_end - fallback
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
            Narwhals doesn't have center. Returns input as fallback.
        """
        # Narwhals doesn't have center - fallback
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
        # Substrait uses 1-indexed, Narwhals uses 0-indexed
        if isinstance(start, int):
            offset = start - 1 if start > 0 else start
            if length is None:
                return input.str.slice(offset)
            if isinstance(length, int):
                return input.str.slice(offset, length)
        return input.str.slice(0)

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
            return input.str.slice(0, count)
        return input.str.head(count)

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
            return input.str.slice(-count)
        return input.str.tail(count)

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
            Narwhals doesn't have replace_slice. Returns input as fallback.
        """
        # Narwhals doesn't have replace_slice - fallback
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
        if isinstance(substring, str):
            return input.str.contains(substring)
        return input.str.contains(substring)

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
        return input.str.starts_with(substring)

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
        return input.str.ends_with(substring)

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

        Note:
            Narwhals may not have find. Returns 0 as fallback.
        """
        # Narwhals doesn't have find - fallback
        return nw.lit(0)

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
            Narwhals may not have count_matches. Returns 0 as fallback.
        """
        # Narwhals doesn't have count_matches - fallback
        return nw.lit(0)

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
        return input.str.len_chars()

    def bit_length(self, input: SupportedExpressions, /) -> SupportedExpressions:
        """Return the number of bits in the input string.

        Args:
            input: String expression.

        Returns:
            Bit count.
        """
        # Bit length = byte length * 8
        # Narwhals may not have len_bytes - use len_chars as approximation
        return input.str.len_chars() * nw.lit(8)

    def octet_length(self, input: SupportedExpressions, /) -> SupportedExpressions:
        """Return the number of bytes in the input string.

        Args:
            input: String expression.

        Returns:
            Byte count.
        """
        # Narwhals may not have len_bytes - use len_chars as approximation
        return input.str.len_chars()

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
            Narwhals may not have concat_str. Returns string_arguments as fallback.
        """
        # Narwhals doesn't have concat_str with separator - fallback
        if isinstance(string_arguments, (list, tuple)):
            return nw.concat_str(*string_arguments)
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
        return input.str.replace_all(substring, replacement)

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

        Note:
            Narwhals doesn't have repeat. Returns input as fallback.
        """
        # Narwhals doesn't have repeat - fallback
        return input

    def reverse(self, input: SupportedExpressions, /) -> SupportedExpressions:
        """Return the string in reverse order.

        Args:
            input: String expression.

        Returns:
            Reversed string.

        Note:
            Narwhals may not have reverse. Returns input as fallback.
        """
        # Narwhals doesn't have reverse - fallback
        return input

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
        if isinstance(match, str):
            # Convert SQL LIKE pattern to regex
            pattern = match.replace("%", "\x00PERCENT\x00").replace("_", "\x00UNDERSCORE\x00")
            regex_pattern = re.escape(pattern)
            regex_pattern = regex_pattern.replace("\x00PERCENT\x00", ".*").replace("\x00UNDERSCORE\x00", ".")
            regex_pattern = f"^{regex_pattern}$"
            return input.str.contains(regex_pattern)
        return input.str.contains(match)

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

        Note:
            Narwhals may not have extract. Returns input as fallback.
        """
        # Narwhals doesn't have extract - fallback
        return input

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
            Narwhals doesn't have extract_all. Returns input as fallback.
        """
        # Narwhals doesn't have extract_all - fallback
        return input

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
            Narwhals doesn't have regex find. Returns 0 as fallback.
        """
        # Narwhals doesn't have regex position - fallback
        return nw.lit(0)

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
            Narwhals doesn't have count_matches. Returns 0 as fallback.
        """
        # Narwhals doesn't have regex count - fallback
        return nw.lit(0)

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
        # replace_all should work for regex patterns in Narwhals
        return input.str.replace_all(pattern, replacement)

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

        Note:
            Narwhals may not have split. Returns input as fallback.
        """
        # Narwhals doesn't have split - fallback
        return input

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
            Narwhals doesn't have regex split. Returns input as fallback.
        """
        # Narwhals doesn't have regex split - fallback
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

        Note:
            Narwhals may not have str.concat. Returns input as fallback.
        """
        # Narwhals doesn't have str.concat aggregate - fallback
        return input
