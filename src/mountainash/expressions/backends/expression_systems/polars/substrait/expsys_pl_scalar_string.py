"""Polars ScalarStringExpressionProtocol implementation.

Implements string operations for the Polars backend.
"""

from __future__ import annotations

import functools
import re
from typing import Any, Optional, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


def _pl_concat_fold(sep: "PolarsExpr", inputs: "tuple[PolarsExpr, ...]") -> "PolarsExpr":
    """Portable IGNORE_NULLS fold: skip null operands, never emit a leading
    or double separator. Shared by concat (sep="") and concat_ws (real sep)."""
    text_acc = pl.lit("")
    any_seen = pl.lit(False)
    for x in inputs:
        present = x.is_not_null()
        piece = pl.when(present).then(
            pl.when(any_seen).then(sep + x).otherwise(x)
        ).otherwise(pl.lit(""))
        text_acc = text_acc + piece
        any_seen = any_seen | present
    return text_acc


_ASCII_UPPER = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_ASCII_LOWER = list("abcdefghijklmnopqrstuvwxyz")


def _pl_fold(expr: "PolarsExpr", case_sensitivity: Any) -> "PolarsExpr":
    """Apply the fold a case_sensitivity option value implies. CASE_SENSITIVE
    (and any other/omitted value) leaves expr unchanged; CASE_INSENSITIVE
    applies full Unicode lowercasing; CASE_INSENSITIVE_ASCII folds only
    A-Z/a-z via a single-pass replace_many, leaving every other code point
    (Kelvin Sign, Turkish I-with-dot, ...) untouched -- see backlog item 75.

    Casts to Utf8 first (a no-op for an already-String expr) so an untyped
    null literal (`ma.lit(None)` for the search operand -- item 80) gets a
    concrete String dtype the .str accessor accepts, instead of crashing
    with SchemaError; the null itself still propagates through .str.*
    unchanged."""
    if case_sensitivity == "CASE_INSENSITIVE":
        return expr.cast(pl.Utf8).str.to_lowercase()
    if case_sensitivity == "CASE_INSENSITIVE_ASCII":
        return expr.cast(pl.Utf8).str.replace_many(_ASCII_UPPER, _ASCII_LOWER)
    return expr


def _regexp_split_excluding_groups(pattern: str, s: str | None) -> list[str] | None:
    """Split `s` on `pattern`, excluding any captured-group substrings from
    the result (unlike bare re.split). Matches the Substrait
    regexp_string_split contract: "the substrings matched by the pattern
    will be used as the separators... and will not be included in the
    resulting list" -- bare re.split leaks capture-group text into the
    output when the pattern contains parentheses (verified against the
    ibis-duckdb oracle, backlog item 85)."""
    if s is None:
        return None
    parts: list[str] = []
    last = 0
    for m in re.finditer(pattern, s):
        parts.append(s[last:m.start()])
        last = m.end()
    parts.append(s[last:])
    return parts


class SubstraitPolarsScalarStringExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol[pl.Expr]):
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
    def _prepare_call_lpad(self, operands):
        prepared = [operands.native(0), operands.native(1)]
        if len(operands) > 2:
            prepared.append(
                operands.raw_literal(2, "Polars padding characters must be literals")
            )
        return prepared

    def _prepare_call_rpad(self, operands):
        prepared = [operands.native(0), operands.native(1)]
        if len(operands) > 2:
            prepared.append(
                operands.raw_literal(2, "Polars padding characters must be literals")
            )
        return prepared

    def _prepare_call_center(self, operands):
        prepared = [
            operands.native(0),
            operands.raw_literal(1, "Polars center length must be a literal"),
        ]
        if len(operands) > 2:
            prepared.append(
                operands.raw_literal(2, "Polars center padding character must be a literal")
            )
        return prepared

    def _prepare_call_replace_slice(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Polars slice start must be a literal"),
            operands.raw_literal(2, "Polars slice length must be a literal"),
            operands.raw_literal(3, "Polars slice replacement must be a literal"),
        ]

    def _prepare_literal_pattern(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Polars replacement patterns must be literals"),
        ] + [operands.native(index) for index in range(2, len(operands))]

    def _prepare_call_replace(self, operands):
        return self._prepare_literal_pattern(operands)

    def _prepare_call_regexp_replace(self, operands):
        return self._prepare_literal_pattern(operands)

    def _prepare_call_repeat(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Polars repeat count must be a literal"),
        ]

    def _prepare_call_like(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Polars LIKE pattern must be a literal"),
        ]

    def _prepare_call_regexp_string_split(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Polars regex split pattern must be a literal"),
        ]


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
            char_set: Omit it or use UTF8 for native Polars behavior.

        Returns:
            Lowercase string.
        """
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports UTF8 char_set. Omit char_set or use UTF8 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
            )
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
            char_set: Omit it or use UTF8 for native Polars behavior.

        Returns:
            Uppercase string.
        """
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports UTF8 char_set. Omit char_set or use UTF8 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
            )
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
            char_set: Omit it or use UTF8 for native Polars behavior.

        Returns:
            String with swapped case.

        Note:
            Polars doesn't have native swapcase. We implement using
            character-by-character transformation via map.
        """
        # Polars doesn't have swapcase, use a workaround
        # This is a simplification - full implementation would need UDF
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports UTF8 char_set. Omit char_set or use UTF8 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE,
            )
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
            char_set: Omit it or use UTF8 for native Polars behavior.

        Returns:
            String with first character capitalized.

        Note:
            Polars doesn't have native capitalize. We use map_elements.
        """
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports UTF8 char_set. Omit char_set or use UTF8 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE,
            )
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
            char_set: Omit it or use UTF8 for native Polars behavior.

        Returns:
            Title-cased string.

        Note:
            Polars has str.to_titlecase() which capitalizes all words.
            Substrait's title() excludes articles - this is a simplification.
        """
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports UTF8 char_set. Omit char_set or use UTF8 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE,
            )
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
            char_set: Omit it or use UTF8 for native Polars behavior.

        Returns:
            String with each word capitalized.
        """
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports UTF8 char_set. Omit char_set or use UTF8 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP,
            )
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
        return input.str.strip_chars(characters)

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
        return input.str.strip_chars_start(characters)

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
        return input.str.strip_chars_end(characters)

    def lpad(
        self,
        input: PolarsExpr,
        /,
        length: PolarsExpr,
        characters: PolarsExpr | str | None = None,
    ) -> PolarsExpr:
        """Left-pad the input string to specified length.

        Args:
            input: String expression.
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            Left-padded string.
        """
        fill_char = " " if characters is None else str(characters)
        return input.str.pad_start(length, fill_char=fill_char)

    def rpad(
        self,
        input: PolarsExpr,
        /,
        length: PolarsExpr,
        characters: PolarsExpr | str | None = None,
    ) -> PolarsExpr:
        """Right-pad the input string to specified length.

        Args:
            input: String expression.
            length: Target length.
            characters: Padding characters (default: space).

        Returns:
            Right-padded string.
        """
        fill_char = " " if characters is None else str(characters)
        return input.str.pad_end(length, fill_char=fill_char)

    def center(
        self,
        input: PolarsExpr,
        /,
        length: PolarsExpr | int,
        character: PolarsExpr | str | None = None,
        padding: Any = None,
    ) -> PolarsExpr:
        """Center the input string by padding both sides.

        Args:
            input: String expression.
            length: Target length.
            character: Single padding character (default: space).
            padding: Omit for Python str.center behavior; explicit directions are unsupported.

        Returns:
            Centered string.
        """
        if padding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars center uses Python str.center padding; explicit LEFT/RIGHT padding is not implemented.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
            )
        char = " " if character is None else str(character)
        target_len = int(length)
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
            negative_start: Omit it or use WRAP_FROM_END for native Polars behavior.

        Returns:
            Substring expression.
        """
        if negative_start not in (None, "WRAP_FROM_END"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports WRAP_FROM_END negative_start. Omit it or use WRAP_FROM_END for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
            )

        if length is None:
            return input.str.slice(start)
        return input.str.slice(start, length)

    def left(
        self,
        input: PolarsExpr,
        /,
        count: PolarsExpr,
    ) -> PolarsExpr:
        """Extract count characters from the left."""
        return input.str.head(count)

    def right(
        self,
        input: PolarsExpr,
        /,
        count: PolarsExpr,
    ) -> PolarsExpr:
        """Extract count characters from the right."""
        return input.str.tail(count)

    def replace_slice(
        self,
        input: PolarsExpr,
        /,
        start: PolarsExpr | int,
        length: PolarsExpr | int,
        replacement: PolarsExpr | str,
    ) -> PolarsExpr:
        """Replace a slice of the input string (1-indexed start, clamped).

        Args:
            input: String expression.
            start: Starting position (1-indexed).
            length: Length to replace.
            replacement: Replacement string.

        Returns:
            String with replaced slice.
        """
        offset = int(start) - 1 if int(start) > 0 else 0
        repl = str(replacement)
        len_val = int(length)
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
            substring: Substring to search for (expression or literal).
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        return _pl_fold(input, case_sensitivity).str.contains(
            _pl_fold(substring, case_sensitivity), literal=True
        )

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
        return _pl_fold(input, case_sensitivity).str.starts_with(
            _pl_fold(substring, case_sensitivity)
        )

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
        return _pl_fold(input, case_sensitivity).str.ends_with(
            _pl_fold(substring, case_sensitivity)
        )

    def strpos(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Return 1-indexed position of substring in input, 0 if not found.

        Args:
            input: String expression.
            substring: Substring to search for (expression or literal).
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.

        Returns:
            Integer expression (1-indexed, 0 = not found).
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
            )

        return input.str.find(substring).fill_null(-1) + 1

    def count_substring(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Count occurrences of substring in input.

        Args:
            input: String expression.
            substring: Substring to count (expression or literal).
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.

        Returns:
            Integer expression. A null substring short-circuits to a null
            result: `.cast(pl.Utf8)` gives an untyped-null literal a
            concrete String dtype (a no-op for an already-String expr)
            before it reaches count_matches(), which otherwise raises a
            SchemaError on the untyped null at SCHEMA-RESOLUTION time --
            `pl.when(...).then(None).otherwise(...)` does NOT avoid this,
            since Polars validates both branches' schemas eagerly
            regardless of the runtime condition (verified empirically).
            Matches the null-propagation convention count_substring's
            Ibis/Narwhals implementations use for the same input (item 78).
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
            )

        return input.str.count_matches(substring.cast(pl.Utf8), literal=True)

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
        *input: PolarsExpr,
        null_handling: Any = None,
    ) -> PolarsExpr:
        """Concatenate strings.

        Args:
            *input: String expressions to concatenate.
            null_handling: How to handle nulls (IGNORE_NULLS or ACCEPT_NULLS;
                default IGNORE_NULLS).

        Returns:
            Concatenated string.
        """
        if null_handling == "ACCEPT_NULLS":
            return functools.reduce(lambda acc, x: acc + x, input[1:], input[0])
        return _pl_concat_fold(pl.lit(""), input)

    def concat_ws(
        self,
        separator: PolarsExpr,
        /,
        *string_arguments: PolarsExpr,
    ) -> PolarsExpr:
        """Concatenate strings with separator.

        Args:
            separator: Separator string.
            *string_arguments: Strings to concatenate.

        Returns:
            Concatenated string with separator. A null separator
            unconditionally propagates to a null result (matching DuckDB's
            own native CONCAT_WS convention), regardless of operand count
            or nullness.
        """
        return pl.when(separator.is_null()).then(
            pl.lit(None, dtype=pl.Utf8)
        ).otherwise(_pl_concat_fold(separator, string_arguments))

    def replace(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr | str,
        replacement: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Replace all occurrences of substring with replacement.

        Args:
            input: String expression.
            substring: Substring to replace.
            replacement: Replacement string.
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.

        Returns:
            String with replacements.
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
            )

        return input.str.replace_all(substring, replacement, literal=True)

    def repeat(
        self,
        input: PolarsExpr,
        /,
        count: PolarsExpr | int,
    ) -> PolarsExpr:
        """Repeat a string count number of times.

        Args:
            input: String expression.
            count: Number of repetitions.

        Returns:
            Repeated string.
        """
        n = int(count)
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
        match: PolarsExpr | str,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """SQL LIKE pattern matching (% and _ wildcards).

        Args:
            input: String expression.
            match: SQL LIKE pattern.
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.

        Returns:
            Boolean expression.
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
            )

        pattern_str = str(match)
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
        position: Optional[int] = None,
        occurrence: Optional[int] = None,
        group: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
        """Extract substring matching regex pattern.

        Args:
            input: String expression.
            pattern: Regex pattern.
            position: Omit it or use 1 for native Polars behavior.
            occurrence: Omit it or use 1 for native Polars behavior.
            group: Capture group number.
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.
            multiline: Omit it or use MULTILINE_DISABLED for native Polars behavior.
            dotall: Omit it or use DOTALL_DISABLED for native Polars behavior.

        Returns:
            Matched substring or null.
        """
        if position not in (None, 1):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports position 1. Omit position or use 1 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            )
        if occurrence not in (None, 1):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports occurrence 1. Omit occurrence or use 1 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            )
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            )
        if multiline not in (None, "MULTILINE_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports MULTILINE_DISABLED multiline. Omit it or use MULTILINE_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            )
        if dotall not in (None, "DOTALL_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports DOTALL_DISABLED dotall. Omit it or use DOTALL_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            )
        # group is a raw int|None option (arguments-vs-options.md); no Expr to guard.
        group_index = 0 if group is None else group
        return input.str.extract(pattern, group_index=group_index)

    def regexp_match_substring_all(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr,
        position: Optional[int] = None,
        group: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
        """Extract all substrings matching regex pattern.

        Args:
            input: String expression.
            pattern: Regex pattern.
            position: Omit it or use 1 for native Polars behavior.
            group: Omit it or use 0 for native Polars behavior.
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.
            multiline: Omit it or use MULTILINE_DISABLED for native Polars behavior.
            dotall: Omit it or use DOTALL_DISABLED for native Polars behavior.

        Returns:
            List of matched substrings.
        """
        if position not in (None, 1):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports position 1. Omit position or use 1 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
            )
        if group not in (None, 0):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports group 0. Omit group or use 0 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
            )
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
            )
        if multiline not in (None, "MULTILINE_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports MULTILINE_DISABLED multiline. Omit it or use MULTILINE_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
            )
        if dotall not in (None, "DOTALL_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports DOTALL_DISABLED dotall. Omit it or use DOTALL_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
            )
        return input.str.extract_all(pattern)

    def regexp_strpos(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr,
        position: Optional[int] = None,
        occurrence: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
        """Return position of regex pattern match (1-indexed).

        Args:
            input: String expression.
            pattern: Regex pattern.
            position: Omit it or use 1 for native Polars behavior.
            occurrence: Omit it or use 1 for native Polars behavior.
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.
            multiline: Omit it or use MULTILINE_DISABLED for native Polars behavior.
            dotall: Omit it or use DOTALL_DISABLED for native Polars behavior.

        Returns:
            Position (1-indexed), or 0 if not found.
        """
        if position not in (None, 1):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports position 1. Omit position or use 1 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
            )
        if occurrence not in (None, 1):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports occurrence 1. Omit occurrence or use 1 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
            )
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
            )
        if multiline not in (None, "MULTILINE_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports MULTILINE_DISABLED multiline. Omit it or use MULTILINE_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
            )
        if dotall not in (None, "DOTALL_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports DOTALL_DISABLED dotall. Omit it or use DOTALL_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
            )
        # Polars doesn't have direct regex position, use find with regex
        return (input.str.find(pattern, literal=False) + 1).fill_null(0)

    def regexp_count_substring(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr,
        position: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
        """Return count of non-overlapping regex matches.

        Args:
            input: String expression.
            pattern: Regex pattern.
            position: Omit it or use 1 for native Polars behavior.
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.
            multiline: Omit it or use MULTILINE_DISABLED for native Polars behavior.
            dotall: Omit it or use DOTALL_DISABLED for native Polars behavior.

        Returns:
            Count of matches.
        """
        if position not in (None, 1):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports position 1. Omit position or use 1 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
            )
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
            )
        if multiline not in (None, "MULTILINE_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports MULTILINE_DISABLED multiline. Omit it or use MULTILINE_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
            )
        if dotall not in (None, "DOTALL_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports DOTALL_DISABLED dotall. Omit it or use DOTALL_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
            )
        return input.str.count_matches(pattern, literal=False)

    def regexp_replace(
        self,
        input: PolarsExpr,
        /,
        pattern: PolarsExpr | str,
        replacement: PolarsExpr,
        position: Optional[int] = None,
        occurrence: Optional[int] = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
        """Replace text matching regex pattern.

        Args:
            input: String expression.
            pattern: Regex pattern.
            replacement: Replacement string.
            position: Omit it or use 1 for native Polars behavior.
            occurrence: Omit it, use 0 to replace all, or use 1 to replace the first match.
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.
            multiline: Omit it or use MULTILINE_DISABLED for native Polars behavior.
            dotall: Omit it or use DOTALL_DISABLED for native Polars behavior.

        Returns:
            String with replacements.
        """
        if position not in (None, 1):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports position 1. Omit position or use 1 for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            )
        if occurrence not in (None, 0, 1):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports occurrence 0 or 1. Omit occurrence, use 0 to replace all, or use 1 to replace the first match.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            )
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            )
        if multiline not in (None, "MULTILINE_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports MULTILINE_DISABLED multiline. Omit it or use MULTILINE_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            )
        if dotall not in (None, "DOTALL_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports DOTALL_DISABLED dotall. Omit it or use DOTALL_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            )
        # If occurrence is 0 or None, replace all
        if occurrence is None or occurrence == 0:
            return input.str.replace_all(pattern, replacement, literal=False)
        # Replace first occurrence only
        return input.str.replace(pattern, replacement, literal=False)

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
        pattern: PolarsExpr | str,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
        """Split a string into a list based on regex pattern.

        Args:
            input: String expression.
            pattern: Regex pattern for separator.
            case_sensitivity: Omit it or use CASE_SENSITIVE for native Polars behavior.
            multiline: Omit it or use MULTILINE_DISABLED for native Polars behavior.
            dotall: Omit it or use DOTALL_DISABLED for native Polars behavior.

        Returns:
            List of strings.

        Note:
            Polars has no native regex-split primitive (str.split/
            split_exact/splitn are literal-substring-only), so this method
            uses map_elements with a capture-group-safe split helper. Pattern
            preparation requires a literal before this method is called.
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports CASE_SENSITIVE case_sensitivity. Omit it or use CASE_SENSITIVE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
            )
        if multiline not in (None, "MULTILINE_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports MULTILINE_DISABLED multiline. Omit it or use MULTILINE_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
            )
        if dotall not in (None, "DOTALL_DISABLED"):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

            raise BackendCapabilityError(
                "Polars only supports DOTALL_DISABLED dotall. Omit it or use DOTALL_DISABLED for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
            )
        return input.map_elements(
            lambda s: _regexp_split_excluding_groups(pattern, s),
            return_dtype=pl.List(pl.String),
        )
