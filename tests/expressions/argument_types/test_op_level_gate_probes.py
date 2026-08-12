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


def test_regexp_string_split_ibis_sqlite_native_still_broken():
    """Dialect-scoped whole-op gate (backlog item 85) — mirrors
    test_like_ibis_polars_native_still_broken exactly. If upstream ever
    ships a RegexSplit compilation rule for ibis-sqlite, this test fails
    outright — a loud signal to revisit the gate."""
    import ibis
    from mountainash.expressions.core.expression_system.expsys_base import (
        get_expression_system,
    )
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

    # make_df() (expressions.argument_types.conftest) and
    # _materialize_result() (_test_template.py) have no ibis-sqlite entry --
    # constructed/materialized directly here, mirroring backend_registry.py's
    # _build_ibis_sqlite and _materialize_result's ibis/ibis-polars branch.
    connection = ibis.sqlite.connect(":memory:")
    df = connection.create_table("option_test", {"text": ["a1b"]}, overwrite=True)
    system = get_expression_system(CONST_BACKEND.IBIS)(dialect="ibis-sqlite")
    visitor = UnifiedExpressionVisitor(system, enforce_capabilities=False)
    compiled = visitor.visit(ma.col("text").str.regexp_string_split(r"\d+")._node)
    with pytest.raises(ibis.common.exceptions.OperationNotDefinedError):
        df.select(compiled.name("__result__")).execute()


def test_regexp_string_split_ibis_polars_dynamic_pattern_native_still_broken():
    """Dialect-scoped LITERAL_ONLY gate (backlog item 85) — a dynamic
    (column-valued) pattern raises Ibis's own IbisError before ever
    reaching Polars. If upstream ever accepts a dynamic pattern for
    Polars re_split, this test fails outright.

    Uses 3 non-uniform rows deliberately: a single-row "column" degenerates
    to something ibis-polars' query optimizer treats as effectively scalar
    and silently succeeds instead of raising (verified empirically,
    2026-08-13) -- multiple, non-uniform rows are required to genuinely
    exercise the dynamic-argument rejection."""
    import ibis
    from expressions.argument_types._test_template import _materialize_result
    from mountainash.expressions.core.expression_system.expsys_base import (
        get_expression_system,
    )
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

    df = make_df(
        {"text": ["a1b", "c2d", "e3f"], "pattern": [r"\d+", r"[a-z]", r"\d"]},
        "ibis-polars",
    )
    system = get_expression_system(CONST_BACKEND.IBIS)(dialect="ibis-polars")
    visitor = UnifiedExpressionVisitor(system, enforce_capabilities=False)
    compiled = visitor.visit(
        ma.col("text").str.regexp_string_split(ma.col("pattern"))._node
    )
    with pytest.raises(ibis.common.exceptions.IbisError):
        _materialize_result(df, compiled, "ibis-polars")


def test_narwhals_regexp_split_native_still_absent():
    """Family-wide whole-op gate (backlog item 85) — probes the RAW
    narwhals API surface directly, not mountainash's own defensive raise
    (which always fires regardless of narwhals' actual capability and so
    cannot self-heal). Two structural checks: (1) no method on
    ExprStringNamespace performs regex splitting, (2) split() has no
    regex-mode parameter (e.g. a `literal=` kwarg mirroring
    replace_all/contains). If narwhals ever adds either, this test fails
    outright -- a loud signal to revisit the gate and implement a real fix."""
    import inspect

    import narwhals as nw
    from narwhals.expr_str import ExprStringNamespace

    public_methods = [
        name for name in dir(ExprStringNamespace) if not name.startswith("_")
    ]
    regex_split_candidates = [
        name for name in public_methods
        if name != "split" and ("split" in name.lower() or "regex" in name.lower())
    ]
    assert not regex_split_candidates, (
        f"narwhals gained a candidate regex-split method: {regex_split_candidates} "
        "-- revisit the NW-STR-20 whole-op gate"
    )

    split_params = inspect.signature(ExprStringNamespace.split).parameters
    assert "literal" not in split_params and "regex" not in split_params, (
        "narwhals's str.split() gained a literal/regex-mode parameter -- "
        "revisit the NW-STR-20 whole-op gate"
    )

    with pytest.raises(TypeError):
        nw.col("text").str.split("1", literal=False)  # type: ignore[call-arg]