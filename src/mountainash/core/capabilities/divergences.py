"""Cross-backend result divergences as data (spec Sections 1, 4-5).

Transcribed from d.cross-backend/core/known-divergences.md; that principle
doc's inventory becomes GENERATED from this module in Phase 4. Divergences
never gate dispatch — they drive declaration-driven xfails
(tests/.../_divergence_helpers.py) and the generated catalog.
"""
from __future__ import annotations

from mountainash.core.capabilities.schema import DivergenceFact, DivergenceKind


def _all() -> tuple[DivergenceFact, ...]:
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_NULL as FK_NULL,
        FKEY_MOUNTAINASH_SCALAR_BOOLEAN as FK_MA_BOOL,
        FKEY_MOUNTAINASH_SCALAR_COMPARISON as FK_MA_CMP,
        FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_MA_DT,
        FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
        FKEY_MOUNTAINASH_WINDOW as FK_WIN,
        FKEY_SUBSTRAIT_CAST as FK_CAST,
        FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_AR,
        FKEY_SUBSTRAIT_SCALAR_BOOLEAN as FK_BOOL,
        FKEY_SUBSTRAIT_SCALAR_COMPARISON as FK_CMP,
        FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
    )

    return (
        DivergenceFact(
            id="IB-CAST-01",
            kind=DivergenceKind.PRECISION,
            operation_keys=(FK_CAST.CAST,),
            backends=("ibis-duckdb",),
            summary="DuckDB uses IEEE 754 banker's rounding (half-to-even) casting float to integer",
            impact="Tests expecting truncation-on-cast produce different results on ibis-duckdb",
            workaround="Explicit floor()/ceil() before cast, or use ibis-sqlite/polars",
            upstream_ref="IB-CAST-01",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-TYPE-02",
            kind=DivergenceKind.SEMANTICS,
            operation_keys=(FK_CMP.IS_NAN, FK_NULL.FILL_NAN),
            backends=("ibis-duckdb", "ibis-sqlite"),
            summary="SQL engines treat NaN as NULL; NaN == NaN yields NULL not False",
            impact="is_nan/fill_nan/NaN comparisons diverge on SQL engines",
            workaround="Use is_null/fill_null on SQL backends",
            upstream_ref="IB-TYPE-02",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-MATH-02",
            kind=DivergenceKind.ENGINE_LENIENCY,
            operation_keys=(
                FK_AR.SINH,
                FK_AR.COSH,
                FK_AR.TANH,
                FK_AR.ASINH,
                FK_AR.ACOSH,
                FK_AR.ATANH,
            ),
            backends=("ibis-sqlite",),
            summary="SQLite lacks hyperbolic math functions",
            impact="sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite",
            workaround="Any backend other than ibis-sqlite",
            upstream_ref="IB-MATH-02",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-DT-06",
            kind=DivergenceKind.SEMANTICS,
            operation_keys=(FK_BOOL.XOR, FK_MA_BOOL.XOR_PARITY),
            backends=("ibis-duckdb",),
            summary="DuckDB ^ is bitwise on integers, not logical XOR on booleans",
            impact="Chained boolean parity via xor diverges on ibis-duckdb",
            workaround="polars, narwhals, or ibis-sqlite for boolean parity",
            upstream_ref="IB-DT-06",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-REL-06",
            kind=DivergenceKind.ENGINE_LENIENCY,
            operation_keys=(),
            backends=("ibis-duckdb",),
            summary="DuckDB rejects tables containing untyped all-NULL columns",
            impact="Projections whose column is entirely null raise a type resolution error",
            workaround="cast the null column to an explicit type first",
            upstream_ref="IB-REL-06",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-CTE-01",
            kind=DivergenceKind.SEMANTICS,
            operation_keys=(),
            backends=("ibis-duckdb", "ibis-polars", "ibis-sqlite"),
            summary="Ibis strips RECURSIVE from generated CTE SQL, turning WITH RECURSIVE into WITH",
            impact="Recursive CTE SQL cannot be generated through Ibis",
            workaround=None,
            upstream_ref="IB-CTE-01",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-MATH-04",
            kind=DivergenceKind.SEMANTICS,
            operation_keys=(FK_AR.DIVIDE,),
            backends=("ibis-sqlite",),
            summary="SQLite performs integer division for two integer operands",
            impact="Division expecting float results silently truncates on ibis-sqlite",
            workaround="Cast one operand to float before dividing",
            upstream_ref="IB-MATH-04",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-MATH-05",
            kind=DivergenceKind.SEMANTICS,
            operation_keys=(FK_AR.MODULO,),
            backends=("ibis-sqlite", "ibis-duckdb"),
            summary="SQL modulo takes the sign of the dividend rather than the divisor",
            impact="Cyclic calculations and hash bucketing with negative dividends diverge",
            workaround="Ensure the dividend is non-negative or normalize with a conditional expression",
            upstream_ref="IB-MATH-05",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-TYPE-04",
            kind=DivergenceKind.TYPE_INFERENCE,
            operation_keys=(),
            backends=("ibis-duckdb", "ibis-polars", "ibis-sqlite"),
            summary="Ibis defers type resolution to its backend, unlike eager Polars",
            impact="Type-sensitive operations and result comparisons can differ despite matching values",
            workaround=None,
            upstream_ref="IB-TYPE-04",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="MA-MATH-01",
            kind=DivergenceKind.PRECISION,
            operation_keys=(),
            backends=("polars", "narwhals", "ibis"),
            summary="Intermediate float precision and rounding differ across backends",
            impact="Exact equality comparisons on float results can fail across backends",
            workaround="Use is_close(precision=...) instead of eq() for float comparisons",
            upstream_ref="MA-MATH-01",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-DT-09",
            kind=DivergenceKind.SEMANTICS,
            operation_keys=(FK_MA_DT.TODAY, FK_MA_DT.NOW),
            backends=("ibis-duckdb", "ibis-polars", "ibis-sqlite"),
            summary="Ibis today() upcasts date to timestamp on ALL ibis backends; now() "
                    "compiles to query-time UTC SQL on ibis-duckdb and ibis-sqlite only "
                    "(ibis-polars evaluates now() like Polars/Narwhals)",
            impact="today() snapshot type differs on all ibis backends; now() evaluation "
                   "instant differs on ibis-duckdb/ibis-sqlite (UTC, query-time)",
            workaround="Use Polars or Narwhals for exact date types; account for UTC query-time now() on ibis-duckdb/ibis-sqlite",
            upstream_ref="IB-DT-09",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-AGG-04",
            kind=DivergenceKind.NAMING,
            operation_keys=(),  # op-diffuse: applies to ANY un-aliased aggregate measure
            backends=("ibis-duckdb", "ibis-polars", "ibis-sqlite"),
            summary='Ibis names un-aliased aggregate measures "Sum(v)" rather than source column "v"',
            impact="Inferred schemas and Ibis runtime output names can disagree",
            workaround="Always alias aggregate measures when pipelines may execute on Ibis",
            upstream_ref="IB-AGG-04",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="IB-CAST-03",
            kind=DivergenceKind.ENGINE_LENIENCY,
            operation_keys=(FK_CAST.CAST,),
            backends=("ibis-sqlite",),
            summary="SQLite CAST is lenient, parsing CAST('1x' AS INTEGER) as 1",
            impact="Strict casts do not raise for malformed input on ibis-sqlite",
            workaround="Validate malformed input via conform/typespec or use another Ibis backend",
            upstream_ref="IB-CAST-03",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="MA-TYPE-01",
            kind=DivergenceKind.TYPE_INFERENCE,
            operation_keys=(),
            backends=("ibis-duckdb", "ibis-polars", "ibis-sqlite"),
            summary="Typed all-NULL columns lose their declared dtype through to_polars()'s pandas bridge",
            impact="Ibis-backed materialization reports String or Float64 instead of the declared dtype",
            workaround="Re-cast after materialization or inspect the pre-materialization Ibis schema",
            upstream_ref="MA-TYPE-01",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="MA-TYPE-02",
            kind=DivergenceKind.SEMANTICS,
            operation_keys=(FK_CAST.CAST,),
            backends=("pandas", "narwhals-pandas"),
            summary="All-NULL casts to non-nullable numpy int64/bool raise or corrupt nulls",
            impact="Pandas-backed integer casts raise and boolean casts can map None to False",
            workaround="Use polars, narwhals-polars, narwhals-lazy, or an Ibis backend",
            upstream_ref="MA-TYPE-02",
            since="2026-07-05",
        ),
        DivergenceFact(
            id="NW-STR-14",
            kind=DivergenceKind.SEMANTICS,
            operation_keys=(FK_STR.TITLE, FK_STR.INITCAP),
            backends=("narwhals-pandas",),
            summary="narwhals-pandas title/initcap route to pandas str.title(); its Unicode titlecasing of sharp-S/ligatures differs from polars to_titlecase (e.g. 'ße' -> 'ẞe' vs 'SSe')",
            impact="title()/initcap() on narwhals-pandas may differ from polars/narwhals-polars on non-ASCII inputs (sharp-S, ligatures); ASCII is identical",
            workaround="Use polars or narwhals-polars where exact polars titlecasing of non-ASCII is required",
            upstream_ref=None,
            since="2026-07-29",
        ),
        DivergenceFact(
            id="NW-WIN-01",
            kind=DivergenceKind.ENGINE_LENIENCY,
            operation_keys=(FK_WIN.DIFF, FK_WIN.CUM_SUM, FK_WIN.CUM_MAX, FK_WIN.CUM_MIN),
            backends=("narwhals-lazy",),
            summary="narwhals-lazy rejects order-dependent window expressions (diff/cumulative) on a LazyFrame (InvalidOperationError)",
            impact="col().diff()/cum_sum()/cum_max()/cum_min() raise on narwhals-lazy; eager narwhals and polars compute them",
            workaround="Use an eager backend, or establish an explicit order before the lazy diff",
            upstream_ref=None,
            since="2026-08-06",
        ),
        DivergenceFact(
            id="IB-WIN-01",
            kind=DivergenceKind.ENGINE_LENIENCY,
            operation_keys=(
                FK_WIN.DIFF,
                FK_WIN.CUM_SUM,
                FK_WIN.CUM_MAX,
                FK_WIN.CUM_MIN,
                FK_MA_CMP.IS_DUPLICATED,
            ),
            backends=("ibis-polars",),
            summary="ibis-polars has no translation rule for the diff/cumulative/is_duplicated WindowFunction (OperationNotDefinedError)",
            impact="col().diff()/cum_sum()/cum_max()/cum_min()/is_duplicated() raise on ibis-polars; ibis-duckdb/ibis-sqlite and polars/narwhals compute them",
            workaround="Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend",
            upstream_ref=None,
            since="2026-08-06",
        ),
        DivergenceFact(
            id="NW-LIST-05",
            kind=DivergenceKind.ENGINE_LENIENCY,
            operation_keys=(
                FK_LIST.GATHER_EVERY,
                FK_LIST.ARG_MIN,
                FK_LIST.ARG_MAX,
                FK_LIST.ALL,
                FK_LIST.ANY,
                FK_LIST.N_UNIQUE,
                FK_LIST.COUNT_MATCHES,
                FK_LIST.DROP_NULLS,
                FK_LIST.SET_UNION,
                FK_LIST.SET_INTERSECTION,
                FK_LIST.SET_DIFFERENCE,
                FK_LIST.STD,
                FK_LIST.VAR,
                FK_LIST.SHIFT,
                FK_LIST.DIFF,
                FK_LIST.CONCAT,
                FK_LIST.JOIN,
                FK_LIST.REVERSE,
                FK_LIST.SLICE,
                FK_LIST.HEAD,
                FK_LIST.TAIL,
                FK_LIST.EXPLODE,
            ),
            backends=("narwhals",),
            summary="Narwhals lacks native list operations; the mountainash narwhals expression "
                    "system raises BackendCapabilityError (unenriched) for these list ops",
            impact="list.gather_every/arg_min/arg_max/all/any/n_unique/count_matches/drop_nulls/"
                   "set_union/set_intersection/set_difference/std/var/shift/diff/concat/join/reverse/"
                   "slice/head/tail/explode raise on narwhals backends",
            workaround="Use a Polars or Ibis backend for these list operations",
            upstream_ref=None,
            since="2026-08-06",
        ),
        DivergenceFact(
            id="IB-LIST-01",
            kind=DivergenceKind.ENGINE_LENIENCY,
            operation_keys=(
                FK_LIST.GATHER_EVERY,
                FK_LIST.ARG_MIN,
                FK_LIST.ARG_MAX,
                FK_LIST.N_UNIQUE,
                FK_LIST.COUNT_MATCHES,
                FK_LIST.DROP_NULLS,
                FK_LIST.SET_DIFFERENCE,
                FK_LIST.STD,
                FK_LIST.VAR,
                FK_LIST.SHIFT,
                FK_LIST.DIFF,
                FK_LIST.REVERSE,
                FK_LIST.SLICE,
                FK_LIST.HEAD,
                FK_LIST.TAIL,
                FK_LIST.MEDIAN,
            ),
            backends=("ibis",),
            summary="Ibis lacks native array operations for these list ops; the mountainash ibis "
                    "expression system raises BackendCapabilityError (unenriched)",
            impact="list.gather_every/arg_min/arg_max/n_unique/count_matches/drop_nulls/set_difference/"
                   "std/var/shift/diff/reverse/slice/head/tail/median raise on ibis backends",
            workaround="Use a Polars backend for these list operations",
            upstream_ref=None,
            since="2026-08-06",
        ),
        DivergenceFact(
            id="PL-LIST-01",
            kind=DivergenceKind.ENGINE_LENIENCY,
            operation_keys=(FK_LIST.EXPLODE,),
            backends=("polars", "polars-lazy"),
            summary="Polars expression-level list.explode() in a multi-column select raises "
                    "ShapeError: the exploded column's row count diverges from un-exploded siblings",
            impact="col('arr').list.explode() projected alongside a non-exploded sibling column raises "
                   "polars.exceptions.ShapeError on eager and lazy Polars",
            workaround="Explode without a mismatched sibling column, or use an Ibis backend",
            upstream_ref=None,
            since="2026-08-06",
        ),
    )


KNOWN_DIVERGENCES: tuple[DivergenceFact, ...] = _all()
_BY_ID = {divergence.id: divergence for divergence in KNOWN_DIVERGENCES}


def divergence_by_id(divergence_id: str) -> DivergenceFact:
    try:
        return _BY_ID[divergence_id]
    except KeyError:
        raise KeyError(
            f"unknown divergence id {divergence_id!r} — declare it in "
            "core/capabilities/divergences.py and registry/upstream-issues.yaml"
        )
