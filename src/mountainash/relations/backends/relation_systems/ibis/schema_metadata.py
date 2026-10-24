"""Physical output-schema description of bound Ibis SQL relations.

Private to ``IbisRelationSystem.describe_output_schema``. An Ibis expression's
own schema is logical: it can promote SQL types differently from the engine and
erases physical detail such as temporal precision. For a relation bound to a
connection whose dialect has a technique below, the connection is asked to
describe the *compiled output query* instead, and the engine's native type text
refines what Ibis' logical types erase.

Each dialect technique is one private function returning the described output
schema plus the engine's native type text per column. Techniques are selected by
the relation's actual execution location and are replaceable independently of
this module's callers: neither the relation-system protocol nor schema
resolution knows what a technique does to describe a query. No technique here
executes data rows, selects a connection, or opens a transaction on a
caller-owned connection beyond the temporary-view step named below.
"""
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from mountainash.core.dtypes import (
    ArrayDtype,
    DurationDtype,
    ListDtype,
    NativeDtype,
    StructDtype,
    TimeDtype,
    TimestampDtype,
    TypeTarget,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from mountainash.core.dtypes.protocols import ResolvedType
    from mountainash.relations.core.execution.location import ExecutionLocation


def describe_physical_output(
    native: Any, location: ExecutionLocation,
) -> dict[str, ResolvedType] | None:
    """Output types of a bound SQL relation as its engine describes them.

    Returns None when the location has no bound connection or its dialect has no
    physical technique; the caller then reports the relation's logical schema.
    Database errors, and SQLite's no-rows inference failure, propagate typed.
    """
    connection = location.connection
    describe = _TECHNIQUES.get(location.dialect)
    if connection is None or describe is None:
        return None

    from mountainash.typespec.adapter_registry import get_native_schema_adapter
    from mountainash.typespec.source_shape import shape_type_evidence

    described, native_types = describe(connection, connection.compile(native))
    shapes = get_native_schema_adapter(TypeTarget.IBIS).decode_schema(described)
    result = {name: shape_type_evidence(shape) for name, shape in shapes.items()}
    for name, native_type in native_types.items():
        result[name] = _refine(result[name], native_type, connection.name)
    return result


# ---------------------------------------------------------------------------
# Dialect techniques: (connection, compiled query) -> (schema, native type text)
# ---------------------------------------------------------------------------


def _describe_sqlite(connection: Any, query: str) -> tuple[Mapping[str, Any], dict[str, str]]:
    """SQLite infers types from returned rows; an empty result has none to infer."""
    from ibis.common.exceptions import IbisError

    try:
        return connection.sql(query).schema(), {}
    except IbisError as error:
        if not str(error).startswith("Failed to infer types for columns "):
            raise
        from mountainash.relations.core.errors import CompileRequiresExecutionError

        raise CompileRequiresExecutionError(
            f"SQLite native metadata has no rows from which to infer output types: {error}"
        ) from error


def _describe_duckdb(connection: Any, query: str) -> tuple[Mapping[str, Any], dict[str, str]]:
    """DuckDB reports each output column's native type name without running rows."""
    relation = connection.con.sql(query)
    native_types = dict(zip(relation.columns, map(str, relation.types)))
    return {
        name: connection.compiler.type_mapper.from_string(native_type)
        for name, native_type in native_types.items()
    }, native_types


def _describe_postgres(connection: Any, query: str) -> tuple[Mapping[str, Any], dict[str, str]]:
    """Describe PostgreSQL output through a temporary view and the system catalog.

    Ibis' PostgreSQL type mapping omits time modifiers and unbounded NUMERIC;
    ``format_type`` over the view's catalog entry supplies them. This is a
    replaceable technique: the view is acquired here and dropped here on success
    or failure, and nothing outside this function sees its name. The caller's
    connection stays caller-owned and is never closed or reconfigured.
    """
    from uuid import uuid4

    import sqlglot as sg
    import sqlglot.expressions as sge

    name = f"ma_schema_{uuid4().hex}"
    create_stmt = sge.Create(
        kind="VIEW",
        this=sg.table(name),
        expression=sg.parse_one(query, read=connection.dialect),
        properties=sge.Properties(expressions=[sge.TemporaryProperty()]),
    ).sql(connection.dialect)
    drop_stmt = sge.Drop(kind="VIEW", this=sg.table(name), exists=True).sql(connection.dialect)
    raw_connection = connection.con
    with raw_connection.cursor() as cursor, raw_connection.transaction():
        cursor.execute(create_stmt)
    try:
        schema = connection.get_schema(name)
        catalog_query = """
            SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod)
            FROM pg_catalog.pg_attribute AS a
            JOIN pg_catalog.pg_class AS c ON c.oid = a.attrelid
            WHERE c.oid = pg_catalog.to_regclass(%s)
              AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY a.attnum
        """
        with raw_connection.cursor() as cursor, raw_connection.transaction():
            rows = cursor.execute(catalog_query, (name,), prepare=True).fetchall()
        return schema, dict(rows)
    finally:
        with raw_connection.cursor() as cursor, raw_connection.transaction():
            cursor.execute(drop_stmt)


_TECHNIQUES: dict[str | None, Callable[[Any, str], tuple[Mapping[str, Any], dict[str, str]]]] = {
    "ibis-sqlite": _describe_sqlite,
    "ibis-duckdb": _describe_duckdb,
    "ibis-postgres": _describe_postgres,
}


# ---------------------------------------------------------------------------
# Physical refinement of Ibis' logical types from native type text
# ---------------------------------------------------------------------------


def _refine(dtype: Any, native_type: str, dialect: str) -> Any:
    """Retain physical temporal/numeric metadata erased by Ibis' logical types."""
    import sqlglot.expressions as sge

    def refine(value: Any, sql_type: Any) -> Any:
        if sql_type.this is sge.DataType.Type.DECIMAL and not sql_type.expressions:
            # PostgreSQL NUMERIC without a typmod is genuinely unbounded, not
            # an unresolved precision/scale placeholder in an Ibis expression.
            return NativeDtype(value=sql_type.sql(dialect=dialect), target=TypeTarget.IBIS)
        if sql_type.this in {sge.DataType.Type.INT128, sge.DataType.Type.UINT128}:
            return NativeDtype(value=sql_type.sql(dialect=dialect), target=TypeTarget.IBIS)
        if sql_type.this is sge.DataType.Type.INTERVAL:
            return DurationDtype(
                unit="us", semantics="calendar",
                native=NativeDtype(value=sql_type.sql(dialect=dialect), target=TypeTarget.IBIS),
            )
        if sql_type.this in {sge.DataType.Type.TIME, sge.DataType.Type.TIMETZ, sge.DataType.Type.TIME_NS}:
            # Both engines store TIME at microsecond resolution; DuckDB TIME_NS
            # stores nanoseconds. PostgreSQL additionally retains explicit typmods.
            precision = (
                int(sql_type.expressions[0].name) if sql_type.expressions
                else 9 if sql_type.this is sge.DataType.Type.TIME_NS else 6
            )
            native = (
                NativeDtype(value=sql_type.sql(dialect=dialect), target=TypeTarget.IBIS)
                if sql_type.this is sge.DataType.Type.TIMETZ
                else getattr(value, "native", None)
            )
            return TimeDtype(precision=precision, native=native)
        if isinstance(value, TimestampDtype) and value.timezone_aware is True:
            return replace(value, timezone=None)
        if isinstance(value, (ListDtype, ArrayDtype)):
            child = sql_type
            depth = len(value.dimensions) if isinstance(value, ArrayDtype) else 1
            for _ in range(depth):
                child = child.expressions[0]
            return replace(value, element=refine(value.element, child))
        if isinstance(value, StructDtype) and isinstance(value.fields, tuple):
            children = {field.name: field.kind for field in sql_type.expressions}
            return replace(value, fields=tuple(
                (name, refine(child, children[name])) for name, child in value.fields
            ))
        return value

    return refine(dtype, sge.DataType.build(native_type, dialect=dialect))
