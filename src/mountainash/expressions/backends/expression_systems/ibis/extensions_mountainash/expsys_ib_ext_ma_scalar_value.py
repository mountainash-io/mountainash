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
        """Exact decimal cast built only from casts, ``round`` and typed decimal literals.

        Ibis ``round`` has no mode: it follows the backend's own tie rule (DuckDB rounds
        half away from zero, Polars half to even). Exact ties are detected with decimal
        arithmetic and corrected one ulp, so every backend returns the requested mode.
        No floor/ceil, integer intermediates, division or modulo. Every literal is typed
        explicitly: DuckDB's default literal type is DECIMAL(18,3), Ibis only combines
        decimals when one type dominates both precision and scale, and Polars returns null
        when a decimal multiply result has precision == scale.
        """
        from decimal import Decimal

        import ibis.expr.datatypes as dt

        def decimal_literal(value: Decimal, literal_scale: int) -> IbisValueExpr:
            return ibis.literal(
                value, type=dt.Decimal(precision=min(38, literal_scale + 2), scale=literal_scale)
            )

        intermediate_precision = 18 if precision <= 16 else 38
        intermediate_scale = intermediate_precision - (precision - scale) - 1
        intermediate = dt.Decimal(intermediate_precision, intermediate_scale)

        # Floats convert by their shortest string form; text is trimmed and "_" removed.
        text = x.cast("string").strip().replace("_", "")
        parsed = (
            text.try_cast(intermediate)
            if failure_behavior == "null"
            else text.cast(intermediate)
        )
        rounded = parsed.round(scale).cast(dt.Decimal(intermediate_precision, scale))

        ulp = decimal_literal(Decimal(1).scaleb(-scale), scale)
        negative_ulp = decimal_literal(-Decimal(1).scaleb(-scale), scale)
        is_exact_tie = (parsed - rounded).abs() == decimal_literal(
            Decimal(5).scaleb(-(scale + 1)), scale + 1
        )
        # Parity of the rounded value's last digit without modulo: r is even iff r*0.5 has
        # no digit beyond `scale`.
        half = rounded.cast(dt.Decimal(intermediate_precision, scale + 1)) * ibis.literal(
            Decimal("0.5"), type=dt.Decimal(2, 1)
        )
        is_odd = half.round(scale) != half
        # Step away from zero by one ulp, selected by the sign of the INPUT (never r, which
        # can round to zero) and without multiplying by a sign (the Polars multiply bug).
        away = ibis.ifelse(parsed < decimal_literal(Decimal(0), 0), negative_ulp, ulp)

        if rounding == "half_to_even":
            result = ibis.ifelse(is_exact_tie & is_odd, rounded - away, rounded)
        elif rounding == "half_away_from_zero":
            result = ibis.ifelse(is_exact_tie & (rounded.abs() < parsed.abs()), rounded + away, rounded)
        else:  # to_zero
            result = ibis.ifelse(rounded.abs() > parsed.abs(), rounded - away, rounded)
        return result.cast(dt.Decimal(precision, scale))

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
