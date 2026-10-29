"""Cross-backend tests for cast operation behavior.

Validates that type casting produces correct values consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, SQLite).

Uses canonical mountainash type strings ("i64", "string", "fp64", etc.)
instead of backend-specific types.
"""

import math
import struct
from contextlib import nullcontext

import ibis
import narwhals as nw
import polars as pl
import pytest
import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS, create_ibis_sqlite_table
from _pytest.outcomes import Failed
from ibis.common.exceptions import OperationNotDefinedError
from mountainash.core.types import BackendCapabilityError
from fixtures.call_expectations import expect_call_failure


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToInteger:
    """Test casting to integer types."""

    def test_cast_string_to_int(self, backend_name, backend_factory, collect_expr):
        data = {"value": ["10", "20", "30", "40", "50"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        values = collect_expr(df, expr)
        assert values == [10, 20, 30, 40, 50], f"[{backend_name}] Expected [10, 20, 30, 40, 50], got {values}"

    def test_cast_bool_to_int(self, backend_name, backend_factory, collect_expr):
        data = {"flag": [True, False, True, False, True]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("flag").cast("i64")
        values = collect_expr(df, expr)
        assert values == [1, 0, 1, 0, 1], f"[{backend_name}] Expected [1, 0, 1, 0, 1], got {values}"

    def test_cast_int64_to_int32(self, backend_name, backend_factory, collect_expr):
        data = {"value": [100, 200, 300]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i32")
        values = collect_expr(df, expr)
        assert values == [100, 200, 300], f"[{backend_name}] Expected [100, 200, 300], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToFloat:
    """Test casting to float types."""

    def test_cast_int_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("fp64")
        values = collect_expr(df, expr)
        assert values == [1.0, 2.0, 3.0, 4.0, 5.0], f"[{backend_name}] Expected [1.0, 2.0, 3.0, 4.0, 5.0], got {values}"

    def test_cast_string_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"value": ["1.5", "2.5", "3.5"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("fp64")
        values = collect_expr(df, expr)
        assert values == [1.5, 2.5, 3.5], f"[{backend_name}] Expected [1.5, 2.5, 3.5], got {values}"

    def test_cast_bool_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"flag": [True, False, True]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("flag").cast("fp64")
        values = collect_expr(df, expr)
        assert values == [1.0, 0.0, 1.0], f"[{backend_name}] Expected [1.0, 0.0, 1.0], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToString:
    """Test casting to string type."""

    def test_cast_int_to_string(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3, 100, 999]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("string")
        values = collect_expr(df, expr)
        assert values == ["1", "2", "3", "100", "999"], f"[{backend_name}] Expected string list, got {values}"

    def test_cast_float_to_string(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1.5, 2.0, 3.75]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("string")
        values = collect_expr(df, expr)
        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        assert "1" in values[0] and "5" in values[0], f"[{backend_name}] Expected '1.5', got {values[0]}"

    def test_cast_bool_to_string(self, backend_name, backend_factory, collect_expr):
        data = {"flag": [True, False, True]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("flag").cast("string")
        values = collect_expr(df, expr)
        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        assert values[0] != values[1], f"[{backend_name}] True and False should differ: {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToBoolean:
    """Test casting to boolean type."""

    def test_cast_int_to_bool(self, backend_name, backend_factory, collect_expr):
        data = {"value": [0, 1, 2, -1, 0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("bool")
        values = collect_expr(df, expr)
        assert values == [False, True, True, True, False], f"[{backend_name}] Expected [F,T,T,T,F], got {values}"

    def test_cast_float_to_bool(self, backend_name, backend_factory, collect_expr):
        data = {"value": [0.0, 1.0, 0.5, -0.5, 0.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("bool")
        values = collect_expr(df, expr)
        assert values == [False, True, True, True, False], f"[{backend_name}] Expected [F,T,T,T,F], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastWithNulls:
    """Test casting with null values."""

    @pytest.mark.parametrize("dtype", ["i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64"])
    @pytest.mark.parametrize("operation", ["select", "with_columns"])
    def test_integer_projection_preserves_nulls(
        self, backend_name, backend_factory, dtype, operation, request,
    ):
        import mountainash as mountainash

        data = {"n": [None, 2, 4], "m": [7, 3, 1], "g": ["a", "a", "b"]}
        source = backend_factory.create(data, backend_name)
        expression = ma.col("n").cast(dtype).alias("n")
        if backend_name in {"pandas", "narwhals-pandas"}:
            from pandas.errors import IntCastingNaNError

            request.applymarker(pytest.mark.xfail(
                strict=True,
                raises=IntCastingNaNError,
                reason="252: native Narwhals NumPy-backed float/NaN -> integer cast cannot preserve nulls",
            ))
        result = getattr(mountainash.relation(source), operation)(expression).to_polars()
        expected = data if operation == "with_columns" else {"n": data["n"]}
        assert result.to_dict(as_series=False) == expected
        assert result.schema["n"].is_integer()

    def test_cast_with_null_int_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("fp64")
        values = collect_expr(df, expr)
        assert values[0] == 1.0
        assert values[2] == 3.0
        assert values[4] == 5.0
        assert values[1] is None or (isinstance(values[1], float) and math.isnan(values[1])), (
            f"[{backend_name}] Second value should be null: {values[1]}"
        )
        assert values[3] is None or (isinstance(values[3], float) and math.isnan(values[3])), (
            f"[{backend_name}] Fourth value should be null: {values[3]}"
        )

    def test_cast_with_null_float_to_string(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1.5, None, 3.5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("string")
        values = collect_expr(df, expr)
        assert isinstance(values[0], str), f"[{backend_name}] First should be string: {values[0]}"
        assert isinstance(values[2], str), f"[{backend_name}] Third should be string: {values[2]}"
        assert values[1] is None, f"[{backend_name}] Second value should be null: {values[1]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastInExpressions:
    """Test using cast within larger expressions."""

    def test_cast_then_arithmetic(self, backend_name, backend_factory, collect_expr):
        data = {"value": ["10", "20", "30"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64") * 2
        values = collect_expr(df, expr)
        assert values == [20, 40, 60], f"[{backend_name}] Expected [20, 40, 60], got {values}"

    def test_cast_then_comparison(self, backend_name, backend_factory, collect_expr):
        data = {"value": ["5", "15", "25"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64").gt(10)
        values = collect_expr(df, expr)
        assert values == [False, True, True], f"[{backend_name}] Expected [F,T,T], got {values}"

    def test_arithmetic_then_cast(self, backend_name, backend_factory, collect_expr):
        data = {"a": [10, 20, 30], "b": [3, 3, 3]}
        df = backend_factory.create(data, backend_name)
        expr = (ma.col("a") + ma.col("b")).cast("string")
        values = collect_expr(df, expr)
        assert values == ["13", "23", "33"], f"[{backend_name}] Expected ['13','23','33'], got {values}"

    def test_cast_with_alias(self, backend_name, backend_factory):
        data = {"price": [100, 200, 300]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("price").cast("fp64").name.alias("price_float")
        backend_expr = expr.compile(df)
        if backend_name.startswith("ibis-"):
            result = df.select(backend_expr)
            values = result.to_pyarrow()["price_float"].to_pylist()
        else:
            result = df.select(backend_expr)
            if hasattr(result, "collect"):
                result = result.collect()
            values = result["price_float"].to_list()
        assert values == [100.0, 200.0, 300.0], f"[{backend_name}] Expected [100.0, 200.0, 300.0], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastEdgeCases:
    """Test edge cases for cast operations."""

    def test_cast_same_type(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        values = collect_expr(df, expr)
        assert values == [1, 2, 3], f"[{backend_name}] Expected [1, 2, 3], got {values}"

    def test_cast_zero_values(self, backend_name, backend_factory, collect_expr):
        data = {"value": [0, 0, 0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("string")
        values = collect_expr(df, expr)
        assert len(values) == 3
        for v in values:
            assert "0" in v, f"[{backend_name}] Expected '0' in {v}"

    def test_cast_large_int_to_float(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1000000, 2000000, 3000000]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("fp64")
        values = collect_expr(df, expr)
        assert values == [1000000.0, 2000000.0, 3000000.0], f"[{backend_name}] Expected floats, got {values}"


_FAILURE_NULL_BACKENDS = [
    b if b in ("pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy") else b for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _FAILURE_NULL_BACKENDS)
class TestCastFailureBehavior:
    """Test CastNode.failure_behavior wiring: default THROW vs NULL-on-failure.

    Previously silently dropped by the visitor -- every backend compiled a
    strict cast regardless of the `failure_behavior` requested via the
    fluent `.cast(dtype, failure_behavior=...)` API. The narwhals/pandas gap is
    and ibis-sqlite gap are covered by exact scoped manifestation bindings.
    """

    def test_cast_failure_behavior_null(self, backend_name, backend_factory, collect_expr):
        from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
            CaseFailureBehaviour,
        )

        data = {"value": ["1", "1x", "3"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64", failure_behavior=CaseFailureBehaviour.NULL)
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-pandas', 'narwhals-polars', 'narwhals-lazy') or backend_name == 'ibis-sqlite',
            reason=('NULL-on-cast-failure cannot materialize on the marked provider.' if backend_name in ('pandas', 'narwhals-pandas', 'narwhals-polars', 'narwhals-lazy') else 'NULL-on-cast-failure cannot materialize on the marked provider.'),
            errors=((BackendCapabilityError,) if backend_name in ('pandas', 'narwhals-pandas', 'narwhals-polars', 'narwhals-lazy') else (OperationNotDefinedError,)),
        ):
            values = collect_expr(df, expr)
            assert values == [1, None, 3], f"[{backend_name}] Expected [1, None, 3], got {values}"


_IBIS_DUCKDB_CAST_BACKENDS = [b for b in ALL_BACKENDS]

_SQLITE_LENIENT_CAST_BACKENDS = [b for b in ALL_BACKENDS]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _IBIS_DUCKDB_CAST_BACKENDS)
class TestCastBankersRounding:
    """Float-to-int cast truncation. ibis-duckdb routes through IB-CAST-01
    (DuckDB uses IEEE-754 banker's rounding, not truncation)."""

    def test_cast_float_to_int(self, backend_name, backend_factory, collect_expr):
        data = {"value": [1.1, 2.9, 3.5, -1.7, -2.3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        with expect_call_failure(
            when=backend_name == 'ibis-duckdb',
            reason='Tests expecting truncation-on-cast produce different results on ibis-duckdb.',
            errors=(AssertionError,),
        ):
            values = collect_expr(df, expr)
            assert values == [1, 2, 3, -1, -2], f"[{backend_name}] Expected [1, 2, 3, -1, -2], got {values}"

    def test_cast_negative_float_to_int(self, backend_name, backend_factory, collect_expr):
        data = {"value": [-1.9, -2.1, -3.5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        with expect_call_failure(
            when=backend_name == 'ibis-duckdb',
            reason='Tests expecting truncation-on-cast produce different results on ibis-duckdb.',
            errors=(AssertionError,),
        ):
            values = collect_expr(df, expr)
            assert values == [-1, -2, -3], f"[{backend_name}] Expected [-1, -2, -3], got {values}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _SQLITE_LENIENT_CAST_BACKENDS)
class TestCastThrowSqliteLenient:
    """THROW-on-invalid cast. ibis-sqlite routes through IB-CAST-03 (SQLite CAST
    is inherently lenient — parses the leading numeric prefix instead of raising)."""

    def test_cast_failure_behavior_throw_default(self, backend_name, backend_factory, collect_expr):
        """Default (THROW) behaviour must remain byte-identical: raises on invalid input."""
        data = {"value": ["1", "1x", "3"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64")
        with expect_call_failure(
            when=backend_name == 'ibis-sqlite',
            reason='Strict casts do not raise for malformed input on ibis-sqlite.',
            errors=(Failed,),
        ):
            with pytest.raises(Exception):
                collect_expr(df, expr)

    def test_cast_failure_behavior_throw_explicit(self, backend_name, backend_factory, collect_expr):
        """Explicit failure_behavior=THROW behaves identically to the default."""
        from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
            CaseFailureBehaviour,
        )

        data = {"value": ["1", "1x", "3"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("value").cast("i64", failure_behavior=CaseFailureBehaviour.THROW)
        with expect_call_failure(
            when=backend_name == 'ibis-sqlite',
            reason='Strict casts do not raise for malformed input on ibis-sqlite.',
            errors=(Failed,),
        ):
            with pytest.raises(Exception):
                collect_expr(df, expr)


@pytest.fixture(params=[
    "polars", "polars-lazy", "pandas", "narwhals-polars",
    "narwhals-pandas", "narwhals-lazy", "narwhals-pyarrow",
])
def temporal_cast_provider(request):
    """Native ns inputs avoid Python datetime's microsecond conversion."""
    import narwhals as nw

    def wrap(frame):
        if request.param == "polars":
            return frame
        if request.param == "polars-lazy":
            return frame.lazy()
        if request.param == "pandas":
            return frame.to_pandas()
        if request.param == "narwhals-pandas":
            return nw.from_native(frame.to_pandas())
        if request.param == "narwhals-pyarrow":
            return nw.from_native(frame.to_arrow())
        return nw.from_native(frame.lazy() if request.param == "narwhals-lazy" else frame)

    return request.param, wrap


def _select_temporal(frame, expression):
    import narwhals as nw
    import pandas as pd
    import polars as pl

    compiled = expression.alias("value").compile(frame)
    selected = (nw.from_native(frame) if isinstance(frame, pd.DataFrame) else frame).select(compiled)
    if isinstance(selected, (pl.LazyFrame, nw.LazyFrame)):
        selected = selected.collect()
    return selected.to_arrow()


@pytest.mark.cross_backend
@pytest.mark.parametrize("kind", ["timestamp", "duration"])
@pytest.mark.parametrize("ticks", [[1, 999, 1001, -1, -1001, None], [], [None]],
                         ids=["fractional", "empty", "all-null"])
def test_bare_temporal_cast_preserves_source(temporal_cast_provider, kind, ticks):
    import polars as pl
    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype as D

    _, wrap = temporal_cast_provider
    native = pl.Datetime("ns", "UTC") if kind == "timestamp" else pl.Duration("ns")
    target = D.TIMESTAMP if kind == "timestamp" else D.DURATION
    frame = wrap(pl.DataFrame({"value": pl.Series(ticks, dtype=pl.Int64).cast(native)}))
    out = _select_temporal(frame, ma.col("value").cast(target))
    expected = pa.timestamp("ns", tz="UTC") if kind == "timestamp" else pa.duration("ns")
    assert out.schema.field("value").type == expected
    assert out["value"].cast(pa.int64()).to_pylist() == ticks


@pytest.mark.cross_backend
@pytest.mark.parametrize("shape", ["computed", "native", "chain", "conditional"])
def test_temporal_cast_composition_preserves_parameters(temporal_cast_provider, shape):
    import narwhals as nw
    import polars as pl
    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype as D, TimestampDtype

    provider, wrap = temporal_cast_provider
    frame = wrap(pl.DataFrame({"value": pl.Series([1, -1001, None], dtype=pl.Int64).cast(
        pl.Datetime("ns", "UTC")
    )}))
    value = ma.col("value")
    expected = [1, -1001, None]
    if shape == "computed":
        expression = value.dt.add_microseconds(1).cast(D.TIMESTAMP)
        expected = [1001, -1, None]
    elif shape == "native":
        expression = ma.native(
            pl.col("value") if provider in {"polars", "polars-lazy"} else nw.col("value")
        ).cast(TimestampDtype())
    elif shape == "chain":
        expression = value.cast(D.TIMESTAMP).cast(TimestampDtype())
    else:
        expression = ma.when(value.is_null()).then(value.cast(D.TIMESTAMP)).otherwise(value)
    out = _select_temporal(frame, expression)
    assert out.schema.field("value").type == pa.timestamp("ns", tz="UTC")
    assert out["value"].cast(pa.int64()).to_pylist() == expected


@pytest.mark.cross_backend
@pytest.mark.parametrize("kind", ["timestamp", "duration"])
def test_bare_temporal_cast_retains_microsecond_range(temporal_cast_provider, kind):
    import polars as pl
    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype as D

    _, wrap = temporal_cast_provider
    ticks = [9223372036854776, -9223372036854776, None]
    native = pl.Datetime("us") if kind == "timestamp" else pl.Duration("us")
    target = D.TIMESTAMP if kind == "timestamp" else D.DURATION
    frame = wrap(pl.DataFrame({"value": pl.Series(ticks, dtype=pl.Int64).cast(native)}))
    out = _select_temporal(frame, ma.col("value").cast(target))
    expected = pa.timestamp("us") if kind == "timestamp" else pa.duration("us")
    assert out.schema.field("value").type == expected
    assert out["value"].cast(pa.int64()).to_pylist() == ticks


@pytest.mark.cross_backend
@pytest.mark.parametrize("provider", ["pandas", "pyarrow"])
@pytest.mark.parametrize("ticks", [[1, -1001, None], [], [None]])
def test_opaque_temporal_cast_evaluates_operand_once(provider, ticks):
    import narwhals as nw
    import polars as pl
    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype as D

    source = pl.DataFrame({"value": pl.Series(ticks, dtype=pl.Int64).cast(
        pl.Datetime("ns", "UTC")
    )})
    frame = nw.from_native(source.to_pandas() if provider == "pandas" else source.to_arrow())
    evaluations = []

    def observe(series):
        evaluations.append(len(series))
        return series

    native = nw.col("value").map_batches(observe, return_dtype=nw.Datetime("ns", "UTC"))
    expression = ma.native(native).cast(D.TIMESTAMP).alias("value")
    compiled = expression.compile(frame)
    assert evaluations == []
    out = frame.select(compiled).to_arrow()
    assert evaluations == [len(ticks)]
    assert out.schema.field("value").type == pa.timestamp("ns", tz="UTC")
    assert out["value"].cast(pa.int64()).to_pylist() == ticks


@pytest.mark.cross_backend
@pytest.mark.parametrize("target_kind", ["bare", "partial"])
def test_ibis_native_temporal_cast_preserves_ticks(target_kind):
    # SQL ticks isolate cast behavior from interval/Arrow export limitations.
    import ibis
    from mountainash.core.dtypes import MountainashDtype as D, TimestampDtype

    connection = ibis.duckdb.connect()
    try:
        table = connection.sql(
            "select make_timestamp_ns(x) as value "
            "from (values (1), (999), (1001), (-1), (-1001), (NULL)) q(x)"
        )
        target = D.TIMESTAMP if target_kind == "bare" else TimestampDtype()
        expression = ma.native(table.value).cast(target).alias("value")
        result = table.select(expression.compile(table))
        sql = str(ibis.to_sql(result))
        actual = connection.raw_sql(f"select epoch_ns(value) from ({sql})").fetchall()
        assert actual == [(1,), (999,), (1001,), (-1,), (-1001,), (None,)]
        assert result.schema()["value"].scale == 9
    finally:
        connection.disconnect()


@pytest.mark.cross_backend
def test_temporal_cast_honors_explicit_precision(temporal_cast_provider):
    import narwhals as nw
    import polars as pl
    import pyarrow as pa
    from mountainash.core.dtypes import TimestampDtype

    provider, wrap = temporal_cast_provider
    frame = wrap(pl.DataFrame({"value": pl.Series([1000, -2000, None], dtype=pl.Int64).cast(
        pl.Datetime("ns", "UTC")
    )}))
    native = pl.col("value") if provider in {"polars", "polars-lazy"} else nw.col("value")
    expression = ma.native(native).cast(TimestampDtype(6, True, "UTC"))
    out = _select_temporal(frame, expression)
    assert out.schema.field("value").type == pa.timestamp("us", tz="UTC")
    assert out["value"].cast(pa.int64()).to_pylist() == [1, -2, None]


@pytest.fixture(params=["narwhals-duckdb", "narwhals-dask"])
def lazy_temporal_cast_provider(request):
    import narwhals as nw

    if request.param == "narwhals-duckdb":
        import duckdb

        with duckdb.connect() as connection:
            yield lambda frame: nw.from_native(connection.from_arrow(frame.to_arrow()))
    else:
        import dask.dataframe as dd

        yield lambda frame: nw.from_native(dd.from_pandas(frame.to_pandas(), npartitions=1))


@pytest.mark.parametrize("partial", [False, True])
@pytest.mark.parametrize("shape", ["field", "native", "computed"])
@pytest.mark.parametrize("ticks", [[1, 999, 1001, -1, -1001, None], [], [None]])
def test_lazy_provider_temporal_binding(lazy_temporal_cast_provider, partial, shape, ticks):
    import narwhals as nw
    import polars as pl
    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype, TimestampDtype

    source = pl.DataFrame({"value": pl.Series(ticks, dtype=pl.Int64).cast(pl.Datetime("ns"))})
    frame = lazy_temporal_cast_provider(source)
    expression = ma.native(nw.col("value")) if shape == "native" else ma.col("value")
    if shape == "computed":
        expression = ma.coalesce(expression, ma.col("value"))
    target = TimestampDtype() if partial else MountainashDtype.TIMESTAMP
    result = _select_temporal(frame, expression.cast(target))
    assert result.schema.field("value").type == pa.timestamp("ns")
    assert result["value"].cast(pa.int64()).to_pylist() == ticks


@pytest.mark.parametrize("provider", ["ibis-duckdb", "narwhals-duckdb"])
def test_duckdb_aware_conversion_has_exact_destination_precision(provider):
    """TIMESTAMPTZ ingestion loses sub-us digits; a cast must add no further loss."""
    import duckdb
    import ibis
    import narwhals as nw
    import pyarrow as pa
    from mountainash import relation
    from mountainash.core.dtypes import MountainashDtype

    ticks = [1, 999, 1001, -1, -1001, None]
    expected = [0, 0, 1000, 0, -1000, None]
    source = pa.table({"value": pa.array(ticks, type=pa.timestamp("ns", tz="UTC"))})
    if provider == "ibis-duckdb":
        connection = ibis.duckdb.connect()
        try:
            frame = connection.create_table("temporal_source", source)
            native = connection.con.sql(
                'SELECT epoch_ns("value") FROM temporal_source'
            ).fetchall()
            result = relation(frame).select(
                ma.col("value").cast(MountainashDtype.TIMESTAMP)
            ).to_pyarrow()
        finally:
            connection.disconnect()
    else:
        with duckdb.connect() as connection:
            frame = connection.from_arrow(source)
            native = frame.select('epoch_ns("value")').fetchall()
            result = _select_temporal(
                nw.from_native(frame), ma.col("value").cast(MountainashDtype.TIMESTAMP),
            )
    assert [row[0] for row in native] == expected
    assert result.schema.field("value").type.unit == "us"
    assert result["value"].cast(pa.timestamp("ns", tz="UTC")).cast(pa.int64()).to_pylist() == expected


def test_explicit_polars_precision_uses_signed_native_conversion():
    import polars as pl
    import pyarrow as pa
    from mountainash.core.dtypes import TimestampDtype

    source = pl.DataFrame({"value": pl.Series([1, 999, 1001, -1, -1001, None], dtype=pl.Int64).cast(
        pl.Datetime("ns")
    )})
    result = _select_temporal(source, ma.col("value").cast(TimestampDtype(6, False)))
    assert result.schema.field("value").type == pa.timestamp("us")
    assert result["value"].cast(pa.int64()).to_pylist() == [0, 0, 1, -1, -2, None]


def test_dask_temporal_binding_does_not_evaluate_partitions():
    import dask.dataframe as dd
    import narwhals as nw
    import polars as pl
    import pyarrow as pa
    from dask import delayed
    from mountainash.core.dtypes import MountainashDtype

    reads = []
    expected = pl.DataFrame({"value": pl.Series([1, -1001, None], dtype=pl.Int64).cast(pl.Duration("ns"))})
    pandas_frame = expected.to_pandas()

    @delayed
    def load():
        reads.append("partition")
        return pandas_frame

    frame = nw.from_native(dd.from_delayed([load()], meta=pandas_frame.iloc[:0]))
    compiled = ma.native(nw.col("value")).cast(MountainashDtype.DURATION).alias("value").compile(frame)
    selected = frame.select(compiled)
    assert reads == []
    result = selected.collect().to_arrow()
    assert reads == ["partition"]
    assert result.schema.field("value").type == pa.duration("ns")
    assert result["value"].cast(pa.int64()).to_pylist() == [1, -1001, None]


def test_duckdb_temporal_binding_does_not_evaluate_source():
    import duckdb
    import narwhals as nw
    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype

    reads = []

    def observe(value):
        reads.append(value)
        return value

    with duckdb.connect() as connection:
        connection.create_function("observe_ticks", observe, ["BIGINT"], "BIGINT", side_effects=True)
        native = connection.sql(
            "SELECT make_timestamp_ns(observe_ticks(ticks)) AS value FROM (VALUES (1), (-1001)) t(ticks)"
        )
        frame = nw.from_native(native)
        compiled = ma.native(nw.col("value")).cast(MountainashDtype.TIMESTAMP).alias("value").compile(frame)
        selected = frame.select(compiled)
        assert reads == []
        result = selected.collect().to_arrow()
        assert reads == [1, -1001]
        assert result.schema.field("value").type == pa.timestamp("ns")
        assert result["value"].cast(pa.int64()).to_pylist() == [1, -1001]


@pytest.mark.parametrize("temporal_cast_provider", ["polars", "narwhals-polars", "narwhals-pyarrow"], indirect=True)
@pytest.mark.parametrize("container", ["list", "array", "struct"])
def test_nested_bare_temporal_expression_cast(temporal_cast_provider, container):
    import polars as pl
    from mountainash.core.dtypes import ArrayDtype, ListDtype, MountainashDtype, StructDtype

    _, wrap = temporal_cast_provider
    native = pl.Datetime("ns", "UTC")
    if container == "struct":
        column = pl.Series("value", [{"v": 1}, None, {"v": -1001}]).cast(pl.Struct({"v": native}))
        target = StructDtype((("v", MountainashDtype.TIMESTAMP),))
    else:
        column = pl.Series("value", [[1, None], None, [-1001, 1001]]).cast(pl.List(native))
        target = ListDtype(MountainashDtype.TIMESTAMP)
        if container == "array":
            column = column.list.to_array(2)
            target = ArrayDtype(MountainashDtype.TIMESTAMP, (2,))
    frame = column.to_frame()
    result = _select_temporal(wrap(frame), ma.col("value").cast(target))
    actual = pl.from_arrow(result)
    assert actual.schema == frame.schema
    assert actual.equals(frame)


@pytest.mark.parametrize("kind", ["timestamp", "duration"])
def test_dask_source_free_cast_retains_native_integer_unit(kind):
    import dask.dataframe as dd
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype

    frame = nw.from_native(dd.from_pandas(pd.DataFrame({"value": [1, -1001]}), npartitions=1))
    target = MountainashDtype.TIMESTAMP if kind == "timestamp" else MountainashDtype.DURATION
    result = _select_temporal(frame, ma.col("value").cast(target))
    expected_type = pa.timestamp("us") if kind == "timestamp" else pa.duration("ns")
    assert result.schema.field("value").type == expected_type
    assert result["value"].cast(pa.int64()).to_pylist() == [1, -1001]


@pytest.mark.parametrize("provider", ["pyarrow", "pandas"])
@pytest.mark.parametrize("kind", ["timestamp", "duration"])
def test_bare_cast_preserves_second_resolution(provider, kind):
    import narwhals as nw
    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype

    native = pa.timestamp("s") if kind == "timestamp" else pa.duration("s")
    source = pa.table({"value": pa.array([1, -1001, None], type=native)})
    frame = nw.from_native(source if provider == "pyarrow" else source.to_pandas())
    target = MountainashDtype.TIMESTAMP if kind == "timestamp" else MountainashDtype.DURATION
    result = _select_temporal(frame, ma.col("value").cast(target))
    assert result.schema.field("value").type == native
    assert result["value"].cast(pa.int64()).to_pylist() == [1, -1001, None]


@pytest.mark.parametrize("temporal_cast_provider", ["narwhals-pandas", "narwhals-pyarrow"], indirect=True)
def test_temporal_cast_preserves_filtered_operand_cardinality(temporal_cast_provider):
    import narwhals as nw
    import polars as pl
    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype

    _, wrap = temporal_cast_provider
    source = pl.DataFrame({"value": pl.Series([1001, None], dtype=pl.Int64).cast(pl.Datetime("ns"))})
    result = _select_temporal(
        wrap(source), ma.native(nw.col("value").drop_nulls()).cast(MountainashDtype.TIMESTAMP),
    )
    assert result.schema.field("value").type == pa.timestamp("ns")
    assert result["value"].cast(pa.int64()).to_pylist() == [1001]


# ---------------------------------------------------------------------------
# Numeric conversion boundaries: values are preserved through implicit
# preparation and resolved targets; an explicit cast keeps the native semantics
# of its provider.
#
# Expected values are hand-written literals or integer-domain arithmetic, never
# produced by the cast under test. The correct oracle for an out-of-range value
# is rejection (or null in null mode). Providers whose native cast does not
# reject it are recorded as known native limitations (strict expected failures),
# not as correct behavior and not as a runtime contract. Outcomes outside this
# scope stay as they are: float -> integer fractional handling, lexical/decimal/
# temporal casts, and existing refusals (Narwhals null mode, SQLite try_cast).
# ---------------------------------------------------------------------------

from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (  # noqa: E402
    CaseFailureBehaviour as _FailureBehaviour,
)

_INTEGER_DOMAINS = {
    "i8": (pl.Int8, -128, 127),
    "i16": (pl.Int16, -32768, 32767),
    "i32": (pl.Int32, -2147483648, 2147483647),
    "i64": (pl.Int64, -9223372036854775808, 9223372036854775807),
    "u8": (pl.UInt8, 0, 255),
    "u16": (pl.UInt16, 0, 65535),
    "u32": (pl.UInt32, 0, 4294967295),
    "u64": (pl.UInt64, 0, 18446744073709551615),
}
_DTYPES = {name: domain[0] for name, domain in _INTEGER_DOMAINS.items()} | {
    "f32": pl.Float32, "f64": pl.Float64,
}
_CAST_NAMES = {"f32": "fp32", "f64": "fp64"}
# 2**53 + 1 is not representable as Float64: a Float64 intermediary corrupts it.
_BEYOND_FLOAT64_EXACT = 9007199254740993


def _f32(value):
    """The Float32 nearest to a Python float (IEEE round-to-nearest-even)."""
    return struct.unpack("f", struct.pack("f", value))[0]


_F32_MAX = 3.4028234663852886e38  # 2**128 - 2**104
# Half a Float32 ulp at the top is 2**103: below it rounds to the maximum, a tie
# rounds to even (infinity), so only the first is a legitimate rounding.
_ROUNDS_DOWN_TO_F32_MAX = _F32_MAX + 2.0**102
_ROUNDS_UP_TO_INFINITY = _F32_MAX + 2.0**103

_SQLITE = "ibis-sqlite"
_WRAPPING_INTEGER_BACKENDS = frozenset({_SQLITE, "pandas", "narwhals-pandas"})
_NATIVE_INTEGER_WRAP = (
    "Known native limitation: this provider's cast wraps or narrows an out-of-range "
    "integer instead of rejecting it (SQLite width, NumPy-backed pandas)."
)
_NATIVE_FLOAT32_INFINITY = (
    "Known native limitation: this provider's Float64 -> Float32 cast yields infinity "
    "for a finite out-of-range value; only DuckDB rejects it."
)
_NULL_MODE_REFUSALS = {
    **dict.fromkeys(("pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy"), BackendCapabilityError),
    _SQLITE: OperationNotDefinedError,
}
_REFUSALS = (BackendCapabilityError, NotImplementedError, OperationNotDefinedError)
_NO_SQLITE = [name for name in ALL_BACKENDS if name != _SQLITE]
# SQLite has no list storage; all registered list-capable carriers participate.
_LIST_ELEMENT_BACKENDS = _NO_SQLITE


def _cast_name(name):
    return _CAST_NAMES.get(name, name)


def _cells(pairs):
    """Backend x (source, target) cells.

    SQLite has one signed 64-bit INTEGER and one 64-bit REAL storage class, so
    only Int64/Float64 sources can be constructed there.
    """
    return [
        pytest.param(backend, source, target, id=f"{backend}-{source}-{target}")
        for backend in ALL_BACKENDS
        for source, target in pairs
        if backend != _SQLITE or source in {"i64", "f64"}
    ]


def _narrowing_pairs():
    """Integer (source, target) pairs whose target domain does not cover the source's."""
    return [
        (source, target)
        for source, (_, source_lo, source_hi) in _INTEGER_DOMAINS.items()
        for target, (_, target_lo, target_hi) in _INTEGER_DOMAINS.items()
        if source in _MATRIX_SOURCES and not (target_lo <= source_lo and source_hi <= target_hi)
    ]


_MATRIX_SOURCES = ("i64", "i32", "u32", "u64")
_NARROWING = _narrowing_pairs()
_WIDENING = [
    ("i8", "i64"), ("i32", "i64"), ("u8", "i16"), ("u32", "i64"), ("u32", "u64"),
    ("i64", "i64"), ("u64", "u64"), ("f32", "f64"), ("f32", "f32"), ("f64", "f64"),
]
_NULL_MODE_PAIRS = [("i64", "i8"), ("i64", "u8"), ("i64", "u64"), ("u64", "i64"), ("u32", "i16")]
_EMPTY_PAIRS = [("i64", "i8"), ("i64", "u64"), ("u64", "i64"), ("f64", "f32"), ("f64", "i32")]


def _integer_cases(source, target):
    """Representable bounds and the immediately out-of-range values of a narrowing."""
    _, source_lo, source_hi = _INTEGER_DOMAINS[source]
    _, target_lo, target_hi = _INTEGER_DOMAINS[target]
    lo, hi = max(source_lo, target_lo), min(source_hi, target_hi)
    passing = {lo, hi, 0}
    if lo <= _BEYOND_FLOAT64_EXACT <= hi:
        passing.add(_BEYOND_FLOAT64_EXACT)
    rejected = {
        value for value in (target_lo - 1, target_hi + 1, source_lo, source_hi)
        if source_lo <= value <= source_hi and not target_lo <= value <= target_hi
    }
    return sorted(passing), sorted(rejected)


def _typed_frame(backend_name, *columns):
    """A provider frame with exact native column dtypes (factory data is Int64/Float64 only)."""
    frame = pl.DataFrame(list(columns))
    if backend_name == "polars":
        return frame
    if backend_name == "polars-lazy":
        return frame.lazy()
    if backend_name == "narwhals-polars":
        return nw.from_native(frame)
    if backend_name == "narwhals-lazy":
        return nw.from_native(frame.lazy())
    if backend_name in {"pandas", "narwhals-pandas"}:
        # NumPy-backed unless nulls or emptiness need Arrow-backed pandas.
        arrow_backed = frame.height == 0 or any(
            column.null_count() or column.dtype.is_nested() for column in columns
        )
        native = frame.to_pandas(use_pyarrow_extension_array=arrow_backed)
        return nw.from_native(native, eager_only=True) if backend_name == "narwhals-pandas" else nw.from_native(native)
    if backend_name == "ibis-duckdb":
        return ibis.duckdb.connect().create_table("typed_cast", frame, overwrite=True)
    if backend_name == _SQLITE:
        return create_ibis_sqlite_table(ibis.sqlite.connect(":memory:"), "typed_cast", frame)
    raise ValueError(backend_name)


def _numeric_frame(backend_factory, backend_name, values, source):
    if source == "i64":
        return backend_factory.create({"value": values}, backend_name)
    return _typed_frame(backend_name, pl.Series("value", values, dtype=_DTYPES[source]))


def _project(frame, expression):
    import mountainash as mountainash

    return mountainash.relation(frame).select(expression.name.alias("result")).to_polars()["result"]


def _native_value(backend_name, frame):
    if backend_name in {"polars", "polars-lazy"}:
        return ma.native(pl.col("value"))
    if backend_name.startswith("ibis-"):
        return ma.native(frame["value"])
    return ma.native(nw.col("value"))


def _assert_physical(series, expected, backend_name):
    if backend_name == _SQLITE:
        assert series.dtype.is_integer() if expected.is_integer() else series.dtype.is_float()
    else:
        assert series.dtype == expected, f"[{backend_name}] {series.dtype} != {expected}"


def _assert_rejected(frame, expression, value):
    """A real conversion failure, not a capability refusal standing in for one."""
    with pytest.raises(Exception) as raised:
        _project(frame, expression)
    assert not isinstance(raised.value, _REFUSALS), f"{value!r} was refused, not rejected: {raised.value!r}"


def _assert_floats(actual, expected):
    assert len(actual) == len(expected), (actual, expected)
    for got, want in zip(actual, expected, strict=True):
        if want is None:
            assert got is None, (actual, expected)
        elif math.isnan(want):
            assert got is not None and math.isnan(got), (actual, expected)
        else:
            assert got == want and math.copysign(1.0, got) == math.copysign(1.0, want), (actual, expected)


def _cast(target, failure):
    kwargs = {"failure_behavior": _FailureBehaviour.NULL} if failure == "null" else {}
    return ma.col("value").cast(_cast_name(target), **kwargs)


def _null_mode_outcome(backend_name):
    """Null mode on Narwhals and SQLite stays an existing refusal; native success is not promotion."""
    error = _NULL_MODE_REFUSALS.get(backend_name)
    return expect_call_failure(
        when=error is not None,
        reason="NULL-on-cast-failure is refused on this provider (existing capability).",
        errors=(error,) if error else (),
    )


def _sqlite_width_unenforced(backend_name):
    # Failed is pytest.raises' no-exception outcome, NOT AssertionError. Valid
    # controls and refusal/type assertions must still fail normally.
    return expect_call_failure(
        when=backend_name in _WRAPPING_INTEGER_BACKENDS, reason=_NATIVE_INTEGER_WRAP, errors=(Failed,),
    )


def _float32_overflow_unenforced(backend_name, *, when=True):
    return expect_call_failure(
        when=when and backend_name != "ibis-duckdb", reason=_NATIVE_FLOAT32_INFINITY, errors=(Failed,),
    )


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name,source,target", _cells(_NARROWING))
def test_integer_narrowing_keeps_bounds_and_rejects_overflow(
    backend_name, source, target, backend_factory,
):
    """Representable bounds pass; exact native wrapping limitations stay explicit."""
    passing, rejected = _integer_cases(source, target)
    expression = _cast(target, "throw")
    result = _project(_numeric_frame(backend_factory, backend_name, passing, source), expression)
    assert result.to_list() == passing
    _assert_physical(result, _DTYPES[target], backend_name)
    with _sqlite_width_unenforced(backend_name):
        for value in rejected:
            _assert_rejected(_numeric_frame(backend_factory, backend_name, [value], source), expression, value)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name,source,target", _cells(_NULL_MODE_PAIRS))
def test_integer_null_mode_nulls_only_overflow(backend_name, source, target, backend_factory):
    passing, rejected = _integer_cases(source, target)
    cells = sorted([(value, True) for value in passing] + [(value, False) for value in rejected])
    frame = _numeric_frame(backend_factory, backend_name, [value for value, _ in cells], source)
    with _null_mode_outcome(backend_name):
        result = _project(frame, _cast(target, "null"))
        assert result.to_list() == [value if valid else None for value, valid in cells]
        _assert_physical(result, _DTYPES[target], backend_name)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name,source,target", _cells(_WIDENING))
def test_widening_and_same_type_cast_is_exact(backend_name, source, target, backend_factory):
    if source in _INTEGER_DOMAINS:
        _, lo, hi = _INTEGER_DOMAINS[source]
        values = sorted({lo, 0, hi})
        column = pl.Series("value", values, dtype=_DTYPES[source])
    elif source == "f32":
        values = [_f32(1.1), _F32_MAX, 2.0**-149]
        column = pl.Series("value", values, dtype=pl.Float32)
    else:
        values = [1 + 2.0**-40, 1e100, -1e-300]
        column = pl.Series("value", values, dtype=pl.Float64)
    frame = (
        backend_factory.create({"value": values}, backend_name) if source in {"i64", "f64"}
        else _typed_frame(backend_name, column)
    )
    result = _project(frame, _cast(target, "throw"))
    assert result.to_list() == values
    _assert_physical(result, _DTYPES[target], backend_name)


@pytest.mark.cross_backend
@pytest.mark.parametrize("failure", ["throw", "null"])
@pytest.mark.parametrize("values", [[], [None]], ids=["empty", "all-null"])
@pytest.mark.parametrize("backend_name,source,target", _cells(_EMPTY_PAIRS))
def test_empty_and_all_null_input_keeps_target_dtype(backend_name, source, target, values, failure):
    """No invented failure, no lost cardinality, and the target physical dtype."""
    frame = _typed_frame(backend_name, pl.Series("value", values, dtype=_DTYPES[source]))
    with _null_mode_outcome(backend_name) if failure == "null" else nullcontext():
        result = _project(frame, _cast(target, failure))
        assert result.to_list() == values
        _assert_physical(result, _DTYPES[target], backend_name)


_FLOAT32_REJECTED = [1e100, -1e100, 2 * _F32_MAX, _ROUNDS_UP_TO_INFINITY]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_float32_finite_overflow_is_rejected(backend_name, backend_factory):
    """A finite Float64 that would become infinity is an error, not a conversion."""
    expression = _cast("f32", "throw")
    valid = _project(backend_factory.create({"value": [1.5, -1.5]}, backend_name), expression)
    assert valid.to_list() == [1.5, -1.5]
    _assert_physical(valid, pl.Float32, backend_name)
    with _float32_overflow_unenforced(backend_name):
        for bad in _FLOAT32_REJECTED:
            _assert_rejected(backend_factory.create({"value": [1.5, bad]}, backend_name), expression, bad)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _NO_SQLITE)
def test_float32_rounding_is_conversion_not_overflow(backend_name, backend_factory):
    """Ordinary destination rounding, including rounding down to the maximum, stays allowed."""
    values = [1 + 2.0**-40, _ROUNDS_DOWN_TO_F32_MAX, -_ROUNDS_DOWN_TO_F32_MAX, 1e-50, 2.0**-149]
    result = _project(backend_factory.create({"value": values}, backend_name), _cast("f32", "throw"))
    assert result.dtype == pl.Float32
    assert result.to_list() == [1.0, _F32_MAX, -_F32_MAX, 0.0, 2.0**-149]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _NO_SQLITE)
def test_float32_cast_retains_existing_special_values(backend_name):
    """Pre-existing NaN/infinity/signed zero/subnormal/null are not newly created overflow."""
    values = [math.nan, math.inf, -math.inf, -0.0, 2.0**-149, None]
    frame = _typed_frame(backend_name, pl.Series("value", values, dtype=pl.Float64))
    result = _project(frame, _cast("f32", "throw"))
    assert result.dtype == pl.Float32
    _assert_floats(result.to_list(), values)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _NO_SQLITE)
def test_float32_null_mode_nulls_only_overflow(backend_name):
    values = [1.5, 1e100, -1e100, None, _ROUNDS_DOWN_TO_F32_MAX, math.inf]
    frame = _typed_frame(backend_name, pl.Series("value", values, dtype=pl.Float64))
    with _null_mode_outcome(backend_name):
        result = _project(frame, _cast("f32", "null"))
        assert result.dtype == pl.Float32
        actual = result.to_list()
        _assert_floats([actual[i] for i in (0, 3, 4, 5)], [1.5, None, _F32_MAX, math.inf])
        with expect_call_failure(
            when=backend_name in {"polars", "polars-lazy"},
            reason="Known native limitation: Polars non-strict Float64 -> Float32 yields infinity, not null.",
            errors=(AssertionError,),
        ):
            assert actual[1:3] == [None, None]


# (target, representable values, immediately out-of-range values): float -> integer
# keeps its existing fractional behavior; only finite out-of-range values are rejected.
_FLOAT_TO_INTEGER = [
    ("i8", [-128.0, 127.0], [-129.0, 128.0]),
    ("u8", [0.0, 255.0], [-1.0, 256.0]),
    ("i32", [-2147483648.0, 2147483647.0], [-2147483649.0, 2147483648.0]),
    ("i64", [-9223372036854775808.0, 9223372036854774784.0], [9223372036854775808.0]),
    ("u64", [0.0, 18446744073709549568.0], [-1.0, 18446744073709551616.0]),
]


# SQLite cannot store an unsigned 64-bit value above its signed INTEGER range.
_FLOAT_TO_INTEGER_CELLS = [
    pytest.param(backend, *case, id=f"{backend}-{case[0]}")
    for backend in ALL_BACKENDS
    for case in _FLOAT_TO_INTEGER
    if backend != _SQLITE or case[0] != "u64"
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name,target,passing,rejected", _FLOAT_TO_INTEGER_CELLS)
def test_float_to_integer_rejects_finite_out_of_range(backend_name, target, passing, rejected, backend_factory):
    expression = _cast(target, "throw")
    result = _project(backend_factory.create({"value": passing}, backend_name), expression)
    assert result.to_list() == [int(value) for value in passing]
    _assert_physical(result, _DTYPES[target], backend_name)
    with _sqlite_width_unenforced(backend_name):
        for bad in rejected:
            _assert_rejected(backend_factory.create({"value": [passing[0], bad]}, backend_name), expression, bad)


# Cast the computed operand, not its source column; native, computed and chained
# operands retain the same native conversion semantics.
_INTEGER_ROUTES = {  # route: (input accepted, input rejected) for ... .cast("i8")
    "column": (127, 128),
    "computed": (126, 127),  # value + 1
    "native": (127, 128),
    "chain": (127, 128),  # cast("u8") first: the second cast sees an unsigned source
}
_FLOAT_ROUTES = {  # route: (input accepted, input rejected, accepted result) for ... .cast("fp32")
    "column": (1e38, 1e39, 1e38),
    "computed": (1e38, 2e38, 2e38),  # value * 2
    "native": (1e38, 1e39, 1e38),
}


def _route_operand(route, backend_name, frame, computed):
    value = ma.col("value")
    if route == "column":
        return value
    if route == "computed":
        return computed(value)
    if route == "native":
        return _native_value(backend_name, frame)
    return value.cast("u8")


@pytest.mark.cross_backend
@pytest.mark.parametrize("route", list(_INTEGER_ROUTES))
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_integer_cast_validates_the_actual_operand(backend_name, route, backend_factory):
    accepted, rejected = _INTEGER_ROUTES[route]

    def expression(frame):
        return _route_operand(route, backend_name, frame, lambda value: value + 1).cast("i8")

    frame = backend_factory.create({"value": [accepted]}, backend_name)
    result = _project(frame, expression(frame))
    assert result.to_list() == [127]
    _assert_physical(result, pl.Int8, backend_name)
    with _sqlite_width_unenforced(backend_name):
        frame = backend_factory.create({"value": [rejected]}, backend_name)
        _assert_rejected(frame, expression(frame), rejected)


@pytest.mark.cross_backend
@pytest.mark.parametrize("route", list(_FLOAT_ROUTES))
@pytest.mark.parametrize("backend_name", _NO_SQLITE)
def test_float32_cast_validates_the_actual_operand(backend_name, route, backend_factory):
    accepted, rejected, accepted_result = _FLOAT_ROUTES[route]

    def expression(frame):
        return _route_operand(route, backend_name, frame, lambda value: value * 2).cast("fp32")

    frame = backend_factory.create({"value": [accepted]}, backend_name)
    result = _project(frame, expression(frame))
    assert result.dtype == pl.Float32
    assert result.to_list() == [_f32(accepted_result)]
    frame = backend_factory.create({"value": [rejected]}, backend_name)
    with _float32_overflow_unenforced(backend_name):
        _assert_rejected(frame, expression(frame), rejected)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _LIST_ELEMENT_BACKENDS)
@pytest.mark.parametrize(
    "element,target,accepted,rejected,expected",
    [(pl.Int64, "i8", 127, 128, 127), (pl.Float64, "fp32", 1.5, 1e100, 1.5)],
    ids=["int64-to-i8", "float64-to-fp32"],
)
def test_list_element_operand_validates_the_extracted_element(
    backend_name, element, target, accepted, rejected, expected,
):
    """Only the selected list element is cast; its sibling must remain irrelevant."""
    def frame_of(first, second):
        return _typed_frame(backend_name, pl.Series("items", [[first, second]], dtype=pl.List(element)))

    result = _project(frame_of(accepted, rejected), ma.col("items").list.get(0).cast(target))
    assert result.to_list() == [expected]
    assert result.dtype == (pl.Int8 if target == "i8" else pl.Float32)
    with _float32_overflow_unenforced(backend_name, when=target == "fp32"):
        _assert_rejected(frame_of(accepted, rejected), ma.col("items").list.get(1).cast(target), rejected)


# ---------------------------------------------------------------------------
# Operand metadata handoff: nested, literal/broadcast, native-computed and
# row-free operands. Observable behavior only.
# ---------------------------------------------------------------------------


def _select_two(frame, first, second):
    import mountainash as mountainash

    return mountainash.relation(frame).select(first.name.alias("first"), second.name.alias("second")).to_polars()


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_nested_narrowing_casts_validate_each_step(backend_name, backend_factory):
    """i64 -> i16 -> i8: the inner result is the outer operand; each step is checked."""
    expression = ma.col("value").cast("i16").cast("i8")
    frame = backend_factory.create({"value": [-128, 127]}, backend_name)
    result = _project(frame, expression)
    assert result.to_list() == [-128, 127]
    _assert_physical(result, pl.Int8, backend_name)
    with _sqlite_width_unenforced(backend_name):
        for bad in (128, -129, 40000):  # outer-only, outer-only, inner (and outer) failure
            _assert_rejected(backend_factory.create({"value": [0, bad]}, backend_name), expression, bad)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_widening_then_narrowing_validates_against_widened_operand(backend_name, backend_factory):
    expression = ma.col("value").cast("i64").cast("i8")
    result = _project(backend_factory.create({"value": [127]}, backend_name), expression)
    assert result.to_list() == [127]
    _assert_physical(result, pl.Int8, backend_name)
    with _sqlite_width_unenforced(backend_name):
        _assert_rejected(backend_factory.create({"value": [128]}, backend_name), expression, 128)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_literal_cast_broadcasts_and_is_validated(backend_name, backend_factory):
    """A literal operand keeps the column's cardinality and its overflow is not silent."""
    frame = backend_factory.create({"value": [1, 2, 3]}, backend_name)
    result = _select_two(frame, ma.col("value"), ma.lit(127).cast("i8"))
    assert result["first"].to_list() == [1, 2, 3]
    assert result["second"].to_list() == [127, 127, 127]
    with _sqlite_width_unenforced(backend_name):
        with pytest.raises(Exception) as raised:
            _select_two(frame, ma.col("value"), ma.lit(128).cast("i8"))
        assert not isinstance(raised.value, _REFUSALS), repr(raised.value)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _NO_SQLITE)
def test_literal_float32_cast_broadcasts_and_is_validated(backend_name, backend_factory):
    frame = backend_factory.create({"value": [1, 2]}, backend_name)
    result = _select_two(frame, ma.col("value"), ma.lit(1.5).cast("fp32"))
    assert result["second"].to_list() == [1.5, 1.5]
    assert result["second"].dtype == pl.Float32
    with _float32_overflow_unenforced(backend_name):
        with pytest.raises(Exception) as raised:
            _select_two(frame, ma.col("value"), ma.lit(1e100).cast("fp32"))
        assert not isinstance(raised.value, _REFUSALS), repr(raised.value)


def _native_computed(backend_name, frame):
    if backend_name in {"polars", "polars-lazy"}:
        return ma.native(pl.col("value") + 1)
    if backend_name.startswith("ibis-"):
        return ma.native(frame["value"] + 1)
    return ma.native(nw.col("value") + 1)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_native_computed_operand_is_validated_by_its_own_value(backend_name, backend_factory):
    """Native arithmetic: the checked value is value + 1, not the source column."""
    def expression(frame):
        return _native_computed(backend_name, frame).cast("i8")

    frame = backend_factory.create({"value": [126]}, backend_name)
    result = _project(frame, expression(frame))
    assert result.to_list() == [127]
    _assert_physical(result, pl.Int8, backend_name)
    with _sqlite_width_unenforced(backend_name):
        frame = backend_factory.create({"value": [127]}, backend_name)
        _assert_rejected(frame, expression(frame), 127)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["polars", "polars-lazy", "pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy", "ibis-duckdb"])
@pytest.mark.parametrize("target", ["i8", "fp32"])
def test_native_operand_cast_keeps_row_free_result_dtype(backend_name, target):
    """A row-free native operand is cast by schema, with no invented failure."""
    source = pl.Int64 if target == "i8" else pl.Float64
    frame = _typed_frame(backend_name, pl.Series("value", [], dtype=source))
    result = _project(frame, _native_value(backend_name, frame).cast(target))
    assert result.to_list() == []
    assert result.dtype == (pl.Int8 if target == "i8" else pl.Float32)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_fractional_float_to_integer_stays_within_neighbouring_integers(backend_name, backend_factory):
    """Control: in-range fractional input is converted (existing semantics), never rejected."""
    frame = backend_factory.create({"value": [2.5, -2.5, 0.25]}, backend_name)
    result = _project(frame, ma.col("value").cast("i8")).to_list()
    assert result[0] in {2, 3}
    assert result[1] in {-3, -2}
    assert result[2] in {0, 1}


@pytest.mark.cross_backend
@pytest.mark.parametrize("target,expected_dtype", [("i64", pl.Int64), ("i8", pl.Int8)], ids=["widening", "narrowing"])
@pytest.mark.parametrize("backend_name", ["narwhals-polars", "narwhals-pandas"])
def test_opaque_native_numeric_operand_is_evaluated_once(backend_name, target, expected_dtype):
    values = [1, -2, 3]
    frame = _typed_frame(backend_name, pl.Series("value", values, dtype=pl.Int32))
    evaluations = []

    def observe(series):
        evaluations.append(len(series))
        return series

    native = nw.col("value").map_batches(observe, return_dtype=nw.Int32)
    compiled = ma.native(native).cast(target).alias("value").compile(frame)
    assert evaluations == []
    result = frame.select(compiled)
    if hasattr(result, "collect"):
        result = result.collect()
    out = pl.from_arrow(result.to_arrow())["value"]
    assert evaluations == [len(values)]
    assert out.to_list() == values
    assert out.dtype == expected_dtype


@pytest.mark.cross_backend
@pytest.mark.parametrize("lazy", [False, True], ids=["eager", "lazy"])
@pytest.mark.parametrize("target", ["i64", "i8"], ids=["widening", "narrowing"])
def test_opaque_polars_native_numeric_operand_is_evaluated_once(lazy, target):
    import mountainash as mountainash

    values = [1, -2, 3]
    source = pl.DataFrame({"value": pl.Series(values, dtype=pl.Int32)})
    source = source.lazy() if lazy else source
    evaluations = []

    def observe(series):
        evaluations.append(len(series))
        return series

    native = pl.col("value").map_batches(observe, return_dtype=pl.Int32)
    query = mountainash.relation(source).select(ma.native(native).cast(target).name.alias("value"))
    assert evaluations == []
    out = query.to_polars()
    if isinstance(out, pl.LazyFrame):
        out = out.collect()
    assert evaluations == [len(values)]
    assert out["value"].to_list() == values
    assert out["value"].dtype == (pl.Int64 if target == "i64" else pl.Int8)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["polars-lazy", "narwhals-lazy"])
@pytest.mark.parametrize("target,expected_dtype", [("i64", pl.Int64), ("i8", pl.Int8), ("fp32", pl.Float32)])
def test_lazy_native_cast_does_not_materialize_source_for_metadata(backend_name, target, expected_dtype):
    """Lazy metadata preparation must not run the source's data pipeline.

    Narwhals map_batches expressions are not supported on LazyFrame; observe
    the lazy source instead, with a supported native computed operand.
    """
    evaluations = []

    def observe(frame):
        evaluations.append(frame.height)
        return frame

    source_dtype = pl.Float64 if target == "fp32" else pl.Int32
    source = pl.DataFrame({"value": pl.Series([1, 2], dtype=source_dtype)}).lazy().map_batches(
        observe, schema={"value": source_dtype},
    )
    if backend_name == "narwhals-lazy":
        source = nw.from_native(source)
        operand = nw.col("value") + 1
    else:
        operand = pl.col("value") + 1
    compiled = ma.native(operand).cast(target).compile(source)
    assert evaluations == []
    projected = source.select(compiled)
    projected.collect_schema()
    assert evaluations == []
    result = pl.from_arrow(projected.collect().to_arrow())
    assert result["value"].to_list() == [2, 3]
    assert result["value"].dtype == expected_dtype
    assert evaluations == [2]
