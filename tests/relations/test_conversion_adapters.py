"""Cross-family coercion preserves native values, dtypes and destination identity."""
from __future__ import annotations

import datetime as dt

import ibis
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma

from mountainash.relations.core.materialization import (
    coerce_narwhals_dialect,
    coerce_to_ibis,
    coerce_to_narwhals,
    coerce_to_polars,
)

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


def _nw_pandas(data: dict):
    return nw.from_native(pd.DataFrame(data), eager_only=True)


def _nw_polars(data: dict, lazy: bool = False):
    native = pl.DataFrame(data)
    if lazy:
        return nw.from_native(native.lazy())
    return nw.from_native(native, eager_only=True)


def _nw_pyarrow(data: dict):
    return nw.from_native(pa.table(data), eager_only=True)


class TestCoerceToPolarsRouteMatrix:
    """Every recognized source family/shape lands as a lazy ``pl.LazyFrame``
    with correct rows, preserved nulls, and preserved dates (item 4.3's
    dtype-fidelity concern: an Arrow route, not a pandas round-trip, must
    not widen ``date32`` to ``datetime64``)."""

    def _assert_result(self, result, expected_rows):
        assert isinstance(result, pl.LazyFrame)
        got = result.collect().sort("id").to_dict(as_series=False)
        assert got == expected_rows

    def test_pandas_source(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        value = pd.DataFrame({"id": [2, 3], "v": [None, 20]})
        result = coerce_to_polars(target, value)
        self._assert_result(result, {"id": [2, 3], "v": [None, 20]})

    def test_pyarrow_source(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        value = pa.table({"id": [2, 3], "v": [None, 20]})
        result = coerce_to_polars(target, value)
        self._assert_result(result, {"id": [2, 3], "v": [None, 20]})

    @pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-sqlite"])
    @pytest.mark.parametrize("endpoint", ["public", "coercion"])
    def test_ibis_source(self, backend_name, backend_factory, endpoint):
        source = backend_factory.create(
            {"id": [1, 2, 3], "value": [10, 20, None]}, backend_name,
        )
        connection = source._find_backend(use_default=False)
        try:
            query = source.filter(source.id > 1).select(source.value.cast("int64").name("value"))
            if endpoint == "public":
                result = ma.relation(query).to_polars()
            else:
                result = coerce_to_polars(pl.DataFrame({"id": [1]}).lazy(), query).collect()
            assert result.schema == {"value": pl.Int64}
            assert result["value"].to_list() == [20, None]
        finally:
            if hasattr(connection, "disconnect"):
                connection.disconnect()

    def test_narwhals_pandas_source(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        value = _nw_pandas({"id": [2, 3], "v": [None, 20]})
        result = coerce_to_polars(target, value)
        self._assert_result(result, {"id": [2, 3], "v": [None, 20]})

    def test_narwhals_pyarrow_source(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        value = _nw_pyarrow({"id": [2, 3], "v": [None, 20]})
        result = coerce_to_polars(target, value)
        self._assert_result(result, {"id": [2, 3], "v": [None, 20]})

    def test_narwhals_lazy_polars_source(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        value = _nw_polars({"id": [2, 3], "v": [None, 20]}, lazy=True)
        result = coerce_to_polars(target, value)
        self._assert_result(result, {"id": [2, 3], "v": [None, 20]})

    def test_dict_source(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        result = coerce_to_polars(target, {"id": [2, 3]})
        self._assert_result(result, {"id": [2, 3]})

    def test_list_of_dict_source(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        result = coerce_to_polars(target, [{"id": 2}, {"id": 3}])
        self._assert_result(result, {"id": [2, 3]})

    def test_polars_lazyframe_source_passthrough(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        value = pl.DataFrame({"id": [2]}).lazy()
        assert coerce_to_polars(target, value) is value

    def test_polars_dataframe_source_lazified(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        value = pl.DataFrame({"id": [2]})
        result = coerce_to_polars(target, value)
        assert isinstance(result, pl.LazyFrame)
        assert result.collect().to_dict(as_series=False) == {"id": [2]}

    def test_date_column_preserved(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        value = pa.table({"d": pa.array([dt.date(2024, 1, 1)], type=pa.date32())})
        result = coerce_to_polars(target, value)
        assert result.collect_schema()["d"] == pl.Date

    def test_unrecognized_source_raises(self):
        target = pl.DataFrame({"id": [1]}).lazy()
        with pytest.raises(Exception, match="Cannot coerce"):
            coerce_to_polars(target, object())


class TestCoerceToNarwhalsRouteMatrix:
    """Mappings preserve values in the target's native namespace."""

    def test_dict_source_builds_target_namespace_directly(self):
        target = _nw_polars({"id": [1]})
        result = coerce_to_narwhals(target, {"id": [2, 3]})
        assert nw.get_native_namespace(result).__name__ == "polars"
        assert result.to_native().to_dict(as_series=False) == {"id": [2, 3]}

    def test_dict_source_preserves_pandas_target(self):
        target = _nw_pandas({"id": [1]})
        result = coerce_to_narwhals(target, {"id": [2, 3]})
        assert result.to_native().to_dict("list") == {"id": [2, 3]}

    def test_list_of_dict_source(self):
        target = _nw_polars({"id": [1]})
        result = coerce_to_narwhals(target, [{"id": 2}, {"id": 3}])
        assert result.to_native().to_dict(as_series=False) == {"id": [2, 3]}

    def test_ibis_source(self):
        target = _nw_polars({"id": [1]})
        con = ibis.duckdb.connect()
        value = con.create_table("t", {"id": [2, 3]})
        result = coerce_to_narwhals(target, value)
        assert sorted(result.to_native().to_dict(as_series=False)["id"]) == [2, 3]

    def test_polars_lazyframe_source_collects_then_matches(self):
        target = _nw_polars({"id": [1]})
        value = pl.DataFrame({"id": [2, 3]}).lazy()
        result = coerce_to_narwhals(target, value)
        assert nw.get_native_namespace(result).__name__ == "polars"
        assert result.to_native().to_dict(as_series=False) == {"id": [2, 3]}

    def test_raw_pyarrow_source(self):
        target = _nw_pyarrow({"id": [1]})
        value = pa.table({"id": [2, 3]})
        result = coerce_to_narwhals(target, value)
        assert nw.get_native_namespace(result).__name__ == "pyarrow"

    def test_unconvertible_source_raises(self):
        target = _nw_polars({"id": [1]})
        with pytest.raises(Exception, match="Cannot coerce"):
            coerce_to_narwhals(target, object())


class TestCoerceToIbisRouteMatrix:
    """Mappings and native inputs retain their values when imported into Ibis."""

    def test_dict_source(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        result = coerce_to_ibis(target, {"id": [2, 3]})
        assert isinstance(result, ibis.expr.types.Table)
        assert sorted(result.to_pyarrow()["id"].to_pylist()) == [2, 3]

    def test_list_of_dict_source(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        result = coerce_to_ibis(target, [{"id": 2}, {"id": 3}])
        assert sorted(result.to_pyarrow()["id"].to_pylist()) == [2, 3]

    def test_narwhals_lazy_source(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        value = _nw_polars({"id": [2, 3]}, lazy=True)
        result = coerce_to_ibis(target, value)
        assert sorted(result.to_pyarrow()["id"].to_pylist()) == [2, 3]

    def test_narwhals_eager_source_passthrough(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        value = _nw_pandas({"id": [2, 3]})
        result = coerce_to_ibis(target, value)
        assert sorted(result.to_pandas()["id"].tolist()) == [2, 3]

    def test_pandas_source_direct_no_arrow_detour(self):
        """A pandas value is itself the selected source family -- passed to
        ``ibis.memtable()`` directly, no Arrow detour."""
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        value = pd.DataFrame({"id": [2, 3]})
        result = coerce_to_ibis(target, value)
        assert sorted(result.to_pandas()["id"].tolist()) == [2, 3]

    def test_unconvertible_source_raises(self):
        con = ibis.duckdb.connect()
        target = con.create_table("t", {"id": [1]})
        with pytest.raises(Exception, match="Cannot coerce"):
            coerce_to_ibis(target, object())


class TestCoerceNarwhalsDialect:
    """Destination-specific ``to_pandas()``/``to_polars()``/``to_arrow()``
    only for the matching dialect (spec 9.1); a lazy target is always
    rejected regardless of the operand's shape."""

    def test_same_dialect_same_shape_is_noop(self):
        target = _nw_polars({"id": [1]})
        value = _nw_polars({"id": [2]})
        assert coerce_narwhals_dialect(target, value) is value

    def test_mismatched_dialect_converts_to_target(self):
        target = _nw_pandas({"id": [1]})
        value = _nw_polars({"id": [2, 3]})
        result = coerce_narwhals_dialect(target, value)
        assert nw.get_native_namespace(result).__name__ == "pandas"
        assert sorted(result.to_native()["id"].tolist()) == [2, 3]

    def test_lazy_value_collected_before_dialect_match(self):
        target = _nw_pandas({"id": [1]})
        value = _nw_polars({"id": [2, 3]}, lazy=True)
        result = coerce_narwhals_dialect(target, value)
        assert nw.get_native_namespace(result).__name__ == "pandas"

    def test_lazy_target_always_rejected(self):
        target = _nw_polars({"id": [1]}, lazy=True)
        value = _nw_pandas({"id": [2]})
        with pytest.raises(Exception, match="lazy"):
            coerce_narwhals_dialect(target, value)

    def test_non_narwhals_inputs_are_noop(self):
        value = {"id": [1]}
        assert coerce_narwhals_dialect(object(), value) is value


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("endpoint", ["public", "coercion"])
def test_polars_conversion_keeps_named_index_out_of_columns(wrapped, endpoint):
    """Native and wrapped pandas must not expose index metadata as data columns."""
    source = pd.DataFrame(
        {"id": [2, 3], "value": [10, None]},
        index=pd.Index([7, 9], name="row_key"),
    )
    if wrapped:
        source = nw.from_native(source)
    if endpoint == "public":
        result = ma.relation(source).to_polars()
    else:
        result = coerce_to_polars(pl.DataFrame({"id": [1]}).lazy(), source).collect()
    assert result.to_dict(as_series=False) == {"id": [2, 3], "value": [10.0, None]}
    assert result.columns == ["id", "value"]
    assert result.schema == {"id": pl.Int64, "value": pl.Float64}


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("endpoint", ["public", "coercion"])
def test_polars_conversion_preserves_native_object_identity(wrapped, endpoint):
    """Native and wrapped Polars objects must not acquire an Arrow representation."""
    token = object()
    source = pl.DataFrame({"obj": pl.Series([token, None], dtype=pl.Object)})
    if wrapped:
        source = nw.from_native(source)
    if endpoint == "public":
        result = ma.relation(source).to_polars()
    else:
        result = coerce_to_polars(pl.DataFrame({"id": [1]}).lazy(), source).collect()
    assert result.schema == {"obj": pl.Object}
    assert result["obj"][0] is token
    assert result["obj"][1] is None
