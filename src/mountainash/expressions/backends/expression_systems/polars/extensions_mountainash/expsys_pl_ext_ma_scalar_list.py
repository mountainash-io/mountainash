"""Polars backend for mountainash list operations."""
from __future__ import annotations

from typing import Any, FrozenSet, Optional
import polars as pl

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarListExpressionSystemProtocol
from mountainash.expressions.constants import CONST_TERNARY_LOGIC_VALUES
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.dtypes import TypeTarget
from .expsys_pl_ext_ma_scalar_struct import _invalid_nested
_T_TRUE = CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE
_T_UNKNOWN = CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN
_T_FALSE = CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE


class MountainAshPolarsScalarListExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarListExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of list operations."""
    def parse_list(
        self,
        x,
        /,
        *,
        item_type: str = "string",
        delimiter: str = ",",
        failure_behavior: str = "throw",
    ):
        values = x.str.split(delimiter)
        if item_type == "string":
            return values
        strict = failure_behavior != "null"
        if item_type == "boolean":
            normalized = (
                pl.element()
                .cast(pl.String, strict=False)
                .replace_strict(
                    {
                        "true": "1",
                        "True": "1",
                        "TRUE": "1",
                        "1": "1",
                        "false": "0",
                        "False": "0",
                        "FALSE": "0",
                        "0": "0",
                    },
                    default="__invalid__",
                    return_dtype=pl.String,
                )
            )
            parsed = values.list.eval(normalized.cast(pl.Int8, strict=strict).cast(pl.Boolean))
        else:
            dtype = {
                "integer": pl.Int64,
                "number": pl.Float64,
                "datetime": pl.Datetime,
                "date": pl.Date,
                "time": pl.Time,
            }[item_type]
            if item_type == "datetime":
                element = (
                    pl.element()
                    .str.to_datetime(strict=strict, time_zone="UTC")
                    .dt.replace_time_zone(None)
                )
            elif item_type == "date":
                element = pl.element().str.to_date(strict=strict)
            elif item_type == "time":
                element = pl.element().str.to_time(strict=strict)
            else:
                element = pl.element().cast(dtype, strict=strict)
            parsed = values.list.eval(element)
        if failure_behavior == "null":
            invalid = parsed.list.eval(pl.element().is_null()).list.any().fill_null(False)
            return pl.when(x.is_null()).then(None).when(invalid).then(None).otherwise(parsed)
        return parsed

    def cast_list_items(
        self,
        x,
        /,
        *,
        item_object_fields: tuple[FieldSpec, ...] = (),
        item_type: str | None = None,
        failure_behavior: str = "throw",
    ):
        if item_type is not None:
            from mountainash.core.dtypes import registry
            from mountainash.typespec.universal_types import parse_universal, to_canonical
            canonical = to_canonical(parse_universal(item_type))
            dtype = registry.to_native_schema(canonical, TypeTarget.POLARS)
            result = x.list.eval(pl.element().cast(dtype, strict=failure_behavior != "null"))
            if failure_behavior == "null":
                original_count = x.list.eval(pl.element().is_not_null()).list.sum()
                result_count = result.list.eval(pl.element().is_not_null()).list.sum()
                invalid = result_count < original_count
                return pl.when(x.is_null()).then(None).when(invalid).then(None).otherwise(result)
            return result
        field = FieldSpec(
            name="_items",
            type=UniversalType.ARRAY,
            item_object_fields=list(item_object_fields),
        )
        dtype = _resolve_field_native(field, TypeTarget.POLARS)
        result = x.cast(dtype, strict=failure_behavior != "null")
        if failure_behavior == "null":
            invalid = _invalid_nested(x, field)
            result = pl.when(x.is_null()).then(None).when(invalid).then(None).otherwise(result)
        return result

    def list_sum(self, x, /):
        return x.list.sum()

    def list_min(self, x, /):
        return x.list.min()

    def list_max(self, x, /):
        return x.list.max()

    def list_mean(self, x, /):
        return x.list.mean()

    def list_len(self, x, /):
        return x.list.len()

    def list_contains(self, x, /, item):
        return x.list.contains(item)

    def list_t_contains(
        self,
        x,
        /,
        item,
        *,
        item_unknown_values: Optional[FrozenSet[Any]] = None,
    ):
        """Ternary list-membership: UNKNOWN for null list / null or sentinel needle.

        A null needle is ALWAYS an UNKNOWN trigger (independent of the declared
        ``item_unknown_values`` sentinel set — the set only adds the equality
        terms for declared sentinels). Each sentinel comparison is wrapped with
        ``.fill_null(False)`` so a null item row never leaks SQL-null into the
        ``is_unknown`` accumulator (mirrors the same null-normalisation
        discipline the Task 5 membership kernel enforces).
        """
        # Unconditional UNKNOWN triggers: null list row OR null needle row.
        is_unknown = x.is_null() | item.is_null()
        if item_unknown_values:
            for val in item_unknown_values:
                # Skip None — already covered by item.is_null() above. Each
                # non-None sentinel becomes a null-safe equality term.
                if val is None:
                    continue
                is_unknown = is_unknown | (item == pl.lit(val)).fill_null(False)
        return (
            pl.when(is_unknown)
            .then(pl.lit(_T_UNKNOWN))
            .otherwise(
                pl.when(x.list.contains(item).fill_null(False))
                .then(pl.lit(_T_TRUE))
                .otherwise(pl.lit(_T_FALSE))
            )
        )

    def list_sort(self, x, /, *, descending: bool = False):
        return x.list.sort(descending=descending)

    def list_unique(self, x, /):
        return x.list.unique()

    def list_explode(self, x, /):
        return x.list.explode()

    def list_join(self, x, /, *, separator: str = ","):
        return x.list.join(separator)

    def list_get(self, x, /, *, index: int = 0):
        return x.list.get(index, null_on_oob=True)

    def list_all(self, x, /):
        return x.list.all()

    def list_any(self, x, /):
        return x.list.any()

    def list_drop_nulls(self, x, /):
        return x.list.drop_nulls()

    def list_median(self, x, /):
        return x.list.median()

    def list_std(self, x, /, *, ddof: int = 1):
        return x.list.std(ddof=ddof)

    def list_var(self, x, /, *, ddof: int = 1):
        return x.list.var(ddof=ddof)

    def list_n_unique(self, x, /):
        return x.list.n_unique()

    def list_count_matches(self, x, /, item):
        return x.list.count_matches(item)

    def list_item(self, x, /, *, index: int = 0):
        return x.list.get(index, null_on_oob=True)

    def list_reverse(self, x, /):
        return x.list.reverse()

    def list_head(self, x, /, n):
        return x.list.head(n)

    def list_tail(self, x, /, n):
        return x.list.tail(n)

    def list_slice(self, x, /, offset, *, length=None):
        return x.list.slice(offset, length)

    def list_gather(self, x, /, indices, *, null_on_oob=False):
        return x.list.gather(indices, null_on_oob=null_on_oob)

    def list_gather_every(self, x, /, n, *, offset=0):
        return x.list.gather_every(n, offset=offset)

    def list_shift(self, x, /, n):
        return x.list.shift(n)

    def list_diff(self, x, /, *, n=1, null_behavior="ignore"):
        return x.list.diff(n=n, null_behavior=null_behavior)

    def list_set_union(self, x, /, other):
        return x.list.set_union(other)

    def list_set_intersection(self, x, /, other):
        return x.list.set_intersection(other)

    def list_set_difference(self, x, /, other):
        return x.list.set_difference(other)

    def list_set_symmetric_difference(self, x, /, other):
        return x.list.set_symmetric_difference(other)

    def list_concat(self, x, /, other):
        return x.list.concat(other)

    def list_filter(self, x, /, mask):
        return x.list.filter(mask)

    def list_to_struct(self, x, /, *, n_field_strategy="first_non_null", fields=None, upper_bound=None):
        kwargs = {}
        if fields is not None:
            kwargs["fields"] = fields
        if upper_bound is not None:
            kwargs["upper_bound"] = upper_bound
        return x.list.to_struct(**kwargs)

    def list_to_array(self, x, /, *, width):
        return x.list.to_array(width)

    def list_arg_min(self, x, /):
        return x.list.arg_min()

    def list_arg_max(self, x, /):
        return x.list.arg_max()

    def list_sample(self, x, /, n=None, *, fraction=None, with_replacement=False, shuffle=False, seed=None):
        kwargs = {"with_replacement": with_replacement, "shuffle": shuffle}
        if n is not None:
            kwargs["n"] = n
        if fraction is not None:
            kwargs["fraction"] = fraction
        if seed is not None:
            kwargs["seed"] = seed
        return x.list.sample(**kwargs)

    def list_agg(self, x, /, expr):
        return x.list.agg(expr)
