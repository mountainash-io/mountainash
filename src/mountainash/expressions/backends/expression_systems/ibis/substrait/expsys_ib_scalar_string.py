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
_ASCII_FOLD_TABLE = str.maketrans(_ASCII_UPPER_STR, _ASCII_LOWER_STR)


def _ib_fold(expr: "IbisValueExpr | str | None", case_sensitivity: Any) -> "IbisValueExpr":
    """Fold raw search literals before constructing native literal expressions.

    Ibis-Polars cannot consume Lowercase(Literal(...)) as a search pattern.
    Dynamic/native operands retain native folding; null literals stay typed.
    """
    if isinstance(expr, str):
        if case_sensitivity == "CASE_INSENSITIVE":
            expr = expr.lower()
        elif case_sensitivity == "CASE_INSENSITIVE_ASCII":
            expr = expr.translate(_ASCII_FOLD_TABLE)
        return ibis.literal(expr)
    if expr is None:
        return ibis.literal(None, type="string")
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
    def _prepare_call_trim(self, operands):
        return [operands.native(0)] + (
            [operands.raw_literal(1, "Ibis trim character sets must be literals")]
            if len(operands) > 1
            else []
        )

    def _prepare_call_ltrim(self, operands):
        return [operands.native(0)] + (
            [operands.raw_literal(1, "Ibis ltrim character sets must be literals")]
            if len(operands) > 1
            else []
        )

    def _prepare_call_rtrim(self, operands):
        return [operands.native(0)] + (
            [operands.raw_literal(1, "Ibis rtrim character sets must be literals")]
            if len(operands) > 1
            else []
        )

    def _prepare_call_center(self, operands):
        prepared = [
            operands.native(0),
            operands.raw_literal(1, "Ibis center length must be a literal"),
        ]
        if len(operands) > 2:
            prepared.append(
                operands.raw_literal(2, "Ibis center padding character must be a literal")
            )
        return prepared

    def _prepare_call_replace_slice(self, operands):
        return [
            operands.native(0),
            operands.raw_literal(1, "Ibis slice start must be a literal"),
            operands.raw_literal(2, "Ibis slice length must be a literal"),
            operands.raw_literal(3, "Ibis slice replacement must be a literal"),
        ]

    def _prepare_literal_pattern(self, operands, literal_message: str):
        pattern = (
            operands.raw_literal(1, literal_message)
            if self.dialect == "ibis-polars"
            else operands.raw_literal_or_native(1)
        )
        return [operands.native(0), pattern] + [
            operands.native(index) for index in range(2, len(operands))
        ]

    def _prepare_call_replace(self, operands):
        return self._prepare_literal_pattern(
            operands, "Ibis Polars replace substring must be a literal"
        )

    def _prepare_call_count_substring(self, operands):
        return self._prepare_literal_pattern(
            operands, "Ibis Polars substring count pattern must be a literal"
        )

    def _prepare_call_regexp_replace(self, operands):
        return self._prepare_literal_pattern(
            operands, "Ibis Polars regex replacement pattern must be a literal"
        )

    def _prepare_call_regexp_match_substring(self, operands):
        return self._prepare_literal_pattern(
            operands, "Ibis Polars regex match pattern must be a literal"
        )

    def _prepare_call_string_split(self, operands):
        return self._prepare_literal_pattern(
            operands, "Ibis Polars split separator must be a literal"
        )

    def _prepare_call_regexp_string_split(self, operands):
        return self._prepare_literal_pattern(
            operands, "Ibis Polars regex split pattern must be a literal"
        )

    def _prepare_search_pattern(self, operands):
        pattern = operands.raw_literal_or_native(1)
        if pattern is not None and not isinstance(pattern, str):
            pattern = operands.native(1)
        return [operands.native(0), pattern]

    def _prepare_call_contains(self, operands):
        return self._prepare_search_pattern(operands)

    def _prepare_call_starts_with(self, operands):
        return self._prepare_search_pattern(operands)

    def _prepare_call_ends_with(self, operands):
        return self._prepare_search_pattern(operands)


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
            char_set: ASCII_ONLY on SQLite, UTF8 elsewhere; omit for native behavior.

        Returns:
            Lowercase string.
        """
        if char_set is not None and char_set != (
            "ASCII_ONLY" if self.dialect == "ibis-sqlite" else "UTF8"
        ):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this character-set mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
            )
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
            char_set: ASCII_ONLY on SQLite, UTF8 elsewhere; omit for native behavior.

        Returns:
            Uppercase string.
        """
        if char_set is not None and char_set != (
            "ASCII_ONLY" if self.dialect == "ibis-sqlite" else "UTF8"
        ):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this character-set mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
            )
        return input.upper()

    def swapcase(
        self,
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
        """Reject swapcase without a Mountainash Ibis implementation."""
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "The Mountainash Ibis backend does not implement swapcase.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE,
        )

    def capitalize(
        self,
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
        """Capitalize the first character of the input string.

        Args:
            input: String expression.
            char_set: ASCII_ONLY on SQLite, UTF8 elsewhere; omit for native behavior.

        Returns:
            String with first character capitalized.
        """
        if char_set is not None and char_set != (
            "ASCII_ONLY" if self.dialect == "ibis-sqlite" else "UTF8"
        ):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this character-set mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE,
            )
        return input.capitalize()

    def title(
        self,
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
        """Reject title without a Mountainash Ibis implementation."""
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "The Mountainash Ibis backend does not implement title.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TITLE,
        )

    def initcap(
        self,
        input: IbisValueExpr,
        /,
        char_set: Any = None,
    ) -> IbisValueExpr:
        """Reject initcap without a Mountainash Ibis implementation."""
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            "The Mountainash Ibis backend does not implement initcap.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP,
        )

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

        The category companion supplies a raw character set before native
        compilation; Ibis strip() itself takes no charset.
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

        The category companion supplies a raw character set before native
        compilation; Ibis lstrip() itself takes no charset.
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

        The category companion supplies a raw character set before native
        compilation; Ibis rstrip() itself takes no charset.
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
        """Center the input string with extra padding on the right.

        Omit padding or use RIGHT. Strings already at least length characters
        long are returned unchanged. Python str.center has different odd-width
        padding behavior; this implementation does not claim that equivalence.
        """
        if padding not in (None, "RIGHT"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Ibis center only implements RIGHT padding.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CENTER,
            )
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
            negative_start: Only WRAP_FROM_END or omission is supported.

        Returns:
            Substring expression.
        """
        if negative_start not in (None, "WRAP_FROM_END"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "The Mountainash Ibis backend supports only wrapped negative substring starts.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING,
            )
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
        substring: IbisValueExpr | str | None,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """Whether the input string contains the substring."""
        if (
            case_sensitivity == "CASE_INSENSITIVE" and self.dialect == "ibis-sqlite"
            or case_sensitivity == "CASE_INSENSITIVE_ASCII" and self.dialect == "ibis-polars"
        ):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this search case-folding mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            )
        input = self._lift_deferred_receiver(input, substring)
        return _ib_fold(input, case_sensitivity).contains(
            _ib_fold(substring, case_sensitivity)
        )

    def starts_with(
        self,
        input: IbisValueExpr,
        substring: IbisValueExpr | str | None,
        /,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """Whether input string starts with the substring."""
        if (
            case_sensitivity == "CASE_INSENSITIVE" and self.dialect == "ibis-sqlite"
            or case_sensitivity == "CASE_INSENSITIVE_ASCII" and self.dialect == "ibis-polars"
        ):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this search case-folding mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH,
            )
        input = self._lift_deferred_receiver(input, substring)
        return _ib_fold(input, case_sensitivity).startswith(
            _ib_fold(substring, case_sensitivity)
        )

    def ends_with(
        self,
        input: IbisValueExpr,
        /,
        substring: IbisValueExpr | str | None,
        case_sensitivity: Any = None,
    ) -> IbisValueExpr:
        """Whether input string ends with the substring."""
        if (
            case_sensitivity == "CASE_INSENSITIVE" and self.dialect == "ibis-sqlite"
            or case_sensitivity == "CASE_INSENSITIVE_ASCII" and self.dialect == "ibis-polars"
        ):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this search case-folding mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH,
            )
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
            case_sensitivity: Only CASE_SENSITIVE or omission is supported.

        Returns:
            Position (1-indexed), or 0 if not found.
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "This Ibis string operation supports only CASE_SENSITIVE or omission.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS,
            )
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
            case_sensitivity: Only CASE_SENSITIVE or omission is supported.

        Returns:
            Count of occurrences.

        Note:
            No single "count non-overlapping occurrences" primitive exists
            across Ibis dialects, so this computes it via length
            arithmetic: (len(input) - len(input with every substring
            occurrence removed)) / len(substring) -- verified empirically
            to match Polars' str.count_matches(literal=True) semantics
            exactly, including its len(input) + 1 convention for an empty
            substring.

            `_extract_literal_if_possible` returns exactly `None` ONLY for
            a compile-time-known null literal (never for a genuinely
            column-valued/Deferred substring, which it passes through
            unchanged) -- unambiguous, so a null pattern short-circuits
            to a null result directly, without ever calling `.replace()`.
            This is required, not just tidy: on ibis-polars specifically,
            `.replace()` with a null pattern raises `pattern cannot be
            'null' in 'replace' expression`, while a null pattern's result
            is unconditionally null regardless of what `.replace()` would
            have done.

            A literal (build-time-known) NON-null substring is
            regex-escaped and removed via `re_replace` (mirrors
            `replace`'s own literal-escape technique above -- see its
            docstring for why `.replace()` alone isn't used there).
            ibis-polars requires that build-time literal during backend
            operand preparation. On ibis-duckdb and ibis-sqlite, a genuinely
            dynamic (column-valued) substring instead uses Ibis's plain,
            non-regex `.replace()`: verified empirically (with a Deferred
            receiver and a Deferred/column pattern) to remove EVERY literal
            occurrence, not just the first, so no regex-escaping is needed
            or possible for a value only known at execution time.
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "This Ibis string operation supports only CASE_SENSITIVE or omission.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING,
            )
        input = self._lift_deferred_receiver(input, substring)
        pattern = self._extract_literal_if_possible(substring)
        if pattern is None:
            null_result = ibis.literal(None, type="int64")
            return self._lift_deferred_receiver(null_result, input)
        if isinstance(pattern, str):
            if pattern == "":
                return input.length() + 1
            removed = input.re_replace(re.escape(pattern), "")
            return (input.length() - removed.length()) // len(pattern)
        removed = input.replace(substring, "")
        sub_len = substring.length()
        diff = input.length() - removed.length()
        cond = self._lift_deferred_receiver(
            sub_len == 0, input.length() + 1, diff // sub_len
        )
        return cond.ifelse(input.length() + 1, diff // sub_len)

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
            case_sensitivity: Only CASE_SENSITIVE or omission is supported.

        Returns:
            String with replacements.

        Note:
            Substrait `replace` is literal substring substitution; regex is the
            separate `regexp_replace`. We use `.re_replace()` because Ibis
            `.replace()` only replaces the FIRST occurrence when `input` is a
            deferred expression (mountainash always compiles to deferreds), while
            `.re_replace()` reliably replaces all. To keep literal semantics we
            `re.escape()` the pattern so metacharacters (e.g. ".") are matched
            literally rather than as a regex. ibis-polars requires a
            build-time literal substring during backend operand preparation;
            other Ibis dialects retain the column-ref raw-expression path.
        """
        if case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "This Ibis string operation supports only CASE_SENSITIVE or omission.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE,
            )
        input = self._lift_deferred_receiver(input, substring, replacement)
        # Extract a literal pattern when available so it can be regex-escaped.
        # Other Ibis dialects may pass a dynamic column pattern through raw.
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
            case_sensitivity: Only CASE_SENSITIVE or omission is supported.

        Returns:
            Boolean expression.
        """
        if self.dialect == "ibis-polars" or case_sensitivity not in (None, "CASE_SENSITIVE"):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Ibis-Polars LIKE is unavailable; other Ibis engines support only CASE_SENSITIVE.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LIKE,
            )
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
            position: Starting position; only None or 1 is supported.
            occurrence: Match occurrence; only None or 1 is supported.
            group: Capture group number.
            case_sensitivity: Explicitly supports only CASE_SENSITIVE.
            multiline: Explicitly supports only MULTILINE_DISABLED.
            dotall: Explicitly supports only DOTALL_DISABLED.

        Returns:
            Matched substring or null.
        """
        from mountainash.core.types import BackendCapabilityError
        if (
            position not in (None, 1)
            or occurrence not in (None, 1)
            or case_sensitivity not in (None, "CASE_SENSITIVE")
            or multiline not in (None, "MULTILINE_DISABLED")
            or dotall not in (None, "DOTALL_DISABLED")
        ):
            raise BackendCapabilityError(
                "Ibis regexp_match_substring supports only position=None/1, "
                "occurrence=None/1, case_sensitivity=CASE_SENSITIVE, "
                "multiline=MULTILINE_DISABLED, and dotall=DOTALL_DISABLED.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            )
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
            position: Starting position; only None or 1 is supported.
            occurrence: Replacement occurrence; only None or 0 (replace all) is supported.
            case_sensitivity: Explicitly supports only CASE_SENSITIVE.
            multiline: Explicitly supports only MULTILINE_DISABLED.
            dotall: Explicitly supports only DOTALL_DISABLED.

        Returns:
            String with replacements.
        """
        from mountainash.core.types import BackendCapabilityError
        if (
            position not in (None, 1)
            or occurrence not in (None, 0)
            or case_sensitivity not in (None, "CASE_SENSITIVE")
            or multiline not in (None, "MULTILINE_DISABLED")
            or dotall not in (None, "DOTALL_DISABLED")
        ):
            raise BackendCapabilityError(
                "Ibis regexp_replace supports only position=None/1, "
                "occurrence=None/0 (replace all), case_sensitivity=CASE_SENSITIVE, "
                "multiline=MULTILINE_DISABLED, and dotall=DOTALL_DISABLED.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE,
            )
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
            case_sensitivity: Explicitly supports only CASE_SENSITIVE.
            multiline: Explicitly supports only MULTILINE_DISABLED.
            dotall: Explicitly supports only DOTALL_DISABLED.

        Returns:
            List of strings.
        """
        from mountainash.core.types import BackendCapabilityError
        if self.dialect == "ibis-sqlite":
            raise BackendCapabilityError(
                "Ibis SQLite does not support regexp_string_split because it has no "
                "RegexSplit compilation rule.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
            )
        if (
            case_sensitivity not in (None, "CASE_SENSITIVE")
            or multiline not in (None, "MULTILINE_DISABLED")
            or dotall not in (None, "DOTALL_DISABLED")
        ):
            raise BackendCapabilityError(
                "Ibis regexp_string_split supports only "
                "case_sensitivity=CASE_SENSITIVE, multiline=MULTILINE_DISABLED, "
                "and dotall=DOTALL_DISABLED.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT,
            )
        input = self._lift_deferred_receiver(input, pattern)
        return input.re_split(pattern)
