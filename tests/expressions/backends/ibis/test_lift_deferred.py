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


# --- _lift_deferred_receiver: method-call analog (item 226c) ---


def _lift_recv(receiver, *args):
    return _Sys()._lift_deferred_receiver(receiver, *args)


def test_receiver_concrete_deferred_arg_lifts():
    r = _lift_recv(ibis.literal("abcx"), ibis._["sub"])
    assert isinstance(r, Deferred)


def test_receiver_deferred_UNTOUCHED():
    a = ibis._["s"]
    assert _lift_recv(a, ibis._["sub"]) is a


def test_receiver_concrete_all_concrete_args_untouched():
    a = ibis.literal("abcx")
    assert _lift_recv(a, ibis.literal("bc")) is a


def test_receiver_lift_ignores_none_args():
    # Optional params default to None (not Deferred) and must not trigger a lift.
    a = ibis.literal("abcx")
    assert _lift_recv(a, None, None) is a


def test_receiver_lift_any_deferred_arg_triggers():
    # A concrete receiver with a concrete first arg but a Deferred second arg
    # (e.g. replace(lit, "x", col)) must still lift.
    r = _lift_recv(ibis.literal("abcx"), ibis.literal("x"), ibis._["rep"])
    assert isinstance(r, Deferred)


def test_lifted_receiver_method_executes():
    con = ibis.duckdb.connect()
    t = con.create_table("t", {"sub": ["bc", "q"]})
    r = _lift_recv(ibis.literal("abcx"), ibis._["sub"])
    expr = r.contains(ibis._["sub"]).resolve(t)
    assert t.select(expr.name("r"))["r"].execute().tolist() == [True, False]
