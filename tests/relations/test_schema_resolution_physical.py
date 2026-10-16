"""Physical SQL type metadata for bound Ibis output expressions."""
from __future__ import annotations

import ibis.expr.datatypes as ibis_dt
import mountainash as ma
from mountainash.core.dtypes import DecimalDtype, NativeDtype, TimeDtype, TimestampDtype
from tests.fixtures.ibis_physical import connection


def _project(connection, sql: str):
    expression = connection.sql(sql)
    return ma.relation(expression).select(
        *(ma.col(name).alias(name) for name in expression.columns)
    )


def test_sql_output_timestamp_keeps_physical_precision_and_awareness(connection):
    if connection.name == "sqlite":
        sql = "SELECT CAST(NULL AS TIMESTAMP(3)) AS local_time"
    else:
        sql = (
            "SELECT CAST(NULL AS TIMESTAMP(3)) AS local_time, "
            "CAST(NULL AS TIMESTAMP WITH TIME ZONE) AS zoned_time"
        )

    schema = _project(connection, sql).schema

    if connection.name == "sqlite":
        assert not isinstance(schema["local_time"], TimestampDtype)
    else:
        assert schema["local_time"] == TimestampDtype(
            precision=3, timezone_aware=False, timezone=None
        )
        assert schema["zoned_time"] == TimestampDtype(
            precision=6, timezone_aware=True, timezone=None
        )
        source = connection.sql(
            "SELECT CAST(NULL AS TIMESTAMP(3)) AS source_time"
        )
        output_schema = ma.relation(source).select(
            ma.col("source_time").cast(ibis_dt.Timestamp(scale=5)).alias("cast_time")
        ).schema
        assert output_schema["cast_time"] == TimestampDtype(
            precision=5 if connection.name == "postgres" else 6,
            timezone_aware=False,
            timezone=None,
        )


def test_sql_output_time_precision_uses_native_metadata(connection):
    if connection.name == "postgres":
        sql = (
            "SELECT CAST(NULL AS TIME(3)) AS clock, "
            "CAST(NULL AS TIME(4) WITH TIME ZONE) AS zoned_clock"
        )
    else:
        sql = "SELECT CAST(NULL AS TIME) AS clock"
    schema = _project(connection, sql).collect_schema()

    if connection.name == "postgres":
        assert schema["clock"] == TimeDtype(precision=3)
        assert schema["zoned_clock"].precision == 4
        assert "TIME" in schema["zoned_clock"].native.value.upper()
    elif connection.name == "sqlite":
        assert not isinstance(schema["clock"], TimeDtype)
    else:
        assert schema["clock"] == TimeDtype(precision=6)


def test_sql_output_decimal_and_nested_types_keep_native_parameters(connection):
    if connection.name == "duckdb":
        sql = (
            "SELECT CAST(NULL AS DECIMAL(12, 5)) AS amount, "
            "CAST(NULL AS DECIMAL) AS default_amount, "
            "[CAST(NULL AS TIMESTAMP(3))] AS events, "
            "struct_pack(at := CAST(NULL AS TIMESTAMP(5))) AS record, "
            "CAST(NULL AS UUID) AS native_id"
        )
    elif connection.name == "postgres":
        sql = (
            "SELECT CAST(NULL AS DECIMAL(12, 5)) AS amount, "
            "CAST(NULL AS NUMERIC) AS default_amount, "
            "ARRAY[CAST(NULL AS TIMESTAMP(3))] AS events, "
            "CAST(NULL AS UUID) AS native_id"
        )
    else:
        sql = (
            "SELECT CAST(NULL AS DECIMAL(12, 5)) AS amount, "
            "CAST(NULL AS TIMESTAMP(3)) AS event"
        )

    schema = _project(connection, sql).collect_schema()

    if connection.name == "sqlite":
        assert not isinstance(schema["amount"], DecimalDtype)
        assert not isinstance(schema["event"], TimestampDtype)
    else:
        assert schema["amount"] == DecimalDtype(precision=12, scale=5)
        assert schema["events"].element == TimestampDtype(
            precision=3, timezone_aware=False, timezone=None
        )
        assert isinstance(schema["native_id"], NativeDtype)
        assert "uuid" in str(schema["native_id"].value).lower()
    if connection.name == "duckdb":
        assert schema["default_amount"] == DecimalDtype(precision=18, scale=3)
        assert schema["record"].fields == (
            ("at", TimestampDtype(precision=6, timezone_aware=False, timezone=None)),
        )
    elif connection.name == "postgres":
        assert isinstance(schema["default_amount"], NativeDtype)
        assert schema["default_amount"].value == "DECIMAL"


def test_building_and_structural_drift_do_not_describe_sql_output(connection, monkeypatch):
    import polars as pl

    source = connection.create_table("schema_build_only", pl.DataFrame({"n": [1]}), overwrite=True)
    try:
        def unexpected_compile(*args, **kwargs):
            raise AssertionError("structural construction must not compile SQL")

        with monkeypatch.context() as context:
            context.setattr(connection, "compile", unexpected_compile)
            relation = ma.relation(source).select("n").conform(ma.typespec({"n": "integer"}))
            assert not any(report.type_mismatches for report in relation.assess_drift())
    finally:
        connection.drop_table("schema_build_only", force=True)


def test_nested_physical_time_and_fixed_array_metadata(connection):
    from mountainash.core.dtypes import ArrayDtype, ListDtype, StructDtype

    if connection.name == "sqlite":
        import pytest
        pytest.xfail("SQLite has no typed SQL arrays or physical TIME")
    if connection.name == "postgres":
        relation = _project(connection, "SELECT ARRAY[NULL::time(3)] AS clocks")
        assert relation.collect_schema() == {"clocks": ListDtype(element=TimeDtype(precision=3))}
    else:
        relation = _project(connection, (
            "SELECT CAST(NULL AS TIME[2][3]) AS clocks, "
            "struct_pack(clock := CAST(NULL AS TIME_NS)) AS record"
        ))
        assert relation.collect_schema() == {
            "clocks": ArrayDtype(element=TimeDtype(precision=6), dimensions=(3, 2)),
            "record": StructDtype(fields=(("clock", TimeDtype(precision=9)),)),
        }


def test_unbound_bounded_string_retains_native_restriction():
    import ibis

    dtype = ibis_dt.String(length=12)
    schema = ma.relation(ibis.table({"code": dtype}, name="bounded_source")).collect_schema()
    assert isinstance(schema["code"], NativeDtype)
    assert schema["code"].value == dtype


def test_sql_calendar_interval_is_not_a_fixed_duration(connection):
    from mountainash.core.dtypes import DurationDtype
    if connection.name == "sqlite":
        import pytest
        pytest.xfail("SQLite has no SQL INTERVAL type")
    relation = _project(connection, "SELECT INTERVAL '1 month' AS span")
    dtype = relation.collect_schema()["span"]
    assert isinstance(dtype, DurationDtype)
    assert dtype.semantics == "calendar"
    assert dtype.unit == "us"
    assert "INTERVAL" in dtype.native.value.upper()
    import pytest
    from mountainash.core.dtypes import TypeTarget, registry
    from mountainash.core.dtypes.errors import DtypeMappingError
    with pytest.raises(DtypeMappingError):
        registry.to_native_schema(dtype, TypeTarget.IBIS)
