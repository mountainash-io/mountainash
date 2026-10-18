"""Disposable DuckDB-to-Polars export metadata probe, not production code."""
import polars as pl
import pyarrow as pa

_SCALARS = {
    "boolean": pa.bool_(),
    "tinyint": pa.int8(), "smallint": pa.int16(),
    "integer": pa.int32(), "bigint": pa.int64(),
    "utinyint": pa.uint8(), "usmallint": pa.uint16(),
    "uinteger": pa.uint32(), "ubigint": pa.uint64(),
    "hugeint": pa.decimal128(38, 0), "uhugeint": pa.decimal128(38, 0),
    "float": pa.float32(), "double": pa.float64(),
    "varchar": pa.string(), "uuid": pa.string(),
    "blob": pa.binary(), "bit": pa.binary(),
    "date": pa.date32(), "time": pa.time64("us"),
    "time with time zone": pa.time64("us"),
    "timestamp_s": pa.timestamp("s"), "timestamp_ms": pa.timestamp("ms"),
    "timestamp": pa.timestamp("us"), "timestamp_ns": pa.timestamp("ns"),
    "interval": pa.month_day_nano_interval(),
    "bignum": pa.opaque(pa.binary(), "bignum", "DuckDB"),
}


def export_schema(native):
    """Read bound types and export settings, never evaluate the source query."""
    settings = dict(native.query(
        "duckdb_settings()",
        "SELECT name, value FROM duckdb_settings() "
        "WHERE name IN ('TimeZone', 'arrow_lossless_conversion')",
    ).fetchall())
    lossless = settings["arrow_lossless_conversion"] == "true"

    def arrow_type(dtype):
        kind = dtype.id
        if lossless:
            if kind == "boolean":
                return pa.bool8()
            if kind in {"hugeint", "uhugeint", "bit", "time with time zone"}:
                name = "time_tz" if kind == "time with time zone" else kind
                return pa.opaque(pa.binary(), name, "DuckDB")
            if kind == "uuid":
                return pa.uuid()
            if str(dtype) == "JSON":
                return pa.json_()
        if kind in _SCALARS:
            return _SCALARS[kind]
        if kind == "timestamp with time zone":
            return pa.timestamp("us", tz=settings["TimeZone"])
        children = dict(dtype.children)
        if kind == "decimal":
            return pa.decimal128(children["precision"], children["scale"])
        if kind == "enum":
            return pa.dictionary(pa.uint32(), pa.string())
        if kind == "list":
            return pa.list_(arrow_type(children["child"]))
        if kind == "array":
            return pa.list_(arrow_type(children["child"]), children["size"])
        if kind == "struct":
            return pa.struct([(name, arrow_type(child)) for name, child in dtype.children])
        if kind == "map":
            return pa.map_(arrow_type(children["key"]), arrow_type(children["value"]))
        if kind == "union":
            return pa.sparse_union([
                pa.field(name, arrow_type(child)) for name, child in dtype.children
            ])
        raise NotImplementedError(f"Spike has no export metadata for {dtype!r}")

    return pl.Schema(pa.schema([
        (name, arrow_type(dtype)) for name, dtype in zip(native.columns, native.types)
    ]))
