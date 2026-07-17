"""Unit tests for IbisBaseExpressionSystem._lift_deferred (item 226b).

Gate is LITERAL-LEFT-ONLY: only `concrete-left ∘ Deferred-right` (the sole
crashing ordering) is lifted; all working orderings are returned untouched.
"""
import ibis
from ibis.common.deferred import Deferred

from mountainash.expressions.backends.expression_systems.ibis.base import (
    IbisBaseExpressionSystem,
)


class _Sys(IbisBaseExpressionSystem):
    """Minimal concrete subclass for exercising the base helper."""


def _lift(x, y):
    return _Sys()._lift_deferred(x, y)


def test_concrete_left_deferred_right_lifts_left():
    # lit + col — the ONLY crashing ordering: lift the concrete left operand.
    x, y = _lift(ibis.literal(5), ibis._["n"])
    assert isinstance(x, Deferred) and isinstance(y, Deferred)


def test_deferred_left_concrete_right_UNTOUCHED():
    # col + lit already works — must be returned byte-identical, NOT rewrapped.
    a, b = ibis._["n"], ibis.literal(5)
    x, y = _lift(a, b)
    assert x is a and y is b


def test_both_concrete_untouched():
    a, b = ibis.literal(1), ibis.literal(2)
    x, y = _lift(a, b)
    assert x is a and y is b


def test_both_deferred_untouched():
    a, b = ibis._["m"], ibis._["n"]
    x, y = _lift(a, b)
    assert x is a and y is b


def test_lifted_op_preserves_order_and_executes():
    con = ibis.duckdb.connect()
    t = con.create_table("t", {"n": [2, 3, 4]})
    x, y = _lift(ibis.literal(100), ibis._["n"])
    expr = (x - y).resolve(t)  # must be 100 - n, NOT n - 100
    assert t.select(expr.name("r"))["r"].execute().tolist() == [98, 97, 96]
