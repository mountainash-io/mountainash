"""Disposable schema-fidelity probe: nonzero exit means bridge design is unqualified."""
import duckdb
import narwhals as nw
import mountainash as ma

queries = {
    "seconds": "SELECT TIMESTAMP_S '2020-01-01 00:00:01' AS value FROM range(2)",
    "decimal": "SELECT CAST(1.25 AS DECIMAL(8,2)) AS value FROM range(2)",
    "enum": "SELECT CAST('a' AS ENUM('a','b')) AS value FROM range(2)",
}
failures = []
for name, sql in queries.items():
    native = duckdb.sql(sql)
    expected = native.pl().head(1)
    try:
        result = ma.relation(nw.from_native(native)).sample(n=1, seed=42).to_polars()
        assert result.schema == expected.schema
        assert result.to_dicts() == expected.to_dicts()
    except Exception as error:
        failures.append(name)
        print(name, "FAILED", type(error).__name__, str(error))
    else:
        print(name, "PASSED", result.schema, result.to_dicts())
if failures:
    raise SystemExit(1)
