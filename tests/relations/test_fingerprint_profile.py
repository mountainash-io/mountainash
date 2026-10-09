"""The versioned Polars profile owns byte/value semantics, not source execution.

These local tests protect the shared algorithm's persistence contract; source
portability and selection have separate public-terminal witnesses.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
import json
import struct
import subprocess
import sys

import polars as pl
import pytest


def fingerprint(frame, keys=("k",), columns=("v",), batch_size=3):
    from mountainash.relations.core.fingerprint_profile import FingerprintAccumulator
    accumulator = FingerprintAccumulator(frame.schema, keys=keys, columns=columns)
    for batch in frame.iter_slices(batch_size):
        accumulator.update(batch)
    return accumulator.finish()


def test_versioned_result_preserves_domain_and_serialization(tmp_path):
    frame = pl.DataFrame({"a": [1, 1, 2, 2], "b": [3, 4, 3, 4],
                          "value": [float("nan"), -0.0, None, 1.125],
                          "__keys__": ["x", "y", "z", "w"]})
    result = fingerprint(frame, ("a", "b"), ("value", "__keys__", "a"))
    assert result.columns == ["kind", "column", "row_count", "fingerprint", "profile", "key_schema", "value_schema"]
    assert result["column"].to_list() == [None, "value", "__keys__", "a"]
    assert result["kind"].to_list() == ["keys", "column", "column", "column"]
    assert result["row_count"].to_list() == [4] * 4
    assert result.schema["row_count"] == pl.UInt64
    assert result["key_schema"][0] == '[["a",{"type":"Int64"}],["b",{"type":"Int64"}]]'
    assert result["value_schema"][1] == '["value",{"type":"Float64"}]'
    assert result["profile"][0] == f"ma-fingerprint/polars-struct-sum64x2/v1;polars={pl.__version__}"
    if pl.__version__ == "1.44.2":
        assert result["fingerprint"].to_list() == [
            "8dc86337a737c1051cfc8906f447c84c", "00cbe0baedec050e4920ac1876cd41db",
            "7ef7be7ad251acaeb076c698878801a7", "c0904800b1d12061027d79877a1a7484",
        ]
    assert result.equals(fingerprint(frame.reverse(), ("a", "b"), ("value", "__keys__", "a"), 1))
    assert result.head(2).equals(fingerprint(frame, ("a", "b"), ("value",), 2))
    path = tmp_path / "result.parquet"
    result.write_parquet(path)
    assert result.equals(pl.read_parquet(path))


NAN_A = struct.unpack(">d", bytes.fromhex("7ff8000000000001"))[0]
NAN_B = struct.unpack(">d", bytes.fromhex("fff8000000000010"))[0]
VALUE_CASES = [
    (pl.String, "", None, False), (pl.String, "a", "a ", False),
    (pl.String, "A", "a", False), (pl.String, "é", "e\u0301", False),
    (pl.String, "null", None, False), (pl.Binary, b"a\0b", b"ab", False),
    (pl.Binary, b"", None, False), (pl.Boolean, False, None, False),
    (pl.Boolean, True, False, False),
    (pl.Decimal(18, 2), Decimal("1.0"), Decimal("1.00"), True),
    (pl.Decimal(38, 2), Decimal("123456789012345678901234567890.01"), Decimal("123456789012345678901234567890.02"), False),
    (pl.Date, dt.date(2026, 1, 1), dt.date(2026, 1, 2), False),
    (pl.Time, dt.time(1, 2, 3, 4), dt.time(1, 2, 3, 5), False),
    (pl.List(pl.Float64), [0.0, NAN_A], [-0.0, NAN_B], True),
    (pl.List(pl.Float64), [1, 2], [2, 1], False),
    (pl.List(pl.Float64), [1], [1, 1], False),
    (pl.List(pl.Float64), [], None, False),
    (pl.List(pl.Float64), [None], [NAN_A], False),
    (pl.Struct({"a": pl.Float64, "b": pl.String}), None, {"a": None, "b": None}, False),
    (pl.Struct({"a": pl.Float64, "b": pl.String}), {"a": 1, "b": "x"}, {"b": "x", "a": 1}, True),
    (pl.List(pl.Struct({"a": pl.List(pl.Float64)})), [{"a": [0.0, NAN_A, None]}], [{"a": [-0.0, NAN_B, None]}], True),
]
for dtype in (pl.Float32, pl.Float64):
    VALUE_CASES.extend((dtype, a, b, eq) for a, b, eq in [
        (0.0, -0.0, True), (NAN_A, NAN_B, True), (NAN_A, None, False),
        (float("inf"), -float("inf"), False), (1.0, 1.125, False), (None, 0.0, False),
    ])
for dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64):
    VALUE_CASES.extend([(dtype, 1, 2, False), (dtype, None, 0, False)])
for unit in ("ms", "us", "ns"):
    VALUE_CASES.extend([(pl.Datetime(unit), 1000001, 1000002, False),
                        (pl.Duration(unit), 1000001, 1000002, False)])
VALUE_CASES.append((pl.Datetime("us", "UTC"), 1000001, 1000002, False))


@pytest.mark.parametrize("dtype,left,right,equal", VALUE_CASES)
def test_typed_value_equivalence(dtype, left, right, equal):
    def digest(value):
        frame = pl.DataFrame({"k": [7], "v": pl.Series([value], dtype=dtype)})
        return fingerprint(frame)["fingerprint"][1]
    assert (digest(left) == digest(right)) is equal


@pytest.mark.parametrize("dtype,descriptor", [
    (pl.Int32, {"type": "Int32"}),
    (pl.Decimal(18, 2), {"type": "decimal", "precision": 18, "scale": 2}),
    (pl.Datetime("ns", "UTC"), {"type": "datetime", "unit": "ns", "timezone": "UTC"}),
    (pl.Duration("ms"), {"type": "duration", "unit": "ms"}),
    (pl.List(pl.Struct({"x": pl.String})), {"type": "list", "element": {"type": "struct", "fields": [["x", {"type": "String"}]]}}),
])
def test_empty_domain_is_typed(dtype, descriptor):
    empty = pl.DataFrame(schema={"k": pl.Int64, "v": dtype})
    out = fingerprint(empty)
    assert out["row_count"].to_list() == [0, 0]
    assert out["fingerprint"].to_list() == ["0" * 32] * 2
    assert json.loads(out["value_schema"][1]) == ["v", descriptor]


@pytest.mark.parametrize("dtype", [pl.Object, pl.Categorical(), pl.Enum(["x"]), pl.Array(pl.Int64, 2),
                                  pl.Int128, pl.Null, pl.Decimal, pl.List(pl.Null),
                                  pl.Struct({"bad": pl.Object})])
def test_unsupported_domain_fails_even_without_rows(dtype):
    from mountainash.relations.core.fingerprint_profile import FingerprintAccumulator
    with pytest.raises(TypeError, match="v"):
        FingerprintAccumulator({"k": pl.Int64, "v": dtype}, keys=("k",), columns=("v",))


def test_schema_drift_does_not_publish_new_domain():
    from mountainash.relations.core.fingerprint_profile import FingerprintAccumulator
    acc = FingerprintAccumulator(pl.Schema({"k": pl.Int64, "v": pl.Int32}), keys=("k",), columns=("v",))
    with pytest.raises(ValueError, match="schema"):
        acc.update(pl.DataFrame({"k": [1], "v": [2]}))


def test_fresh_process_profile_repeats():
    script = '''import polars as pl
from mountainash.relations.core.fingerprint_profile import FingerprintAccumulator
f = pl.DataFrame({"k": [1, 2], "v": [float("nan"), -0.0]})
a = FingerprintAccumulator(f.schema, keys=("k",), columns=("v",))
a.update(f)
print(a.finish().write_json())
'''
    first = subprocess.check_output([sys.executable, "-c", script], text=True)
    second = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert first == second


@pytest.mark.parametrize("keys,columns,batch_size,error", [
    ("k", ["v"], 1, TypeError), ({"k"}, ["v"], 1, TypeError),
    ([], ["v"], 1, ValueError), (["k", "k"], ["v"], 1, ValueError),
    (["k"], [], 1, ValueError), (["k"], [1], 1, TypeError),
    (["k"], ["v"], True, TypeError), (["k"], ["v"], 0, ValueError),
    (["k"], ["v"], 1.5, TypeError),
])
def test_invalid_request(keys, columns, batch_size, error):
    from mountainash.relations.core.fingerprint_profile import normalize_request
    with pytest.raises(error):
        normalize_request(keys, columns, batch_size)
