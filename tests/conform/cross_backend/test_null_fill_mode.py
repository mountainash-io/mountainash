"""Cross-backend tests for missing_columns="null_fill" (item 48 Task 10).

A declared field whose source root is entirely absent from the input is,
under this contract mode, emitted as a TYPED null (``ma.lit(None).cast(
declared_canon)``) instead of being skipped. The "typed" part matters
(review finding 11): an untyped all-NULL column is rejected by some
backends (e.g. DuckDB/Ibis reject an ambiguous NULL-typed column), so the
null is always cast to the declared canonical dtype whenever one is known.

Detection/emission is backend-agnostic (it runs entirely on
``available_columns``/canonical dtype tokens, never a compiled expression),
so the structural assertions (which columns are emitted, the drift report)
hold identically across every backend. Enforcement -- actually compiling
``lit(None).cast(dtype)`` -- is exercised per-backend via ``.to_polars()``,
mountainash's universal cross-backend materialization terminal.
"""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.conform.contract import FIELDS_MATCH_PRESETS
from mountainash.conform.drift import ColumnDrift
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS

# Ibis backends: the compiled Ibis schema and SQL are correctly typed
# (verified: `CAST(NULL AS BIGINT)`, `.schema()` reports `int64`), but
# `Relation.to_polars()`'s `result.to_pandas()` -> `pl.from_pandas(...)`
# bridge loses the dtype for an all-NULL column that isn't natively
# float-representable (int64 -> pandas `object`/`float64`, bool ->
# `object`) -- `.to_pyarrow()` preserves it, `.to_pandas()` does not.
# STRING/NUMBER survive because `object`/`float64` already round-trip to
# String/Float64 by coincidence. See known-divergences.md #21.
_IBIS_DTYPE_LOSS_BACKENDS = {"ibis-duckdb", "ibis-polars", "ibis-sqlite"}
_IBIS_DTYPE_LOSS_TYPES = {"integer", "boolean"}

# pandas / narwhals-pandas: mountainash's canonical -> pandas dtype mapping
# targets non-nullable numpy dtypes (int64, bool). Casting an all-null
# column to int64 raises; casting to bool silently maps None -> False
# (data corruption, not just a wrong dtype). Reproduces for any
# null-containing cast on these two backends, not just null_fill -- see
# known-divergences.md #22.
_PANDAS_NULLABLE_CAST_BACKENDS = {"pandas", "narwhals-pandas"}
_PANDAS_NULLABLE_CAST_TYPES = {"integer", "boolean"}


# ---------------------------------------------------------------------------
# Typed null emission -- a handful of representative declared types, each
# cast to the concrete Polars dtype conform declares for it (registry-backed,
# not a guess).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTypedNullEmission:
    @pytest.mark.parametrize(
        "type_id,universal_type,expected_polars_dtype",
        [
            ("integer", UniversalType.INTEGER, pl.Int64),
            ("number", UniversalType.NUMBER, pl.Float64),
            ("string", UniversalType.STRING, pl.String),
            ("boolean", UniversalType.BOOLEAN, pl.Boolean),
        ],
        ids=["integer", "number", "string", "boolean"],
    )
    def test_missing_field_emits_typed_all_null_column(
        self, backend_name, backend_factory, type_id, universal_type, expected_polars_dtype,
    ):
        if (
            backend_name in _PANDAS_NULLABLE_CAST_BACKENDS
            and type_id in _PANDAS_NULLABLE_CAST_TYPES
        ):
            pytest.xfail(
                f"[{backend_name}] casting an all-null column to "
                f"{universal_type.value} maps to a non-nullable numpy dtype "
                f"(int64 raises 'cannot convert float NaN to integer'; bool "
                f"silently coerces None -> False) -- observed on pandas / "
                f"narwhals-pandas (both route through Narwhals' pandas-like "
                f"Series.cast). See known-divergences.md #22."
            )

        df = backend_factory.create({"a": [1, 2, 3]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=universal_type),
            ],
            fields_match="open",
            contract={"missing_columns": "null_fill"},
        )

        result = ma.relation(df).conform(spec).to_polars()

        assert "b" in result.columns, (
            f"[{backend_name}] missing field 'b' should still be emitted "
            f"under missing_columns=null_fill, got columns={result.columns}"
        )
        assert result["b"].is_null().all(), (
            f"[{backend_name}] typed null column 'b' should be all-null, "
            f"got {result['b'].to_list()}"
        )
        # The present field is untouched.
        assert result["a"].to_list() == [1, 2, 3]

        if backend_name in _IBIS_DTYPE_LOSS_BACKENDS and type_id in _IBIS_DTYPE_LOSS_TYPES:
            pytest.xfail(
                f"[{backend_name}] Ibis compiles and schemas the null "
                f"literal correctly (CAST(NULL AS ...), schema reports "
                f"{universal_type.value}), but Relation.to_polars()'s "
                f"to_pandas() bridge loses the dtype for this all-NULL, "
                f"non-float-representable column -- values stay null, only "
                f"the reported dtype is wrong. See known-divergences.md #21."
            )
        assert result["b"].dtype == expected_polars_dtype, (
            f"[{backend_name}] expected typed null column 'b' with dtype "
            f"{expected_polars_dtype}, got {result['b'].dtype}"
        )

    def test_present_field_is_never_null_filled(self, backend_name, backend_factory):
        """null_fill only fires for ABSENT source roots -- a present field's
        real values pass through the ordinary transform pipeline unchanged,
        never replaced by a typed null."""
        df = backend_factory.create({"a": [1, 2, 3]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.INTEGER)],
            fields_match="open",
            contract={"missing_columns": "null_fill"},
        )

        result = ma.relation(df).conform(spec).to_polars()

        assert result["a"].to_list() == [1, 2, 3]
        assert not result["a"].is_null().any()


# ---------------------------------------------------------------------------
# select-mode parity -- null_fill must also work under strict fieldsMatch
# presets once explicitly overridden (the presets themselves never select
# null_fill on their own -- see TestPresetsUnaffected below).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNullFillUnderStrictPresetOverride:
    def test_equal_preset_with_null_fill_override_emits_missing_field(
        self, backend_name, backend_factory,
    ):
        # "equal" normally freezes on a missing field (MissingFieldsError);
        # an explicit contract override selects null_fill instead.
        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.STRING),
            ],
            fields_match="equal",
            contract={"missing_columns": "null_fill"},
        )

        result = ma.relation(df).conform(spec).to_polars()

        assert set(result.columns) == {"a", "b"}
        assert result["b"].dtype == pl.String
        assert result["b"].is_null().all()


# ---------------------------------------------------------------------------
# Drift reporting -- ColumnDrift(action="null_fill") recorded under
# missing_columns. Purely structural (derived from available_columns, never
# a compiled expression), so this is backend-uniform by construction; still
# exercised across the full matrix since collect_with_drift() is itself a
# per-backend terminal.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNullFillDriftRecording:
    def test_missing_field_records_null_fill_column_drift(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.STRING),
            ],
            fields_match="open",
            contract={"missing_columns": "null_fill"},
        )

        collection = ma.relation(df).conform(spec).collect_with_drift()

        assert collection.drift.missing_columns == [
            ColumnDrift(name="b", action="null_fill")
        ], (
            f"[{backend_name}] expected a single null_fill ColumnDrift for "
            f"'b', got {collection.drift.missing_columns!r}"
        )
        # `effective_schema` is derived from the ACTUAL materialized frame
        # (backend-agnostic canonical dtypes) -- confirms 'b' was really
        # emitted as a column, not just reported in the drift structurally.
        assert "b" in collection.effective_schema


# ---------------------------------------------------------------------------
# Preset isolation -- none of the six fields_match presets select
# missing_columns="null_fill" on their own; null_fill only ever fires via an
# explicit contract layer (TypeSpec.contract or conform(contract=...)).
# Plain unit assertions -- no backend/frame involved.
# ---------------------------------------------------------------------------


class TestPresetsUnaffected:
    def test_no_preset_defaults_to_null_fill(self):
        offenders = {
            name: contract.missing_columns
            for name, contract in FIELDS_MATCH_PRESETS.items()
            if contract.missing_columns == "null_fill"
        }
        assert offenders == {}, (
            "missing_columns=null_fill must only be reachable via an explicit "
            f"contract layer, but these presets default to it: {offenders!r}"
        )

    def test_open_preset_still_skips_missing_field_without_override(self):
        # Behavioural regression guard: the "open" preset's default
        # missing_columns="skip" is unaffected by null_fill existing --
        # a missing field is skipped (not emitted as a null column) unless
        # a contract explicitly opts into null_fill.
        df = pl.DataFrame({"a": [1]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.STRING),
            ],
            fields_match="open",
        )

        result = ma.relation(df).conform(spec).to_polars()

        assert set(result.columns) == {"a"}
