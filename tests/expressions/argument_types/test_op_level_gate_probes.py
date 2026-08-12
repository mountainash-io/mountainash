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



def test_like_ibis_polars_native_still_broken():
    """Dialect-scoped whole-op gate (backlog item 83) — `like`'s
    `WILDCARD_PARAM` `UNSUPPORTED` fact is `dialect="ibis-polars"`, not a
    `BROKEN_STRING_OPS_BY_BACKEND` (family-wide, dialect=None) entry, so it
    is not covered by `_gated_params()`/`op_level_result()` above, which
    only has `_FAMILY_FIXTURES`/`_FIXTURE_DIALECT` entries for the bare
    "ibis" family identity. Build the gate-disabled visitor directly
    instead (mirrors test_capability_probes.py::test_native_path_probe's
    construction). Asserts the SPECIFIC native exception, not a bare
    `Exception` — a broad catch would silently accept an unrelated harness
    failure forever instead of the intended native limitation. If upstream
    ever ships a StringSQLLike translation rule for ibis-polars, this test
    fails outright — a loud signal to revisit the gate."""
    import ibis
    from expressions.argument_types._test_template import _materialize_result
    from mountainash.expressions.core.expression_system.expsys_base import (
        get_expression_system,
    )
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

    df = make_df({"text": ["hello"]}, "ibis-polars")
    system = get_expression_system(CONST_BACKEND.IBIS)(dialect="ibis-polars")
    visitor = UnifiedExpressionVisitor(system, enforce_capabilities=False)
    compiled = visitor.visit(ma.col("text").str.like("J%")._node)
    with pytest.raises(ibis.common.exceptions.OperationNotDefinedError):
        _materialize_result(df, compiled, "ibis-polars")