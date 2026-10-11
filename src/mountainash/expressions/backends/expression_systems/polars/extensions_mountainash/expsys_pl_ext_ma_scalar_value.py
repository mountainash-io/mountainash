"""Polars lowering for Mountainash scalar value classification."""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import polars as pl

from mountainash.core.value_classification import (
    boolean_value as scalar_boolean_value,
)
from mountainash.core.value_classification import (
    text_value as scalar_text_value,
)
from mountainash.core.value_classification import (
    value_kind as scalar_value_kind,
)
from mountainash.expressions.backends.expression_systems.polars.base import (
    PolarsBaseExpressionSystem,
)
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarValueExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from mountainash.expressions.types import PolarsExpr


class MountainAshPolarsScalarValueExpressionSystem(
    PolarsBaseExpressionSystem,
    MountainAshScalarValueExpressionSystemProtocol[pl.Expr],
):
    """Polars implementation of original-value classification and projections."""

    def value_kind(self, x: PolarsExpr, /) -> PolarsExpr:
        """Return a null-first label for the original scalar domain."""
        operand = self.operand_type("x")
        if operand.storage_kind == "polars_object":
            return _object_map(x, lambda value: scalar_value_kind(value).value, pl.String)
        return _kind_for_typed_operand(x, operand.logical_kind)

    def boolean_value(
        self,
        x: PolarsExpr,
        /,
        *,
        source: str = "boolean",
    ) -> PolarsExpr:
        """Project one explicitly selected Boolean-producing domain."""
        operand = self.operand_type("x")
        if operand.storage_kind == "polars_object":
            return _object_map(
                x,
                lambda value: scalar_boolean_value(value, source=source),
                pl.Boolean,
            )

        kind = operand.logical_kind
        if source == "boolean" and kind == "boolean":
            return x
        if source == "binary_number" and kind in {"integer", "float"}:
            return _binary_number_candidate(x)
        if source == "finite_number":
            if kind == "integer":
                return x.ne(0)
            if kind == "float":
                return pl.when(x.is_finite()).then(x.ne(0)).otherwise(
                    pl.lit(None, dtype=pl.Boolean)
                )
        return _null_like(x, pl.Boolean)

    def text_value(self, x: PolarsExpr, /) -> PolarsExpr:
        """Preserve only actual text as a nullable Polars string projection."""
        operand = self.operand_type("x")
        if operand.storage_kind == "polars_object":
            return _object_map(x, scalar_text_value, pl.String)
        if operand.logical_kind == "text":
            return x
        return _null_like(x, pl.String)

    def decimal_cast(
        self,
        x: PolarsExpr,
        /,
        *,
        precision: int,
        scale: int,
        rounding: str,
        failure_behavior: str,
    ) -> PolarsExpr:
        """Exact decimal cast: one native rounding of the value the author wrote.

        The engine's own text-to-decimal cast parses and rounds the original text once (half to
        even on Polars), so no intermediate can round first. ``to_zero`` parses into a wide decimal
        and truncates natively, so the engine interprets the text (exponents included). The tie
        correction for ``half_away_from_zero`` reads plain decimal text only; any other text,
        exponents included, simply takes the engine's own rounding.

        Invalid text raises under ``"throw"`` and becomes null under ``"null"``; integer-part
        overflow always raises, because the final cast is strict in both modes.
        """
        target = pl.Decimal(precision, scale)
        # Floats convert by their shortest string form; text is trimmed and "_" removed.
        text = x.cast(pl.String).str.strip_chars().str.replace_all("_", "", literal=True)
        # Whether the text is a finite number is decided by its shape (digits, one point, an exponent),
        # never by a float parse: that overflows to infinity for a huge finite number, which is then
        # indistinguishable from the text "inf". nan, infinity and anything else are invalid text.
        # It is only consulted for rows the parse returned null for, so valid input never pays for it.
        shape = r"^[+-]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][+-]?[0-9]+)?$"

        def resolved(parsed: PolarsExpr, wide: pl.Decimal) -> PolarsExpr:
            """Return ``parsed``, raising for the rows that must fail.

            A finite number the decimal parse cannot hold is out of range and always raises; text that
            is not a number raises under ``"throw"`` and stays null under ``"null"``. The failure is
            forced by a strict cast whose *input* is masked, so only the rows that must fail see a
            value that cannot parse. (A strict cast under ``when/then`` is evaluated for constants
            whatever the condition, so the condition must change the cast input, not skip the cast.)
            """
            unparsed = parsed.is_null() & text.is_not_null()
            must_fail = unparsed if failure_behavior == "throw" else unparsed & text.str.contains(shape)
            forced = pl.when(must_fail).then(text + pl.lit("!")).otherwise(pl.lit("0")).cast(wide, strict=True)
            return pl.when(must_fail).then(forced).otherwise(parsed)

        if rounding == "to_zero":
            # Plain decimal text of any length is cut after `scale` fractional digits and parsed: exact,
            # because no digit past the cut is ever rounded. Any other text (exponents) goes to the
            # engine: a wide parse then a native truncate, exact while the value fits the 38-digit parse.
            wide = pl.Decimal(38, 38 - (precision - scale) - 3)
            engine = resolved(text.cast(wide, strict=False), wide).truncate(scale)
            plain = text.str.contains(r"^[+-]?[0-9]*\.?[0-9]*$") & text.str.contains(r"[0-9]")
            cut = text.str.extract(rf"^[+-]?[0-9]*(?:\.[0-9]{{0,{scale}}})?", 0).cast(pl.Decimal(38, scale), strict=False)
            if scale == 0:
                # At scale 0 the cut of ".99" is "." (no digits), which does not parse, and that is the only
                # case that truncates to zero by itself. Decided by the text (a leading-point fraction),
                # never by the parse failing: an integer too wide for the parse fails too, and must reach
                # the overflow path, not become zero.
                leading_point = text.str.contains(r"^[+-]?\.[0-9]*$") & text.str.contains(r"[0-9]")
                cut = cut.fill_null(pl.when(leading_point).then(pl.lit(0).cast(pl.Decimal(38, 0))))
            return pl.when(plain & cut.is_not_null()).then(cut).otherwise(engine).cast(target, strict=True)
        # Parse at the target scale into the widest decimal: the engine rounds once here, and the
        # strict narrowing below raises for a value that does not fit the target, in both modes.
        wide = pl.Decimal(38, scale)
        converted = resolved(text.cast(wide, strict=False), wide).cast(target, strict=True)
        if rounding == "half_away_from_zero":
            # The native cast rounds an exact tie to even; half-away differs exactly when the even
            # neighbour is the lower one, i.e. when the last kept digit is even. The patterns match
            # plain decimal text only, so other text keeps the engine's rounding.
            tie = text.str.contains(rf"^[+-]?[0-9]*\.[0-9]{{{scale}}}50*$")
            # At scale 0 the kept digit is the one before the point; ".5" has none, which is a zero. The
            # digit is only read where `tie` holds, so defaulting it elsewhere changes nothing.
            if scale == 0:
                kept_digit = text.str.extract(r"([0-9])\.50*$", 1).fill_null("0")
            else:
                kept_digit = text.str.extract(rf"\.[0-9]{{{scale - 1}}}([0-9])50*$", 1)
            kept = kept_digit.cast(pl.Int8, strict=False)
            ulp = pl.lit(Decimal(1).scaleb(-scale), dtype=target)
            away = pl.when(text.str.starts_with("-")).then(converted - ulp).otherwise(converted + ulp)
            # Decimal arithmetic widens the type; cast back so the result type is exact and a corrected
            # value that no longer fits (9999999.999 + one ulp) raises like any other overflow.
            converted = pl.when(tie & (kept % 2 == 0)).then(away).otherwise(converted).cast(target, strict=True)
        return converted


def _kind_for_typed_operand(x: PolarsExpr, logical_kind: str) -> PolarsExpr:
    label = {
        "boolean": "boolean",
        "integer": "integer",
        "float": "float",
        "text": "text",
        "null": "absent",
    }.get(logical_kind, "unsupported")
    return pl.when(x.is_null()).then(pl.lit("absent")).otherwise(pl.lit(label))


def _binary_number_candidate(x: PolarsExpr) -> PolarsExpr:
    return (
        pl.when(x.is_null())
        .then(pl.lit(None, dtype=pl.Boolean))
        .when(x.eq(0))
        .then(pl.lit(False))
        .when(x.eq(1))
        .then(pl.lit(True))
        .otherwise(pl.lit(None, dtype=pl.Boolean))
    )


def _null_like(x: PolarsExpr, dtype: pl.DataType | type[pl.DataType]) -> PolarsExpr:
    """Produce a typed null expression with the operand's row shape."""
    return pl.when(x.is_null()).then(pl.lit(None, dtype=dtype)).otherwise(
        pl.lit(None, dtype=dtype)
    )


def _object_map(
    x: PolarsExpr,
    projection: Callable[[object], object],
    dtype: pl.DataType | type[pl.DataType],
) -> PolarsExpr:
    """Apply shared scalar semantics to original Object values at execution time."""

    def project_batch(batch: pl.Series) -> pl.Series:
        return pl.Series(
            batch.name,
            [projection(batch[index]) for index in range(len(batch))],
            dtype=dtype,
        )

    return x.map_batches(
        project_batch,
        return_dtype=dtype,
        is_elementwise=True,
    )
