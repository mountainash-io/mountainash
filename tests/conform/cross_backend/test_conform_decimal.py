"""Conform with declared DecimalDtype fields (item 241, R19).

Conform verifies a declared decimal field and never converts it: a column that already
matches passes unchanged, and any other actual type follows the existing ``data_type`` policy
(evolve keeps the actual column, freeze raises drift) or raises a typed error pointing at the
explicit ``.cast(DecimalDtype(...), rounding=...)``.
"""
from __future__ import annotations

import sqlite3
from decimal import Decimal as D

import ibis
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.conform.errors import DecimalConversionRequiredError, SchemaDriftError
from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

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


def _decimal_frame(backend_name, precision, scale, value):
    """Native decimal(precision, scale) column per identity (the shared factory builds from plain data)."""
    table = pa.table({"x": pa.array([value], pa.decimal128(precision, scale))})
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
def test_evolve_keeps_the_actual_column(backend_name, backend_factory):
    df = backend_factory.create({"x": ["1.5"]}, backend_name)
    out = ma.relation(df).conform(SPEC, contract={"data_type": "evolve"}).to_dict()
    assert out["x"] == ["1.5"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_freeze_raises_drift(backend_name, backend_factory):
    df = backend_factory.create({"x": ["1.5"]}, backend_name)
    with pytest.raises(SchemaDriftError):
        ma.relation(df).conform(SPEC, contract={"data_type": "freeze"}).to_polars()


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", NATIVE_DECIMAL_BACKENDS)
@pytest.mark.parametrize("mode", ["coerce", "evolve", "freeze", "discard_value"])
def test_matching_decimal_passes_unchanged(backend_name, mode):
    frame = _decimal_frame(backend_name, 10, 3, D("1.500"))
    out = ma.relation(frame).conform(SPEC, contract={"data_type": mode}).to_polars()
    assert out.schema["x"] == pl.Decimal(10, 3)
    assert out["x"].to_list() == [D("1.500")]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", NATIVE_DECIMAL_BACKENDS)
def test_different_precision_scale_is_a_mismatch(backend_name):
    frame = _decimal_frame(backend_name, 12, 4, D("1.5000"))
    with pytest.raises(DecimalConversionRequiredError) as err:
        ma.relation(frame).conform(SPEC).to_polars()
    assert err.value.declared == D103
    assert "decimal(10,3)" in str(err.value) and "280" in str(err.value)
    with pytest.raises(SchemaDriftError):
        ma.relation(frame).conform(SPEC, contract={"data_type": "freeze"}).to_polars()


def test_matching_decimal_with_missing_value_sentinels_does_not_crash():
    """Schema-level missingValues are text sentinels; they must not be applied to a decimal column."""
    frame = pl.DataFrame({"x": pl.Series([D("1.500"), None], dtype=pl.Decimal(10, 3))})
    spec = TypeSpec(
        fields=[FieldSpec(name="x", type=UniversalType.NUMBER, dtype=D103)],
        missing_values=[""],
    )
    assert ma.relation(frame).conform(spec).to_dict()["x"] == [D("1.500"), None]


def test_spec_without_dtype_is_unchanged():
    frame = pl.DataFrame({"x": ["1.5"]})
    spec = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.NUMBER)])
    assert ma.relation(frame).conform(spec).to_polars()["x"].to_list() == [1.5]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_null_fill_of_a_missing_declared_decimal_keeps_its_type(backend_name, backend_factory):
    """A missing declared decimal materialises as a typed decimal null, not a float null."""
    spec = TypeSpec(
        fields=[
            FieldSpec(name="amount", type=UniversalType.NUMBER, dtype=D103),
            FieldSpec(name="k", type=UniversalType.INTEGER),
        ],
        fields_match="subset",
    )
    df = backend_factory.create({"k": ["1"]}, backend_name)
    out = ma.relation(df).conform(spec, contract={"missing_columns": "null_fill"}).to_polars()
    assert out.schema["amount"] == pl.Decimal(10, 3)
    assert out["amount"].to_list() == [None]
