"""Self-healing probes + public-path gate assertions for op-level gated string ops (61a)."""
from __future__ import annotations
import mountainash as ma
import pytest

from expressions.argument_types._op_level_helpers import op_level_result
from expressions.argument_types.conftest import make_df
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.backends.capabilities.string import (
    BROKEN_STRING_OPS_BY_BACKEND,
    OP_LEVEL_FKEYS,
)
from tests.fixtures.capability_gating import (
    assert_capability_gated,
    gate_dialect,
    gate_family,
)

# op -> (build, single-row input, ASCII oracle = polars/Python semantics)
_OP_CASES = {
    "swapcase":   (lambda: ma.col("s").str.swapcase(),   {"s": ["Hello World"]}, ["hELLO wORLD"]),
    "title":      (lambda: ma.col("s").str.title(),      {"s": ["hello world"]}, ["Hello World"]),
    "initcap":    (lambda: ma.col("s").str.initcap(),    {"s": ["hello world"]}, ["Hello World"]),
    "capitalize": (lambda: ma.col("s").str.capitalize(), {"s": ["hELLO wORLD"]}, ["Hello world"]),
    "center":     (lambda: ma.col("s").str.center(6),    {"s": ["ab"]},          ["  ab  "]),
}
_FAMILY_FIXTURES = {
    CONST_BACKEND.IBIS: ("ibis",),
    CONST_BACKEND.NARWHALS: ("narwhals-polars", "narwhals-pandas"),
}


def _gated_params():
    out = []
    for family, ops in BROKEN_STRING_OPS_BY_BACKEND.items():
        for op in sorted(ops):
            for fixture in _FAMILY_FIXTURES[family]:
                out.append(pytest.param(op, fixture, id=f"{op}-{fixture}"))
    # The broken map is never empty in this codebase; a structural guard, not a skip.
    assert out, "no gated string ops found — BROKEN_STRING_OPS_BY_BACKEND unexpectedly empty"
    return out


@pytest.mark.parametrize("op,fixture", _gated_params())
@pytest.mark.xfail(strict=True, reason="op is gated as broken; XPASS => native fix landed, remove the gate")
def test_gated_op_is_still_broken(op, fixture):
    build, data, oracle = _OP_CASES[op]
    assert op_level_result(build, data, fixture) == oracle


@pytest.mark.parametrize("op,fixture", _gated_params())
def test_gated_op_raises_on_public_path(op, fixture):
    build, data, _ = _OP_CASES[op]
    df = make_df(data, fixture)
    assert_capability_gated(
        OP_LEVEL_FKEYS[op],
        gate_family(fixture),
        dialect=gate_dialect(fixture),
        build=lambda: ma.relation(df).select(build().name.alias("r")).to_dict(),
    )
