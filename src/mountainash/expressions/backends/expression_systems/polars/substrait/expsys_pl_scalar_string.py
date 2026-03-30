"""Polars ScalarStringExpressionProtocol implementation.

Implements string operations for the Polars backend.
"""

from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsScalarStringExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol["pl.Expr"]):
    """Polars implementation of ScalarStringExpressionProtocol.

    Implements 37 string methods across categories:
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
        input: PolarsExpr,
        /,
        char_set: Any = None,
    ) -> PolarsExpr:
        """Transform the string to lower case characters.

        Args:
            input: String expression.
            char_set: Character set (ignored in Polars).

        Returns:
            Lowercase string.
        """
        return input.str.to_lowercase()

    def upper(
        self,
        input: PolarsExpr,
        /,
        char_set: Any = None,
    ) -> PolarsExpr:
        """Transform the string to upper case characters.

        Args:
            input: String expression.
            char_set: Character set (ignored in Polars).

        Returns:
            Uppercase string.
        """
        return input.str.to_uppercase()

    def swapcase(
        self,
        input: PolarsExpr,
        /,
        char_set: Any = None,
    ) -> PolarsExpr:
        """Swap case of characters (lowercase to uppercase and vice versa).

        Args:
            input: String expression.
            char_set: Character set (ignored in Polars).

        Returns:
            String with swapped case.

        Note:
            Polars doesn't have native swapcase. We implement using
            character-by-character transformation via map.
        """
        # Polars doesn't have swapcase, use a workaround
        # This is a simplification - full implementation would need UDF
        return input.map_elements(
            lambda s: s.swapcase() if s is not None else None,
            return_dtype=pl.String,
        )

    def capitalize(
        self,
        input: PolarsExpr,
        /,
        char_set: Any = None,
    ) -> PolarsExpr:
        """Capitalize the first character of the input string.

        Args:
            input: String expression.
            char_set: Character set (ignored in Polars).

        Returns:
            String with first character capitalized.

        Note:
            Polars doesn't have native capitalize. We use map_elements.
        """
        return input.map_elements(
            lambda s: s.capitalize() if s is not None else None,
            return_dtype=pl.String,
        )

    def title(
        self,
        input: PolarsExpr,
        /,
        char_set: Any = None,
    ) -> PolarsExpr:
        """Convert to title case (capitalize first char of each word except articles).

        Args:
            input: String expression.
            char_set: Character set (ignored in Polars).

        Returns:
            Title-cased string.

        Note:
            Polars has str.to_titlecase() which capitalizes all words.
            Substrait's title() excludes articles - this is a simplification.
        """
        return input.str.to_titlecase()

    def initcap(
        self,
        input: PolarsExpr,
        /,
        char_set: Any = None,
    ) -> PolarsExpr:
        """Capitalize first character of each word.

        Unlike title(), this includes articles.

        Args:
            input: String expression.
            char_set: Character set (ignored in Polars).

        Returns:
            String with each word capitalized.
        """
        return input.str.to_titlecase()

    # =========================================================================
    # Trim and Pad Operations
    # =========================================================================

    def trim(
        self,
        input: PolarsExpr,
        /,
        characters: PolarsExpr = None,
    ) -> PolarsExpr:
        """Remove characters from both sides of the string.

        Args:
            input: String expression.
            characters: Characters to remove (default: whitespace).

        Returns:
            Trimmed string.
        """
        if characters is None:
            return input.str.strip_chars()
        chars_val = self._extract_literal_value(characters)
        return input.str.strip_chars(chars_val)

    def ltrim(
        self,
        input: PolarsExpr,
        /,
        characters: PolarsExpr = None,
    ) -> PolarsExpr:
        """Remove characters from the left side of the string.

        Args:
            input: String expression.
            characters: Characters to remove (default: whitespace).

        Returns:
            Left-trimmed string.
        """
        if characters is None:
            return input.str.strip_chars_start()
        chars_val = self._extract_literal_value(characters)
        return input.str.strip_chars_start(chars_val)

    def rtrim(
        self,
        input: PolarsExpr,
        /,
        characters: PolarsExpr = None,
    ) -> PolarsExpr:
        """Remove characters from the right side of the string.

        Args:
            input: String expression.
            characters: Characters to remove (default: whitespace).

        Returns:
            Right-trimmed string.
        """
        if characters is None:
            return input.str.strip_chars_end()
        chars_val = self._extract_literal_value(characters)
        return input.str.strip_chars_end(chars_val)

    def lpad(
        self,
        input: PolarsExpr,
        /,
        length: PolarsExpr,
        characters: PolarsExpr = None,
    ) -> PolarsExpr:
        """Left-pad the input string to specified length.

        Args:
            input: String expression.
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            Left-padded string.
        """
        length_val = self._extract_literal_value(length)
        fill_char = " " if characters is None else self._extract_literal_value(characters)
        return input.str.pad_start(length_val, fill_char)

    def rpad(
        self,
        input: PolarsExpr,
        /,
        length: PolarsExpr,
        characters: PolarsExpr = None,
    ) -> PolarsExpr:
        """Right-pad the input string to specified length.

        Args:
            input: String expression.
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            Right-padded string.
        """
        length_val = self._extract_literal_value(length)
        fill_char = " " if characters is None else self._extract_literal_value(characters)
        return input.str.pad_end(length_val, fill_char)

    def center(
        self,
        input: PolarsExpr,
        /,
        length: PolarsExpr,
        character: PolarsExpr = None,
        padding: Any = None,
    ) -> PolarsExpr:
        """Center the input string by padding both sides.

        Args:
            input: String expression.
            length: Target length.
            character: Single padding character (default: space).
            padding: Which side gets extra padding (ignored).

        Returns:
            Centered string.
        """
        fill_char_val = " " if character is None else self._extract_literal_value(character)
        length_val = self._extract_literal_value(length)
        target_len = int(length_val)
        char = str(fill_char_val) if not isinstance(fill_char_val, str) else fill_char_val
        return input.map_elements(
            lambda s: s.center(target_len, char) if s is not None else None,
            return_dtype=pl.String,
        )

    # =========================================================================
    # Substring Operations
    # =========================================================================

    def substring(
        self,
        input: PolarsExpr,
        /,
        start: PolarsExpr,
        length: PolarsExpr = None,
        negative_start: Any = None,
    ) -> PolarsExpr:
        """Extract a substring.

        Args:
            input: String expression.
            start: Starting position (0-indexed for API consistency).
            length: Length of substring.
            negative_start: How to handle negative start values.

        Returns:
            Substring expression.
        """
        # Extract literal values where possible; Polars str.slice accepts expressions
        start_val = self._extract_literal_value(start)
        length_val = self._extract_literal_value(length) if length is not None else None

        if length_val is None:
            return input.str.slice(start_val)
        return input.str.slice(start_val, length_val)

    def left(
        self,
        input: PolarsExpr,
        /,
        count: PolarsExpr,
    ) -> PolarsExpr:
        """Extract count characters from the left."""
        count_val = self._extract_literal_value(count)
        return input.str.slice(0, count_val)

    def right(
        self,
        input: PolarsExpr,
        /,
        count: PolarsExpr,
    ) -> PolarsExpr:
        """Extract count characters from the right."""
        count_val = self._extract_literal_value(count)
        return input.str.slice(-count_val)

    def replace_slice(
        self,
        input: PolarsExpr,
        /,
        start: PolarsExpr,
        length: PolarsExpr,
        replacement: PolarsExpr,
    ) -> PolarsExpr:
        """Replace a slice of the input string.

        Args:
            input: String expression.
            start: Starting position (1-indexed).
            length: Length to replace.
            replacement: Replacement string.

        Returns:
            String with replaced slice.
        """
        start_val = self._extract_literal_value(start)
        length_val = self._extract_literal_value(length)
        replacement_val = self._extract_literal_value(replacement)
        offset = int(start_val) - 1 if int(start_val) > 0 else 0
        repl = str(replacement_val)
        len_val = int(length_val)
        return input.map_elements(
            lambda s: (s[:offset] + repl + s[offset + len_val :]) if s is not None else None,
            return_dtype=pl.String,
        )

    # =========================================================================
    # Search Operations
    # =========================================================================

    def contains(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Whether the input string contains the substring.

        Args:
            input: String expression.
            substring: Substring to search for (can be literal or regex pattern).
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        # Extract literal value from Expr if needed
        pattern = self._extract_literal_value(substring)

        regex_chars = r".*+?^${}[]|()\\"
        is_regex = any(c in str(pattern) for c in regex_chars)
        return input.str.contains(str(pattern), literal=not is_regex)

    def starts_with(
        self,
        input: PolarsExpr,
        substring: PolarsExpr,
        /,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
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
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
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
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Return position of first occurrence of substring (1-indexed).

        Args:
            input: String expression.
            substring: Substring to find.
            case_sensitivity: Case sensitivity option.

        Returns:
            Position (1-indexed), or 0 if not found.
        """
        # Polars find returns 0-indexed position, -1 if not found
        # Substrait expects 1-indexed, 0 if not found
        sub_val = self._extract_literal_value(substring)
        return (input.str.find(sub_val, literal=True) + 1).fill_null(0)

    def count_substring(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Return the number of non-overlapping occurrences of substring.

        Args:
            input: String expression.
            substring: Substring to count.
            case_sensitivity: Case sensitivity option.

        Returns:
            Count of occurrences.
        """
        sub_val = self._extract_literal_value(substring)
        return input.str.count_matches(sub_val, literal=True)

    # =========================================================================
    # Length Operations
    # =========================================================================

    def char_length(self, input: PolarsExpr, /) -> PolarsExpr:
        """Return the number of characters in the input string.

        Args:
            input: String expression.

        Returns:
            Character count.
        """
        return input.str.len_chars()

    def bit_length(self, input: PolarsExpr, /) -> PolarsExpr:
        """Return the number of bits in the input string.

        Args:
            input: String expression.

        Returns:
            Bit count.
        """
        # Bit length = byte length * 8
        return input.str.len_bytes() * 8

    def octet_length(self, input: PolarsExpr, /) -> PolarsExpr:
        """Return the number of bytes in the input string.

        Args:
            input: String expression.

        Returns:
            Byte count.
        """
        return input.str.len_bytes()

    # =========================================================================
    # Transform Operations
    # =========================================================================

    def concat(
        self,
        input: PolarsExpr,
        /,
        null_handling: Any = None,
    ) -> PolarsExpr:
        """Concatenate strings.

        Note: This is variadic in Substrait. For single input, returns input.
        Use + operator for multi-string concat in Polars.

        Args:
            input: String expression (or list of expressions).
            null_handling: How to handle nulls (IGNORE_NULLS or ACCEPT_NULLS).

        Returns:
            Concatenated string.
        """
        # Single input case - return as-is
        return input

    def concat_ws(
        self,
        separator: PolarsExpr,
        /,
        string_arguments: PolarsExpr,
    ) -> PolarsExpr:
        """Concatenate strings with separator.

        Args:
            separator: Separator string.
            string_arguments: Strings to concatenate.

        Returns:
            Concatenated string with separator.
        """
        # Polars concat_str handles this
        if isinstance(string_arguments, (list, tuple)):
            return pl.concat_str(*string_arguments, separator=separator)
        return string_arguments

    def replace(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        replacement: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Replace all occurrences of substring with replacement.

        Args:
            input: String expression.
            substring: Substring to replace.
            replacement: Replacement string.
            case_sensitivity: Case sensitivity option.

        Returns:
            String with replacements.
        """
        return input.str.replace_all(substring, replacement, literal=True)

    def repeat(
        self,
        input: PolarsExpr,
        /,
        count: PolarsExpr,
    ) -> PolarsExpr:
        """Repeat a string count number of times.

        Args:
            input: String expression.
            count: Number of repetitions.

        Returns:
            Repeated string.
        """
        count_val = self._extract_literal_value(count)
        n = int(count_val)
        return input.map_elements(
            lambda s: s * n if s is not None else None,
            return_dtype=pl.String,
        )

    def reverse(self, input: PolarsExpr, /) -> PolarsExpr:
        """Return the string in reverse order.

        Args:
            input: String expression.

        Returns:
            Reversed string.
        """
        return input.str.reverse()

    # =========================================================================
    # Pattern Matching Operations
    # =========================================================================

    def like(
        self,
        input: PolarsExpr,
        /,
        match: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """SQL LIKE pattern matching (% and _ wildcards).

        Args:
            input: String expression.
            match: SQL LIKE pattern.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        # Extract literal value from Expr if needed
        pattern = self._extract_literal_value(match)

        pattern_str = str(pattern)
        # Convert SQL LIKE pattern to regex
        # Use placeholders to avoid conflicts during escaping
        like_pattern = pattern_str.replace("%", "\x00PERCENT\x00").replace("_", "\x00UNDERSCORE\x00")
        regex_pattern = re.escape(like_pattern)
        regex_pattern = regex_pattern.replace("\x00PERCENT\x00", ".*").replace("\x00UNDERSCORE\x00", ".")
        regex_pattern = f"^{regex_pattern}$"
        return input.str.contains(regex_pattern, literal=False)

    def regexp_match_substring(
        self,
        input: PolarsExpr,
        pattern: PolarsExpr,
        /,
        position: PolarsExpr = None,
        occurrence: PolarsExpr = None,
        group: PolarsExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
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
        return input.str.extract(pattern, group_index=group_index)

    def regexp_match_substring_all(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr,
        position: PolarsExpr = None,
        group: PolarsExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
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
        """
        return input.str.extract_all(pattern)

    def regexp_strpos(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr,
        position: PolarsExpr = None,
        occurrence: PolarsExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
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
        """
        # Polars doesn't have direct regex position, use find with regex
        return (input.str.find(pattern, literal=False) + 1).fill_null(0)

    def regexp_count_substring(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr,
        position: PolarsExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
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
        """
        return input.str.count_matches(pattern, literal=False)

    def regexp_replace(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr,
        replacement: PolarsExpr,
        position: PolarsExpr = None,
        occurrence: PolarsExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
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
        # Extract literal values from Expr objects if needed
        regex_pattern = self._extract_literal_value(pattern)
        repl = self._extract_literal_value(replacement)

        # If occurrence is 0 or None, replace all
        if occurrence is None or occurrence == 0:
            return input.str.replace_all(regex_pattern, repl, literal=False)
        # Replace first occurrence only
        return input.str.replace(regex_pattern, repl, literal=False)

    # =========================================================================
    # Split Operations
    # =========================================================================

    def string_split(
        self,
        input: PolarsExpr,
        /,
        separator: PolarsExpr,
    ) -> PolarsExpr:
        """Split a string into a list based on separator.

        Args:
            input: String expression.
            separator: Separator string.

        Returns:
            List of strings.
        """
        return input.str.split(separator)

    def regexp_string_split(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
        """Split a string into a list based on regex pattern.

        Args:
            input: String expression.
            pattern: Regex pattern for separator.
            case_sensitivity: Case sensitivity option.
            multiline: Multiline mode.
            dotall: Dotall mode.

        Returns:
            List of strings.
        """
        return input.str.split(pattern)
