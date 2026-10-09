"""Run the disposable item-241 shape proof; not a permanent test suite.

PYTHONPATH=src <existing-hatch-python> scripts/spike_241_numeric.py
The backend kernels intentionally use real Python UDF execution, not native-only lowering.
"""
from decimal import Decimal, getcontext
import json

import ibis
import polars as pl
import pyarrow as pa
import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D, registry, TypeTarget
from mountainash.core.dtypes.casts import classify_cast
from mountainash.core.dtypes.spike_numeric import DecimalDtype, LEXICAL_INTEGER, LEXICAL_DECIMAL, numeric_text
from mountainash.typespec import TypeSpec, FieldSpec, UniversalType
from mountainash.typespec.converters import to_arrow_schema, to_polars_schema, to_ibis_schema
from mountainash.typespec.extraction import extract_from_dataframe
from mountainash.relations.core.spike_numeric_lineage import LexicalNumericUseError
from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash.api_bldr_ext_ma_spike_numeric import numeric_cast_node


checks = []


def equal(label, actual, expected):
    assert actual == expected, (label, actual, expected)
    checks.append(label)
    print(f"PASS {label}: {actual}")


def raises(label, call, message, error_type=Exception):
    try:
        call()
    except error_type as error:
        assert message.lower() in str(error).lower(), (label, type(error).__name__, str(error))
        checks.append(label)
        print(f"PASS {label}: {type(error).__name__}: {str(error).splitlines()[0]}")
    else:
        raise AssertionError(f"{label}: expected rejection")


print("DISPOSABLE SPIKE; Python UDF kernels; not native-only performance or full-backend proof")
print("versions", pl.__version__, pa.__version__, ibis.__version__)
amount = DecimalDtype(20, 3)
spec = TypeSpec(fields=[FieldSpec(name="amount", type=UniversalType.NUMBER, dtype=amount)])
encoded = json.loads(json.dumps(spec.to_frictionless()))
restored = TypeSpec.from_frictionless(encoded)
equal("portable TypeSpec JSON round-trip", restored.fields[0].dtype, amount)
equal("Arrow lowering", to_arrow_schema(restored).field("amount").type, pa.decimal128(20, 3))
equal("Polars lowering", to_polars_schema(restored)["amount"], pl.Decimal(20, 3))
equal("Ibis lowering", str(to_ibis_schema(restored)["amount"]), "decimal(20, 3)")
raises("unsupported precision rejected", lambda: DecimalDtype(39, 2), "precision")
raises("unsupported scale rejected", lambda: DecimalDtype(5, -1), "scale")
raises("conflicting field hints rejected", lambda: FieldSpec(name="x", type=UniversalType.NUMBER, dtype=amount, backend_type="double"), "conflicts")
raises("unimplemented schema target rejected", lambda: registry.to_native_schema(amount, TypeTarget.NARWHALS), "does not implement")

arrow = pa.table({"amount": pa.array([Decimal("9007199254740993.125"), None], type=pa.decimal128(20, 3))})
connection = ibis.duckdb.connect()
ibis_decimal = connection.create_table("spike_241_decimal", arrow)
for label, native in (("Arrow", arrow), ("Polars", pl.from_arrow(arrow)), ("Ibis", ibis_decimal)):
    extracted = extract_from_dataframe(native)
    reloaded = TypeSpec.from_frictionless(json.loads(json.dumps(extracted.to_frictionless())))
    equal(label + " extraction retains decimal parameters", reloaded.fields[0].dtype, amount)
    equal(label + " extraction back to Arrow", to_arrow_schema(reloaded), arrow.schema)

for source, target, expected in (
    (D.I32, D.I64, "safe"),
    (D.I64, D.I32, "narrowing"),
    (D.I64, D.FP64, "lossy"),
    (D.TIMESTAMP, D.DATE, "lossy"),
    (D.STRING, D.I64, "unsafe"),
    (LEXICAL_INTEGER, D.I64, "narrowing"),
    (DecimalDtype(5, 2), DecimalDtype(7, 3), "safe"),
    (DecimalDtype(5, 2), DecimalDtype(4, 2), "narrowing"),
    (DecimalDtype(5, 3), DecimalDtype(3, 2), "lossy"),
):
    equal(f"classification {source} -> {target}", classify_cast(source, target).value, expected)

# A source binding can invoke the same value codec before a native table exists.
# No int(text) limit and no default-context Decimal.normalize() rounding.
old_precision = getcontext().prec
getcontext().prec = 6
try:
    huge = "9" * 5000
    equal("unbounded lexical integer length", len(numeric_text(huge, LEXICAL_INTEGER)), 5000)
    assert numeric_text(huge, LEXICAL_INTEGER) == huge
    equal("exponent numeric lexical canonicalization", numeric_text("1.234567890123456789012345678901e+4", LEXICAL_DECIMAL), "12345.67890123456789012345678901")
    equal("integer lexical normalization", numeric_text("+00020.000", LEXICAL_INTEGER), "20")
finally:
    getcontext().prec = old_precision

values = ["12.345", "12.355", "-12.345", "-12.355", "12.340", "1.234567890123456789e1", None]
text_frame = pl.DataFrame({"x": values})
ibis_text = connection.create_table("spike_241_text", text_frame.to_arrow())
lexical_spec = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.STRING, dtype=LEXICAL_INTEGER)])
lex_frame = pl.DataFrame({"x": ["+00020", "100", str(2**70)]})
ibis_lex = connection.create_table("spike_241_lex", lex_frame.to_arrow())
bad_frame = pl.DataFrame({"x": ["999.995", "-999.995", "nonsense", "12.345", None]})
ibis_bad = connection.create_table("spike_241_bad", bad_frame.to_arrow())

for backend, text, lexical_source, bad, native_decimal_source in (
    ("Polars", text_frame, lex_frame, bad_frame, pl.from_arrow(arrow)),
    ("DuckDB", ibis_text, ibis_lex, ibis_bad, ibis_decimal),
):
    dtype = DecimalDtype(5, 2)
    result = ma.relation(text).select(
        ma.col("x").cast(dtype).name.alias("even"),
        ma.col("x").cast(dtype, rounding="TIE_AWAY_FROM_ZERO").name.alias("away"),
    ).to_polars()
    equal(backend + " ties-to-even", result["even"].to_list(), [Decimal(x) if x is not None else None for x in ["12.34", "12.36", "-12.34", "-12.36", "12.34", "12.35", None]])
    equal(backend + " ties-away", result["away"].to_list(), [Decimal(x) if x is not None else None for x in ["12.35", "12.36", "-12.35", "-12.36", "12.34", "12.35", None]])
    rounded_null = ma.relation(bad).select(ma.col("x").cast(dtype, failure_behavior="null")).to_polars()
    equal(backend + " failure=null and overflow-after-rounding", rounded_null["x"].to_list(), [None, None, None, Decimal("12.34"), None])
    raises(backend + " failure=throw", lambda: ma.relation(bad).select(ma.col("x").cast(dtype)).to_polars(), "overflow")
    exact = ma.relation(native_decimal_source).conform(restored).to_polars()
    equal(backend + " exact conform with default missing sentinels", exact["amount"].to_list(), [Decimal("9007199254740993.125"), None])
    preserving = ma.col("x")
    preserving = preserving.create(numeric_cast_node(preserving.node, dtype, preserve=True))
    raises(backend + " preservation rejects rounding", lambda: ma.relation(text).select(preserving).to_polars(), "lose precision")
    rel = ma.relation(lexical_source).conform(lexical_spec).select(ma.col("x").name.alias("renamed")).rename({"renamed": "n"})
    equal(backend + " lexical values survive alias and rename", rel.to_polars()["n"].to_list(), ["20", "100", str(2**70)])
    raises(backend + " lexical sort blocked before native sorting", lambda: rel.sort("n").to_polars(), "explicit conversion", LexicalNumericUseError)
    raises(backend + " lexical arithmetic blocked", lambda: rel.select((ma.col("n") + 1).name.alias("n")).to_polars(), "explicit", LexicalNumericUseError)
    numeric = rel.select(ma.col("n").cast(DecimalDtype(30, 0))).sort("n").to_polars()
    equal(backend + " explicit numeric conversion enables sort", numeric["n"].to_list(), [Decimal(20), Decimal(100), Decimal(2**70)])
    textual = rel.select(ma.col("n").cast("string")).sort("n").to_polars()
    equal(backend + " explicit STRING conversion opts into text ordering", textual["n"].to_list(), ["100", str(2**70), "20"])
    exported = rel.to_polars()
    equal(backend + " native export loses semantic identity by contract", ma.relation(exported).sort("n").to_polars()["n"].to_list(), ["100", str(2**70), "20"])

print(json.dumps({"passed": len(checks), "backends_executed": ["Polars", "Ibis-DuckDB"], "schema_targets": ["Arrow", "Polars", "Ibis"], "kernel": "Python UDF", "status": "disposable shape proof"}))
