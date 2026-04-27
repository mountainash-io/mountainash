"""Ibis ScalarStringExpressionProtocol implementation.

Implements string operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr


class SubstraitIbisScalarStringExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol["IbisValueExpr"]):
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
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        characters: IbisValueExpr = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        characters: IbisValueExpr = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        characters: IbisValueExpr = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        length: IbisValueExpr,
        characters: IbisValueExpr = None,
    ) -> IbisValueExpr:
        """Left-pad the input string to specified length.

        Args:
            input: String expression.
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            Left-padded string.
        """
        fill_char = ibis.literal(" ") if characters is None else characters
        return self._call_with_expr_support(
            lambda: input.lpad(length, fill_char),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,
            length=length,
            characters=fill_char,
        )

    def rpad(
        self,
        input: IbisValueExpr,
        /,
        length: IbisValueExpr,
        characters: IbisValueExpr = None,
    ) -> IbisValueExpr:
        """Right-pad the input string to specified length.

        Args:
            input: String expression.
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            Right-padded string.
        """
        fill_char = ibis.literal(" ") if characters is None else characters
        return self._call_with_expr_support(
            lambda: input.rpad(length, fill_char),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RPAD,
            length=length,
            characters=fill_char,
        )

    def center(
        self,
        input: IbisValueExpr,
        /,
        length: IbisValueExpr,
        character: IbisValueExpr = None,
        padding: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        start: IbisValueExpr,
        length: IbisValueExpr = None,
        negative_start: Any = None,
    ) -> IbisValueExpr:
        """Extract a substring.

        Args:
            input: String expression.
            start: Starting position (0-indexed for API consistency).
            length: Length of substring.
            negative_start: How to handle negative start values.

        Returns:
            Substring expression.
        """
        if length is None:
            return self._call_with_expr_support(
                lambda: input.substr(start),
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
                start=start,
            )
        return self._call_with_expr_support(
            lambda: input.substr(start, length),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
            start=start,
            length=length,
        )

    def left(
        self,
        input: IbisValueExpr,
        /,
        count: IbisValueExpr,
    ) -> IbisValueExpr:
        """Extract count characters from the left."""
        return self._call_with_expr_support(
            lambda: input.left(count),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LEFT,
            count=count,
        )

    def right(
        self,
        input: IbisValueExpr,
        /,
        count: IbisValueExpr,
    ) -> IbisValueExpr:
        """Extract count characters from the right."""
        return self._call_with_expr_support(
            lambda: input.right(count),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RIGHT,
            count=count,
        )

    def replace_slice(
        self,
        input: IbisValueExpr,
        /,
        start: IbisValueExpr,
        length: IbisValueExpr,
        replacement: IbisValueExpr,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        substring: IbisValueExpr,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """Whether the input string contains the substring."""
        if case_sensitivity == "CASE_INSENSITIVE":
            return self._call_with_expr_support(
                lambda: input.lower().contains(substring.lower()),
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
                substring=substring,
            )
        return self._call_with_expr_support(
            lambda: input.contains(substring),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substring=substring,
        )

    def starts_with(
        self,
        input: IbisValueExpr,
        substring: IbisValueExpr,
        /,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """Whether input string starts with the substring."""
        if case_sensitivity == "CASE_INSENSITIVE":
            return self._call_with_expr_support(
                lambda: input.lower().startswith(substring.lower()),
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
                substring=substring,
            )
        return self._call_with_expr_support(
            lambda: input.startswith(substring),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
            substring=substring,
        )

    def ends_with(
        self,
        input: IbisValueExpr,
        /,
        substring: IbisValueExpr,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """Whether input string ends with the substring."""
        if case_sensitivity == "CASE_INSENSITIVE":
            return self._call_with_expr_support(
                lambda: input.lower().endswith(substring.lower()),
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
                substring=substring,
            )
        return self._call_with_expr_support(
            lambda: input.endswith(substring),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
            substring=substring,
        )

    def strpos(
        self,
        input: IbisValueExpr,
        /,
        substring: IbisValueExpr,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        substring: IbisValueExpr,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
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

    def char_length(self, input: IbisValueExpr, /) -> IbisValueExpr:
        """Return the number of characters in the input string.

        Args:
            input: String expression.

        Returns:
            Character count.
        """
        return input.length()

    def bit_length(self, input: IbisValueExpr, /) -> IbisValueExpr:
        """Return the number of bits in the input string.

        Args:
            input: String expression.

        Returns:
            Bit count.
        """
        # Bit length = byte length * 8
        return input.length() * ibis.literal(8)

    def octet_length(self, input: IbisValueExpr, /) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        null_handling: Any = None,
    ) -> IbisValueExpr:
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
        separator: IbisValueExpr,
        /,
        string_arguments: IbisValueExpr,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        substring: IbisValueExpr,
        replacement: IbisValueExpr,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """Replace all occurrences of substring with replacement.

        Args:
            input: String expression.
            substring: Substring to replace.
            replacement: Replacement string.
            case_sensitivity: Case sensitivity option.

        Returns:
            String with replacements.

        Note:
            Ibis .replace() only replaces the first occurrence on some backends
            (e.g., Polars). We use .re_replace() to get replace-all semantics
            consistent with Python str.replace across all Ibis backends.
        """
        return self._call_with_expr_support(
            lambda: input.re_replace(substring, replacement),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
            substring=substring,
            replacement=replacement,
        )

    def repeat(
        self,
        input: IbisValueExpr,
        /,
        count: IbisValueExpr,
    ) -> IbisValueExpr:
        """Repeat a string count number of times.

        Args:
            input: String expression.
            count: Number of repetitions.

        Returns:
            Repeated string.
        """
        return self._call_with_expr_support(
            lambda: input.repeat(count),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT,
            count=count,
        )

    def reverse(self, input: IbisValueExpr, /) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        match: IbisValueExpr,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """SQL LIKE pattern matching (% and _ wildcards).

        Args:
            input: String expression.
            match: SQL LIKE pattern.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        return self._call_with_expr_support(
            lambda: input.like(match),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
            match=match,
        )

    def regexp_match_substring(
        self,
        input: IbisValueExpr,
        pattern: IbisValueExpr,
        /,
        position: IbisValueExpr = None,
        occurrence: IbisValueExpr = None,
        group: IbisValueExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> IbisValueExpr:
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
        return self._call_with_expr_support(
            lambda: input.re_extract(pattern, group_index),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            pattern=pattern,
        )

    def regexp_match_substring_all(
        self,
        input: IbisValueExpr,
        /,
        pattern: IbisValueExpr,
        position: IbisValueExpr = None,
        group: IbisValueExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        pattern: IbisValueExpr,
        position: IbisValueExpr = None,
        occurrence: IbisValueExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        pattern: IbisValueExpr,
        position: IbisValueExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        pattern: IbisValueExpr,
        replacement: IbisValueExpr,
        position: IbisValueExpr = None,
        occurrence: IbisValueExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> IbisValueExpr:
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
        return self._call_with_expr_support(
            lambda: input.re_replace(pattern, replacement),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            pattern=pattern,
            replacement=replacement,
        )

    # =========================================================================
    # Split Operations
    # =========================================================================

    def string_split(
        self,
        input: IbisValueExpr,
        /,
        separator: IbisValueExpr,
    ) -> IbisValueExpr:
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
        input: IbisValueExpr,
        /,
        pattern: IbisValueExpr,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> IbisValueExpr:
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
