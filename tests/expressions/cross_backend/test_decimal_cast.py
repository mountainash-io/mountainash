"""DecimalDtype casts with explicit rounding, across all nine backend identities (item 241).

Expected values are hand-written. Narwhals-based identities refuse through declared capability
facts (strict xfail, linked to the upstream registry); ibis-sqlite refuses intrinsically.
"""
from __future__ import annotations

from decimal import Decimal as D

import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash._operation_options import (
    InvalidOptionValueError,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_VALUE,
)

NARWHALS = {"narwhals-polars", "narwhals-lazy", "narwhals-pandas", "pandas"}
REFUSAL_REASON = (
    "Narwhals has no round mode / non-strict cast: "
    "registry NW-MATH-11 (narwhals#3698), NW-CAST-01 (narwhals#3702)"
)

# (source values, p, s, mode, expected per value). Expected values are written by hand.
CASES = [
    (["0.00449", "0.0045", "-0.0045", "0.0055", "-0.0005"], 10, 3, "half_to_even",
     [D("0.004"), D("0.004"), D("-0.004"), D("0.006"), D("0.000")]),
    (["0.00449", "0.0045", "-0.0045", "0.0055", "-0.0005"], 10, 3, "half_away_from_zero",
     [D("0.004"), D("0.005"), D("-0.005"), D("0.006"), D("-0.001")]),
    (["0.00449", "0.0045", "-0.0045", "0.0059", "-0.0059"], 10, 3, "to_zero",
     [D("0.004"), D("0.004"), D("-0.004"), D("0.005"), D("-0.005")]),
    ([" 1_000.5 ", "+1.5", ".5", "5.", "1e2"], 10, 3, "half_to_even",
     [D("1000.500"), D("1.500"), D("0.500"), D("5.000"), D("100.000")]),
    (["2.5", "-2.5", "3.5", "0.5"], 1, 0, "half_to_even", [D("2"), D("-2"), D("4"), D("0")]),
    (["2.5", "-2.5", "3.5"], 16, 0, "half_away_from_zero", [D("3"), D("-3"), D("4")]),
    (["12.3455", "-12.3455"], 16, 3, "half_to_even", [D("12.346"), D("-12.346")]),
    (["0.0000045", "-0.0000055"], 15, 5, "half_to_even", [D("0.00000"), D("-0.00001")]),
    (["0.123456789012345685"], 16, 15, "half_to_even", [D("0.123456789012346")]),
    # underscores: every one is removed, on every backend (review: ibis-polars removed only the first)
    (["1_0_0", "1__0", "1_000_000.5", "_1"], 10, 3, "half_to_even",
     [D("100.000"), D("10.000"), D("1000000.500"), D("1.000")]),
    # rounding carry out of the integer part that still fits the target: exact, never an abort
    (["8.5", "9.4", "-8.5"], 1, 0, "half_to_even", [D("8"), D("9"), D("-8")]),
    (["0.05"], 1, 1, "half_to_even", [D("0.0")]),
    # documented limit 2: parse rounds to 0.0045, then away -> 0.005 (exact answer 0.004)
    (["0.00449999999999"], 10, 3, "half_away_from_zero", [D("0.005")]),
]
OVERFLOW_CASES = [
    # The carry needs one more integer digit than the target and the intermediate hold: Polars
    # aborts the process on its own Decimal.round unless the rounding runs in a wider decimal.
    ("99.5", 1, 0, "half_to_even"),
    ("9.95", 1, 1, "half_to_even"),
    ("9.5", 1, 0, "half_away_from_zero"),
    ("9999999.9995", 10, 3, "half_to_even"),
    ("9999999.9995", 10, 3, "half_away_from_zero"),
    ("-9.5", 1, 0, "half_away_from_zero"),
]
TO_ZERO_NO_OVERFLOW = ("9999999.9995", 10, 3, "to_zero", D("9999999.999"))


def _cast(col, p, s, mode, fb="throw"):
    return ma.col(col).cast(ma.DecimalDtype(precision=p, scale=s), rounding=mode, failure_behavior=fb)


BACKENDS = [
    pytest.param(b, marks=pytest.mark.xfail(strict=True, raises=BackendCapabilityError, reason=REFUSAL_REASON))
    if b in NARWHALS else b
    for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize("values,p,s,mode,expected", CASES)
@pytest.mark.parametrize("fb", ["throw", "null"])
def test_decimal_cast_values(backend_name, backend_factory, collect_expr, values, p, s, mode, expected, fb):
    df = backend_factory.create({"v": values}, backend_name)
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError) as err:
            collect_expr(df, _cast("v", p, s, mode, fb))
        assert err.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
        return
    assert collect_expr(df, _cast("v", p, s, mode, fb)) == expected
    out = ma.relation(df).select(_cast("v", p, s, mode, fb).alias("r")).to_polars()
    assert out.schema["r"] == pl.Decimal(p, s)  # exact result type on every case


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)  # not BACKENDS: refusals asserted in-body
@pytest.mark.parametrize("value,p,s,mode", OVERFLOW_CASES)
@pytest.mark.parametrize("fb", ["throw", "null"])
def test_integer_overflow_always_raises(backend_name, backend_factory, collect_expr, value, p, s, mode, fb):
    df = backend_factory.create({"v": [value]}, backend_name)
    if backend_name == "ibis-sqlite" or backend_name in NARWHALS:
        # The refusal fires before any value is computed. Asserted directly: a broad
        # pytest.raises(Exception) would swallow the gate error and make a strict xfail XPASS.
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, _cast("v", p, s, mode, fb))
        return
    with pytest.raises(Exception) as err:
        collect_expr(df, _cast("v", p, s, mode, fb))
    assert not isinstance(err.value, BackendCapabilityError)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
def test_to_zero_does_not_overflow_on_carry(backend_name, backend_factory, collect_expr):
    value, p, s, mode, expected = TO_ZERO_NO_OVERFLOW
    df = backend_factory.create({"v": [value]}, backend_name)
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, _cast("v", p, s, mode))
        return
    assert collect_expr(df, _cast("v", p, s, mode)) == [expected]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
def test_invalid_input_and_nulls(backend_name, backend_factory, collect_expr):
    df = backend_factory.create({"v": [None, "1.5", "12x", ""]}, backend_name)
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, _cast("v", 10, 3, "half_to_even", "null"))
        return
    assert collect_expr(df, _cast("v", 10, 3, "half_to_even", "null")) == [None, D("1.500"), None, None]
    with pytest.raises(Exception):
        collect_expr(df, _cast("v", 10, 3, "half_to_even", "throw"))


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
def test_float_and_int_sources(backend_name, backend_factory, collect_expr):
    df = backend_factory.create({"f": [2.675, 2.5, 0.1], "i": [7, -7, 0]}, backend_name)
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, _cast("f", 10, 2, "half_to_even"))
        return
    # R17: floats convert by their shortest string form, not their binary value
    assert collect_expr(df, _cast("f", 10, 2, "half_to_even")) == [D("2.68"), D("2.50"), D("0.10")]
    assert collect_expr(df, _cast("f", 10, 2, "to_zero")) == [D("2.67"), D("2.50"), D("0.10")]
    assert collect_expr(df, _cast("i", 10, 3, "half_to_even")) == [D("7.000"), D("-7.000"), D("0.000")]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
def test_native_round_tie_rule_pins(backend_name, backend_factory, collect_expr):
    """Ibis corrections assume DuckDB rounds ties away from zero and Polars to even; fail loudly if that changes."""
    df = backend_factory.create({"v": ["0.0045"]}, backend_name)
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, _cast("v", 10, 3, "half_to_even"))
        return
    assert collect_expr(df, _cast("v", 10, 3, "half_to_even")) == [D("0.004")]
    assert collect_expr(df, _cast("v", 10, 3, "half_away_from_zero")) == [D("0.005")]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
def test_rules_range_examples_with_decimal_literals(backend_name, backend_factory):
    """Rules §20.5.5: endpoints and contexts in the same decimal domain, compared exactly."""
    df = backend_factory.create({"ctx": ["0.00449", "0.00451", "0.01950"]}, backend_name)
    d = ma.DecimalDtype(precision=10, scale=3)
    v = _cast("ctx", 10, 3, "half_to_even")
    singleton = (v >= ma.lit(D("0.004"), dtype=d)) & (v <= ma.lit(D("0.004"), dtype=d))
    half_open = (v >= ma.lit(D("0.010"), dtype=d)) & (v < ma.lit(D("0.020"), dtype=d))
    rel = ma.relation(df).select(singleton.alias("s"), half_open.alias("h"))
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError):
            rel.to_dict()
        return
    out = rel.to_dict()
    assert out["s"] == [True, False, False]   # 0.00449 -> 0.004 matches; 0.00451 -> 0.005 doesn't
    assert out["h"] == [False, False, False]  # 0.01950 -> 0.020 is outside [0.010, 0.020)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
def test_limit_wider_than_intermediate(backend_name, backend_factory, collect_expr):
    """Documented limit 1: a value too wide for the intermediate is an error in throw mode, null in null mode."""
    df = backend_factory.create({"v": ["999999999999999999"]}, backend_name)
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, _cast("v", 10, 3, "half_to_even", "null"))
        return
    assert collect_expr(df, _cast("v", 10, 3, "half_to_even", "null")) == [None]
    with pytest.raises(Exception):
        collect_expr(df, _cast("v", 10, 3, "half_to_even", "throw"))


class TestCastContract:
    @pytest.mark.parametrize(
        "call",
        [
            lambda: ma.col("v").cast(ma.DecimalDtype(precision=10, scale=3)),  # rounding missing
            lambda: ma.col("v").cast("i64", rounding="half_to_even"),  # rounding on a non-decimal
            lambda: ma.col("v").cast(ma.DecimalDtype(precision=10, scale=3), rounding="bankers"),  # unknown mode
            lambda: ma.col("v").cast(ma.DecimalDtype(precision=17, scale=3), rounding="to_zero"),  # p > 16
            lambda: ma.col("v").cast(
                ma.DecimalDtype(precision=10, scale=3), rounding="to_zero", failure_behavior="explode"
            ),
        ],
    )
    def test_build_time_errors(self, call):
        with pytest.raises(InvalidOptionValueError):
            call()

    def test_non_decimal_cast_keeps_the_dtype_keyword(self):
        """Non-decimal targets behave as before, including the `dtype=` keyword form."""
        df = pl.DataFrame({"v": ["7", "8"]})
        assert ma.relation(df).select(ma.col("v").cast(dtype="i64").alias("r")).to_dict()["r"] == [7, 8]
        assert ma.relation(df).select(ma.col("v").cast("i64").alias("r")).to_dict()["r"] == [7, 8]

    def test_a_declaration_can_exceed_the_cast_cap(self):
        """A DecimalDtype up to 38 digits can be declared; only a cast target is capped at 16."""
        assert ma.DecimalDtype(precision=38, scale=10).precision == 38
        with pytest.raises(InvalidOptionValueError):
            ma.col("v").cast(ma.DecimalDtype(precision=38, scale=10), rounding="to_zero")
        ma.col("v").cast(ma.DecimalDtype(precision=16, scale=16), rounding="to_zero")  # at the cap: builds
