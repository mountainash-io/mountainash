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
    ([" 1_000.5 ", "+1.5", ".5", "5."], 10, 3, "half_to_even",
     [D("1000.500"), D("1.500"), D("0.500"), D("5.000")]),
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
    # Single rounding: the mode applies to the value the author wrote, never to a pre-rounded parse.
    # (Rules consumer review of PR 355: each value is what direct rounding of the typed text gives.)
    (["0.00449999999999", "0.00450000000001"], 10, 3, "half_away_from_zero", [D("0.004"), D("0.005")]),
    (["0.00450000000001", "0.0045", "0.00449999999999"], 10, 3, "half_to_even", [D("0.005"), D("0.004"), D("0.004")]),
    (["1.2451", "1.25499", "1.2449"], 16, 2, "half_to_even", [D("1.25"), D("1.25"), D("1.24")]),
    (["1.99999", "-1.99999"], 10, 3, "to_zero", [D("1.999"), D("-1.999")]),
    (["1.995", "-1.995"], 16, 2, "to_zero", [D("1.99"), D("-1.99")]),
    # same text and scale, different precision: the result must not depend on precision
    (["1.2451"], 10, 2, "half_to_even", [D("1.25")]),
    (["1.2451"], 16, 2, "half_to_even", [D("1.25")]),
    (["0.51", "0.49", "-0.51"], 16, 0, "half_to_even", [D("1"), D("0"), D("-1")]),
    # exact ties follow the requested mode on every backend, whatever the engine's own tie rule
    (["1.245", "1.255", "-1.245", "0.005", "0.025"], 16, 2, "half_to_even",
     [D("1.24"), D("1.26"), D("-1.24"), D("0.00"), D("0.02")]),
    (["1.245", "1.255", "-1.245", "0.005", "0.025"], 16, 2, "half_away_from_zero",
     [D("1.25"), D("1.26"), D("-1.25"), D("0.01"), D("0.03")]),
    # many more digits than the target scale
    (["1.2450000000000000001", "1.2449999999999999999"], 16, 2, "half_to_even", [D("1.25"), D("1.24")]),
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
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)  # not BACKENDS: refusals asserted in-body
@pytest.mark.parametrize("fb", ["throw", "null"])
def test_a_value_too_wide_for_the_target_always_raises(backend_name, backend_factory, collect_expr, fb):
    """Integer-part overflow is the author's range mistake: it raises under both failure behaviours."""
    df = backend_factory.create({"v": ["999999999999999999"]}, backend_name)
    if backend_name == "ibis-sqlite" or backend_name in NARWHALS:
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, _cast("v", 10, 3, "half_to_even", fb))
        return
    with pytest.raises(Exception) as err:
        collect_expr(df, _cast("v", 10, 3, "half_to_even", fb))
    assert not isinstance(err.value, BackendCapabilityError)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)  # not BACKENDS: refusals asserted in-body
@pytest.mark.parametrize("text", ["12x", "1.2.3", "0x1F", "1,5", "nan", "inf", "-inf", "-", "."])
def test_text_that_is_not_a_number_is_invalid_input(backend_name, backend_factory, collect_expr, text):
    """Text that is not a finite number is invalid: null under "null", an error under "throw"."""
    df = backend_factory.create({"v": [text]}, backend_name)
    if backend_name == "ibis-sqlite" or backend_name in NARWHALS:
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, _cast("v", 10, 3, "half_to_even", "null"))
        return
    assert collect_expr(df, _cast("v", 10, 3, "half_to_even", "null")) == [None]
    with pytest.raises(Exception) as err:
        collect_expr(df, _cast("v", 10, 3, "half_to_even", "throw"))
    assert not isinstance(err.value, BackendCapabilityError)


def _exact(text, scale, mode):
    """Independent oracle (test only, never in the data path): Python's Decimal."""
    from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext

    rounding = {"half_to_even": ROUND_HALF_EVEN, "half_away_from_zero": ROUND_HALF_UP, "to_zero": ROUND_DOWN}[mode]
    with localcontext() as ctx:
        ctx.prec = 90
        return D(text).quantize(D(1).scaleb(-scale), rounding=rounding)


# Exponent text goes to the backend, which interprets it. Every engine agrees with the exact value on
# these, so the cross-backend contract holds for them.
EXPONENT_TEXT = ["1e2", "1E2", "1.5e-3", "5e-1", "0.5e0", "1245e-3", "2.5e0", "12.5e1", "1e-3", "-1.5e2", "+1e1"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize("mode", ["half_to_even", "half_away_from_zero", "to_zero"])
@pytest.mark.parametrize("fb", ["throw", "null"])
def test_exponent_text_is_interpreted_by_the_backend(backend_name, backend_factory, collect_expr, mode, fb):
    df = backend_factory.create({"v": EXPONENT_TEXT}, backend_name)
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, _cast("v", 12, 3, mode, fb))
        return
    assert collect_expr(df, _cast("v", 12, 3, mode, fb)) == [_exact(t, 3, mode) for t in EXPONENT_TEXT]


# Documented DuckDB limitation: its own text-to-decimal cast rounds a value that the exponent pushes
# below the last decimal place by the first mantissa digit (7e-11 -> 0.001, exact 0.000), an error of
# one unit in the last place. Plain text such as 0.00000000007 is exact. Polars-based engines are exact.
DUCKDB_EXPONENT_DEFECT = ["7e-11", "5e-5", "6e-9", "9e-12"]


@pytest.mark.cross_backend
@pytest.mark.parametrize(
    "backend_name",
    [
        pytest.param(
            b,
            marks=pytest.mark.xfail(
                strict=True,
                reason="DuckDB rounds exponent text below the last place by its mantissa digit (one unit off)",
            ),
        )
        if b == "ibis-duckdb" else b
        for b in BACKENDS
    ],
)
def test_exponent_text_far_below_the_last_place(backend_name, backend_factory, collect_expr):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": DUCKDB_EXPONENT_DEFECT}, backend_name)
    assert collect_expr(df, _cast("v", 12, 3, "half_to_even")) == [_exact(t, 3, "half_to_even") for t in DUCKDB_EXPONENT_DEFECT]


# Documented limit: exact ties are resolved by reading plain decimal text, so a tie written with an exponent
# takes the engine's own tie rule (Polars: half to even; DuckDB: half away from zero). The same tie written
# without an exponent is identical on every engine. Each row is (plain spelling, exponent spelling, p, s).
_EXACT_TIES = [("0.125", "1.25e-1", 10, 2), ("2.5", "25e-1", 10, 0), ("0.00000000005", "5e-11", 10, 10)]
_ENGINE_TIE_RULE = {
    "polars": "half_to_even", "polars-lazy": "half_to_even", "ibis-polars": "half_to_even",
    "ibis-duckdb": "half_away_from_zero",
}


@pytest.mark.cross_backend
@pytest.mark.parametrize("mode", ["half_to_even", "half_away_from_zero"])
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize("plain,exponent,p,s", _EXACT_TIES)
def test_an_exact_tie_written_plainly_follows_the_requested_mode(
    backend_name, backend_factory, collect_expr, mode, plain, exponent, p, s
):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [plain]}, backend_name)
    assert collect_expr(df, _cast("v", p, s, mode)) == [_exact(plain, s, mode)]


def _tie_mismatch(backend_name, mode):
    """True where the engine's own tie rule is not the requested mode, so the exponent spelling is wrong."""
    return _ENGINE_TIE_RULE.get(backend_name) not in (None, mode)


@pytest.mark.cross_backend
@pytest.mark.parametrize("mode", ["half_to_even", "half_away_from_zero"])
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize("plain,exponent,p,s", _EXACT_TIES)
def test_an_exact_tie_written_with_an_exponent_takes_the_engines_rule(
    request, backend_name, backend_factory, collect_expr, mode, plain, exponent, p, s
):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    if _tie_mismatch(backend_name, mode):
        request.applymarker(pytest.mark.xfail(
            strict=True,
            reason=f"exact tie written with an exponent follows the engine's own rule, not {mode} (documented limit)",
        ))
    df = backend_factory.create({"v": [exponent]}, backend_name)
    assert collect_expr(df, _cast("v", p, s, mode)) == [_exact(exponent, s, mode)]


# Documented DuckDB limitation: at a target scale of 12 or more its own parse returns nothing for a valid
# in-range exponent number (8% of random exponent inputs at scale 12, 26% at scale 16, none up to scale 10).
# The conversion raises, naming the value, under both failure behaviours. The same value written without an
# exponent parses on every engine.
_EXPONENT_AT_HIGH_SCALE = ("8386712e-7", 16, 12, D("0.838671200000"))
_SAME_VALUE_PLAIN = ("0.8386712", 16, 12, D("0.838671200000"))


@pytest.mark.cross_backend
@pytest.mark.parametrize("fb", ["throw", "null"])
@pytest.mark.parametrize(
    "backend_name",
    [
        pytest.param(
            b,
            marks=pytest.mark.xfail(
                strict=True,
                reason="DuckDB cannot parse valid exponent text at a target scale of 12 or more (documented limit)",
            ),
        )
        if b == "ibis-duckdb" else b
        for b in BACKENDS
    ],
)
def test_exponent_text_at_a_high_target_scale(backend_name, backend_factory, collect_expr, fb):
    text, p, s, expected = _EXPONENT_AT_HIGH_SCALE
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [text]}, backend_name)
    assert collect_expr(df, _cast("v", p, s, "half_to_even", fb)) == [expected]


# to_zero falls back to a smaller parse where DuckDB's own parse returns nothing, so it is not affected.
@pytest.mark.cross_backend
@pytest.mark.parametrize("fb", ["throw", "null"])
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize("text,p,s,expected", [
    ("8386712e-7", 16, 12, D("0.838671200000")),
    ("83867e-7", 16, 16, D("0.0083867000000000")),
    ("83867e-7", 1, 0, D("0")),
    ("-64279e-9", 2, 0, D("0")),
])
def test_to_zero_converts_exponent_text_the_half_modes_cannot_parse(backend_name, backend_factory, collect_expr, fb, text, p, s, expected):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [text]}, backend_name)
    assert collect_expr(df, _cast("v", p, s, "to_zero", fb)) == [expected]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
def test_the_same_value_as_plain_text_at_a_high_target_scale(backend_name, backend_factory, collect_expr):
    text, p, s, expected = _SAME_VALUE_PLAIN
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [text]}, backend_name)
    assert collect_expr(df, _cast("v", p, s, "half_to_even")) == [expected]


# Documented limit of `to_zero` on the Ibis backends. DuckDB has no truncate-to-places and a wide decimal
# parse costs ~17 s per million rows, so `to_zero` rounds on a 64-bit parse and steps back one unit. The
# parse keeps 17 - p + s fractional digits, so 17 - p digits beyond the target scale are exact; past that the
# parse rounds first. At (16, 2) one extra digit is exact, so "1.99999" (three) gives 2.00 instead of 1.99.
# Polars cuts plain text after the scale, so it is exact for any length.
# Reported by the Rules consumer review of PR 355.
_TO_ZERO_BEYOND_17_MINUS_P = (["1.99999", "-1.99999", "12.3499999"], 16, 2, [D("1.99"), D("-1.99"), D("12.34")])


@pytest.mark.cross_backend
@pytest.mark.parametrize(
    "backend_name",
    [
        pytest.param(
            b,
            marks=pytest.mark.xfail(
                strict=True,
                reason="to_zero on a 64-bit parse is exact only within 17 - p digits past the scale (documented limit)",
            ),
        )
        if b in ("ibis-duckdb", "ibis-polars") else b
        for b in BACKENDS
    ],
)
def test_to_zero_beyond_the_ibis_exactness_limit(backend_name, backend_factory, collect_expr):
    values, p, s, expected = _TO_ZERO_BEYOND_17_MINUS_P
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": values}, backend_name)
    assert collect_expr(df, _cast("v", p, s, "to_zero")) == expected


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
def test_to_zero_within_the_ibis_exactness_limit(backend_name, backend_factory, collect_expr):
    """Within 17 - p extra digits `to_zero` is exact on every engine (p=10: seven)."""
    values = ["1.9999999999", "-1.9999999999", "0.0009999999"]   # three kept digits plus seven extra
    expected = [D("1.999"), D("-1.999"), D("0.000")]
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": values}, backend_name)
    assert collect_expr(df, _cast("v", 10, 3, "to_zero")) == expected


# Regressions from the Rules consumer review of 47ec97d. Expectations are written by hand.
# Plain decimal text may omit the integer digit: ".5" is 0.5 and must tie like it at every scale.
@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize(
    "mode,expected",
    [
        ("half_away_from_zero", [D("1"), D("-1"), D("1"), D("3"), D("-3"), D("0")]),
        ("half_to_even", [D("0"), D("0"), D("0"), D("2"), D("-2"), D("0")]),
    ],
)
def test_a_leading_point_text_ties_like_the_same_value_with_a_zero(
    backend_name, backend_factory, collect_expr, mode, expected
):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [".5", "-.5", "+.5", "2.5", "-2.5", ".4"]}, backend_name)
    assert collect_expr(df, _cast("v", 10, 0, mode)) == expected


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize("text", [".", "-.", "+.", ".e3"])
def test_a_bare_point_is_not_a_number(backend_name, backend_factory, collect_expr, text):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [text]}, backend_name)
    assert collect_expr(df, _cast("v", 10, 2, "half_to_even", "null")) == [None]


# A value that already fits the target needs no digits discarded, so no mode may change it.
@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize("mode", ["half_to_even", "half_away_from_zero", "to_zero"])
@pytest.mark.parametrize("text,p,s", [
    ("0.1234567890123456", 16, 16),
    ("0.123456789012", 16, 12),
    ("0.12345678901", 16, 11),
    ("-0.1234567890123456", 16, 16),
    ("1.23456789", 16, 8),
])
def test_a_value_that_already_fits_the_target_is_unchanged(backend_name, backend_factory, collect_expr, mode, text, p, s):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [text]}, backend_name)
    assert collect_expr(df, _cast("v", p, s, mode)) == [D(text)]


# to_zero reads plain text of any length exactly on Polars (cut after `scale` digits); the Ibis backends
# keep the documented window (limit 1), so this row is pinned for them as a strict xfail.
_LONG_NINES = "1." + "9" * 40


@pytest.mark.cross_backend
@pytest.mark.parametrize(
    "backend_name",
    [
        pytest.param(b, marks=pytest.mark.xfail(strict=True, reason="Ibis to_zero window (documented limit 1)"))
        if b in ("ibis-duckdb", "ibis-polars") else b
        for b in BACKENDS
    ],
)
def test_to_zero_of_a_very_long_plain_fraction_is_exact_where_the_engine_allows(backend_name, backend_factory, collect_expr):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [_LONG_NINES, "-" + _LONG_NINES]}, backend_name)
    assert collect_expr(df, _cast("v", 10, 2, "to_zero")) == [D("1.99"), D("-1.99")]


# A finite number too large for any float is still a number: it is out of range, so it raises under
# both failure behaviours. Only text that is not a number is null under "null".
@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize("fb", ["throw", "null"])
@pytest.mark.parametrize("text", ["1e309", "9" * 400, "-" + "9" * 400])
def test_a_finite_number_beyond_any_float_raises_in_both_failure_modes(backend_name, backend_factory, collect_expr, fb, text):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [text]}, backend_name)
    with pytest.raises(Exception) as err:
        collect_expr(df, _cast("v", 10, 3, "half_to_even", fb))
    if backend_name in NARWHALS:
        raise err.value  # a refusal is the declared outcome there (the strict xfail on BackendCapabilityError)
    assert not isinstance(err.value, BackendCapabilityError)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", BACKENDS)
@pytest.mark.parametrize("text", ["nan", "inf", "-inf", "infinity", "12x", "1e", "e5"])
def test_text_that_is_not_a_finite_number_is_null_under_null_mode(backend_name, backend_factory, collect_expr, text):
    if backend_name == "ibis-sqlite":
        pytest.skip("covered by the refusal tests")
    df = backend_factory.create({"v": [text]}, backend_name)
    assert collect_expr(df, _cast("v", 10, 3, "half_to_even", "null")) == [None]


# A literal source is a constant to the engines. Polars-based engines evaluate a strict cast for a constant
# whatever the surrounding condition, so a forced-failure branch poisoned every constant (regression found by
# the argument matrix on Polars and by a literal sweep on ibis-polars; no column test could see it).
@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)  # not BACKENDS: refusals asserted in-body
@pytest.mark.parametrize("mode", ["half_to_even", "half_away_from_zero", "to_zero"])
@pytest.mark.parametrize("fb", ["throw", "null"])
def test_a_literal_source_converts_like_a_column(backend_name, backend_factory, mode, fb):
    df = backend_factory.create({"x": [1, 2]}, backend_name)
    expr = ma.lit("0.0045").cast(ma.DecimalDtype(precision=10, scale=3), rounding=mode, failure_behavior=fb)
    rel = ma.relation(df).select(expr.alias("r"))
    if backend_name == "ibis-sqlite" or backend_name in NARWHALS:
        with pytest.raises(BackendCapabilityError):
            rel.to_dict()
        return
    assert set(rel.to_dict()["r"]) == {_exact("0.0045", 3, mode)}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)  # not BACKENDS: refusals asserted in-body
@pytest.mark.parametrize("fb", ["throw", "null"])
@pytest.mark.parametrize("text", ["12x", "nan", "1e50"])
def test_an_invalid_or_out_of_range_literal_follows_the_failure_rules(backend_name, backend_factory, fb, text):
    """Text that is not a number: null or error by mode. A number too large for the target: always an error."""
    df = backend_factory.create({"x": [1, 2]}, backend_name)
    rel = ma.relation(df).select(
        ma.lit(text).cast(ma.DecimalDtype(precision=10, scale=3), rounding="half_to_even", failure_behavior=fb).alias("r")
    )
    if backend_name == "ibis-sqlite" or backend_name in NARWHALS:
        with pytest.raises(BackendCapabilityError):
            rel.to_dict()
        return
    if text == "1e50" or fb == "throw":
        with pytest.raises(Exception) as err:
            rel.to_dict()
        assert not isinstance(err.value, BackendCapabilityError)
    else:
        assert set(rel.to_dict()["r"]) == {None}


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
