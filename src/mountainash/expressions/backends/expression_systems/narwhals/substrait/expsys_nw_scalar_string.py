"""Narwhals ScalarStringExpressionProtocol implementation.

Implements string operations for the Narwhals backend.
"""

from __future__ import annotations

import functools
import re
from typing import Any, Optional, TYPE_CHECKING, cast

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


def _nw_concat_fold(sep: "NarwhalsExpr", inputs: "tuple[NarwhalsExpr, ...]") -> "NarwhalsExpr":
    """Portable IGNORE_NULLS fold — mirrors the Polars/Ibis shape. Never
    routes through nw.concat_str(ignore_nulls=...) (the exact NW-STR-19
    trailing-separator bug on narwhals-pandas)."""
    text_acc = nw.lit("")
    any_seen = nw.lit(False)
    for x in inputs:
        present = ~x.is_null()
        piece = nw.when(present).then(
            nw.when(any_seen).then(sep + x).otherwise(x)
        ).otherwise(nw.lit(""))
        text_acc = text_acc + piece
        any_seen = any_seen | present
    return text_acc


_ASCII_UPPER_STR = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ASCII_LOWER_STR = "abcdefghijklmnopqrstuvwxyz"
_ASCII_TRANSLATION = str.maketrans(_ASCII_UPPER_STR, _ASCII_LOWER_STR)


def _nw_fold(expr: "NarwhalsExpr | str | None", case_sensitivity: Any) -> "NarwhalsExpr | str | None":
    """Apply the fold a case_sensitivity option value implies, to a
    NarwhalsExpr, a literal Python str operand, or a bare None -- contains/
    starts_with/ends_with's `substring` parameter is typed
    `NarwhalsExpr | str`, and a literal string must fold via plain Python
    (no narwhals call), distinct from the NarwhalsExpr branch's `.str`
    method chain (mirrors the existing CASE_INSENSITIVE branch's isinstance
    split). CASE_SENSITIVE (and any other/omitted value) leaves expr
    unchanged; CASE_INSENSITIVE applies full Unicode lowercasing;
    CASE_INSENSITIVE_ASCII folds only A-Z/a-z via 26 chained
    single-character replaces (narwhals has no batch-translate primitive),
    leaving every other code point (Kelvin Sign, Turkish I-with-dot, ...)
    untouched -- see backlog item 75.

    A null search operand (item 80) arrives EITHER as a bare Python `None`
    (narwhals-pandas) or an untyped-null NarwhalsExpr (narwhals-polars) --
    both backends probed directly. `expr is None` short-circuits the
    former; `.cast(nw.String)` (a no-op for an already-String expr) gives
    the latter a concrete dtype the .str accessor accepts, instead of
    crashing. The null itself still propagates through either path
    unchanged."""
    if expr is None:
        return None
    if case_sensitivity == "CASE_INSENSITIVE":
        if isinstance(expr, str):
            return expr.lower()
        return expr.cast(nw.String).str.to_lowercase()
    if case_sensitivity == "CASE_INSENSITIVE_ASCII":
        if isinstance(expr, str):
            return expr.translate(_ASCII_TRANSLATION)
        folded = expr.cast(nw.String)
        for upper, lower in zip(_ASCII_UPPER_STR, _ASCII_LOWER_STR):
            folded = folded.str.replace_all(upper, lower, literal=True)
        return folded
    return expr


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
    def _prepare_literal_or_native_second(self, operands):
        second = (
            operands.raw_literal(
                1, "Narwhals pandas search substrings must be literals"
            )
            if self.dialect == "narwhals-pandas"
            else operands.raw_literal_or_native(1)
        )
        return [operands.native(0), second] + [
            operands.native(index) for index in range(2, len(operands))
        ]

    def _prepare_optional_trim(self, operands):
        return [operands.native(0)] + (
            [
                operands.raw_literal(
                    1, "Narwhals trim character sets must be literals"
                )
            ]
            if len(operands) > 1
            else []
        )

    def _prepare_call_trim(self, operands):
        return self._prepare_optional_trim(operands)

    def _prepare_call_ltrim(self, operands):
        return self._prepare_optional_trim(operands)

    def _prepare_call_rtrim(self, operands):
        return self._prepare_optional_trim(operands)

    def _prepare_call_contains(self, operands):
        return self._prepare_literal_or_native_second(operands)

    def _prepare_call_starts_with(self, operands):
        return self._prepare_literal_or_native_second(operands)

    def _prepare_call_ends_with(self, operands):
        return self._prepare_literal_or_native_second(operands)

    def _prepare_call_replace(self, operands):
        replacement = (
            operands.raw_literal(
                2, "Narwhals pandas replacements must be literals"
            )
            if self.dialect == "narwhals-pandas"
            else operands.raw_literal_or_native(2)
        )
        return [
            operands.native(0),
            operands.raw_literal(
                1, "Narwhals replacement substrings must be literals"
            ),
            replacement,
        ] + [operands.native(index) for index in range(3, len(operands))]

    def _prepare_call_regexp_replace(self, operands):
        replacement = (
            operands.raw_literal(
                2, "Narwhals pandas regex replacements must be literals"
            )
            if self.dialect == "narwhals-pandas"
            else operands.raw_literal_or_native(2)
        )
        return [
            operands.native(0),
            operands.raw_literal(1, "Narwhals regex patterns must be literals"),
            replacement,
        ] + [operands.native(index) for index in range(3, len(operands))]

    def _prepare_call_substring(self, operands):
        prepared = [
            operands.native(0),
            operands.raw_literal(1, "Narwhals substring start must be a literal"),
        ]
        if len(operands) > 2:
            prepared.append(
                operands.raw_literal(2, "Narwhals substring length must be a literal")
            )
        return prepared

    def _prepare_call_lpad(self, operands):
        prepared = [
            operands.native(0),
            operands.raw_literal(1, "Narwhals padding length must be a literal"),
        ]
        if len(operands) > 2:
            prepared.append(
                operands.raw_literal(2, "Narwhals padding characters must be literals")
            )
        return prepared

    def _prepare_call_rpad(self, operands):
        prepared = [
            operands.native(0),
            operands.raw_literal(1, "Narwhals padding length must be a literal"),
        ]
        if len(operands) > 2:
            prepared.append(
                operands.raw_literal(2, "Narwhals padding characters must be literals")
            )
        return prepared

    def _prepare_call_left(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Narwhals left count must be a literal"),
        ]

    def _prepare_call_right(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Narwhals right count must be a literal"),
        ]

    def _prepare_call_count_substring(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Narwhals substring count pattern must be a literal"),
        ]

    def _prepare_call_like(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Narwhals LIKE pattern must be a literal"),
        ]

    def _prepare_call_string_split(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(
                1, "Narwhals split separators must be literals"
            ),
        ]


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
            char_set: Omit it or use UTF8 for native Narwhals behavior.
        Returns:
            Lowercase string.
        """
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Narwhals only supports UTF8 char_set. Omit char_set or use UTF8 "
                "for native Narwhals behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
            )
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
            char_set: Omit it or use UTF8 for native Narwhals behavior.
        Returns:
            Uppercase string.
        """
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Narwhals only supports UTF8 char_set. Omit char_set or use UTF8 "
                "for native Narwhals behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
            )
        return input.str.to_uppercase()

    def swapcase(
        self,
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
        """Swap case of characters (lowercase to uppercase and vice versa)."""
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "Mountainash Narwhals implementation of swapcase is unavailable.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE,
        )

    def capitalize(
        self,
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
        """Capitalize the first character of the input string."""
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "Mountainash Narwhals implementation of capitalize is unavailable.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE,
        )

    def title(
        self,
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
        """Convert to title case.

        Args:
            input: String expression.
            char_set: Omit it or use UTF8 for native Narwhals behavior.
        Returns:
            Title-cased string.

        Note:
            Maps to Narwhals str.to_titlecase(), matching Polars' documented
            non-article-aware simplification.
        """
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Narwhals only supports UTF8 char_set. Omit char_set or use UTF8 "
                "for native Narwhals behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE,
            )
        return input.str.to_titlecase()

    def initcap(
        self,
        input: NarwhalsExpr,
        /,
        char_set: Any = None,
    ) -> NarwhalsExpr:
        """Capitalize first character of each word.

        Args:
            input: String expression.
            char_set: Omit it or use UTF8 for native Narwhals behavior.
        Returns:
            String with each word capitalized.

        Note:
            Maps to Narwhals str.to_titlecase().
        """
        if char_set is not None and char_set != "UTF8":
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Narwhals only supports UTF8 char_set. Omit char_set or use UTF8 "
                "for native Narwhals behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP,
            )
        return input.str.to_titlecase()

    # =========================================================================
    # Trim and Pad Operations
    # =========================================================================

    def trim(
        self,
        input: NarwhalsExpr,
        /,
        characters: NarwhalsExpr | str = None,
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
        return input.str.strip_chars(characters)

    def ltrim(
        self,
        input: NarwhalsExpr,
        /,
        characters: NarwhalsExpr | str = None,
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
        return input.str.strip_chars(characters)

    def rtrim(
        self,
        input: NarwhalsExpr,
        /,
        characters: NarwhalsExpr | str = None,
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
        return input.str.strip_chars(characters)

    def lpad(
        self,
        input: NarwhalsExpr,
        /,
        length: NarwhalsExpr | int,
        characters: NarwhalsExpr | str = None,
    ) -> NarwhalsExpr:
        """Left-pad the input string to specified length."""
        fill = str(characters) if characters is not None else " "
        return input.str.pad_start(int(length), fill)

    def rpad(
        self,
        input: NarwhalsExpr,
        /,
        length: NarwhalsExpr | int,
        characters: NarwhalsExpr | str = None,
    ) -> NarwhalsExpr:
        """Right-pad the input string to specified length."""
        fill = str(characters) if characters is not None else " "
        return input.str.pad_end(int(length), fill)

    def center(
        self,
        input: NarwhalsExpr,
        /,
        length: NarwhalsExpr,
        character: NarwhalsExpr = None,
        padding: Any = None,
    ) -> NarwhalsExpr:
        """Center the input string by padding both sides."""
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "Mountainash Narwhals implementation of center is unavailable.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
        )

    # =========================================================================
    # Substring Operations
    # =========================================================================

    def substring(
        self,
        input: NarwhalsExpr,
        /,
        start: NarwhalsExpr | int,
        length: NarwhalsExpr | int = None,
        negative_start: Any = None,
    ) -> NarwhalsExpr:
        """Extract a substring.

        Args:
            input: String expression.
            start: Starting position (0-indexed for API consistency).
            length: Length of substring.
            negative_start: None or WRAP_FROM_END retains native negative-slice
                behavior; other negative-start modes are unavailable in this
                implementation.

        Returns:
            Substring expression.
        """
        if negative_start not in (None, "WRAP_FROM_END"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Mountainash Narwhals substring supports negative_start only as "
                "None or WRAP_FROM_END.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
            )
        if length is None:
            return input.str.slice(int(start))
        return input.str.slice(int(start), int(length))

    def left(
        self,
        input: NarwhalsExpr,
        /,
        count: NarwhalsExpr | int,
    ) -> NarwhalsExpr:
        """Extract count characters from the left."""
        return input.str.head(int(count))

    def right(
        self,
        input: NarwhalsExpr,
        /,
        count: NarwhalsExpr | int,
    ) -> NarwhalsExpr:
        """Extract count characters from the right."""
        return input.str.tail(int(count))

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
        substring: NarwhalsExpr | str,
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
        # input is always NarwhalsExpr (never str), unlike substring -- cast
        # narrows _nw_fold's Union return so mypy resolves `.str` here.
        folded_input = cast("NarwhalsExpr", _nw_fold(input, case_sensitivity))
        folded_substring = _nw_fold(substring, case_sensitivity)
        # A null-typed search operand short-circuits to a null result before
        # the native call rather than crashing (backlog item 61 precedent,
        # generalized here). Wrapped in nw.when(folded_input.is_null())
        # .then(nw.lit(None)).otherwise(nw.lit(None)) rather than a bare
        # nw.lit(None) -- narwhals-pandas does NOT broadcast a literal with
        # no column reference to the input's row count under .select()
        # (collapses to a single row regardless of input length -- backlog
        # item 82); wrapping the null result in a `when` whose CONDITION
        # references folded_input gives it a row-shape to broadcast
        # against, independent of the condition's truth value. A null
        # INPUT row is a narrower, separate, documented limitation on
        # narwhals-pandas/pandas specifically (see backlog item 80):
        # plain-numpy-backed pandas boolean columns have no null
        # representation, and wrapping the result in nw.when/then to force
        # one produces an object-dtype column of Python bool objects,
        # which silently breaks `~` elsewhere (Python bitwise-NOT on bool is
        # not logical negation: ~True == -2). Not fixable at this layer
        # without either regressing negation or forcing every narwhals-pandas
        # DataFrame onto a nullable dtype backend end-to-end.
        if folded_substring is None:
            return nw.when(folded_input.is_null()).then(nw.lit(None)).otherwise(nw.lit(None))
        return folded_input.str.contains(folded_substring)

    def starts_with(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr | str,
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
        folded_input = cast("NarwhalsExpr", _nw_fold(input, case_sensitivity))
        folded_substring = _nw_fold(substring, case_sensitivity)
        # See contains() above for the row-count-broadcast rationale
        # (backlog item 82) -- narwhals-pandas does not broadcast a bare
        # nw.lit(None) to the input's row count under .select().
        if folded_substring is None:
            return nw.when(folded_input.is_null()).then(nw.lit(None)).otherwise(nw.lit(None))
        return folded_input.str.starts_with(folded_substring)

    def ends_with(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr | str,
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
        folded_input = cast("NarwhalsExpr", _nw_fold(input, case_sensitivity))
        folded_substring = _nw_fold(substring, case_sensitivity)
        # See contains() above for the row-count-broadcast rationale
        # (backlog item 82) -- narwhals-pandas does not broadcast a bare
        # nw.lit(None) to the input's row count under .select().
        if folded_substring is None:
            return nw.when(folded_input.is_null()).then(nw.lit(None)).otherwise(nw.lit(None))
        return folded_input.str.ends_with(folded_substring)

    def strpos(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Return the position of the first occurrence of substring (1-indexed).

        This Mountainash Narwhals implementation is unavailable.
        """
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "Mountainash Narwhals implementation of strpos is unavailable.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
        )

    def count_substring(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr | str,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Return the number of non-overlapping occurrences of substring.

        Args:
            input: String expression.
            substring: Literal substring to count. The category companion
                enforces the native scalar requirement before this method.
            case_sensitivity: Only None or CASE_SENSITIVE is supported.

        Returns:
            Count of occurrences.

        Note:
            This implementation computes non-overlapping matches via length
            arithmetic: (len(input) - len(input with every occurrence
            removed)) / len(substring), matching Polars'
            str.count_matches(literal=True) semantics, including its
            len(input) + 1 convention for an empty substring.

            A null literal substring short-circuits to a null result
            before the native call rather than crashing on `len(None)`
            (backlog item 80 precedent). Wrapped in `nw.when(input.is_null())
            .then(nw.lit(None)).otherwise(nw.lit(None))` rather than a bare
            `nw.lit(None)` -- narwhals-pandas does NOT broadcast a literal
            with no column reference to the input's row count under
            `.select()` (verified empirically: collapses to a single row
            regardless of input length); wrapping the null result in a
            `when` whose CONDITION references `input` gives it a row-shape
            to broadcast against, independent of the condition's truth
            value. Case sensitivity is not lowered by this implementation.
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Mountainash Narwhals count_substring supports case_sensitivity "
                "only as None or CASE_SENSITIVE.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
            )
        if substring is None:
            return nw.when(input.is_null()).then(nw.lit(None)).otherwise(nw.lit(None))
        if substring == "":
            return input.str.len_chars() + 1
        removed = input.str.replace_all(substring, "", literal=True)
        return (input.str.len_chars() - removed.str.len_chars()) // len(substring)

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
        *input: NarwhalsExpr,
        null_handling: Any = None,
    ) -> NarwhalsExpr:
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
        return _nw_concat_fold(nw.lit(""), input)

    def concat_ws(
        self,
        separator: NarwhalsExpr,
        /,
        *string_arguments: NarwhalsExpr,
    ) -> NarwhalsExpr:
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
        return nw.when(separator.is_null()).then(nw.lit(None)).otherwise(
            _nw_concat_fold(separator, string_arguments)
        )

    def replace(
        self,
        input: NarwhalsExpr,
        /,
        substring: NarwhalsExpr | str,
        replacement: NarwhalsExpr | str,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Replace all occurrences of substring with replacement.

        Args:
            input: String expression.
            substring: Substring to replace.
            replacement: Replacement string.
            case_sensitivity: Only None or CASE_SENSITIVE is supported.

        Returns:
            String with replacements.
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Mountainash Narwhals replace supports case_sensitivity only as "
                "None or CASE_SENSITIVE.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
            )
        # Substrait `replace` is literal substring substitution (regex is the
        # separate `regexp_replace`). replace_all defaults to literal=False, so
        # a regex metacharacter in the pattern (e.g. ".") would match wrongly.
        return input.str.replace_all(substring, replacement, literal=True)

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
        match: NarwhalsExpr | str,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """SQL LIKE pattern matching (% and _ wildcards).

        The SQL-LIKE -> regex conversion is Python-side and the category
        companion supplies its required literal pattern.

        Args:
            input: String expression.
            match: SQL LIKE pattern (literal string).
            case_sensitivity: Only None or CASE_SENSITIVE is supported.

        Returns:
            Boolean expression.
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Mountainash Narwhals like supports case_sensitivity only as "
                "None or CASE_SENSITIVE.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
            )
        # Convert SQL LIKE pattern to regex
        like_pattern = match.replace("%", "\x00PERCENT\x00").replace("_", "\x00UNDERSCORE\x00")
        regex_pattern = re.escape(like_pattern)
        regex_pattern = regex_pattern.replace("\x00PERCENT\x00", ".*").replace("\x00UNDERSCORE\x00", ".")
        regex_pattern = f"^{regex_pattern}$"
        return input.str.contains(regex_pattern)

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
        """Extract substring matching regex pattern."""
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "Mountainash Narwhals implementation of regexp_match_substring is "
            "unavailable.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
        )

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
        pattern: NarwhalsExpr | str,
        replacement: NarwhalsExpr | str,
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
            position: Starting position; only 1 or omission is supported.
            occurrence: Only 0 (all matches) or omission is supported.
            case_sensitivity: Only CASE_SENSITIVE or omission is supported.
            multiline: Only MULTILINE_DISABLED or omission is supported.
            dotall: Only DOTALL_DISABLED or omission is supported.

        Returns:
            String with replacements.
        """
        if (
            position not in (None, 1)
            or occurrence not in (None, 0)
            or case_sensitivity not in (None, "CASE_SENSITIVE")
            or multiline not in (None, "MULTILINE_DISABLED")
            or dotall not in (None, "DOTALL_DISABLED")
        ):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "The Mountainash Narwhals backend supports regex replacement only "
                "from position 1, for all occurrences, with default regex flags.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            )
        return input.str.replace_all(pattern, replacement)

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
            separator must be a literal -- gated via a LITERAL_ONLY
            CapabilityFact (NW-STR-21); narwhals's str.split(by: str)
            cannot accept an Expr at all, confirmed 2026-08-13 (raises
            TypeError even for an Expr-wrapped literal, not just a dynamic
            column reference). narwhals-pandas additionally requires a
            pyarrow-backed series -- a storage-dependent limitation, not an
            intrinsic gap, so it's enriched via a MATERIALIZE_RESIDUE fact
            (NW-STR-22) rather than gated at build time (a pyarrow-backed
            pandas DataFrame genuinely works).
        """
        return self._call_with_expr_support(
            lambda: input.str.split(separator),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SPLIT,
            separator=separator,
        )

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
            Narwhals has no regex-split primitive at the pinned version --
            gated as a family-wide WILDCARD_PARAM UNSUPPORTED
            CapabilityFact (NW-STR-20).
        """
        from mountainash.core.types import BackendCapabilityError
        raise BackendCapabilityError(
            "Narwhals has no regex-split primitive (str.split is "
            "literal-only, no method accepts a regex pattern). Use a "
            "Polars backend, or ibis-duckdb/ibis-polars (literal pattern) "
            "for regex split.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
        )
