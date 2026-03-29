"""
Parametrized tests for SchemaConfig.apply() across backends and transform types.

Covers:
- Cast transforms: backend × universal type combinations
- Rename transforms: all 5 backends
- Null fill transforms: Polars, Pandas, Narwhals
- Multi-transform: combined cast + rename + null_fill on Polars
- keep_only_mapped: extra columns are dropped
"""
from __future__ import annotations

import pytest
import polars as pl
import pandas as pd
import pyarrow as pa

from mountainash.schema.config.schema_config import SchemaConfig


# ============================================================================
# DataFrame factory helpers
# ============================================================================

def _polars_df(col_name: str, values: list) -> pl.DataFrame:
    return pl.DataFrame({col_name: values, "extra": [1] * len(values)})


def _pandas_df(col_name: str, values: list) -> pd.DataFrame:
    return pd.DataFrame({col_name: values, "extra": [1] * len(values)})


def _pyarrow_table(col_name: str, values: list):
    return pa.table({col_name: values, "extra": [1] * len(values)})


def _narwhals_df(col_name: str, values: list):
    import narwhals as nw
    return nw.from_native(pl.DataFrame({col_name: values, "extra": [1] * len(values)}))


def _ibis_table(col_name: str, values: list):
    import ibis
    return ibis.memtable({col_name: values, "extra": [1] * len(values)})


# ============================================================================
# Source data (all string values so casts have something to do)
# ============================================================================

CAST_SOURCE: dict[str, list[str]] = {
    "string":   ["hello", "world", "test"],
    "integer":  ["1", "2", "3"],
    "number":   ["1.5", "2.5", "3.5"],
    "boolean":  ["true", "false", "true"],
    "date":     ["2024-01-01", "2024-06-15", "2024-12-31"],
    "datetime": ["2024-01-01T00:00:00", "2024-06-15T12:30:00", "2024-12-31T23:59:59"],
}

# Which (backend_label, utype) combos are expected to work without error.
# Combos NOT in this set are marked xfail(strict=False).
#
# Known production bugs / limitations:
#   polars/narwhals boolean: Polars cannot cast Utf8View → Boolean
#                            (InvalidOperationError: casting from Utf8View to Boolean not supported)
#   pandas-*:  CastSchemaFactory backend-detection broken for pandas.DataFrame
#              (factory raises "No strategy key found for data of type pandas.DataFrame")
#   pyarrow-*: cast_schema_pyarrow.py imports wrong module name
#              (ModuleNotFoundError: 'schema_transform_narwhals' not found)
#   ibis-*:    CastSchemaIbis._col() calls ibis.col() which doesn't exist
#              (AttributeError: module 'ibis' has no attribute 'col')
SUPPORTED_CAST_COMBOS: set[tuple[str, str]] = {
    # Polars — string/integer/number/date/datetime work; boolean broken (Utf8View→Boolean)
    ("polars", "string"),
    ("polars", "integer"),
    ("polars", "number"),
    ("polars", "date"),
    ("polars", "datetime"),
    # Narwhals — string/integer/number/date/datetime work; boolean broken (same Polars issue)
    ("narwhals", "string"),
    ("narwhals", "integer"),
    ("narwhals", "number"),
    ("narwhals", "date"),
    ("narwhals", "datetime"),
    # Pandas, PyArrow, Ibis: production bugs prevent any cast from working
    # (added as xfail below via _BROKEN_BACKENDS)
}

_ALL_BACKENDS = ["polars", "pandas", "narwhals", "pyarrow", "ibis"]
_ALL_UTYPES   = ["string", "integer", "number", "boolean", "date", "datetime"]

# Backends with known production bugs that block all casts.
_BROKEN_BACKENDS: dict[str, str] = {
    "pandas":  "CastSchemaFactory backend-detection broken for pandas.DataFrame",
    "pyarrow": "cast_schema_pyarrow.py imports missing module 'schema_transform_narwhals'",
    "ibis":    "CastSchemaIbis._col() calls ibis.col() which does not exist",
}


def _make_cast_params():
    """Build pytest.param entries for the cast matrix."""
    params = []
    for backend in _ALL_BACKENDS:
        for utype in _ALL_UTYPES:
            if backend in _BROKEN_BACKENDS:
                # Whole backend is broken — xfail every combo
                mark = [pytest.mark.xfail(
                    strict=False,
                    reason=_BROKEN_BACKENDS[backend],
                )]
            elif (backend, utype) not in SUPPORTED_CAST_COMBOS:
                # Specific backend/type combo is known unsupported
                mark = [pytest.mark.xfail(
                    strict=False,
                    reason=f"{backend} does not reliably cast string→{utype}",
                )]
            else:
                mark = []
            params.append(pytest.param(backend, utype, marks=mark, id=f"{backend}-{utype}"))
    return params


# ============================================================================
# Helpers
# ============================================================================

def _build_cast_df(backend: str, utype: str):
    """Create a DataFrame whose 'col' column contains string values."""
    col_name = "col"
    values = CAST_SOURCE[utype]
    if backend == "polars":
        return _polars_df(col_name, values)
    if backend == "pandas":
        return _pandas_df(col_name, values)
    if backend == "narwhals":
        return _narwhals_df(col_name, values)
    if backend == "pyarrow":
        return _pyarrow_table(col_name, values)
    if backend == "ibis":
        return _ibis_table(col_name, values)
    raise ValueError(f"Unknown backend: {backend}")


def _get_columns(result, backend: str) -> list[str]:
    """Return column names from a result regardless of backend type."""
    if backend == "polars":
        return result.columns
    if backend == "pandas":
        return list(result.columns)
    if backend == "narwhals":
        return result.columns
    if backend == "pyarrow":
        return result.column_names
    if backend == "ibis":
        return result.columns
    raise ValueError(f"Unknown backend: {backend}")


# ============================================================================
# TestCastTransform
# ============================================================================

class TestCastTransform:
    """
    Cast transforms: backend × universal type.

    For each (backend, utype), build a DataFrame with string values,
    apply a cast config, and verify .apply() returns without error.
    """

    @pytest.mark.parametrize("backend,utype", _make_cast_params())
    def test_cast_does_not_crash(self, backend: str, utype: str):
        df = _build_cast_df(backend, utype)
        config = SchemaConfig(columns={"col": {"cast": utype}})
        result = config.apply(df)
        assert result is not None


# ============================================================================
# TestRenameTransform
# ============================================================================

_RENAME_BACKENDS = [
    pytest.param("polars",   id="polars"),
    pytest.param("pandas",   id="pandas",
                 marks=pytest.mark.xfail(strict=False, reason=_BROKEN_BACKENDS["pandas"])),
    pytest.param("narwhals", id="narwhals"),
    pytest.param("pyarrow",  id="pyarrow",
                 marks=pytest.mark.xfail(strict=False, reason=_BROKEN_BACKENDS["pyarrow"])),
    pytest.param("ibis",     id="ibis",
                 marks=pytest.mark.xfail(strict=False, reason=_BROKEN_BACKENDS["ibis"])),
]


class TestRenameTransform:
    """Rename transform across all 5 backends."""

    def _make_df(self, backend: str):
        col_name = "old_name"
        values = ["a", "b", "c"]
        if backend == "polars":
            return pl.DataFrame({col_name: values, "other": [1, 2, 3]})
        if backend == "pandas":
            return pd.DataFrame({col_name: values, "other": [1, 2, 3]})
        if backend == "narwhals":
            import narwhals as nw
            return nw.from_native(pl.DataFrame({col_name: values, "other": [1, 2, 3]}))
        if backend == "pyarrow":
            return pa.table({col_name: values, "other": [1, 2, 3]})
        if backend == "ibis":
            import ibis
            return ibis.memtable({col_name: values, "other": [1, 2, 3]})
        raise ValueError(f"Unknown backend: {backend}")

    @pytest.mark.parametrize("backend", _RENAME_BACKENDS)
    def test_rename_produces_new_column(self, backend: str):
        df = self._make_df(backend)
        config = SchemaConfig(columns={"old_name": {"rename": "new_name"}})
        result = config.apply(df)
        cols = _get_columns(result, backend)
        assert "new_name" in cols, f"Expected 'new_name' in columns, got: {cols}"

    @pytest.mark.parametrize("backend", _RENAME_BACKENDS)
    def test_rename_removes_old_column(self, backend: str):
        df = self._make_df(backend)
        config = SchemaConfig(columns={"old_name": {"rename": "new_name"}})
        result = config.apply(df)
        cols = _get_columns(result, backend)
        assert "old_name" not in cols, f"'old_name' should be gone, got: {cols}"


# ============================================================================
# TestNullFillTransform
# ============================================================================

class TestNullFillTransform:
    """Null fill transforms on backends that support it well."""

    def test_null_fill_polars(self):
        df = pl.DataFrame({"val": [1.0, None, 3.0], "extra": [10, 20, 30]})
        config = SchemaConfig(columns={"val": {"null_fill": 0.0}})
        result = config.apply(df)
        assert result["val"].null_count() == 0
        assert result["val"][1] == pytest.approx(0.0)

    @pytest.mark.xfail(
        strict=False,
        reason=_BROKEN_BACKENDS["pandas"],
    )
    def test_null_fill_pandas(self):
        df = pd.DataFrame({"val": [1.0, None, 3.0], "extra": [10, 20, 30]})
        config = SchemaConfig(columns={"val": {"null_fill": 0.0}})
        result = config.apply(df)
        assert result["val"].isna().sum() == 0
        assert result["val"].iloc[1] == pytest.approx(0.0)

    def test_null_fill_narwhals(self):
        import narwhals as nw
        base = pl.DataFrame({"val": [1.0, None, 3.0], "extra": [10, 20, 30]})
        df = nw.from_native(base)
        config = SchemaConfig(columns={"val": {"null_fill": 0.0}})
        result = config.apply(df)
        # config.apply returns same-type object; collect to Polars for inspection
        if isinstance(result, (nw.DataFrame, nw.LazyFrame)):
            native = nw.to_native(result)
        else:
            # Narwhals may return native Polars when given a Narwhals-wrapped Polars df
            native = result
        assert native["val"].null_count() == 0
        assert native["val"][1] == pytest.approx(0.0)

    def test_null_fill_integer_polars(self):
        df = pl.DataFrame({"score": [10, None, 30], "extra": ["a", "b", "c"]})
        config = SchemaConfig(columns={"score": {"null_fill": -1}})
        result = config.apply(df)
        assert result["score"].null_count() == 0
        assert result["score"][1] == -1

    def test_null_fill_string_polars(self):
        df = pl.DataFrame({"label": ["x", None, "z"], "extra": [1, 2, 3]})
        config = SchemaConfig(columns={"label": {"null_fill": "unknown"}})
        result = config.apply(df)
        assert result["label"].null_count() == 0
        assert result["label"][1] == "unknown"


# ============================================================================
# TestMultiTransform
# ============================================================================

class TestMultiTransform:
    """Combined transforms on Polars: cast + rename + null_fill."""

    def test_cast_and_rename_polars(self):
        df = pl.DataFrame({"user_id": ["1", "2", "3"], "extra": ["a", "b", "c"]})
        config = SchemaConfig(columns={
            "user_id": {"cast": "integer", "rename": "id"},
        })
        result = config.apply(df)
        assert "id" in result.columns
        assert "user_id" not in result.columns
        assert result["id"].dtype in (pl.Int32, pl.Int64, pl.UInt32, pl.UInt64)

    def test_cast_rename_null_fill_polars(self):
        df = pl.DataFrame({
            "raw_score": ["1.5", None, "3.5"],
            "raw_label": ["foo", "bar", None],
            "extra":     [10, 20, 30],
        })
        config = SchemaConfig(columns={
            "raw_score": {"cast": "number",  "rename": "score",  "null_fill": 0.0},
            "raw_label": {"rename": "label", "null_fill": "n/a"},
        })
        result = config.apply(df)
        assert "score" in result.columns
        assert "label" in result.columns
        assert result["score"].null_count() == 0
        assert result["label"].null_count() == 0
        assert result["label"][2] == "n/a"

    def test_keep_only_mapped_drops_extra_columns(self):
        df = pl.DataFrame({
            "keep_me": ["a", "b", "c"],
            "drop_me": [1, 2, 3],
            "also_drop": [True, False, True],
        })
        config = SchemaConfig(
            columns={"keep_me": {"rename": "kept"}},
            keep_only_mapped=True,
        )
        result = config.apply(df)
        assert result.columns == ["kept"]

    def test_keep_only_mapped_false_preserves_extra_columns(self):
        df = pl.DataFrame({
            "mapped": ["a", "b"],
            "extra1": [1, 2],
            "extra2": [True, False],
        })
        config = SchemaConfig(
            columns={"mapped": {"rename": "renamed"}},
            keep_only_mapped=False,
        )
        result = config.apply(df)
        assert "renamed" in result.columns
        assert "extra1" in result.columns
        assert "extra2" in result.columns

    def test_multi_column_cast_polars(self):
        # Note: boolean cast from Utf8View is a known Polars limitation, so we
        # test only integer and number here. See test_cast_does_not_crash for
        # the xfail coverage of string→boolean.
        df = pl.DataFrame({
            "age":    ["25", "30", "35"],
            "salary": ["50000.0", "75000.5", "90000.0"],
            "label":  ["x", "y", "z"],
        })
        config = SchemaConfig(columns={
            "age":    {"cast": "integer"},
            "salary": {"cast": "number"},
            "label":  {"cast": "string"},
        })
        result = config.apply(df)
        assert result is not None
        assert "age" in result.columns
        assert "salary" in result.columns
        assert "label" in result.columns
