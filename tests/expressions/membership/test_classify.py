"""Tests for closed build-time membership classifier (Task 3).

Two halves:
1. **Branch-table tests** — per spec §4.1 structural disambiguation rule.
2. **Property tests** — disjointness + exhaustiveness over a representative
   object matrix (every input falls into exactly one outcome; no input
   falls into an "unknown" outcome).
"""
from __future__ import annotations

import enum
from collections import namedtuple
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from types import GeneratorType

import pytest

import mountainash as ma
from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.membership.classify import (
    _is_container,
    _is_expression,
    _is_unsupported_iterable,
    classify_members,
)
from mountainash.expressions.membership.errors import (
    BareExpressionCollectionError,
    EmptyMembershipError,
    MembershipArgumentError,
    NativeExprMemberError,
    NestedCollectionError,
    UnsupportedCollectionError,
)


# =========================================================================
# §4.1 Branch-Table Tests
# =========================================================================


class TestEmpty:
    """No collection at all (or an empty container) → EmptyMembershipError."""

    def test_no_args_raises(self) -> None:
        with pytest.raises(EmptyMembershipError) as exc_info:
            classify_members(())
        assert exc_info.value.value is None

    def test_empty_list_raises(self) -> None:
        with pytest.raises(EmptyMembershipError) as exc_info:
            classify_members(([],))
        assert exc_info.value.value == []

    def test_empty_tuple_raises(self) -> None:
        with pytest.raises(EmptyMembershipError):
            classify_members(((),))

    def test_empty_set_raises(self) -> None:
        with pytest.raises(EmptyMembershipError):
            classify_members((set(),))

    def test_empty_frozenset_raises(self) -> None:
        with pytest.raises(EmptyMembershipError):
            classify_members((frozenset(),))


class TestSingleBareExpression:
    """A single bare expression (MA or native) → BareExpressionCollectionError."""

    def test_ma_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError) as exc_info:
            classify_members((ma.col("x"),))
        assert isinstance(exc_info.value.value, BaseExpressionAPI)

    def test_ma_lit_scalar_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError) as exc_info:
            classify_members((ma.lit(5),))
        assert isinstance(exc_info.value.value, BaseExpressionAPI)

    def test_ma_lit_list_raises(self) -> None:
        """ma.lit([...]) is an MA expression → same as bare expr."""
        with pytest.raises(BareExpressionCollectionError):
            classify_members((ma.lit([1, 2, 3]),))

    def test_ma_t_col_raises(self) -> None:
        with pytest.raises(BareExpressionCollectionError):
            classify_members((ma.t_col("x"),))

    def test_polars_expr_raises(self) -> None:
        pytest.importorskip("polars")
        import polars as pl

        expr = pl.col("x")
        with pytest.raises(BareExpressionCollectionError) as exc_info:
            classify_members((expr,))
        # Value is the polars Expr that was passed
        assert exc_info.value.value is expr

    def test_narwhals_expr_raises(self) -> None:
        pytest.importorskip("narwhals")
        import narwhals as nw

        with pytest.raises(BareExpressionCollectionError):
            classify_members((nw.col("x"),))

    def test_ibis_expr_raises(self) -> None:
        pytest.importorskip("ibis")
        import ibis

        with pytest.raises(BareExpressionCollectionError):
            classify_members((ibis.literal(1),))

    def test_ibis_deferred_raises(self) -> None:
        pytest.importorskip("ibis")
        import ibis.common.deferred as idd

        with pytest.raises(BareExpressionCollectionError):
            classify_members((idd.Deferred("x"),))

    def test_error_message_mentions_list_contains(self) -> None:
        """Brief §12.7 / docstring requires migration guidance."""
        with pytest.raises(BareExpressionCollectionError) as exc_info:
            classify_members((ma.col("x"),))
        msg = str(exc_info.value)
        assert ".list.contains" in msg
        assert ".list.t_contains" in msg


class TestSingleScalarLiteral:
    """One bare scalar → 1-element list (case 4 / 1-element native set)."""

    def test_int(self) -> None:
        assert classify_members((5,)) == [5]

    def test_float(self) -> None:
        assert classify_members((3.14,)) == [3.14]

    def test_str(self) -> None:
        assert classify_members(("hello",)) == ["hello"]

    def test_bytes(self) -> None:
        assert classify_members((b"abc",)) == [b"abc"]

    def test_bool(self) -> None:
        assert classify_members((True,)) == [True]

    def test_none(self) -> None:
        assert classify_members((None,)) == [None]

    def test_decimal_accepted_in_list_form(self) -> None:
        """Out-of-table scalars are accepted as 1-element list (not in a set)."""
        d = Decimal("1.5")
        assert classify_members((d,)) == [d]

    def test_date_accepted_in_list_form(self) -> None:
        d = date(2026, 1, 1)
        assert classify_members((d,)) == [d]

    def test_datetime_accepted_in_list_form(self) -> None:
        dt = datetime(2026, 1, 1, 12, 0, 0)
        assert classify_members((dt,)) == [dt]

    def test_nan_accepted_in_list_form(self) -> None:
        """NaN is OK as a single scalar (only rejected in set/frozenset form)."""
        nan = float("nan")
        result = classify_members((nan,))
        assert len(result) == 1
        assert result[0] is nan

    def test_custom_object_accepted_as_scalar(self) -> None:
        class MyObj:
            pass

        obj = MyObj()
        assert classify_members((obj,)) == [obj]

    def test_numpy_scalar_accepted_in_list_form(self) -> None:
        pytest.importorskip("numpy")
        import numpy as np

        v = np.int64(5)
        result = classify_members((v,))
        assert result == [v]


class TestLiteralContainerFlattened:
    """Single list/tuple → flatten to items, preserve order, allow duplicates."""

    def test_list_flattens(self) -> None:
        assert classify_members(([1, 2, 3],)) == [1, 2, 3]

    def test_tuple_flattens(self) -> None:
        assert classify_members(((1, 2, 3),)) == [1, 2, 3]

    def test_list_preserves_duplicates(self) -> None:
        assert classify_members(([1, 2, 1, 2],)) == [1, 2, 1, 2]

    def test_list_preserves_mixed_types(self) -> None:
        assert classify_members(([1, "a", 3.14, True],)) == [1, "a", 3.14, True]

    def test_list_with_ma_expr_member_accepted(self) -> None:
        """MA expression as a member of a list is OK (OR-chain element)."""
        col = ma.col("y")
        result = classify_members(([1, col, 3],))
        assert result == [1, col, 3]

    def test_list_with_ma_lit_member_accepted(self) -> None:
        lit = ma.lit(5)
        result = classify_members(([1, lit, 3],))
        assert result == [1, lit, 3]

    def test_list_with_native_expr_member_rejected(self) -> None:
        """Native expression as a member → NativeExprMemberError (§12.7)."""
        pytest.importorskip("polars")
        import polars as pl

        expr = pl.col("x")
        with pytest.raises(NativeExprMemberError) as exc_info:
            classify_members(([1, expr],))
        assert exc_info.value.value is expr

    def test_list_with_nested_list_rejected(self) -> None:
        with pytest.raises(NestedCollectionError):
            classify_members(([1, [2, 3]],))

    def test_list_with_nested_tuple_rejected(self) -> None:
        with pytest.raises(NestedCollectionError):
            classify_members(([1, (2, 3)],))

    def test_list_with_nested_dict_rejected(self) -> None:
        with pytest.raises(NestedCollectionError):
            classify_members(([1, {"a": 1}],))

    def test_list_with_nested_set_rejected(self) -> None:
        with pytest.raises(NestedCollectionError):
            classify_members(([1, {2, 3}],))

    def test_list_with_nested_generator_rejected(self) -> None:
        def gen():
            yield 1

        with pytest.raises(NestedCollectionError):
            classify_members(([1, gen()],))


class TestSetCanonicalization:
    """set/frozenset → closed ordering table (bool,int,float,str,bytes)."""

    def test_int_set_sorted_ascending(self) -> None:
        result = classify_members(({3, 1, 2},))
        assert result == [1, 2, 3]

    def test_frozenset_sorted_ascending(self) -> None:
        result = classify_members((frozenset({3, 1, 2}),))
        assert result == [1, 2, 3]

    def test_str_set_sorted(self) -> None:
        result = classify_members(({"banana", "apple", "cherry"},))
        assert result == ["apple", "banana", "cherry"]

    def test_mixed_types_sort_by_table_order(self) -> None:
        """Sort key is (table_rank, value): bool < int < float < str < bytes.

        Note: the closed table's logical order is used (not alphabetical on
        type_name) — this is the order the brief specifies for the closed
        canonicalisation table (§12.4).
        """
        result = classify_members(({2, True, 1.5, "x", b"a"},))
        assert result == [True, 2, 1.5, "x", b"a"]

    def test_bool_before_int(self) -> None:
        """Table rank: bool (0) < int (1) regardless of value."""
        # {1, True} deduplicates to 1 element in Python (1 == True).
        # Use {True, 2} instead — distinct types, no dedup.
        result = classify_members(({True, 2},))
        assert result == [True, 2]

    def test_nan_in_set_rejected(self) -> None:
        with pytest.raises(UnsupportedCollectionError) as exc_info:
            classify_members(({float("nan")},))
        assert isinstance(exc_info.value.value, float)

    def test_nan_in_frozenset_rejected(self) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members((frozenset({float("nan")}),))

    def test_decimal_in_set_rejected(self) -> None:
        """Out-of-table types accepted only in list/tuple form."""
        with pytest.raises(UnsupportedCollectionError) as exc_info:
            classify_members(({Decimal("1.5")},))
        assert isinstance(exc_info.value.value, Decimal)

    def test_date_in_set_rejected(self) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members(({date(2026, 1, 1)},))

    def test_datetime_in_set_rejected(self) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members(({datetime(2026, 1, 1, 12, 0, 0)},))

    def test_enum_in_set_rejected(self) -> None:
        class Color(enum.Enum):
            RED = 1

        with pytest.raises(UnsupportedCollectionError):
            classify_members(({Color.RED},))

    def test_numpy_scalar_in_set_rejected(self) -> None:
        pytest.importorskip("numpy")
        import numpy as np

        with pytest.raises(UnsupportedCollectionError):
            classify_members(({np.int64(5)},))

    def test_none_in_set_rejected(self) -> None:
        """`None` is out-of-table (closed table is bool/int/float/str/bytes)
        and must be rejected in set/frozenset form alongside the other
        out-of-table types. `None` is accepted as a 1-element list (single
        bare scalar literal branch).
        """
        with pytest.raises(UnsupportedCollectionError) as exc_info:
            classify_members(({1, None},))
        assert exc_info.value.value is None

    def test_set_with_mixed_valid_and_invalid_rejected(self) -> None:
        """If any member is out-of-table, the set is rejected (closed table)."""
        with pytest.raises(UnsupportedCollectionError):
            classify_members(({1, 2, Decimal("1.5")},))

    def test_list_with_decimal_accepted(self) -> None:
        """List form is unconstrained — Decimal is fine in a list."""
        d = Decimal("1.5")
        assert classify_members(([1, d, 3],)) == [1, d, 3]

    def test_list_with_nan_accepted(self) -> None:
        """NaN is fine in a list — only rejected in set/frozenset."""
        nan = float("nan")
        result = classify_members(([1, nan],))
        assert len(result) == 2


class TestMultipleArgs:
    """2+ args → element-set (list of args), no flattening of nested containers."""

    def test_two_scalars(self) -> None:
        assert classify_members((1, 2)) == [1, 2]

    def test_three_scalars(self) -> None:
        assert classify_members((1, 2, 3)) == [1, 2, 3]

    def test_mixed_scalar_and_ma_expr(self) -> None:
        col = ma.col("y")
        assert classify_members((1, col, 3)) == [1, col, 3]

    def test_two_ma_exprs(self) -> None:
        a, b = ma.col("a"), ma.col("b")
        assert classify_members((a, b)) == [a, b]

    def test_multi_with_native_expr_member_rejected(self) -> None:
        pytest.importorskip("polars")
        import polars as pl

        with pytest.raises(NativeExprMemberError):
            classify_members((1, 2, pl.col("x")))

    def test_multi_with_nested_container_rejected(self) -> None:
        """Multi-arg case doesn't flatten — a list in args is a nested member."""
        with pytest.raises(NestedCollectionError):
            classify_members((1, [2, 3]))

    def test_multi_with_unsupported_iterable_rejected(self) -> None:
        def gen():
            yield 1

        with pytest.raises(NestedCollectionError):
            classify_members((1, gen()))

    def test_multi_with_empty_string_accepted(self) -> None:
        """str is a scalar, not a container or iterable."""
        assert classify_members(("a", "b")) == ["a", "b"]


# =========================================================================
# Unsupported-iterable Tests (Single-arg detection by type, not iter)
# =========================================================================


class TestSingleUnsupportedIterable:
    """Single arg of an unsupported-iterable type → UnsupportedCollectionError."""

    def test_namedtuple_rejected(self) -> None:
        """namedtuple is a tuple subclass; exact-type check excludes it."""
        NT = namedtuple("NT", ["a", "b"])
        nt = NT(1, 2)
        with pytest.raises(UnsupportedCollectionError) as exc_info:
            classify_members((nt,))
        assert exc_info.value.value is nt

    def test_list_subclass_rejected(self) -> None:
        class MyList(list):
            pass

        with pytest.raises(UnsupportedCollectionError):
            classify_members((MyList([1, 2, 3]),))

    def test_tuple_subclass_rejected(self) -> None:
        class MyTuple(tuple):
            pass

        with pytest.raises(UnsupportedCollectionError):
            classify_members((MyTuple((1, 2, 3)),))

    def test_range_rejected(self) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members((range(3),))

    def test_dict_rejected(self) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members(({"a": 1},))

    def test_ordereddict_rejected(self) -> None:
        from collections import OrderedDict

        with pytest.raises(UnsupportedCollectionError):
            classify_members((OrderedDict([("a", 1)]),))

    def test_defaultdict_rejected(self) -> None:
        from collections import defaultdict

        with pytest.raises(UnsupportedCollectionError):
            classify_members((defaultdict(int, {"a": 1}),))

    def test_dict_keys_rejected(self) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members(({"a": 1}.keys(),))

    def test_dict_values_rejected(self) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members(({"a": 1}.values(),))

    def test_dict_items_rejected(self) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members(({"a": 1}.items(),))

    def test_polars_series_rejected(self) -> None:
        pytest.importorskip("polars")
        import polars as pl

        s = pl.Series([1, 2, 3])
        with pytest.raises(UnsupportedCollectionError) as exc_info:
            classify_members((s,))
        assert exc_info.value.value is s

    def test_pandas_series_rejected(self) -> None:
        pytest.importorskip("pandas")
        import pandas as pd

        s = pd.Series([1, 2, 3])
        with pytest.raises(UnsupportedCollectionError):
            classify_members((s,))

    def test_generator_rejected_and_not_consumed(self) -> None:
        """Critical: detect by type, not by calling iter(); do not consume."""

        def gen():
            yield 1
            yield 2
            yield 3

        g = gen()
        with pytest.raises(UnsupportedCollectionError) as exc_info:
            classify_members((g,))
        # Generator was not consumed — it still yields all 3 values
        assert list(g) == [1, 2, 3]
        assert exc_info.value.value is g


class TestNumpyNdarray:
    """ndarray 0-d/1-d/N-d all → UnsupportedCollectionError (type check)."""

    @pytest.fixture
    def np(self):
        pytest.importorskip("numpy")
        import numpy as np

        return np

    def test_0d_array_rejected(self, np) -> None:
        """The rev-1 bug: 0-d array raises TypeError under iter(); must detect by type."""
        arr = np.array(5)
        with pytest.raises(UnsupportedCollectionError) as exc_info:
            classify_members((arr,))
        # Value is the array that was passed (compare, not identity, since
        # numpy arrays are not hashable / may not be the same object)
        assert exc_info.value.value is arr

    def test_1d_array_rejected(self, np) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members((np.array([1, 2, 3]),))

    def test_2d_array_rejected(self, np) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members((np.array([[1, 2], [3, 4]]),))

    def test_3d_array_rejected(self, np) -> None:
        with pytest.raises(UnsupportedCollectionError):
            classify_members((np.zeros((2, 2, 2)),))


# =========================================================================
# Helper-level unit tests (verifying the branch table primitives directly)
# =========================================================================


class TestIsContainer:
    """_is_container: type(x) in (list, tuple, set, frozenset) — exact type."""

    def test_list_is_container(self) -> None:
        assert _is_container([1, 2, 3]) is True

    def test_tuple_is_container(self) -> None:
        assert _is_container((1, 2, 3)) is True

    def test_set_is_container(self) -> None:
        assert _is_container({1, 2, 3}) is True

    def test_frozenset_is_container(self) -> None:
        assert _is_container(frozenset({1, 2, 3})) is True

    def test_namedtuple_is_not_container(self) -> None:
        NT = namedtuple("NT", ["a", "b"])
        assert _is_container(NT(1, 2)) is False

    def test_list_subclass_is_not_container(self) -> None:
        class MyList(list):
            pass

        assert _is_container(MyList()) is False

    def test_tuple_subclass_is_not_container(self) -> None:
        class MyTuple(tuple):
            pass

        assert _is_container(MyTuple()) is False

    def test_dict_is_not_container(self) -> None:
        assert _is_container({"a": 1}) is False

    def test_range_is_not_container(self) -> None:
        assert _is_container(range(3)) is False

    def test_str_is_not_container(self) -> None:
        assert _is_container("hello") is False

    def test_int_is_not_container(self) -> None:
        assert _is_container(5) is False

    def test_ndarray_is_not_container(self) -> None:
        pytest.importorskip("numpy")
        import numpy as np

        assert _is_container(np.array([1, 2, 3])) is False


class TestIsExpression:
    """_is_expression: MA expr or backend-native expr."""

    def test_ma_col(self) -> None:
        assert _is_expression(ma.col("x")) is True

    def test_ma_lit(self) -> None:
        assert _is_expression(ma.lit(5)) is True

    def test_ma_t_col(self) -> None:
        assert _is_expression(ma.t_col("x")) is True

    def test_polars_expr(self) -> None:
        pytest.importorskip("polars")
        import polars as pl

        assert _is_expression(pl.col("x")) is True

    def test_narwhals_expr(self) -> None:
        pytest.importorskip("narwhals")
        import narwhals as nw

        assert _is_expression(nw.col("x")) is True

    def test_ibis_expr(self) -> None:
        pytest.importorskip("ibis")
        import ibis

        assert _is_expression(ibis.literal(1)) is True

    def test_int_is_not_expression(self) -> None:
        assert _is_expression(5) is False

    def test_str_is_not_expression(self) -> None:
        assert _is_expression("hello") is False

    def test_list_is_not_expression(self) -> None:
        assert _is_expression([1, 2, 3]) is False

    def test_dict_is_not_expression(self) -> None:
        assert _is_expression({"a": 1}) is False

    def test_ma_col_is_BaseExpressionAPI(self) -> None:
        """Brief fix: use real isinstance check, no `if False else object`."""
        assert isinstance(ma.col("x"), BaseExpressionAPI)


class TestIsUnsupportedIterable:
    """_is_unsupported_iterable: detect by type, not by calling iter()."""

    def test_str_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable("hello") is False

    def test_bytes_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable(b"abc") is False

    def test_list_is_not_unsupported_iterable(self) -> None:
        """Exact list is a container — already classified."""
        assert _is_unsupported_iterable([1, 2, 3]) is False

    def test_tuple_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable((1, 2, 3)) is False

    def test_set_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable({1, 2, 3}) is False

    def test_frozenset_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable(frozenset({1, 2, 3})) is False

    def test_ma_expr_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable(ma.col("x")) is False

    def test_polars_expr_is_not_unsupported_iterable(self) -> None:
        pytest.importorskip("polars")
        import polars as pl

        assert _is_unsupported_iterable(pl.col("x")) is False

    def test_namedtuple_is_unsupported_iterable(self) -> None:
        NT = namedtuple("NT", ["a", "b"])
        assert _is_unsupported_iterable(NT(1, 2)) is True

    def test_list_subclass_is_unsupported_iterable(self) -> None:
        class MyList(list):
            pass

        assert _is_unsupported_iterable(MyList()) is True

    def test_range_is_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable(range(3)) is True

    def test_dict_is_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable({"a": 1}) is True

    def test_dict_keys_is_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable({"a": 1}.keys()) is True

    def test_polars_series_is_unsupported_iterable(self) -> None:
        pytest.importorskip("polars")
        import polars as pl

        assert _is_unsupported_iterable(pl.Series([1, 2, 3])) is True

    def test_pandas_series_is_unsupported_iterable(self) -> None:
        pytest.importorskip("pandas")
        import pandas as pd

        assert _is_unsupported_iterable(pd.Series([1, 2, 3])) is True

    def test_0d_ndarray_is_unsupported_iterable(self) -> None:
        """The rev-1 bug: do not call iter(); detect 0-d arrays by type."""
        pytest.importorskip("numpy")
        import numpy as np

        # iter(np.array(5)) would raise TypeError — but we never call iter().
        arr = np.array(5)
        assert _is_unsupported_iterable(arr) is True

    def test_1d_ndarray_is_unsupported_iterable(self) -> None:
        pytest.importorskip("numpy")
        import numpy as np

        assert _is_unsupported_iterable(np.array([1, 2, 3])) is True

    def test_2d_ndarray_is_unsupported_iterable(self) -> None:
        pytest.importorskip("numpy")
        import numpy as np

        assert _is_unsupported_iterable(np.array([[1, 2], [3, 4]])) is True

    def test_generator_is_unsupported_iterable(self) -> None:
        def gen():
            yield 1

        assert _is_unsupported_iterable(gen()) is True

    def test_int_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable(5) is False

    def test_float_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable(3.14) is False

    def test_none_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable(None) is False

    def test_decimal_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable(Decimal("1.5")) is False

    def test_date_is_not_unsupported_iterable(self) -> None:
        assert _is_unsupported_iterable(date(2026, 1, 1)) is False

    def test_custom_obj_is_not_unsupported_iterable(self) -> None:
        class MyObj:
            pass

        assert _is_unsupported_iterable(MyObj()) is False

    def test_numpy_scalar_is_not_unsupported_iterable(self) -> None:
        """NumPy scalars (np.int64, np.float64, …) have __getitem__ via
        inheritance on the type but are genuinely scalar — must not be
        classified as unsupported iterables.
        """
        pytest.importorskip("numpy")
        import numpy as np

        assert _is_unsupported_iterable(np.int64(5)) is False
        assert _is_unsupported_iterable(np.float64(1.5)) is False

    def test_enum_member_is_not_unsupported_iterable(self) -> None:
        """Enum *classes* are iterable but enum *members* are scalars."""
        pytest.importorskip("enum")
        import enum as enum_mod

        class Color(enum_mod.Enum):
            RED = 1

        assert _is_unsupported_iterable(Color.RED) is False


# =========================================================================
# Property Tests: Disjointness + Exhaustiveness over a representative matrix
# =========================================================================


BRANCH_RETURNED = "returned"
BRANCH_EMPTY = "empty"
BRANCH_BARE_EXPR = "bare_expression"
BRANCH_UNSUPPORTED = "unsupported"
BRANCH_NESTED = "nested"
BRANCH_NATIVE_MEMBER = "native_member"

ALL_KNOWN_BRANCHES = frozenset(
    {
        BRANCH_RETURNED,
        BRANCH_EMPTY,
        BRANCH_BARE_EXPR,
        BRANCH_UNSUPPORTED,
        BRANCH_NESTED,
        BRANCH_NATIVE_MEMBER,
    }
)


def _resolve_branch(args: tuple) -> str:
    """Call classify_members and return the branch label for the input.

    Disjointness is enforced by construction: classify_members either returns
    a list or raises one of 5 specific typed errors. We map each outcome to
    a branch label and assert the result is in the known set.
    """
    try:
        result = classify_members(args)
    except EmptyMembershipError:
        return BRANCH_EMPTY
    except BareExpressionCollectionError:
        return BRANCH_BARE_EXPR
    except NestedCollectionError:
        return BRANCH_NESTED
    except NativeExprMemberError:
        return BRANCH_NATIVE_MEMBER
    except UnsupportedCollectionError:
        return BRANCH_UNSUPPORTED
    if isinstance(result, list):
        return BRANCH_RETURNED
    return "unknown"


def _build_matrix() -> list[tuple[str, tuple]]:
    """Build a comprehensive representative-object matrix per the brief.

    Includes: scalars (int/float/str/bytes/bool/None/Decimal/date/datetime/
    enum/NaN/custom obj/NumPy scalar), containers (list/tuple/set/frozenset),
    namedtuple, list/tuple subclasses, range, dict+dict_keys, Series,
    ndarray 0-d/1-d/N-d, generators, MA col/lit/t_col, all native expr types,
    ma.lit([...]), nested containers, and out-of-table set members.
    """
    matrix: list[tuple[str, tuple]] = []

    # -- Scalars (single arg → 1-element set / SCALAR branch) --
    matrix.append(("scalar_int", (5,)))
    matrix.append(("scalar_float", (3.14,)))
    matrix.append(("scalar_str", ("hello",)))
    matrix.append(("scalar_bytes", (b"abc",)))
    matrix.append(("scalar_bool_true", (True,)))
    matrix.append(("scalar_bool_false", (False,)))
    matrix.append(("scalar_none", (None,)))
    matrix.append(("scalar_decimal", (Decimal("1.5"),)))
    matrix.append(("scalar_date", (date(2026, 1, 1),)))
    matrix.append(("scalar_datetime", (datetime(2026, 1, 1, 12, 0, 0),)))
    matrix.append(("scalar_nan", (float("nan"),)))

    class Color(enum.Enum):
        RED = 1

    matrix.append(("scalar_enum", (Color.RED,)))

    class MyObj:
        pass

    matrix.append(("scalar_custom_obj", (MyObj(),)))

    # NumPy scalars
    try:
        import numpy as np

        matrix.append(("scalar_numpy_int", (np.int64(5),)))
        matrix.append(("scalar_numpy_float", (np.float64(1.5),)))
    except ImportError:
        pass

    # -- Containers --
    matrix.append(("container_list", ([1, 2, 3],)))
    matrix.append(("container_tuple", ((1, 2, 3),)))
    matrix.append(("container_set", ({1, 2, 3},)))
    matrix.append(("container_frozenset", (frozenset({1, 2, 3}),)))
    matrix.append(("container_empty_list", ([],)))

    # -- Namedtuple / list+tuple subclasses / range / dict+dict_keys --
    NT = namedtuple("NT", ["a", "b"])
    matrix.append(("namedtuple", (NT(1, 2),)))

    class MyList(list):
        pass

    class MyTuple(tuple):
        pass

    matrix.append(("list_subclass", (MyList([1, 2, 3]),)))
    matrix.append(("tuple_subclass", (MyTuple((1, 2, 3)),)))
    matrix.append(("range", (range(3),)))
    matrix.append(("dict", ({"a": 1},)))
    matrix.append(("dict_keys", ({"a": 1}.keys(),)))
    matrix.append(("dict_values", ({"a": 1}.values(),)))
    matrix.append(("dict_items", ({"a": 1}.items(),)))

    # -- Series --
    try:
        import polars as pl

        matrix.append(("polars_series", (pl.Series([1, 2, 3]),)))
    except ImportError:
        pass

    try:
        import pandas as pd

        matrix.append(("pandas_series", (pd.Series([1, 2, 3]),)))
    except ImportError:
        pass

    # -- ndarray 0-d/1-d/N-d --
    try:
        import numpy as np

        matrix.append(("ndarray_0d", (np.array(5),)))
        matrix.append(("ndarray_1d", (np.array([1, 2, 3]),)))
        matrix.append(("ndarray_2d", (np.array([[1, 2], [3, 4]]),)))
    except ImportError:
        pass

    # -- Generators (not consumed) --
    def gen_factory():
        def gen():
            yield 1
            yield 2
            yield 3

        return gen()

    matrix.append(("generator", (gen_factory(),)))

    # -- MA expressions (BaseExpressionAPI) --
    matrix.append(("ma_col", (ma.col("x"),)))
    matrix.append(("ma_lit_scalar", (ma.lit(5),)))
    matrix.append(("ma_t_col", (ma.t_col("x"),)))
    matrix.append(("ma_lit_list", (ma.lit([1, 2, 3]),)))

    # -- Native expression types --
    try:
        import polars as pl

        matrix.append(("pl_col", (pl.col("x"),)))
        matrix.append(("pl_lit", (pl.lit(5),)))
    except ImportError:
        pass

    try:
        import narwhals as nw

        matrix.append(("nw_col", (nw.col("x"),)))
    except ImportError:
        pass

    try:
        import ibis

        matrix.append(("ibis_literal", (ibis.literal(1),)))
    except ImportError:
        pass

    try:
        import ibis.common.deferred as idd

        matrix.append(("ibis_deferred", (idd.Deferred("x"),)))
    except ImportError:
        pass

    # -- Nested containers (member is a container/unsupported-iterable) --
    matrix.append(("nested_list_member", ([1, [2, 3]],)))
    matrix.append(("nested_tuple_member", ([1, (2, 3)],)))
    matrix.append(("nested_dict_member", ([1, {"a": 1}],)))

    def gen_for_nested():
        def gen():
            yield 1

        return gen()

    matrix.append(("nested_generator_member", ([1, gen_for_nested()],)))

    # -- Multi-arg cases --
    matrix.append(("multi_scalars", (1, 2, 3)))
    matrix.append(("multi_ma_exprs", (ma.col("a"), ma.col("b"))))
    matrix.append(("multi_mixed_scalar_ma", (1, ma.col("a"), 3)))

    try:
        import polars as pl

        matrix.append(("multi_with_native_member", (1, 2, pl.col("x"))))
    except ImportError:
        pass

    matrix.append(("multi_with_nested_list", (1, [2, 3])))

    # -- Sets with out-of-table types (canonicalize → reject) --
    matrix.append(("set_with_decimal", ({Decimal("1.5")},)))
    matrix.append(("set_with_date", ({date(2026, 1, 1)},)))
    matrix.append(("set_with_datetime", ({datetime(2026, 1, 1, 12, 0, 0)},)))
    matrix.append(("set_with_enum", ({Color.RED},)))
    matrix.append(("set_with_nan", ({float("nan")},)))
    matrix.append(("set_with_none", ({None},)))

    try:
        import numpy as np

        matrix.append(("set_with_numpy_int", ({np.int64(5)},)))
        matrix.append(("set_with_numpy_float", ({np.float64(1.5)},)))
    except ImportError:
        pass

    return matrix


MATRIX = _build_matrix()
MATRIX_LABELS = [m[0] for m in MATRIX]

# Filter to single-arg inputs only — the disjointness property of the
# branch predicates (_is_expression / _is_container / _is_unsupported_iterable)
# is a single-arg claim. Multi-arg inputs take the `else` branch of the
# decision tree and don't exercise these guards.
SINGLE_ARG_MATRIX = [(label, args) for label, args in MATRIX if len(args) == 1]
SINGLE_ARG_LABELS = [m[0] for m in SINGLE_ARG_MATRIX]


class TestPropertyDisjointness:
    """Branch predicates are mutually exclusive for every single-arg input.

    This is a genuinely distinct property from exhaustiveness: it proves
    the if/elif guards in `classify_members` (the three private
    predicates) do not overlap, independent of the order they are checked
    in. If any two predicates returned True for the same input, the
    decision tree would have ambiguous behaviour regardless of ordering.
    """

    @pytest.mark.parametrize(
        "label,args", SINGLE_ARG_MATRIX, ids=SINGLE_ARG_LABELS
    )
    def test_predicates_mutually_exclusive(self, label: str, args: tuple) -> None:
        # Single-arg input: `args == (x,)`, extract `x`.
        (x,) = args
        flags = [
            _is_expression(x),
            _is_container(x),
            _is_unsupported_iterable(x),
        ]
        # At most one True: the three predicates partition the single-arg
        # decision tree (zero True means "scalar literal" → 1-element set).
        # Two or more True is a real predicate-overlap bug — fix the
        # predicate, not the assertion.
        assert sum(bool(f) for f in flags) <= 1, (
            f"{label}: predicates overlap on {x!r} — "
            f"_is_expression={flags[0]}, _is_container={flags[1]}, "
            f"_is_unsupported_iterable={flags[2]}"
        )


class TestPropertyExhaustiveness:
    """Every input in the matrix is classified — no input is silently skipped.

    This is a genuinely distinct property from disjointness: it proves the
    classifier's *outcome* (return or one of 5 typed errors) covers every
    input — no input falls into an "unknown" / unhandled case. The matrix
    is the brief's representative-object set; each row is a real case the
    classifier must handle with a definite verdict.
    """

    @pytest.mark.parametrize("label,args", MATRIX, ids=MATRIX_LABELS)
    def test_no_silent_skip(self, label: str, args: tuple) -> None:
        """Exhaustiveness: the classifier produces a result or a typed error,
        never an 'unknown' outcome. The matrix labels every input as a real
        case; the classifier must give it a definite classification.
        """
        branch = _resolve_branch(args)
        assert branch in ALL_KNOWN_BRANCHES, (
            f"{label}: input {args!r} was not classified (branch={branch!r})"
        )


class TestErrorSubclasses:
    """All raised errors are MembershipArgumentError subclasses."""

    @pytest.mark.parametrize(
        "args",
        [
            ((),),
            ([],),
            (ma.col("x"),),
            (ma.lit([1, 2, 3]),),
            pytest.param((pl.col("x"),) if False else (1,), id="scalar"),
        ],
    )
    def test_all_errors_subclass_base(self, args: tuple) -> None:
        try:
            classify_members(args)
        except MembershipArgumentError:
            pass  # All branch errors subclass this
        else:
            # No error raised — fine (returned a list)
            pass


# Reference imports (used only in test parameters / fixtures) for typing
_ = GeneratorType
_ = Mapping
