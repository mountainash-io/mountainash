"""Cross-backend tests for execute-mode contract evaluation (item 48 Task 7).

Covers ``UnifiedRelationVisitor.apply_conform``'s data_type-dimension
threading: dtype-aware detection parity, the ``evolve``/``discard_value``/
``discard_row``/``freeze`` policies, and the discard_row row-filter
predicate (finding 12: drop iff the source is non-null AND a null-on-failure
cast of it fails; a legitimately-null source row is always kept).

``evolve`` and ``freeze`` never execute a cast (evolve skips the cast
entirely; freeze raises before compiling), so both work identically across
every backend. ``discard_value``/``discard_row`` compile a
``cast(dtype, failure_behavior=NULL)``, which is a genuine backend
capability gap on narwhals-routed backends (pandas shares the narwhals
ExpressionSystem) and on ibis-sqlite (no TryCast compilation rule) — see
``tests/expressions/cross_backend/test_cast.py::TestCastFailureBehavior``
for the same divergence pinned at the expression layer, and
known-divergences.md #19/#20.
"""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.conform.errors import SchemaDriftError
from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS

# Backends that compile conform's cast expressions through the Narwhals
# ExpressionSystem (plain "pandas" DataFrames share this route — see
# expsys_base.py CONST_VISITOR_BACKENDS.PANDAS routing) and therefore hit
# the same "Narwhals Expr.cast has no strict/failure-behavior parameter"
# capability gap as tests/expressions/cross_backend/test_cast.py.
_NARWHALS_ROUTED_BACKENDS = {"pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy"}


def _as_float_list(values):
    """Normalize a mixed int/float/None list for cross-backend comparison.

    Ibis's null-on-failure cast round-trips through pyarrow as a nullable
    float column even for an integer declared type (observed: DuckDB and
    Polars ibis backends), while Polars keeps the declared int dtype. Both
    are correct realisations of "cast succeeded / failed" — only the
    numeric identity matters here, not the exact dtype.
    """
    return [None if v is None else float(v) for v in values]


# ---------------------------------------------------------------------------
# Detection parity — same ConformDrift shape from the same declared-vs-actual
# mismatch, independent of which backend produced the actual-dtype evidence.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ["polars", "pandas", "ibis-duckdb"])
class TestDetectionParity:
    def test_string_declared_integer_detected_identically(self, backend_name, backend_factory):
        from mountainash.conform.expressions import resolve_conform_output
        from mountainash.relations.schema_inference import _schema_from_dataframe

        df = backend_factory.create({"n": ["1", "2", "3"]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])

        actual_dtypes = _schema_from_dataframe(df)
        assert actual_dtypes.get("n") is MountainashDtype.STRING, (
            f"[{backend_name}] expected STRING evidence, got {actual_dtypes!r} "
            "-- _schema_from_dataframe should yield real dtypes for this backend."
        )

        output_contract = resolve_conform_output(
            spec, available_columns=["n"], actual_dtypes=actual_dtypes,
        )
        assert output_contract.drift is not None
        assert len(output_contract.drift.type_mismatches) == 1
        mismatch = output_contract.drift.type_mismatches[0]
        assert mismatch.name == "n"
        assert mismatch.declared is MountainashDtype.I64
        assert mismatch.actual is MountainashDtype.STRING
        assert mismatch.safety == "unsafe"
        assert mismatch.action == "coerce"  # default data_type policy


# ---------------------------------------------------------------------------
# evolve — no cast is emitted; output keeps the source's actual dtype.
# Never compiles a cast, so this is backend-uniform.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestEvolvePolicy:
    def test_evolve_keeps_source_dtype_and_values(self, backend_name, backend_factory):
        df = backend_factory.create({"n": ["1", "2", "3"]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])

        result = ma.relation(df).conform(spec, contract={"data_type": "evolve"}).to_polars()

        assert result["n"].dtype == pl.String, (
            f"[{backend_name}] evolve must skip the cast -- expected String, "
            f"got {result['n'].dtype}"
        )
        assert result["n"].to_list() == ["1", "2", "3"]


# ---------------------------------------------------------------------------
# discard_value — cast(dtype, failure_behavior=NULL); unparseable values
# become null, parseable values still cast through.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDiscardValuePolicy:
    def test_discard_value_nulls_unparseable(self, backend_name, backend_factory):
        if backend_name in _NARWHALS_ROUTED_BACKENDS:
            pytest.xfail(
                "Narwhals Expr.cast(dtype) has no strict/failure-behavior parameter "
                "(observed narwhals 2.23.0) -- cast always raises on invalid conversion. "
                "mountainash raises BackendCapabilityError for failure_behavior='null' "
                "on this backend. Plain 'pandas' DataFrames compile via the Narwhals "
                "backend and share this limitation. See known-divergences.md."
            )
        if backend_name == "ibis-sqlite":
            pytest.xfail(
                "Ibis compiles failure_behavior='null' to ibis.TryCast, which "
                "ibis-sqlite (observed ibis 12.0.0) has no SQL compilation rule for: "
                "'OperationNotDefinedError: Compilation rule for TryCast operation "
                "is not defined'. Works on ibis-duckdb and ibis-polars. "
                "See known-divergences.md."
            )
        df = backend_factory.create({"n": ["1", "bad", "3"]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])

        result = ma.relation(df).conform(
            spec, contract={"data_type": "discard_value"}
        ).to_polars()

        assert _as_float_list(result["n"].to_list()) == [1.0, None, 3.0], (
            f"[{backend_name}] expected [1, None, 3], got {result['n'].to_list()}"
        )


# ---------------------------------------------------------------------------
# discard_row — same null-on-failure cast, plus a row-drop predicate.
# Finding 12: drop iff source non-null AND the null-cast failed; a
# legitimately-null source row is always kept.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDiscardRowPolicy:
    def test_discard_row_drops_failed_keeps_legit_null(self, backend_name, backend_factory):
        if backend_name in _NARWHALS_ROUTED_BACKENDS:
            pytest.xfail(
                "Narwhals Expr.cast(dtype) has no strict/failure-behavior parameter "
                "(observed narwhals 2.23.0) -- the discard_row row-filter predicate "
                "compiles the same cast(dtype, failure_behavior=NULL) as discard_value "
                "and hits the identical capability gap. See known-divergences.md."
            )
        if backend_name == "ibis-sqlite":
            pytest.xfail(
                "Ibis compiles failure_behavior='null' to ibis.TryCast, which "
                "ibis-sqlite (observed ibis 12.0.0) has no SQL compilation rule for "
                "TryCast -- the discard_row row-filter predicate hits the same gap "
                "as discard_value. See known-divergences.md."
            )
        # id=1 -> "1" (parses); id=2 -> "bad" (non-null, cast fails -> DROP);
        # id=3 -> None (legitimately null -> KEPT, n stays null);
        # id=4 -> "3" (parses).
        df = backend_factory.create(
            {"id": [1, 2, 3, 4], "n": ["1", "bad", None, "3"]}, backend_name
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="n", type=UniversalType.INTEGER)],
            fields_match="open",
        )

        result = ma.relation(df).conform(
            spec, contract={"data_type": "discard_row"}
        ).to_polars()

        assert result["id"].to_list() == [1, 3, 4], (
            f"[{backend_name}] expected id row [1, 3, 4] (id=2 dropped), "
            f"got {result['id'].to_list()}"
        )
        assert _as_float_list(result["n"].to_list()) == [1.0, None, 3.0], (
            f"[{backend_name}] expected n [1, None, 3], got {result['n'].to_list()}"
        )


# ---------------------------------------------------------------------------
# freeze — raises SchemaDriftError before any cast is compiled; the drift
# report is attached to the exception. Backend-uniform (never compiles).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestFreezePolicy:
    def test_freeze_raises_with_drift_attached(self, backend_name, backend_factory):
        df = backend_factory.create({"n": ["1", "2", "3"]}, backend_name)
        spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])

        with pytest.raises(SchemaDriftError) as exc_info:
            ma.relation(df).conform(spec, contract={"data_type": "freeze"}).to_polars()

        drift = exc_info.value.drift
        assert drift is not None
        assert len(drift.type_mismatches) == 1
        mismatch = drift.type_mismatches[0]
        assert mismatch.name == "n"
        assert mismatch.declared is MountainashDtype.I64
        assert mismatch.actual is MountainashDtype.STRING
        assert mismatch.action == "freeze"
