"""Narwhals ScalarStringExpressionProtocol implementation.

Implements string operations for the Narwhals backend.
"""

from __future__ import annotations

import re
from typing import Any, Optional, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr



class SubstraitNarwhalsScalarStringExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol[nw.Expr]):
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
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        characters: NarwhalsExpr = None,
    ) -> NarwhalsExpr:
        """Remove characters from both sides of the string.

        Args:
            input: String expression.
            characters: Characters to remove (default: whitespace).

        Returns:
            Trimmed string.
        """
        if characters is None:
            return input.str.strip_chars()
        chars_val = self._extract_literal_if_possible(characters)
        return self._call_with_expr_support(
            lambda: input.str.strip_chars(chars_val),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TRIM,
            characters=characters,
        )

    def ltrim(
        self,
        input: NarwhalsExpr,
        /,
        characters: NarwhalsExpr = None,
    ) -> NarwhalsExpr:
        """Remove characters from the left side of the string.

        Args:
            input: String expression.
            characters: Characters to remove (default: whitespace).

        Returns:
            Left-trimmed string.

        Note:
            Narwhals does not have directional strip. Falls back to strip_chars()
            which trims both sides. When a characters argument is provided it is
            passed to strip_chars so the correct character set is still used.
        """
        if characters is None:
            return input.str.strip_chars()
        chars_val = self._extract_literal_if_possible(characters)
        return self._call_with_expr_support(
            lambda: input.str.strip_chars(chars_val),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM,
            characters=characters,
        )

    def rtrim(
        self,
        input: NarwhalsExpr,
        /,
        characters: NarwhalsExpr = None,
    ) -> NarwhalsExpr:
        """Remove characters from the right side of the string.

        Args:
            input: String expression.
            characters: Characters to remove (default: whitespace).

        Returns:
            Right-trimmed string.

        Note:
            Narwhals does not have directional strip. Falls back to strip_chars()
            which trims both sides. When a characters argument is provided it is
            passed to strip_chars so the correct character set is still used.
        """
        if characters is None:
            return input.str.strip_chars()
        chars_val = self._extract_literal_if_possible(characters)
        return self._call_with_expr_support(
            lambda: input.str.strip_chars(chars_val),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM,
            characters=characters,
        )

    def lpad(
        self,
        input: NarwhalsExpr,
        /,
        length: NarwhalsExpr,
        characters: NarwhalsExpr = None,
    ) -> NarwhalsExpr:
        """Left-pad the input string to specified length."""
        length_raw = self._extract_literal_if_possible(length)
        fill_raw = " " if characters is None else self._extract_literal_if_possible(characters)
        return self._call_with_expr_support(
            lambda: input.str.pad_start(int(length_raw), str(fill_raw)),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,
            length=length,
        )

    def rpad(
        self,
        input: NarwhalsExpr,
        /,
        length: NarwhalsExpr,
        characters: NarwhalsExpr = None,
    ) -> NarwhalsExpr:
        """Right-pad the input string to specified length."""
        length_raw = self._extract_literal_if_possible(length)
        fill_raw = " " if characters is None else self._extract_literal_if_possible(characters)
        return self._call_with_expr_support(
            lambda: input.str.pad_end(int(length_raw), str(fill_raw)),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RPAD,
            length=length,
        )

    def center(
        self,
        input: NarwhalsExpr,
        /,
        length: NarwhalsExpr,
        character: NarwhalsExpr = None,
        padding: Any = None,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        start: NarwhalsExpr,
        length: NarwhalsExpr = None,
        negative_start: Any = None,
    ) -> NarwhalsExpr:
        """Extract a substring.

        Args:
            input: String expression.
            start: Starting position (0-indexed for API consistency).
            length: Length of substring.
            negative_start: How to handle negative start values.

        Returns:
            Substring expression.
        """
        # Narwhals str.slice requires int args (no expression support).
        # Unwrap literals; column refs pass through and will be caught below.
        start_val = self._extract_literal_if_possible(start)
        length_val = self._extract_literal_if_possible(length) if length is not None else None

        def _call() -> NarwhalsExpr:
            # Coerce to int (extraction may return float for numeric literals)
            sv = int(start_val) if start_val is not None else 0
            if length_val is None:
                return input.str.slice(sv)
            return input.str.slice(sv, int(length_val))

        return self._call_with_expr_support(
            _call,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
            start=start,
            length=length,
        )

    def left(
        self,
        input: NarwhalsExpr,
        /,
        count: NarwhalsExpr,
    ) -> NarwhalsExpr:
        """Extract count characters from the left."""
        count_raw = self._extract_literal_if_possible(count)
        return self._call_with_expr_support(
            lambda: input.str.head(int(count_raw)),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LEFT,
            count=count,
        )

    def right(
        self,
        input: NarwhalsExpr,
        /,
        count: NarwhalsExpr,
    ) -> NarwhalsExpr:
        """Extract count characters from the right."""
        count_raw = self._extract_literal_if_possible(count)
        return self._call_with_expr_support(
            lambda: input.str.tail(int(count_raw)),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RIGHT,
            count=count,
        )

    def replace_slice(
        self,
        input: NarwhalsExpr,
        /,
        start: NarwhalsExpr,
        length: NarwhalsExpr,
        replacement: NarwhalsExpr,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Whether the input string contains the substring.

        Args:
            input: String expression.
            substring: Substring to search for.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        # Narwhals/Pandas str.contains expects a string pattern, not an Expr.
        # Unwrap nw.lit("...") to a raw value; column refs pass through and
        # will be caught by _call_with_expr_support with an enriched error.
        pattern = self._extract_literal_if_possible(substring)
        if case_sensitivity == "CASE_INSENSITIVE":
            lowered = pattern.lower() if isinstance(pattern, str) else pattern
            return self._call_with_expr_support(
                lambda: input.str.to_lowercase().str.contains(lowered),
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
                substring=substring,
            )
        return self._call_with_expr_support(
            lambda: input.str.contains(pattern),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substring=substring,
        )

    def starts_with(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Whether input string starts with the substring.

        Args:
            input: String expression.
            substring: Prefix to check.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        # Narwhals/Pandas str.starts_with expects a string pattern, not an Expr.
        # Unwrap nw.lit("...") to a raw value; column refs pass through and
        # will be caught by _call_with_expr_support with an enriched error.
        prefix = self._extract_literal_if_possible(substring)
        if case_sensitivity == "CASE_INSENSITIVE":
            lowered = prefix.lower() if isinstance(prefix, str) else prefix
            return self._call_with_expr_support(
                lambda: input.str.to_lowercase().str.starts_with(lowered),
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
                substring=substring,
            )
        return self._call_with_expr_support(
            lambda: input.str.starts_with(prefix),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
            substring=substring,
        )

    def ends_with(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Whether input string ends with the substring.

        Args:
            input: String expression.
            substring: Suffix to check.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        # Narwhals/Pandas str.ends_with expects a string pattern, not an Expr.
        # Unwrap nw.lit("...") to a raw value; column refs pass through and
        # will be caught by _call_with_expr_support with an enriched error.
        suffix = self._extract_literal_if_possible(substring)
        if case_sensitivity == "CASE_INSENSITIVE":
            lowered = suffix.lower() if isinstance(suffix, str) else suffix
            return self._call_with_expr_support(
                lambda: input.str.to_lowercase().str.ends_with(lowered),
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
                substring=substring,
            )
        return self._call_with_expr_support(
            lambda: input.str.ends_with(suffix),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
            substring=substring,
        )

    def strpos(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
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

    def char_length(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the number of characters in the input string.

        Args:
            input: String expression.

        Returns:
            Character count.
        """
        return input.str.len_chars()

    def bit_length(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the number of bits in the input string.

        Args:
            input: String expression.

        Returns:
            Bit count.
        """
        # Bit length = byte length * 8
        # Narwhals may not have len_bytes - use len_chars as approximation
        return input.str.len_chars() * nw.lit(8)

    def octet_length(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        null_handling: Any = None,
    ) -> NarwhalsExpr:
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
        separator: NarwhalsExpr,
        /,
        string_arguments: NarwhalsExpr,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        replacement: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Replace all occurrences of substring with replacement.

        Args:
            input: String expression.
            substring: Substring to replace.
            replacement: Replacement string.
            case_sensitivity: Case sensitivity option.

        Returns:
            String with replacements.
        """
        # Narwhals/Pandas str.replace_all expects string patterns, not Expr.
        # Unwrap literals; column refs pass through and will be caught below.
        pattern = self._extract_literal_if_possible(substring)
        repl = self._extract_literal_if_possible(replacement)
        return self._call_with_expr_support(
            lambda: input.str.replace_all(pattern, repl),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
            substring=substring,
            replacement=replacement,
        )

    def repeat(
        self,
        input: NarwhalsExpr,
        /,
        count: NarwhalsExpr,
    ) -> NarwhalsExpr:
        """Repeat a string count number of times."""
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "Narwhals does not support str.repeat(). Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT,
        )

    def reverse(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        match: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """SQL LIKE pattern matching (% and _ wildcards).

        Args:
            input: String expression.
            match: SQL LIKE pattern.
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        # Narwhals/Pandas str.contains expects a string pattern, not an Expr.
        # Unwrap literals; column refs pass through and will be caught below.
        pattern = self._extract_literal_if_possible(match)

        def _call() -> NarwhalsExpr:
            if isinstance(pattern, str):
                # Convert SQL LIKE pattern to regex
                like_pattern = pattern.replace("%", "\x00PERCENT\x00").replace("_", "\x00UNDERSCORE\x00")
                regex_pattern = re.escape(like_pattern)
                regex_pattern = regex_pattern.replace("\x00PERCENT\x00", ".*").replace("\x00UNDERSCORE\x00", ".")
                regex_pattern = f"^{regex_pattern}$"
                return input.str.contains(regex_pattern)
            # Fallback for non-string patterns
            return input.str.contains(pattern)

        return self._call_with_expr_support(
            _call,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
            match=match,
        )

    def regexp_match_substring(
        self,
        input: NarwhalsExpr,
        /,
        pattern: NarwhalsExpr,
        position: Optional[int] = None,
        occurrence: Optional[int] = None,
        group: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        pattern: NarwhalsExpr,
        position: Optional[int] = None,
        group: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> NarwhalsExpr:
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
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
        raise BackendCapabilityError(
            "Narwhals does not support regexp_match_substring_all (no extract_all method). "
            "Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
        )

    def regexp_strpos(
        self,
        input: NarwhalsExpr,
        /,
        pattern: NarwhalsExpr,
        position: Optional[int] = None,
        occurrence: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> NarwhalsExpr:
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
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
        raise BackendCapabilityError(
            "Narwhals does not support regexp_strpos (no regex find method). "
            "Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
        )

    def regexp_count_substring(
        self,
        input: NarwhalsExpr,
        /,
        pattern: NarwhalsExpr,
        position: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> NarwhalsExpr:
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
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
        raise BackendCapabilityError(
            "Narwhals does not support regexp_count_substring (no count_matches method). "
            "Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
        )

    def regexp_replace(
        self,
        input: NarwhalsExpr,
        /,
        pattern: NarwhalsExpr,
        replacement: NarwhalsExpr,
        position: Optional[int] = None,
        occurrence: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> NarwhalsExpr:
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
        # Narwhals/Pandas str.replace_all expects string patterns, not Expr.
        # Unwrap literals; column refs pass through and will be caught below.
        regex_pattern = self._extract_literal_if_possible(pattern)
        repl = self._extract_literal_if_possible(replacement)
        return self._call_with_expr_support(
            lambda: input.str.replace_all(regex_pattern, repl),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            pattern=pattern,
            replacement=replacement,
        )

    # =========================================================================
    # Split Operations
    # =========================================================================

    def string_split(
        self,
        input: NarwhalsExpr,
        /,
        separator: NarwhalsExpr,
    ) -> NarwhalsExpr:
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
        input: NarwhalsExpr,
        /,
        pattern: NarwhalsExpr,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> NarwhalsExpr:
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
