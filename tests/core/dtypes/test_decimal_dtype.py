"""DecimalDtype descriptor: bounds, registry lowering/extraction, typed literals (item 241)."""
from __future__ import annotations

from decimal import Decimal

import ibis.expr.datatypes as dt
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from mountainash.core.dtypes import DecimalDtype, TypeTarget, parse_cast_target, registry
from mountainash.core.dtypes.errors import UnknownDtypeError


class TestDecimalDtype:
    def test_valid_bounds(self):
        assert DecimalDtype(precision=1, scale=0).precision == 1
        assert DecimalDtype(precision=38, scale=38).scale == 38

    @pytest.mark.parametrize(
        "p,s", [(0, 0), (39, 2), (5, 6), (5, -1), (True, 0), (5, True), (5.0, 2), ("5", 2)]
    )
    def test_invalid_bounds_raise_typed_error(self, p, s):
        with pytest.raises(UnknownDtypeError):
            DecimalDtype(precision=p, scale=s)

    def test_frozen_and_hashable(self):
        a, b = DecimalDtype(precision=10, scale=3), DecimalDtype(precision=10, scale=3)
        assert a == b and hash(a) == hash(b)
        with pytest.raises(Exception):
            a.precision = 11

    def test_cast_target_passthrough(self):
        d = DecimalDtype(precision=10, scale=3)
        assert parse_cast_target(d) is d

    def test_str(self):
        assert str(DecimalDtype(precision=10, scale=3)) == "decimal(10,3)"


D103 = DecimalDtype(precision=10, scale=3)


@pytest.mark.parametrize(
    "target,expected",
    [
        (TypeTarget.POLARS, pl.Decimal(10, 3)),
        (TypeTarget.PYARROW, pa.decimal128(10, 3)),
        (TypeTarget.IBIS, dt.Decimal(10, 3)),
        (TypeTarget.NARWHALS, nw.Decimal(10, 3)),
        (TypeTarget.PANDAS, pd.ArrowDtype(pa.decimal128(10, 3))),
        (TypeTarget.PYTHON, Decimal),
    ],
)
def test_lowering_keeps_precision_and_scale(target, expected):
    assert registry.to_native_schema(D103, target) == expected
    assert registry.to_native_cast(D103, target) == expected


@pytest.mark.parametrize(
    "native,target",
    [
        (pl.Decimal(12, 4), TypeTarget.POLARS),
        (pa.decimal128(12, 4), TypeTarget.PYARROW),
        (pa.decimal256(12, 4), TypeTarget.PYARROW),
        (dt.Decimal(12, 4), TypeTarget.IBIS),
        (nw.Decimal(12, 4), TypeTarget.NARWHALS),
        (pd.ArrowDtype(pa.decimal128(12, 4)), TypeTarget.PANDAS),
    ],
)
def test_extraction_keeps_precision_and_scale(native, target):
    assert registry.from_native(native, target) == DecimalDtype(precision=12, scale=4)


def test_extraction_of_unparameterised_python_decimal_is_not_decimal_dtype():
    # A bare decimal.Decimal hint carries no p/s: it must not become a DecimalDtype.
    with pytest.raises(UnknownDtypeError):
        registry.from_native(Decimal, TypeTarget.PYTHON)


def test_arrow_decimal_beyond_precision_38_is_rejected():
    with pytest.raises(UnknownDtypeError):
        registry.from_native(pa.decimal256(50, 4), TypeTarget.PYARROW)


def test_typed_literal_lowers_natively_on_polars():
    df = pl.DataFrame({"x": [1]})
    out = ma.relation(df).select(ma.lit(Decimal("0.004"), dtype=D103).alias("v"))
    result = out.to_polars()
    assert result.schema["v"] == pl.Decimal(10, 3)
    assert result["v"].to_list() == [Decimal("0.004")]


def test_lit_without_dtype_is_unchanged():
    df = pl.DataFrame({"x": [1]})
    result = ma.relation(df).select(ma.lit(Decimal("0.004")).alias("v")).to_polars()
    assert result["v"].to_list() == [Decimal("0.004")]
