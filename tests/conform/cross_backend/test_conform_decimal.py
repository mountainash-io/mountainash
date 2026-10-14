"""Declared decimal conform: explicit native rounding and unchanged policy boundaries."""
from __future__ import annotations

import sqlite3
from decimal import Decimal as D

import duckdb
import ibis
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.conform.errors import DecimalConversionRequiredError, SchemaDriftError
from mountainash.exceptions import BackendCapabilityError, InvalidOptionValueError
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_VALUE
from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
from mountainash.typespec.frictionless import typespec_from_frictionless, typespec_to_frictionless

D103 = ma.DecimalDtype(precision=10, scale=3)

# A matching native decimal column cannot be built on SQLite (create_table raises). Strict xfail keeps the
# identity visible: if SQLite ever gains a decimal column, this XPASSes and the test must be revisited.
NATIVE_DECIMAL_BACKENDS = [
    pytest.param(
        b,
        marks=pytest.mark.xfail(
            strict=True,
            raises=sqlite3.ProgrammingError,
            reason="SQLite has no fixed-precision decimal type; a native decimal column cannot be created",
        ),
    )
    if b == "ibis-sqlite" else b
    for b in ALL_BACKENDS
]
SPEC = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.NUMBER, dtype=D103)])

CONVERSION_BACKENDS = [
    pytest.param(name, marks=pytest.mark.xfail(
        strict=True,
        raises=BackendCapabilityError,
        reason="NW-MATH-11 (narwhals#3698), NW-CAST-01 (narwhals#3702): decimal cast unsupported",
    ))
    if name in {"narwhals-polars", "narwhals-lazy", "narwhals-pandas", "pandas"} else name
    for name in ALL_BACKENDS
]


def _decimal_frame(backend_name, precision, scale, values):
    """Native decimal(precision, scale) column per identity (the shared factory builds from plain data)."""
    table = pa.table({"x": pa.array(values, pa.decimal128(precision, scale))})
    if backend_name == "polars":
        return pl.from_arrow(table)
    if backend_name == "polars-lazy":
        return pl.from_arrow(table).lazy()
    if backend_name in ("narwhals-polars", "narwhals-lazy"):
        frame = pl.from_arrow(table)
        return nw.from_native(frame.lazy() if backend_name == "narwhals-lazy" else frame)
    if backend_name in ("pandas", "narwhals-pandas"):
        frame = table.to_pandas(types_mapper=pd.ArrowDtype)
        return nw.from_native(frame, eager_only=True)
    if backend_name == "ibis-duckdb":
        return ibis.duckdb.connect().create_table("t", table, overwrite=True)
    if backend_name == "ibis-polars":
        return ibis.polars.connect().create_table("t", pl.from_arrow(table), overwrite=True)
    # ibis-sqlite: SQLite has no fixed-precision decimal type, so the column cannot be created.
    return ibis.sqlite.connect(":memory:").create_table("t", table, overwrite=True)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("mode", ["coerce", "discard_value", "discard_row"])
def test_text_column_needs_explicit_cast(backend_name, backend_factory, mode):
    df = backend_factory.create({"x": ["1.5"]}, backend_name)
    with pytest.raises(DecimalConversionRequiredError) as err:
        ma.relation(df).conform(SPEC, contract={"data_type": mode}).to_polars()
    assert err.value.field_name == "x"
    assert err.value.declared == D103


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_float_column_is_not_silently_converted(backend_name, backend_factory):
    df = backend_factory.create({"x": [1.5]}, backend_name)
    with pytest.raises(DecimalConversionRequiredError):
        ma.relation(df).conform(SPEC).to_polars()


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("action,transforms", [("evolve", True), ("coerce", False)])
def test_no_conversion_keeps_actual_values_and_drift(backend_name, backend_factory, action, transforms):
    df = backend_factory.create({"x": ["1.5"]}, backend_name)
    rel = ma.relation(df).conform(
        SPEC, contract={"data_type": action}, apply_value_transforms=transforms,
    )
    out = rel.collect_with_drift()
    assert out.frame["x"].to_list() == ["1.5"]
    from mountainash.core.dtypes import dtype_family

    assert out.effective_schema == rel.schema
    assert {name: dtype_family(dtype) for name, dtype in rel.schema.items()} == {
        "x": ma.MountainashDtype.STRING,
    }
    mismatch, = out.drift.type_mismatches
    assert mismatch.action == action
    assert mismatch.applied is False


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_freeze_raises_drift(backend_name, backend_factory):
    df = backend_factory.create({"x": ["1.5"]}, backend_name)
    with pytest.raises(SchemaDriftError):
        ma.relation(df).conform(SPEC, contract={"data_type": "freeze"}).to_polars()


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", NATIVE_DECIMAL_BACKENDS)
@pytest.mark.parametrize("mode", ["coerce", "evolve", "freeze", "discard_value", "discard_row"])
def test_matching_decimal_passes_unchanged(backend_name, mode):
    frame = _decimal_frame(backend_name, 17, 2, [D("1.25"), None])
    target = ma.DecimalDtype(precision=17, scale=2)
    spec = TypeSpec(fields=[FieldSpec(
        name="x", type=UniversalType.NUMBER, dtype=target, null_fill="9.995",
    )])
    rel = ma.relation(frame).conform(spec, contract={"data_type": mode})
    out = rel.to_polars()
    assert out.schema["x"] == pl.Decimal(17, 2)
    assert rel.schema == {"x": target}
    assert out["x"].to_list() == [D("1.25"), None]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", NATIVE_DECIMAL_BACKENDS)
def test_different_precision_scale_is_a_mismatch(backend_name):
    frame = _decimal_frame(backend_name, 12, 4, [D("1.5000")])
    with pytest.raises(DecimalConversionRequiredError) as err:
        ma.relation(frame).conform(SPEC).to_polars()
    assert err.value.declared == D103
    with pytest.raises(SchemaDriftError):
        ma.relation(frame).conform(SPEC, contract={"data_type": "freeze"}).to_polars()




def test_spec_without_dtype_is_unchanged():
    frame = pl.DataFrame({"x": ["1.5"]})
    spec = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.NUMBER)])
    assert ma.relation(frame).conform(spec).to_polars()["x"].to_list() == [1.5]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_null_fill_of_a_missing_declared_decimal_keeps_its_type(backend_name, backend_factory):
    """The requested Polars result retains a typed decimal null, not a float null."""
    spec = TypeSpec(
        fields=[
            FieldSpec(name="amount", type=UniversalType.NUMBER, dtype=D103),
            FieldSpec(name="k", type=UniversalType.INTEGER),
        ],
        fields_match="subset",
    )
    df = backend_factory.create({"k": ["1"]}, backend_name)
    rel = ma.relation(df).conform(spec, contract={"missing_columns": "null_fill"})
    out = rel.to_polars()
    assert out.schema["amount"] == pl.Decimal(10, 3)
    assert out["amount"].to_list() == [None]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", CONVERSION_BACKENDS)
def test_declared_rounding_controls_conform(backend_name, backend_factory):
    descriptor = {"fields": [
        {"name": name, "type": "number", "x-mountainash": {
            "dtype": {"kind": "decimal", "precision": 5, "scale": 2},
            "rounding": mode,
        }}
        for name, mode in [("amount", "half_to_even"), ("fee", "half_away_from_zero")]
    ]}
    spec = typespec_from_frictionless(descriptor)
    assert typespec_to_frictionless(spec) == descriptor
    source = backend_factory.create(
        {"amount": ["12.345", "-12.345"], "fee": ["12.345", "-12.345"]}, backend_name,
    )
    rel = ma.relation(source).conform(spec)
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError) as raised:
            rel.to_polars()
        assert raised.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
        return
    result = rel.to_polars()
    assert result.to_dict(as_series=False) == {
        "amount": [D("12.34"), D("-12.34")], "fee": [D("12.35"), D("-12.35")],
    }
    target = ma.DecimalDtype(precision=5, scale=2)
    assert result.schema == {"amount": pl.Decimal(5, 2), "fee": pl.Decimal(5, 2)}
    assert rel.schema == {"amount": target, "fee": target}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", CONVERSION_BACKENDS)
@pytest.mark.parametrize("fill,expected", [
    (None, [D("12.34"), None]),
    ("1.2349", [D("12.34"), D("1.23")]),
])
def test_decimal_source_preparation(backend_name, fill, expected):
    if backend_name == "ibis-sqlite":
        with pytest.raises(sqlite3.ProgrammingError):
            _decimal_frame(backend_name, 6, 3, [D("12.345"), None])
        return
    frame = _decimal_frame(backend_name, 6, 3, [D("12.345"), None])
    spec = TypeSpec(fields=[FieldSpec(
        name="x", type=UniversalType.NUMBER, dtype=ma.DecimalDtype(precision=5, scale=2),
        rounding="half_to_even", null_fill=fill,
    )])
    out = ma.relation(frame).conform(spec).to_polars()
    assert out["x"].to_list() == expected
    assert out.schema["x"] == pl.Decimal(5, 2)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", CONVERSION_BACKENDS)
@pytest.mark.parametrize("values,mode,action,options,precision,expected", [
    pytest.param(["12.349", "-12.349"], "to_zero", "coerce", {}, 5,
                 [D("12.34"), D("-12.34")], id="truncate-signed"),
    pytest.param([7], "half_to_even", "coerce", {}, 5, [D("7.00")], id="integer"),
    pytest.param([2.675], "half_to_even", "coerce", {}, 5, [D("2.68")], id="float"),
    pytest.param(["12.345", "bad", None], "half_to_even", "discard_value", {}, 5,
                 [D("12.34"), None, None], id="discard-value"),
    pytest.param(["12.345", "bad", None], "half_to_even", "discard_row", {}, 5,
                 [D("12.34"), None], id="discard-row"),
    pytest.param(["NA", None, "bad", "1.235"], "half_to_even", "discard_row",
                 {"missing_values": ["NA"], "null_fill": "1.235"}, 5,
                 [D("1.24"), D("1.24"), D("1.24")], id="sentinels-fill"),
    pytest.param(["1.234,565"], "half_to_even", "coerce",
                 {"group_char": ".", "decimal_char": ","}, 6, [D("1234.56")], id="separators"),
    pytest.param(["USD12.345"], "half_to_even", "coerce",
                 {"bare_number": False}, 5, [D("12.34")], id="numeric-text"),
    pytest.param(["12.345"], "half_to_even", "coerce",
                 {"rename_from": "raw_x"}, 5, [D("12.34")], id="rename"),
    pytest.param(["1.25"], "half_to_even", "coerce", {}, 16, [D("1.25")], id="precision-limit"),
])
def test_conversion_preparation_and_policies(
    backend_name, backend_factory, values, mode, action, options, precision, expected,
):
    target = ma.DecimalDtype(precision=precision, scale=2)
    spec = TypeSpec(fields=[FieldSpec(
        name="x", type=UniversalType.NUMBER, dtype=target, rounding=mode, **options,
    )])
    source = backend_factory.create({options.get("rename_from", "x"): values}, backend_name)
    rel = ma.relation(source).conform(spec, contract={"data_type": action})
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError) as raised:
            rel.to_polars()
        assert raised.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
        return
    out = rel.collect_with_drift()
    frame = ma.relation(out.frame).to_polars()
    assert frame.to_dict(as_series=False) == {"x": expected}
    assert frame.schema == {"x": pl.Decimal(precision, 2)}
    assert out.effective_schema == rel.schema == {"x": target}
    mismatch, = out.drift.type_mismatches
    assert mismatch.name == "x"
    assert mismatch.action == action
    assert mismatch.applied is True


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_conversion_precision_limit_is_not_a_declaration_limit(backend_name, backend_factory):
    spec = TypeSpec(fields=[FieldSpec(
        name="x", type=UniversalType.NUMBER, dtype=ma.DecimalDtype(precision=17, scale=2),
        rounding="half_to_even",
    )])
    source = backend_factory.create({"x": ["1.25"]}, backend_name)
    with pytest.raises(InvalidOptionValueError):
        ma.relation(source).conform(spec).to_polars()


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", CONVERSION_BACKENDS)
@pytest.mark.parametrize("value,action", [
    ("bad", "coerce"), ("999.995", "discard_value"), ("999.995", "discard_row"),
])
def test_conversion_errors_are_not_hidden(backend_name, backend_factory, value, action):
    spec = TypeSpec(fields=[FieldSpec(
        name="x", type=UniversalType.NUMBER, dtype=ma.DecimalDtype(precision=5, scale=2),
        rounding="half_to_even",
    )])
    source = backend_factory.create({"x": [value]}, backend_name)
    rel = ma.relation(source).conform(spec, contract={"data_type": action})
    if backend_name == "ibis-sqlite":
        with pytest.raises(BackendCapabilityError) as raised:
            rel.to_polars()
        assert raised.value.function_key is FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST
        return
    error = duckdb.ConversionException if backend_name == "ibis-duckdb" else pl.exceptions.InvalidOperationError
    with pytest.raises(error):
        rel.to_polars()
    if value == "999.995":
        safe = backend_factory.create({"x": ["999.985"]}, backend_name)
        assert ma.relation(safe).conform(spec, contract={"data_type": action}).to_dict() == {
            "x": [D("999.98")],
        }
