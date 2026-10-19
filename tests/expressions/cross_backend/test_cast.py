"""Cross-backend tests for cast operation behavior.

Validates that type casting produces correct values consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).

Uses canonical mountainash type strings ("i64", "string", "fp64", etc.)
instead of backend-specific types.
"""

import pytest
import math
import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS
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
