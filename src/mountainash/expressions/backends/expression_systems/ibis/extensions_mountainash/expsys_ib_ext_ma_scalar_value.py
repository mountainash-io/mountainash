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
