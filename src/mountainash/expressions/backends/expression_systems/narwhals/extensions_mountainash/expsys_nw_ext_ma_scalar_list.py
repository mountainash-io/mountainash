"""Narwhals backend for mountainash list operations."""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, FrozenSet, Optional

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarListExpressionSystemProtocol

from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.dtypes import TypeTarget

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr

class MountainAshNarwhalsScalarListExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarListExpressionSystemProtocol[nw.Expr]):
    def parse_list(
        self,
        x,
        /,
        *,
        item_type: str = "string",
        delimiter: str = ",",
        failure_behavior: str = "throw",
    ):
        return self._call_with_expr_support(
            lambda: self._parse_list_impl(
                x,
                item_type=item_type,
                delimiter=delimiter,
                failure_behavior=failure_behavior,
            ),
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
            item_type=item_type,
            failure_behavior=failure_behavior,
        )

    def _parse_list_impl(
        self,
        x,
        *,
        item_type: str,
        delimiter: str,
        failure_behavior: str,
    ):
        values = x.str.split(delimiter)
        if item_type == "string":
            return values
        if item_type == "boolean":
            import re

            escaped = re.escape(delimiter)
            normalized = x
            for tokens, replacement in (
                ("true|True|TRUE|1", "1"),
                ("false|False|FALSE|0", "0"),
            ):
                normalized = normalized.str.replace_all(
                    rf"(^|{escaped})({tokens})",
                    rf"${{1}}{replacement}",
                )
            return normalized.str.split(delimiter).cast(nw.List(nw.Int8)).cast(nw.List(nw.Boolean))
        target = {
            "integer": nw.Int64,
            "number": nw.Float64,
            "datetime": nw.Datetime,
            "date": nw.Date,
            "time": nw.Time,
        }[item_type]
        return values.cast(nw.List(target()))

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
            from mountainash.typespec.universal_types import parse_universal, to_canonical
            canonical = to_canonical(parse_universal(item_type))
            from mountainash.core.dtypes import registry
            dtype = registry.to_native_schema(canonical, TypeTarget.NARWHALS)
            return x.cast(nw.List(dtype))
        field = FieldSpec(name="_items", type=UniversalType.ARRAY, item_object_fields=list(item_object_fields))
        dtype = _resolve_field_native(field, TypeTarget.NARWHALS)
        return x.cast(dtype)

    def list_sum(self, x: NarwhalsExpr, /):
        return x.list.sum()

    def list_min(self, x: NarwhalsExpr, /):
        return x.list.min()

    def list_max(self, x: NarwhalsExpr, /):
        return x.list.max()

    def list_mean(self, x: NarwhalsExpr, /):
        return x.list.mean()

    def list_len(self, x: NarwhalsExpr, /):
        return x.list.len()

    def list_contains(self, x: NarwhalsExpr, /, item: Any):
        return x.list.contains(item)

    def list_t_contains(
        self,
        x: NarwhalsExpr,
        /,
        item: Any,
        *,
        item_unknown_values: Optional[FrozenSet[Any]] = None,
    ):
        T_TRUE = 1
        T_UNKNOWN = 0
        T_FALSE = -1

        is_unknown = x.is_null()
        if isinstance(item, nw.Expr):
            is_unknown = is_unknown | item.is_null()
            if item_unknown_values:
                for val in item_unknown_values:
                    if val is None:
                        continue
                    is_unknown = is_unknown | (item == nw.lit(val)).fill_null(False)
        else:
            if item is None:
                is_unknown = nw.lit(True)
            elif item_unknown_values and item in item_unknown_values:
                is_unknown = nw.lit(True)

        return (
            nw.when(is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(x.list.contains(item).fill_null(False))
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    def list_sort(self, x: NarwhalsExpr, /, *, descending: bool = False):
        return x.list.sort(descending=descending)

    def list_unique(self, x: NarwhalsExpr, /):
        return x.list.unique()

    def list_explode(self, x: NarwhalsExpr, /):
        raise BackendCapabilityError(
            "Narwhals does not support list.explode(). "
            "Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE,
        )

    def list_join(self, x: NarwhalsExpr, /, *, separator: str = ","):
        raise BackendCapabilityError(
            "Narwhals does not support list.join(). "
            "Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.JOIN,
        )

    def list_get(self, x: NarwhalsExpr, /, *, index: int = 0):
        return self._call_with_expr_support(
            lambda: x.list.get(index),
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.GET,
            index=index,
        )

    def list_median(self, x: NarwhalsExpr, /):
        return x.list.median()

    def list_all(self, x: NarwhalsExpr, /):
        raise BackendCapabilityError(
            "Narwhals does not support list.all(). Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ALL,
        )

    def list_any(self, x: NarwhalsExpr, /):
        raise BackendCapabilityError(
            "Narwhals does not support list.any(). Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ANY,
        )

    def list_drop_nulls(self, x: NarwhalsExpr, /):
        raise BackendCapabilityError(
            "Narwhals does not support list.drop_nulls(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS,
        )

    def list_std(self, x: NarwhalsExpr, /, *, ddof: int = 1):
        raise BackendCapabilityError(
            "Narwhals does not support list.std(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.STD,
        )

    def list_var(self, x: NarwhalsExpr, /, *, ddof: int = 1):
        raise BackendCapabilityError(
            "Narwhals does not support list.var(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.VAR,
        )

    def list_n_unique(self, x: NarwhalsExpr, /):
        raise BackendCapabilityError(
            "Narwhals does not support list.n_unique(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE,
        )

    def list_count_matches(self, x: NarwhalsExpr, /, item):
        raise BackendCapabilityError(
            "Narwhals does not support list.count_matches(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES,
        )

    def list_item(self, x: NarwhalsExpr, /, *, index: int = 0):
        raise BackendCapabilityError(
            "Narwhals does not support list.item(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ITEM,
        )

    def list_reverse(self, x: NarwhalsExpr, /):
        raise BackendCapabilityError(
            "Narwhals does not support list.reverse(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE,
        )

    def list_head(self, x: NarwhalsExpr, /, n):
        raise BackendCapabilityError(
            "Narwhals does not support list.head(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.HEAD,
        )

    def list_tail(self, x: NarwhalsExpr, /, n):
        raise BackendCapabilityError(
            "Narwhals does not support list.tail(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.TAIL,
        )

    def list_slice(self, x: NarwhalsExpr, /, offset, *, length=None):
        raise BackendCapabilityError(
            "Narwhals does not support list.slice(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SLICE,
        )

    def list_gather(self, x: NarwhalsExpr, /, indices, *, null_on_oob=False):
        raise BackendCapabilityError(
            "Narwhals does not support list.gather(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.GATHER,
        )

    def list_gather_every(self, x: NarwhalsExpr, /, n, *, offset=0):
        raise BackendCapabilityError(
            "Narwhals does not support list.gather_every(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY,
        )

    def list_shift(self, x: NarwhalsExpr, /, n):
        raise BackendCapabilityError(
            "Narwhals does not support list.shift(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT,
        )

    def list_diff(self, x: NarwhalsExpr, /, *, n=1, null_behavior="ignore"):
        raise BackendCapabilityError(
            "Narwhals does not support list.diff(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.DIFF,
        )

    def list_set_union(self, x: NarwhalsExpr, /, other):
        raise BackendCapabilityError(
            "Narwhals does not support list.set_union(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_UNION,
        )

    def list_set_intersection(self, x: NarwhalsExpr, /, other):
        raise BackendCapabilityError(
            "Narwhals does not support list.set_intersection(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_INTERSECTION,
        )

    def list_set_difference(self, x: NarwhalsExpr, /, other):
        raise BackendCapabilityError(
            "Narwhals does not support list.set_difference(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE,
        )

    def list_set_symmetric_difference(self, x: NarwhalsExpr, /, other):
        raise BackendCapabilityError(
            "Narwhals does not support list.set_symmetric_difference(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_SYMMETRIC_DIFFERENCE,
        )

    def list_concat(self, x: NarwhalsExpr, /, other):
        raise BackendCapabilityError(
            "Narwhals does not support list.concat(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.CONCAT,
        )

    def list_filter(self, x: NarwhalsExpr, /, mask):
        raise BackendCapabilityError(
            "Narwhals does not support list.filter(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.FILTER,
        )

    def list_to_struct(self, x: NarwhalsExpr, /, *, n_field_strategy="first_non_null", fields=None, upper_bound=None):
        raise BackendCapabilityError(
            "Narwhals does not support list.to_struct(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT,
        )

    def list_to_array(self, x: NarwhalsExpr, /, *, width):
        raise BackendCapabilityError(
            "Narwhals does not support list.to_array(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY,
        )

    def list_arg_min(self, x: NarwhalsExpr, /):
        raise BackendCapabilityError(
            "Narwhals does not support list.arg_min(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN,
        )

    def list_arg_max(self, x: NarwhalsExpr, /):
        raise BackendCapabilityError(
            "Narwhals does not support list.arg_max(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX,
        )

    def list_sample(self, x: NarwhalsExpr, /, n=None, *, fraction=None, with_replacement=False, shuffle=False, seed=None):
        raise BackendCapabilityError(
            "Narwhals does not support list.sample(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SAMPLE,
        )

    def list_agg(self, x: NarwhalsExpr, /, expr):
        raise BackendCapabilityError(
            "Narwhals does not support list.agg(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.AGG,
        )
