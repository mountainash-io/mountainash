"""Disposable public-API witness for native export metadata, not permanent tests."""
import duckdb
import narwhals as nw
import mountainash as ma
import sys

EXPRESSIONS = {
    "boolean": "true", "signed": "CAST(-120 AS TINYINT)",
    "unsigned": "CAST(250 AS UTINYINT)", "float": "CAST(1.25 AS FLOAT)",
    "decimal": "CAST(1.25 AS DECIMAL(8,2))",
    "hugeint": "CAST(123 AS HUGEINT)", "uhugeint": "CAST(123 AS UHUGEINT)",
    "uuid": "UUID '550e8400-e29b-41d4-a716-446655440000'",
    "blob": "'abc'::BLOB", "bit": "CAST('101' AS BIT)",
    "bignum": "CAST('123' AS BIGNUM)", "json": "JSON '{\"a\":1}'",
    "date": "DATE '2020-01-01'", "time": "TIME '12:34:56'",
    "timetz": "TIMETZ '12:34:56+01'",
    "seconds": "TIMESTAMP_S '2020-01-01 00:00:01'",
    "nanos": "TIMESTAMP_NS '2020-01-01 00:00:01.123456789'",
    "zoned": "TIMESTAMPTZ '2020-01-01 00:00:01+00'",
    "map": "MAP {'a':1,'b':2}", "enum": "CAST('a' AS ENUM('a','b'))",
    "enum_list": "[CAST('a' AS ENUM('a','b'))]",
    "enum_struct": "{'cat':CAST('a' AS ENUM('a','b'))}",
    "enum_array": "CAST([CAST('a' AS ENUM('a','b'))] AS ENUM('a','b')[1])",
    "nested": "{'a':[MAP {'key': TIMESTAMPTZ '2020-01-01 00:00:01+00'}]}",
}
connection = duckdb.connect()
# A test-owned connection setting, not a change made by the implementation.
connection.execute("SET TimeZone='Europe/London'")
if "--lossless" in sys.argv:
    connection.execute("SET arrow_lossless_conversion=true")
reads = []
def witness(value):
    reads.append(value)
    return value
connection.create_function("witness", witness, ["BIGINT"], "BIGINT", side_effects=True)
for name, expression in EXPRESSIONS.items():
    native = connection.sql(
        "SELECT witness(i * 2 + j) AS id, value "
        f"FROM range(2) t(i) CROSS JOIN (VALUES (0, {expression}), (1, NULL)) v(j, value)"
    )
    expected = native.pl()
    expected_rows = {row['id']: row for row in expected.to_dicts()}
    reads.clear()
    query = ma.relation(nw.from_native(native)).sample(n=2, seed=42).select("id", "value")
    query.schema
    query.explain()
    compiled = query.compile()
    assert not reads, (name, "source evaluated before terminal", reads)
    out = query.to_polars()
    assert reads and out.height == 2
    assert out.schema == expected.schema, (name, out.schema, expected.schema)
    assert len(set(out['id'])) == 2
    assert all(row == expected_rows[row['id']] for row in out.to_dicts())
    assert compiled.collect().to_native().to_dicts() == out.to_dicts()
    print(name, "PASS", out.schema['value'])

aggregate = connection.sql("SELECT sum(witness(i)) AS total FROM range(10000) t(i)")
expected_aggregate = aggregate.pl().to_dicts()
reads.clear()
query = ma.relation(nw.from_native(aggregate)).sample(n=1, seed=42)
query.schema
query.explain()
query.compile()
assert not reads
assert query.to_dicts() == expected_aggregate
assert len(reads) == 10000
print("blocking aggregate PASS: zero pre-terminal source reads; exact terminal result")
connection.close()
