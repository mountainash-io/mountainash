"""Public deferred-execution and export-fidelity contracts for Narwhals providers."""
from __future__ import annotations

from collections import Counter
from contextlib import ExitStack, contextmanager

import duckdb
import narwhals as nw
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma


def _duckdb_relation(connection, query: str):
    return nw.from_native(connection.sql(query))


def _register_witness(connection, reads):
    def witness(value):
        reads.append(value)
        return value

    connection.create_function("ma_witness", witness, [int], int, side_effects=True)


def _observed_duckdb_source(connection, reads, *, size=7):
    _register_witness(connection, reads)
    return _duckdb_relation(
        connection,
        f"SELECT ma_witness(i)::BIGINT AS id, (i * 10)::BIGINT AS paired "
        f"FROM range({size}) AS input(i)",
    )


@contextmanager
def _duckdb_connection():
    connection = duckdb.connect(":memory:")
    try:
        yield connection
    finally:
        connection.close()


@pytest.mark.parametrize("seed", [None, 0, 42])
@pytest.mark.parametrize("n,expected", [(0, 0), (2, 2), (10, 7), (2**100, 7)])
def test_duckdb_sample_is_deferred_and_preserves_complete_rows(seed, n, expected):
    with _duckdb_connection() as connection:
        reads = []
        source = _observed_duckdb_source(connection, reads)
        query = ma.relation(source).sample(n=n, seed=seed).select("id", "paired")

        query.schema
        query.collect_schema()
        query.explain()
        query.compile()
        assert reads == []

        result = query.collect()
        assert isinstance(result, pa.Table)
        rows = result.to_pylist()
        assert len(rows) == expected
        assert len({row["id"] for row in rows}) == expected
        assert all(row["paired"] == row["id"] * 10 for row in rows)
        assert result.schema == pa.schema({"id": pa.int64(), "paired": pa.int64()})
        assert expected == 0 or reads


@pytest.mark.parametrize("fraction,expected", [(0.0, 0), (0.5, 3), (1.0, 7)])
def test_duckdb_fractional_sample_keeps_local_cardinality(fraction, expected):
    with _duckdb_connection() as connection:
        reads = []
        source = _observed_duckdb_source(connection, reads)
        query = ma.relation(source).sample(fraction=fraction, seed=42).select("id", "paired")
        query.compile()
        assert reads == []

        result = query.to_polars()
        assert result.height == expected
        assert all(paired == value * 10 for value, paired in result.iter_rows())


@pytest.mark.parametrize("size,n,expected", [(0, 2, 0), (4, 10, 4)])
def test_duckdb_sample_handles_empty_and_oversized_sources(size, n, expected):
    with _duckdb_connection() as connection:
        reads = []
        source = _observed_duckdb_source(connection, reads, size=size)
        result = ma.relation(source).sample(n=n, seed=42).to_polars()
        assert result.height == expected
        assert all(row["paired"] == row["id"] * 10 for row in result.to_dicts())


@pytest.mark.parametrize("lossless", [False, True], ids=["default-export", "lossless-export"])
@pytest.mark.parametrize(
    "native_type,expression",
    [
        ("boolean", "TRUE"),
        ("tinyint", "1::TINYINT"),
        ("smallint", "1::SMALLINT"),
        ("integer", "1::INTEGER"),
        ("bigint", "1::BIGINT"),
        ("utinyint", "1::UTINYINT"),
        ("usmallint", "1::USMALLINT"),
        ("uinteger", "1::UINTEGER"),
        ("ubigint", "1::UBIGINT"),
        ("float", "1::FLOAT"),
        ("double", "1::DOUBLE"),
        ("decimal", "1.25::DECIMAL(8, 2)"),
        ("null", "NULL"),
        ("blob", "'abc'::BLOB"),
        ("time_ns", "TIME '12:34:56'::TIME_NS"),
        ("date", "DATE '2025-01-02'"),
        ("time", "TIME '12:34:56'"),
        ("timestamp_s", "make_timestamp(1735689600)::TIMESTAMP_S"),
        ("timestamp_ms", "make_timestamp_ms(1735689600000)"),
        ("timestamp_ns", "make_timestamp_ns(1735689600000000000)"),
        ("timestamp_tz", "TIMESTAMPTZ '2025-01-02 03:04:05+02:00'"),
        ("timetz", "TIME WITH TIME ZONE '12:34:56+02:00'"),
        ("uuid", "'550e8400-e29b-41d4-a716-446655440000'::UUID"),
        ("hugeint", "1::HUGEINT"),
        ("uhugeint", "1::UHUGEINT"),
        ("bit", "'10101'::BIT"),
        ("bignum", "'12345678901234567890'::BIGNUM"),
        ("json", "'{\"a\":1}'::JSON"),
        ("enum", "'red'::ENUM('red', 'blue')"),
        ("list", "[1, NULL, 3]::INTEGER[]"),
        ("array", "[1, 2, 3]::INTEGER[3]"),
        ("struct", "{'amount': 1.25::DECIMAL(6, 2), 'enabled': TRUE}"),
        ("map", "MAP {'a': 1, 'b': 2}"),
        ("list_of_enum", "['red'::ENUM('red', 'blue'), 'blue'::ENUM('red', 'blue')]"),
        ("list_of_struct", "[{'amount': 1::INTEGER}, {'amount': 2::INTEGER}]"),
        ("struct_with_list", "{'items': [1, 2]::INTEGER[], 'label': 'x'::VARCHAR}"),
        ("array_of_arrays", "[[1, 2], [3, 4]]::INTEGER[2][2]"),
        ("map_of_lists", "MAP {'a': [1, 2]::INTEGER[], 'b': [3]::INTEGER[]}"),
    ],
)
def test_duckdb_sample_matches_independent_native_export(lossless, native_type, expression):
    with _duckdb_connection() as connection:
        connection.execute(f"SET arrow_lossless_conversion = {str(lossless).lower()}")
        reads = []
        _register_witness(connection, reads)
        source = _duckdb_relation(
            connection,
            "SELECT ma_witness(i * 2 + typed.seq)::BIGINT AS id, typed.payload "
            "FROM range(3) AS input(i) "
            f"CROSS JOIN (VALUES (0::INTEGER, {expression}), (1::INTEGER, NULL)) AS typed(seq, payload)",
        )
        # DuckDB's native Arrow export is the independent physical oracle.
        expected = source.to_native().arrow().read_all()
        reads.clear()
        query = ma.relation(source).sample(n=2, seed=42)
        query.schema
        from mountainash.exceptions import IncompleteSchemaError

        # Native-only types may remain incomplete in the canonical resolver.
        # That does not authorize evaluation or weaken the physical output oracle.
        try:
            query.collect_schema()
        except IncompleteSchemaError:
            pass
        query.explain()
        query.compile()
        assert reads == [], native_type

        result = query.collect()
        expected_rows = {row["id"]: row for row in expected.to_pylist()}
        assert result.schema.equals(expected.schema, check_metadata=True), native_type
        assert len(result.column("id").unique()) == 2, native_type
        assert result.to_pylist() == [expected_rows[row["id"]] for row in result.to_pylist()], native_type
        assert set(reads) == set(range(6)), native_type
        reads.clear()
        polars_result = query.to_polars()
        expected_polars = pl.from_arrow(expected)
        assert polars_result.schema == expected_polars.schema, native_type
        rows_by_id = {row["id"]: row for row in expected_polars.to_dicts()}
        assert polars_result.to_dicts() == [rows_by_id[row["id"]] for row in polars_result.to_dicts()], native_type
        assert set(reads) == set(range(6)), native_type


def test_duckdb_sample_preserves_blocking_aggregate_phase_boundary():
    with _duckdb_connection() as connection:
        reads = []
        _register_witness(connection, reads)
        source = _duckdb_relation(
            connection,
            "SELECT i::BIGINT AS id, sum(ma_witness(i)::BIGINT) OVER () AS total "
            "FROM range(10000) AS input(i)",
        )
        expected = source.to_native().pl()
        reads.clear()
        query = ma.relation(source).sample(n=2, seed=0)
        query.compile()
        assert reads == []

        result = query.to_polars()
        assert result.height == 2
        assert result.schema == expected.schema
        assert result.get_column("total").to_list() == [expected["total"][0]] * 2
        assert len(reads) == 10000


@pytest.mark.parametrize("projection", ["drop", "rename", "with_columns"])
def test_duckdb_sample_projection_treats_selector_like_names_literally(projection):
    from fixtures.call_expectations import expect_call_failure

    with _duckdb_connection() as connection:
        reads = []
        _register_witness(connection, reads)
        source = _duckdb_relation(
            connection,
            'SELECT ma_witness(i)::BIGINT AS id, (i + 10)::BIGINT AS "*", '
            '(i + 20)::BIGINT AS "^id$", (i + 40)::BIGINT AS "a.b", '
            '(i + 50)::BIGINT AS "quo""te", (i + 30)::BIGINT AS _ma_sample_index '
            'FROM range(5) AS input(i)',
        )
        query = ma.relation(source).sample(n=3, seed=4)
        expected_columns = ["id", "*", "^id$", "a.b", 'quo"te']
        if projection == "drop":
            query = query.drop("_ma_sample_index")
        elif projection == "rename":
            query = query.rename({"_ma_sample_index": "renamed"})
            expected_columns.append("renamed")
        else:
            query = query.with_columns(ma.lit(99).alias("added"))
            expected_columns.extend(["_ma_sample_index", "added"])
        with expect_call_failure(
            reason="355 / NW-REL-02: native DuckDB projections parse literal identifiers",
            errors=(duckdb.BinderException, duckdb.ParserException, nw.exceptions.DuplicateError),
            when=(nw.__version__, duckdb.__version__) == ("2.27.1", "1.5.6"),
        ):
            try:
                query.compile()
            finally:
                assert reads == []

            result = query.to_polars()
            assert result.columns == expected_columns
            assert result.height == 3
            assert result["id"].n_unique() == 3
            offsets = {"*": 10, "^id$": 20, "a.b": 40, 'quo"te': 50}
            if projection == "rename":
                offsets["renamed"] = 30
            elif projection == "with_columns":
                offsets["_ma_sample_index"] = 30
                assert result["added"].to_list() == [99, 99, 99]
            assert all(result.schema[name] == pl.Int64 for name in ["id", *offsets])
            assert all(
                row[name] == row["id"] + offset
                for row in result.to_dicts() for name, offset in offsets.items()
            )


@pytest.mark.parametrize(
    "retained, errors",
    [(2**53 + 1, (AssertionError,)), (2**64 - 1, (pa.ArrowInvalid,))],
    ids=["exact-above-2-53", "uint64-maximum"],
)
def test_pandas_arrow_struct_mask_retains_unsigned_child(retained, errors):
    """Native pandas witness for 374 / NW-CAST-02; not public support or an unwrapping route."""
    import pandas as pd
    from fixtures.call_expectations import expect_call_failure

    dtype = pa.struct([("number", pa.float32()), ("keep", pa.uint64())])
    rows = [
        {"number": None, "keep": 7},
        {"number": 1.0, "keep": retained},
        {"number": None, "keep": None},
        {"number": None, "keep": 7},
    ]
    series = pd.Series(pa.array(rows, type=dtype), dtype=pd.ArrowDtype(dtype))
    keep = pd.Series([False, True, False, True])
    reason = "374 / NW-CAST-02: pandas Arrow struct where loses nullable UInt64 child integers"
    with expect_call_failure(
        reason=reason, errors=errors, when=errors == (pa.ArrowInvalid,),
    ):
        result = series.where(keep)
    assert result.dtype == series.dtype
    actual = result.array.__arrow_array__().to_pylist()
    assert len(actual) == 4
    assert actual[0] is None and actual[2] is None
    assert actual[3] == {"number": None, "keep": 7}
    assert actual[1]["number"] == 1.0
    with expect_call_failure(reason=reason, errors=(AssertionError,)):
        assert actual[1]["keep"] == retained


def test_duckdb_shared_sample_branches_preserve_complete_rows():
    with _duckdb_connection() as connection:
        reads = []
        source = _observed_duckdb_source(connection, reads)
        sampled = ma.relation(source).sample(n=3, seed=11)
        expected = sampled.to_polars()
        reads.clear()
        combined = ma.concat([sampled, sampled])
        combined.compile()
        assert reads == []

        result = combined.to_polars()
        expected_rows = Counter(tuple(sorted(row.items())) for row in expected.to_dicts())
        actual_rows = Counter(tuple(sorted(row.items())) for row in result.to_dicts())
        assert result.height == 6
        assert actual_rows == Counter({row: count * 2 for row, count in expected_rows.items()})
        assert all(row["paired"] == row["id"] * 10 for row in result.to_dicts())


@pytest.mark.parametrize(
    "operation,expected",
    [
        ("tail", [6]),
        ("slice", [1]),
        ("large_head", [0, 1, 2, 3, 4, 5, 6]),
        ("large_slice", []),
    ],
)
def test_duckdb_sample_composes_with_positional_operations(operation, expected):
    with _duckdb_connection() as connection:
        reads = []
        source = _observed_duckdb_source(connection, reads)
        query = ma.relation(source).sample(n=7, seed=9).sort("id")
        if operation == "tail":
            query = query.tail(1)
        elif operation == "slice":
            query = query.slice(1, 1)
        elif operation == "large_head":
            query = query.head(2**40)
        else:
            query = query.slice(2**40, 1)
        query.compile()
        assert reads == []
        assert query.collect().column("id").to_pylist() == expected



@pytest.mark.parametrize("kind", ["decimal", "list"])
@pytest.mark.parametrize("options,count", [
    ({"n": 0}, 0), ({"n": 2}, 2), ({"n": 10}, 3), ({"fraction": 0.5}, 1),
])
def test_dask_sampling_preserves_object_values_and_native_terminal(kind, options, count):
    """Unknown Arrow output types must not force early Dask computation."""
    from decimal import Decimal

    import dask
    import dask.dataframe as dd
    import pandas as pd
    from dask import delayed
    from pandas.testing import assert_frame_equal
    from polars.testing import assert_frame_equal as assert_polars_equal

    payload = ([Decimal("1.25"), None, Decimal("3.50")]
               if kind == "decimal" else [[1], None, [3, 4]])
    frame = pd.DataFrame({"id": [1, 2, 3], "payload": payload})
    reads = []

    @delayed
    def load(partition):
        reads.append(len(partition))
        return partition

    with dask.config.set({"dataframe.convert-string": False}):
        native = dd.from_delayed(
            [load(frame.iloc[:1]), load(frame.iloc[1:])], meta=frame.iloc[:0],
        )
        query = ma.relation(nw.from_native(native)).sample(**options, seed=42)
        query.schema
        query.explain()
        query.compile()
        assert reads == []
        result = query.collect()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == count
        assert result.index.is_unique
        assert set(result.index) <= set(frame.index)
        expected = frame.loc[result.index]
        assert_frame_equal(result, expected)
        assert_frame_equal(query.collect(), result)
        if count:
            assert reads
        assert_polars_equal(query.to_polars(), pl.from_pandas(expected))


def test_sqlframe_duckdb_sampling_preserves_native_map_metadata():
    from sqlframe.duckdb import DuckDBSession
    from mountainash.exceptions import IncompleteSchemaError

    with _duckdb_connection() as connection, ExitStack() as cleanup:
        session = DuckDBSession(conn=connection)
        cleanup.callback(session.stop)
        reads = []
        _register_witness(connection, reads)
        connection.sql(
            "SELECT ma_witness(i)::BIGINT id, MAP {'a': i} payload FROM range(7)t(i)"
        ).create_view("sample_source")
        source = nw.from_native(session.table("sample_source"))
        query = ma.relation(source).sample(n=2, seed=42)
        query.schema
        try:
            query.collect_schema()
        except IncompleteSchemaError:
            pass
        query.explain()
        query.compile()
        assert reads == []
        result = query.collect()
        assert isinstance(result, pa.Table)
        assert len(result) == 2
        assert len(result.column("id").unique()) == 2
        assert pa.types.is_map(result.schema.field("payload").type)
        assert all(dict(row["payload"]) == {"a": row["id"]} for row in result.to_pylist())
        assert reads


@pytest.mark.parametrize("provider", ["duckdb", "sqlframe-duckdb"])
@pytest.mark.parametrize("operation,expected", [("sample_zero", 0), ("sample_half", 3), ("tail", 2)])
def test_native_helpers_preserve_case_insensitive_user_columns(provider, operation, expected):
    names = ["_MA_SAMPLE_INDEX", "_MA_SAMPLE_RANK", "_MA_SAMPLE_TOTAL",
             "_MA_TAIL_INDEX", "_MA_TAIL_TOTAL", "__0", "__1", "__2"]
    with _duckdb_connection() as connection, ExitStack() as cleanup:
        reads = []
        _register_witness(connection, reads)
        native = connection.sql(
            "SELECT ma_witness(i)::BIGINT id, "
            + ", ".join(f'0::BIGINT AS "{name}"' for name in names)
            + " FROM range(7)t(i)"
        )
        if provider == "sqlframe-duckdb":
            from sqlframe.duckdb import DuckDBSession

            native.create_view("case_source")
            session = DuckDBSession(conn=connection)
            cleanup.callback(session.stop)
            native = session.table("case_source")
        relation = ma.relation(nw.from_native(native))
        query = (
            relation.sort("id").tail(2) if operation == "tail"
            else relation.sample(fraction=0.0 if operation == "sample_zero" else 0.5, seed=42)
        )
        query.schema
        query.collect_schema()
        query.explain()
        query.compile()
        assert reads == []
        result = query.collect()
        assert isinstance(result, pa.Table)
        assert result.column_names == ["id", *names]
        assert len(result) == expected
        assert len(result.column("id").unique()) == expected
        assert all(row[name] == 0 for row in result.to_pylist() for name in names)
        if operation == "tail":
            assert result.column("id").to_pylist() == [5, 6]
        assert expected == 0 or reads
