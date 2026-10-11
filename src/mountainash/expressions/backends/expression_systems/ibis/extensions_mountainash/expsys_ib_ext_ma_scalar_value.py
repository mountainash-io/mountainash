"""SQL-native Ibis lowering for value-domain classification and projection."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import ibis

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarValueExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr


class MountainAshIbisScalarValueExpressionSystem(
    IbisBaseExpressionSystem,
    MountainAshScalarValueExpressionSystemProtocol["IbisValueExpr"],
):
    """Lower known Ibis domains without materializing or inspecting Python rows."""

    def value_kind(self, x: IbisValueExpr, /) -> IbisValueExpr:
        """Return a row-shaped original-domain label with SQL NULL first."""
        operand = self.operand_type("x")
        logical_kind = operand.logical_kind
        if operand.storage_kind == "sql_dynamic":
            return self._dynamic_value_kind(x, logical_kind)
        return self._typed_value_kind(x, logical_kind)

    def boolean_value(
        self,
        x: IbisValueExpr,
        /,
        *,
        source: Literal["boolean", "binary_number", "finite_number"] = "boolean",
    ) -> IbisValueExpr:
        """Project one selected Boolean domain as a nullable SQL expression."""
        operand = self.operand_type("x")
        logical_kind = operand.logical_kind
        if operand.storage_kind == "sql_dynamic":
            return self._dynamic_boolean_value(x, logical_kind, source)
        return self._typed_boolean_value(x, logical_kind, source)

    def text_value(self, x: IbisValueExpr, /) -> IbisValueExpr:
        """Preserve text only; all other domains yield a row-shaped string NULL."""
        operand = self.operand_type("x")
        logical_kind = operand.logical_kind
        if operand.storage_kind == "sql_dynamic" and logical_kind not in {
            "boolean",
            "other",
        }:
            storage = x.typeof()
            return ibis.ifelse(
                x.isnull(),
                self._null_like(x, "string"),
                ibis.ifelse(
                    storage == "text", x.cast("string"), self._null_like(x, "string")
                ),
            )
        if logical_kind == "text":
            return ibis.ifelse(x.isnull(), self._null_like(x, "string"), x)
        return self._null_like(x, "string")

    def decimal_cast(
        self,
        x: IbisValueExpr,
        /,
        *,
        precision: int,
        scale: int,
        rounding: str,
        failure_behavior: str,
    ) -> IbisValueExpr:
        """Exact decimal cast: one native rounding of the value the author wrote.

        The engine's own text-to-decimal cast parses and rounds the original text once, so no
        intermediate can round first. The two Ibis backends disagree on how that cast breaks an
        exact tie (DuckDB away from zero, Polars to even), so exact ties are resolved from the
        text instead of the engine: the pattern matches plain decimal text only, and any other
        text (exponents included) takes the engine's own rounding.

        ``to_zero`` truncates on the decimal: it parses into a 64-bit decimal, rounds natively and
        steps back one unit when that rounded away from zero. The parse keeps ``17 - p + s``
        fractional digits (falling back to 8 where DuckDB's own parse returns nothing for valid exponent
        text), so ``17 - p`` digits beyond the target scale are exact; past that the parse rounds first
        (documented).

        Invalid text raises under ``"throw"`` and becomes null under ``"null"``. Integer-part
        overflow raises under both, because the narrowing to the target is a strict cast.
        """
        from decimal import Decimal

        import ibis.expr.datatypes as dt

        target = dt.Decimal(precision, scale)
        # Floats convert by their shortest string form; text is trimmed and "_" removed.
        # re_replace, not replace: Ibis' replace removes only the first match on the Polars backend.
        text = x.cast("string").strip().re_replace("_", "")

        def truncated_to_scale(parsed):
            """Truncate toward zero on the decimal: round, then step back one unit if that rounded away."""
            rounded = parsed.round(scale)
            unit = ibis.literal(Decimal(1).scaleb(-scale), type=dt.Decimal(18, scale))
            zero = ibis.literal(Decimal(0), type=dt.Decimal(2, 0))
            stepped = ibis.ifelse(parsed < zero, rounded + unit, rounded - unit)
            return ibis.ifelse(rounded.abs() > parsed.abs(), stepped, rounded)

        if rounding == "to_zero":
            # Keep as many fractional digits as the 64-bit width allows beside the target's integers, so an
            # already-representable value is never touched. DuckDB's own parse returns null for some valid
            # exponent text at a large scale, so where the wide parse is null the parse falls back to scale 8.
            fraction = 18 - (precision - scale) - 1
            wide = text.try_cast(dt.Decimal(18, fraction))
            if fraction > 8:
                narrow = text.try_cast(dt.Decimal(18, 8))
                converted = ibis.ifelse(wide.notnull(), truncated_to_scale(wide), truncated_to_scale(narrow))
            else:
                converted = truncated_to_scale(wide)
        else:
            parsed = text.try_cast(dt.Decimal(18, scale))
            converted = parsed
            # An exact tie is resolved from the truncated text, not from the engine's tie rule.
            tie = text.re_search(rf"^[+-]?[0-9]*\.[0-9]{{{scale}}}50*$")
            # A tie may have no integer digit (".5", "-.5"). That digit is a zero: the retained digit at
            # scale 0 is then "0", and the kept prefix gains a "0" so that it parses as a number.
            no_integer = ~text.re_search(r"^[+-]?[0-9]")
            kept_pattern = r"([0-9])\.50*$" if scale == 0 else rf"\.[0-9]{{{scale - 1}}}([0-9])50*$"
            kept_text = text.re_extract(kept_pattern, 1)
            if scale == 0:
                # No digit before the point (".5") is a zero. DuckDB returns "" for no match and Ibis-Polars
                # null, so both are normalised first. The digit is only read where `tie` holds.
                kept_text = ibis.coalesce(kept_text.nullif(""), ibis.literal("0"))
            kept = kept_text.cast("int64")
            prefix = text.re_extract(rf"^[+-]?[0-9]*(?:\.[0-9]{{0,{scale}}})?", 0)
            sign = ibis.ifelse(text.startswith("-"), "-", "")
            unsigned = ibis.ifelse(text.startswith("-") | text.startswith("+"), prefix.substr(1), prefix)
            truncated = ibis.ifelse(no_integer, sign + "0" + unsigned, prefix).try_cast(dt.Decimal(18, scale))
            unit = ibis.literal(Decimal(1).scaleb(-scale), type=dt.Decimal(18, scale))
            away = ibis.ifelse(text.startswith("-"), truncated - unit, truncated + unit)
            if rounding == "half_away_from_zero":
                tie_value = away
            else:  # half_to_even: step away from zero only when the last kept digit is odd
                tie_value = ibis.ifelse(kept % 2 == 1, away, truncated)
            converted = ibis.ifelse(tie, tie_value, converted)

        # The parse is non-strict so that the two reasons a row can fail to parse can be told apart.
        # Whether the text is a finite number is decided by its shape (digits, one point, an exponent),
        # never by a float parse: that overflows to infinity for a huge finite number, which is then
        # indistinguishable from the text "inf". nan, infinity and anything else are invalid text. A
        # finite number the parse cannot hold is out of range and always raises; text that is not a
        # number raises under "throw" and stays null under "null".
        unparsed = converted.isnull() & text.notnull()
        is_number = text.re_search(r"^[+-]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][+-]?[0-9]+)?$")
        must_fail = unparsed if failure_behavior == "throw" else unparsed & is_number
        # The failure is forced by a strict cast whose *input* is masked: only rows that must fail see a
        # character no number can contain (the error names the value). Some engines evaluate a strict
        # cast for constants whatever the condition, so the condition must change the input, not skip it.
        forced = ibis.ifelse(must_fail, text + "!", ibis.literal("0")).cast(dt.Decimal(18, scale))
        converted = ibis.ifelse(must_fail, forced, converted)
        # Narrowing to the target is strict, so a value that does not fit raises under both behaviours.
        return converted.cast(target)

    def _typed_value_kind(self, x: IbisValueExpr, logical_kind: str) -> IbisValueExpr:
        label = {
            "boolean": "boolean",
            "integer": "integer",
            "float": "float",
            "text": "text",
        }.get(logical_kind, "unsupported")
        if logical_kind == "null":
            label = "absent"
        return ibis.ifelse(x.isnull(), ibis.literal("absent"), ibis.literal(label))

    def _dynamic_value_kind(self, x: IbisValueExpr, logical_kind: str) -> IbisValueExpr:
        # SQLite logical Boolean is semantically Boolean even though it stores 0/1
        # as INTEGER. Known out-of-domain logical types remain unsupported; a
        # sql_dynamic ``null`` descriptor is ambiguous and must inspect storage.
        if logical_kind == "boolean":
            return self._typed_value_kind(x, logical_kind)
        if logical_kind == "other":
            return self._typed_value_kind(x, logical_kind)

        storage = x.typeof()
        return ibis.cases(
            (x.isnull(), ibis.literal("absent")),
            (storage == "integer", ibis.literal("integer")),
            (storage == "real", ibis.literal("float")),
            (storage == "text", ibis.literal("text")),
            else_=ibis.literal("unsupported"),
        )

    def _typed_boolean_value(
        self, x: IbisValueExpr, logical_kind: str, source: str
    ) -> IbisValueExpr:
        if source == "boolean":
            if logical_kind == "boolean":
                return ibis.ifelse(x.isnull(), self._null_like(x, "boolean"), x)
            return self._null_like(x, "boolean")
        if logical_kind == "integer":
            return self._integer_boolean_value(x, source)
        if logical_kind == "float":
            return self._float_boolean_value(x, source)
        return self._null_like(x, "boolean")

    def _dynamic_boolean_value(
        self, x: IbisValueExpr, logical_kind: str, source: str
    ) -> IbisValueExpr:
        if logical_kind == "boolean":
            return self._typed_boolean_value(x, logical_kind, source)
        if logical_kind == "other" or source == "boolean":
            return self._null_like(x, "boolean")

        storage = x.typeof()
        is_integer = storage == "integer"
        is_float = storage == "real"
        integer = x.cast("int64")
        floating = x.cast("float64")
        null = self._null_like(x, "boolean")
        if source == "binary_number":
            return ibis.ifelse(
                x.isnull(),
                null,
                ibis.ifelse(
                    is_integer,
                    self._binary_number_value(integer),
                    ibis.ifelse(is_float, self._binary_number_value(floating), null),
                ),
            )
        return ibis.ifelse(
            x.isnull(),
            null,
            ibis.ifelse(
                is_integer,
                integer != 0,
                ibis.ifelse(is_float, self._float_finite_value(floating), null),
            ),
        )

    def _integer_boolean_value(self, x: IbisValueExpr, source: str) -> IbisValueExpr:
        if source == "binary_number":
            return self._binary_number_value(x)
        return ibis.ifelse(x.isnull(), self._null_like(x, "boolean"), x != 0)

    def _float_boolean_value(self, x: IbisValueExpr, source: str) -> IbisValueExpr:
        if source == "binary_number":
            return self._binary_number_value(x)
        return self._float_finite_value(x)

    def _binary_number_value(self, x: IbisValueExpr) -> IbisValueExpr:
        null = self._null_like(x, "boolean")
        return ibis.ifelse(
            x.isnull(),
            null,
            ibis.ifelse(x == 0, ibis.literal(False), ibis.ifelse(x == 1, ibis.literal(True), null)),
        )

    def _float_finite_value(self, x: IbisValueExpr) -> IbisValueExpr:
        """Use the Task 1 verified strict infinity bounds, not ``isnan``/``isinf``."""
        null = self._null_like(x, "boolean")
        finite = (x < float("inf")) & (x > -float("inf"))
        return ibis.ifelse(x.isnull(), null, ibis.ifelse(finite, x != 0, null))

    @staticmethod
    def _null_like(x: IbisValueExpr, dtype: str) -> IbisValueExpr:
        """Return a typed NULL retaining the operand's scalar/column shape."""
        null = ibis.null().cast(dtype)
        return ibis.ifelse(x.isnull(), null, null)
