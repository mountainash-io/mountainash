"""Persisted numeric declarations must suffice without live source/visitor state."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

import mountainash as ma
from mountainash.core.dtypes.numeric import convert_numeric
from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
from mountainash.typespec.converters import to_arrow_schema
from mountainash.typespec.frictionless import typespec_to_frictionless

_RELOAD = r'''
import json
import sys
from decimal import Decimal
from pathlib import Path
import polars as pl
import pyarrow.parquet as pq
import mountainash as ma
from mountainash.typespec.converters import to_arrow_schema, to_polars_schema
from mountainash.typespec.extraction import extract_from_dataframe
from mountainash.typespec.frictionless import typespec_from_frictionless
from mountainash.typespec.spec import compare_specs

root = Path(sys.argv[1])
declared = typespec_from_frictionless(json.loads((root / "schema.json").read_text()))
physical = extract_from_dataframe(pl.DataFrame(schema=to_polars_schema(declared)))
expected_rows = {
    "populated": [
        {"amount": Decimal("12345678901234567.891"),
         "integer_text": "1606938044258990275541962092341162602522202993782792835301395",
         "decimal_text": "123456789012345678901234567890.00123"},
        {"amount": None, "integer_text": None, "decimal_text": None},
    ],
    "empty": [],
    "nulls": [{"amount": None, "integer_text": None, "decimal_text": None}] * 2,
    "independent": [
        {"amount": Decimal("-0.001"), "integer_text": "-1180591620717411303424",
         "decimal_text": "0.00000000000000000000000000000000000001"},
    ],
}
def verify_lexical_values(frame):
    for field in declared.fields:
        if field.dtype not in (
            ma.MountainashDtype.LEXICAL_INTEGER, ma.MountainashDtype.LEXICAL_DECIMAL,
        ):
            continue
        candidate = ma.relation(frame).select(
            ma.col(field.name).cast(field.dtype, failure_behavior="throw").cast("string")
        ).to_dict()[field.name]
        if candidate != frame[field.name].to_list():
            raise ValueError("stored lexical values are not canonical")

for name, expected in expected_rows.items():
    table = pq.read_table(root / (name + ".parquet"))
    assert table.schema == to_arrow_schema(declared)
    frame = pl.from_arrow(table)
    assert compare_specs(extract_from_dataframe(frame), physical).is_compatible
    verify_lexical_values(frame)
    rows = ma.relation(frame).to_dicts()
    assert rows == expected
    if name == "populated":
        # Binding-owned decoding witness, not an implicit Mountainash inverse codec.
        assert int(rows[0]["integer_text"]) == 2**200 + 19
        assert Decimal(rows[0]["decimal_text"]) == Decimal("123456789012345678901234567890.00123")
for name in ("wrong_scale", "wrong_precision", "wrong_float"):
    frame = pl.read_parquet(root / (name + ".parquet"))
    diff = compare_specs(extract_from_dataframe(frame), physical)
    assert not diff.is_compatible
    assert "amount" in diff.type_changes

for name in ("invalid_integer", "noncanonical_integer", "invalid_decimal", "noncanonical_decimal"):
    frame = pl.read_parquet(root / (name + ".parquet"))
    assert compare_specs(extract_from_dataframe(frame), physical).is_compatible
    unchanged = frame.to_dicts()
    try:
        verify_lexical_values(frame)
    except (ValueError, pl.exceptions.ComputeError):
        pass
    else:
        raise AssertionError("strict readback accepted " + name)
    assert frame.to_dicts() == unchanged

# Actual persisted dtype drives conversion; operation policies remain authored here.
amount_dtype = declared.get_field("amount").dtype
converted = ma.relation(pl.DataFrame({"amount": ["12.3456", "99999999999999999.9995"]})).select(
    ma.col("amount").cast(amount_dtype, failure_behavior="null")
).to_dict()
assert converted == {"amount": [Decimal("12.346"), None]}
print("verified populated/empty/null exact reload, three schema refusals, and loaded-dtype conversion")
'''


def test_numeric_schema_and_values_survive_independent_reload(tmp_path):
    spec = TypeSpec(fields=[
        FieldSpec(name="amount", type=UniversalType.NUMBER, dtype=ma.DecimalDtype(precision=20, scale=3)),
        FieldSpec(name="integer_text", type=UniversalType.STRING, dtype=ma.MountainashDtype.LEXICAL_INTEGER),
        FieldSpec(name="decimal_text", type=UniversalType.STRING, dtype=ma.MountainashDtype.LEXICAL_DECIMAL),
    ])
    (tmp_path / "schema.json").write_text(json.dumps(typespec_to_frictionless(spec)))
    schema = to_arrow_schema(spec)
    raw = {
        "amount": [Decimal("12345678901234567.891"), None],
        "integer_text": [2**200 + 19, None],
        "decimal_text": [Decimal("123456789012345678901234567890.0012300"), None],
    }
    # Exercise the shared checked representation before schema-first construction.
    # No inferred native frame can truncate/round these original values first.
    prepared = {
        field.name: [convert_numeric(value, field.dtype, preserve=True) for value in raw[field.name]]
        for field in spec.fields
    }
    for name, data in (
        ("populated", prepared),
        ("empty", {field.name: [] for field in spec.fields}),
        ("nulls", {field.name: [None, None] for field in spec.fields}),
    ):
        pq.write_table(pa.Table.from_pydict(data, schema=schema), tmp_path / (name + ".parquet"))
    for name, dtype, value in (
        ("wrong_scale", pa.decimal128(20, 2), Decimal("12.34")),
        ("wrong_precision", pa.decimal128(21, 3), Decimal("12.340")),
        ("wrong_float", pa.float64(), 12.34),
    ):
        changed = schema.set(0, pa.field("amount", dtype))
        data = {"amount": [value], "integer_text": ["20"], "decimal_text": ["12.34"]}
        pq.write_table(pa.Table.from_pydict(data, schema=changed), tmp_path / (name + ".parquet"))
    # Independent storage producer: no codec or retained source object participates.
    independent = {
        "amount": [Decimal("-0.001")],
        "integer_text": ["-1180591620717411303424"],
        "decimal_text": ["0.00000000000000000000000000000000000001"],
    }
    pq.write_table(pa.Table.from_pydict(independent, schema=schema), tmp_path / "independent.parquet")
    for name, column, value in (
        ("invalid_integer", "integer_text", "12x"),
        ("noncanonical_integer", "integer_text", "+00020"),
        ("invalid_decimal", "decimal_text", "1e+"),
        ("noncanonical_decimal", "decimal_text", "1.2300"),
    ):
        data = {**independent, column: [value]}
        pq.write_table(pa.Table.from_pydict(data, schema=schema), tmp_path / (name + ".parquet"))
    environment = {**os.environ, "PYTHONPATH": str(Path(ma.__file__).parents[1])}
    result = subprocess.run(
        [sys.executable, "-c", _RELOAD, str(tmp_path)],
        cwd=tmp_path, env=environment, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
