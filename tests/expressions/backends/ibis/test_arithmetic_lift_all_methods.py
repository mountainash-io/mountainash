"""Every routed ibis arithmetic method must accept a literal-left operand (item 226b)."""
import ibis
import pytest

from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_scalar_arithmetic import (
    SubstraitIbisScalarArithmeticExpressionSystem as Sys,
)


def _exec(built):
    con = ibis.duckdb.connect()
    t = con.create_table("t", {"n": [2, 3, 4]})
    from ibis.common.deferred import Deferred
    expr = built.resolve(t) if isinstance(built, Deferred) else built
    return t.select(expr.name("r"))["r"].execute().tolist()


@pytest.mark.parametrize(
    "method, lit, expected",
    [
        ("add",         ibis.literal(10),  [12, 13, 14]),
        ("subtract",    ibis.literal(10),  [8, 7, 6]),
        ("multiply",    ibis.literal(10),  [20, 30, 40]),
        ("divide",      ibis.literal(12.0), [6.0, 4.0, 3.0]),
        ("modulus",     ibis.literal(10),  [0, 1, 2]),
        ("power",       ibis.literal(2),   [4, 8, 16]),
        ("bitwise_and", ibis.literal(6),   [2, 2, 4]),
        ("bitwise_or",  ibis.literal(1),   [3, 3, 5]),
        ("bitwise_xor", ibis.literal(6),   [4, 5, 2]),
        ("shift_left",  ibis.literal(1),   [4, 8, 16]),   # 1 << n
        ("shift_right", ibis.literal(64),  [16, 8, 4]),   # 64 >> n
    ],
)
def test_literal_left_routed_method(method, lit, expected):
    sys = Sys()
    built = getattr(sys, method)(lit, ibis._["n"])
    assert _exec(built) == expected


def test_atan2_literal_left():
    import math
    sys = Sys()
    built = sys.atan2(ibis.literal(1.0), ibis._["n"])
    out = _exec(built)
    # ibis atan2(x, y) computes atan2 of the two operands; assert exact values,
    # order-sensitively (x=literal 1.0, y=col n) — not merely "3 floats".
    expected = [math.atan2(1.0, n) for n in (2, 3, 4)]
    assert out == pytest.approx(expected)


def test_extraction_path_intact_add_days():
    """add_days extracts a literal amount via _extract_literal_if_possible; the
    arithmetic-method edits must not disturb that untouched ibis path."""
    import datetime
    import mountainash.expressions as ma
    con = ibis.duckdb.connect()
    df = con.create_table(
        "dt", {"d": [datetime.datetime(2020, 1, 1), datetime.datetime(2020, 1, 2)]}
    )
    be = ma.col("d").dt.add_days(ma.lit(3)).compile(df)
    out = df.select(be.name("r"))["r"].execute().tolist()
    assert [v.date().isoformat() for v in out] == ["2020-01-04", "2020-01-05"]
