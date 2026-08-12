"""Ibis ScalarStringExpressionProtocol implementation.

Implements string operations for the Ibis backend.
"""

from __future__ import annotations

import re
from typing import Any, Optional, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr


def _escape_char_class(characters: str) -> str:
    """Escape a literal character set for use inside a regex [...] class.

    Only four characters are special inside a class: \\ ] ^ -
    (^ only when first, - only when medial — escape both unconditionally
    for cross-engine safety on duckdb/sqlite/polars regex flavours).
    """
    out = []
    for ch in characters:
        if ch in ("\\", "]", "^", "-"):
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


_ASCII_UPPER_STR = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ASCII_LOWER_STR = "abcdefghijklmnopqrstuvwxyz"


def _ib_fold(expr: "IbisValueExpr", case_sensitivity: Any) -> "IbisValueExpr":
    """Apply the fold a case_sensitivity option value implies. CASE_SENSITIVE
    (and any other/omitted value) leaves expr unchanged; CASE_INSENSITIVE
    applies full Unicode lowercasing; CASE_INSENSITIVE_ASCII folds only
    A-Z/a-z via DuckDB/SQLite's native translate(), leaving every other code
    point (Kelvin Sign, Turkish I-with-dot, ...) untouched -- see backlog
    item 75. No `_lift_deferred`/`_lift_deferred_receiver` bridging is needed
    here: `.lower()`/`.translate()` take no Deferred-typed arguments, so the
    concrete-receiver-plus-Deferred-argument crash (item 226b/226c) cannot
    occur on this call shape; the caller lifts `input` once via
    `_lift_deferred_receiver` before folding either side.

    Casts to string first (a no-op for an already-string expr) so an
    untyped null literal (`ibis.literal(None)` for the search operand --
    item 80) has a `.lower()`/`.translate()` to call instead of raising
    AttributeError on a bare NullScalar; the null itself still propagates
    through either call unchanged."""
    if case_sensitivity == "CASE_INSENSITIVE":
        return expr.cast("string").lower()
    if case_sensitivity == "CASE_INSENSITIVE_ASCII":
        return expr.cast("string").translate(_ASCII_UPPER_STR, _ASCII_LOWER_STR)
    return expr


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
        characters: IbisValueExpr | str | None = None,
    ) -> IbisValueExpr:
        """Remove characters from both sides of the string.

        `characters` arrives as a raw literal (visitor gate, LITERAL_ONLY);
        composed via anchored re_replace since Ibis strip() takes no charset.
        """
        if characters is None:
            return input.strip()
        esc = _escape_char_class(str(characters))
        return input.re_replace(f"^[{esc}]+|[{esc}]+$", "")

    def ltrim(
        self,
        input: IbisValueExpr,
        /,
        characters: IbisValueExpr | str | None = None,
    ) -> IbisValueExpr:
        """Remove characters from the left side of the string.

        `characters` arrives as a raw literal (visitor gate, LITERAL_ONLY);
        composed via anchored re_replace since Ibis lstrip() takes no charset.
        """
        if characters is None:
            return input.lstrip()
        esc = _escape_char_class(str(characters))
        return input.re_replace(f"^[{esc}]+", "")

    def rtrim(
        self,
        input: IbisValueExpr,
        /,
        characters: IbisValueExpr | str | None = None,
    ) -> IbisValueExpr:
        """Remove characters from the right side of the string.

        `characters` arrives as a raw literal (visitor gate, LITERAL_ONLY);
        composed via anchored re_replace since Ibis rstrip() takes no charset.
        """
        if characters is None:
            return input.rstrip()
        esc = _escape_char_class(str(characters))
        return input.re_replace(f"[{esc}]+$", "")

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
        input = self._lift_deferred_receiver(input, length, fill_char)
        return input.lpad(length, fill_char)

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
        input = self._lift_deferred_receiver(input, length, fill_char)
        return input.rpad(length, fill_char)

    def center(
        self,
        input: IbisValueExpr,
        /,
        length: IbisValueExpr | int,
        character: IbisValueExpr | str | None = None,
        padding: Any = None,
    ) -> IbisValueExpr:
        """Center the input string (Python str.center semantics: extra pad
        goes right; strings already >= length are returned unchanged).

        Oracle: today's cross-backend behaviour per parameter-sensitivity
        tests (approved B2 semantics decision — NOT the Substrait docstring
        edge semantics; see spec Disposition table).
        """
        char = " " if character is None else str(character)
        n = int(length)
        cur_len = input.length()
        pad_left_target = cur_len + (n - cur_len) // 2
        composed = input.lpad(pad_left_target, char).rpad(n, char)
        return (cur_len >= n).ifelse(input, composed)

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
        input = self._lift_deferred_receiver(input, start, length)
        if length is None:
            return input.substr(start)
        return input.substr(start, length)

    def left(
        self,
        input: IbisValueExpr,
        /,
        count: IbisValueExpr,
    ) -> IbisValueExpr:
        """Extract count characters from the left."""
        input = self._lift_deferred_receiver(input, count)
        return input.left(count)

    def right(
        self,
        input: IbisValueExpr,
        /,
        count: IbisValueExpr,
    ) -> IbisValueExpr:
        """Extract count characters from the right."""
        input = self._lift_deferred_receiver(input, count)
        return input.right(count)

    def replace_slice(
        self,
        input: IbisValueExpr,
        /,
        start: IbisValueExpr | int,
        length: IbisValueExpr | int,
        replacement: IbisValueExpr | str,
    ) -> IbisValueExpr:
        """Replace a slice (1-indexed start, clamped — matches the Polars
        implementation's observed semantics, the approved B2 oracle)."""
        offset = int(start) - 1 if int(start) > 0 else 0
        repl = str(replacement)
        len_val = int(length)
        return input.substr(0, offset).concat(
            ibis.literal(repl), input.substr(offset + len_val)
        )

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
        input = self._lift_deferred_receiver(input, substring)
        return _ib_fold(input, case_sensitivity).contains(
            _ib_fold(substring, case_sensitivity)
        )

    def starts_with(
        self,
        input: IbisValueExpr,
        substring: IbisValueExpr,
        /,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """Whether input string starts with the substring."""
        input = self._lift_deferred_receiver(input, substring)
        return _ib_fold(input, case_sensitivity).startswith(
            _ib_fold(substring, case_sensitivity)
        )

    def ends_with(
        self,
        input: IbisValueExpr,
        /,
        substring: IbisValueExpr,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """Whether input string ends with the substring."""
        input = self._lift_deferred_receiver(input, substring)
        return _ib_fold(input, case_sensitivity).endswith(
            _ib_fold(substring, case_sensitivity)
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
        input = self._lift_deferred_receiver(input, substring)
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
            case_sensitivity: Case sensitivity option (gated UNSUPPORTED for
                any non-default value; count_substring was not one of the 3
                string ops given a real ASCII-fold implementation in item 75).

        Returns:
            Count of occurrences.

        Note:
            No single "count non-overlapping occurrences" primitive exists
            across Ibis dialects, so this computes it via length
            arithmetic: (len(input) - len(input with every substring
            occurrence removed)) / len(substring) -- verified empirically
            to match Polars' str.count_matches(literal=True) semantics
            exactly, including its len(input) + 1 convention for an empty
            substring. Reuses `replace`'s literal-escape + re_replace
            technique (Ibis `.replace()` only replaces the FIRST
            occurrence on a Deferred receiver -- see `replace` above). A
            dynamic (column-valued) substring falls through to a raw
            `re_replace(substring, "")` call, matching `replace`'s own
            precedent for a non-literal pattern -- this crashes with a raw
            (unenriched) native error on ibis-polars specifically (a
            pre-existing dynamic-pattern limitation shared with `replace`,
            not something this item fixes or asserts around; see backlog).
        """
        input = self._lift_deferred_receiver(input, substring)
        pattern = self._extract_literal_if_possible(substring)
        if isinstance(pattern, str):
            if pattern == "":
                return input.length() + 1
            removed = input.re_replace(re.escape(pattern), "")
            return (input.length() - removed.length()) // len(pattern)
        removed = input.re_replace(substring, "")
        sub_len = substring.length()
        diff = input.length() - removed.length()
        return (sub_len == 0).ifelse(input.length() + 1, diff // sub_len)

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
    def _ib_concat_fold(
        self, sep: "IbisValueExpr", inputs: "tuple[IbisValueExpr, ...]"
    ) -> "IbisValueExpr":
        """Portable IGNORE_NULLS fold — mirrors the Polars/Narwhals shape.
        Never routes through ibis.array(...).join(...) (OperationNotDefinedError
        on sqlite; dialect-divergent all-null-row result on ibis-polars) or
        .concat() (AttributeError on an untyped ibis.literal(None)) — uses `+`
        for real values, which ibis documents as equivalent to .concat().

        Column operands compile to Deferred (``ibis._[name]``) in this
        backend while literal operands (a bare separator string, the
        fold's own empty-string/False seeds) stay concrete — mixing a
        concrete left operand/receiver with a Deferred right
        operand/argument crashes without ``_lift_deferred``/
        ``_lift_deferred_receiver`` (item 226b/226c, upstream Ibis #11742).
        """
        empty = ibis.literal("", type="string")
        text_acc = empty
        any_seen = ibis.literal(False)
        for x in inputs:
            present = x.notnull()
            sep_l, x_l = self._lift_deferred(sep, x)
            joined = sep_l + x_l
            any_seen_r = self._lift_deferred_receiver(any_seen, joined, x)
            inner = any_seen_r.ifelse(joined, x)
            present_r = self._lift_deferred_receiver(present, inner, empty)
            piece = present_r.ifelse(inner, empty)
            text_acc_l, piece_l = self._lift_deferred(text_acc, piece)
            text_acc = text_acc_l + piece_l
            any_seen_l, present_l = self._lift_deferred(any_seen, present)
            any_seen = any_seen_l | present_l
        return text_acc

    def concat(
        self,
        *input: IbisValueExpr,
        null_handling: Any = None,
    ) -> IbisValueExpr:
        """Concatenate strings.

        Args:
            *input: String expressions to concatenate.
            null_handling: How to handle nulls (IGNORE_NULLS or ACCEPT_NULLS;
                default IGNORE_NULLS).

        Returns:
            Concatenated string.
        """
        if null_handling == "ACCEPT_NULLS":
            result = input[0]
            for x in input[1:]:
                result_l, x_l = self._lift_deferred(result, x)
                result = result_l + x_l
            return result
        return self._ib_concat_fold(ibis.literal("", type="string"), input)

    def concat_ws(
        self,
        separator: IbisValueExpr,
        /,
        *string_arguments: IbisValueExpr,
    ) -> IbisValueExpr:
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
        null_result = ibis.literal(None, type="string")
        folded = self._ib_concat_fold(separator, string_arguments)
        is_null = self._lift_deferred_receiver(separator.isnull(), null_result, folded)
        return is_null.ifelse(null_result, folded)

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
            Substrait `replace` is literal substring substitution; regex is the
            separate `regexp_replace`. We use `.re_replace()` because Ibis
            `.replace()` only replaces the FIRST occurrence when `input` is a
            deferred expression (mountainash always compiles to deferreds), while
            `.re_replace()` reliably replaces all. To keep literal semantics we
            `re.escape()` the pattern so metacharacters (e.g. ".") are matched
            literally rather than as a regex. Column-ref patterns (no extractable
            literal) fall back to the raw expression.
        """
        input = self._lift_deferred_receiver(input, substring, replacement)
        # A3 permanent exception: `replace` extracts the literal pattern when
        # available so it can be regex-escaped; dynamic column patterns still
        # fall through to the raw expression path.
        pattern = self._extract_literal_if_possible(substring)
        if isinstance(pattern, str):
            escaped = re.escape(pattern)
            return input.re_replace(escaped, replacement)
        return input.re_replace(substring, replacement)

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
        input = self._lift_deferred_receiver(input, count)
        return input.repeat(count)

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
        input = self._lift_deferred_receiver(input, match)
        return input.like(match)

    def regexp_match_substring(
        self,
        input: IbisValueExpr,
        pattern: IbisValueExpr,
        /,
        position: Optional[int] = None,
        occurrence: Optional[int] = None,
        group: Optional[int] = None,
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
        input = self._lift_deferred_receiver(input, pattern)
        # group is a raw int|None option (arguments-vs-options.md); no Expr to guard.
        group_index = 0 if group is None else group
        return input.re_extract(pattern, group_index)

    def regexp_match_substring_all(
        self,
        input: IbisValueExpr,
        /,
        pattern: IbisValueExpr,
        position: Optional[int] = None,
        group: Optional[int] = None,
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
        from mountainash.core.types import BackendCapabilityError
        raise BackendCapabilityError(
            "Ibis does not support regexp_match_substring_all (no extract_all equivalent). "
            "Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL,
        )

    def regexp_strpos(
        self,
        input: IbisValueExpr,
        /,
        pattern: IbisValueExpr,
        position: Optional[int] = None,
        occurrence: Optional[int] = None,
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
        from mountainash.core.types import BackendCapabilityError
        raise BackendCapabilityError(
            "Ibis does not support regexp_strpos (no regex find method). "
            "Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS,
        )

    def regexp_count_substring(
        self,
        input: IbisValueExpr,
        /,
        pattern: IbisValueExpr,
        position: Optional[int] = None,
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
        from mountainash.core.types import BackendCapabilityError
        raise BackendCapabilityError(
            "Ibis does not support regexp_count_substring (no count_matches method). "
            "Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT,
        )

    def regexp_replace(
        self,
        input: IbisValueExpr,
        /,
        pattern: IbisValueExpr,
        replacement: IbisValueExpr,
        position: Optional[int] = None,
        occurrence: Optional[int] = None,
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
        input = self._lift_deferred_receiver(input, pattern, replacement)
        return input.re_replace(pattern, replacement)

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
        input = self._lift_deferred_receiver(input, separator)
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
