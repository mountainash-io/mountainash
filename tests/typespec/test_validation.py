"""
Tests for mountainash.typespec.validation.

Covers:
- validate_match / assert_match
- validate_schema_match / assert_schema_match (aliases)
"""
from __future__ import annotations

import pytest
import polars as pl

from mountainash.typespec.validation import (
    SchemaValidationError,
    assert_match,
    validate_match,
)
from mountainash.typespec.spec import FieldDefinition, TableSchema


# ============================================================================
# TestValidateMatch
# ============================================================================

class TestValidateMatch:
    """validate_match() tests."""

    def test_matching_schema_passes(self):
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        is_valid, errors = validate_match(df, expected)
        assert is_valid is True
        assert errors == []

    def test_missing_column_fails(self):
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        df = pl.DataFrame({"id": [1, 2]})  # missing 'name'
        is_valid, errors = validate_match(df, expected)
        assert is_valid is False
        assert len(errors) > 0
        assert any("name" in e for e in errors)

    def test_strict_true_extra_columns_fails(self):
        expected = TableSchema.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2], "extra": ["x", "y"]})
        is_valid, errors = validate_match(df, expected, strict=True)
        assert is_valid is False

    def test_strict_false_extra_columns_passes(self):
        expected = TableSchema.from_simple_dict({"id": "integer"})
        df = pl.DataFrame({"id": [1, 2], "extra": ["x", "y"]})
        is_valid, errors = validate_match(df, expected, strict=False)
        assert is_valid is True
        assert errors == []


# ============================================================================
# TestAssertMatch
# ============================================================================

class TestAssertMatch:
    """assert_match() tests."""


    def test_raises_schema_validation_error_when_invalid(self):
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        df = pl.DataFrame({"id": [1, 2]})  # missing 'name'
        with pytest.raises(SchemaValidationError):
            assert_match(df, expected)




def test_partial_declared_timestamp_accepts_compatible_detailed_source():
    from mountainash.core.dtypes import SchemaTypeStatus, TimestampDtype

    expected = TableSchema(fields={"at": FieldDefinition(
        dtype=TimestampDtype(SchemaTypeStatus.UNKNOWN, True, "UTC"),
    )})
    frame = pl.DataFrame(schema={"at": pl.Datetime("ns", "UTC")})
    valid, errors = validate_match(frame, expected)
    assert valid
    assert errors == []
def test_unknown_dtype_refinement_does_not_erase_declared_broad_constraint():
    from mountainash.core.dtypes import SchemaTypeStatus
    from mountainash.typespec.universal_types import UniversalType

    expected = TableSchema(fields={"value": FieldDefinition(
        type=UniversalType.INTEGER, dtype=SchemaTypeStatus.UNKNOWN,
    )})
    valid, errors = validate_match(pl.DataFrame({"value": ["text"]}), expected)
    assert not valid
    assert errors


@pytest.mark.parametrize("carrier", ["pandas", "pyarrow", "narwhals-pandas", "narwhals-pyarrow"])
@pytest.mark.parametrize("precision", [None, 6, 9])
def test_time_validation_uses_carrier_precision_without_constructing_source_cast(carrier, precision):
    import mountainash as ma
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa
    from mountainash.core.dtypes import SchemaTypeStatus, TimeDtype

    dtype = TimeDtype() if precision is None else TimeDtype(precision)
    expected = TableSchema(fields={"clock": FieldDefinition(dtype=dtype)})
    pandas_frame = pd.DataFrame({"clock": pd.Series([], dtype=pd.ArrowDtype(pa.time64("us")))})
    arrow_frame = pa.Table.from_arrays([pa.array([], type=pa.time64("us"))], names=["clock"])
    frames = {
        "pandas": pandas_frame,
        "pyarrow": arrow_frame,
        "narwhals-pandas": nw.from_native(pandas_frame),
        "narwhals-pyarrow": nw.from_native(arrow_frame),
    }
    valid, errors = validate_match(frames[carrier], expected)
    assert valid is (precision != 9)
    if precision == 9:
        assert errors
    else:
        assert errors == []
    reports = ma.relation(frames[carrier]).conform(expected).assess_drift()
    assert any(report.type_mismatches for report in reports) is (precision == 9)
    if precision is None:
        assert expected.fields["clock"].dtype.precision is SchemaTypeStatus.UNKNOWN
    else:
        assert expected.fields["clock"].dtype.precision == precision


@pytest.mark.parametrize("unit,valid", [(b"items", True), (b"boxes", False)])
def test_nested_native_field_qualifiers_remain_authoritative_in_validation(unit, valid):
    import pyarrow as pa
    from mountainash.core.dtypes import NativeDtype, TypeTarget

    required = pa.field("", pa.int16(), nullable=False, metadata={b"unit": b"items"})
    expected = TableSchema(fields={"record": FieldDefinition(fields={
        "qty": FieldDefinition(backend_type=NativeDtype(value=required, target=TypeTarget.PYARROW)),
    })})
    observed = pa.struct([pa.field("qty", pa.int16(), nullable=False, metadata={b"unit": unit})])
    frame = pa.Table.from_arrays([pa.array([], type=observed)], names=["record"])
    result, errors = validate_match(frame, expected)
    assert result is valid
    assert bool(errors) is not valid


@pytest.mark.parametrize("precision,valid", [(None, True), (6, False)])
def test_validation_does_not_invent_missing_observed_time_precision(precision, valid):
    import ibis
    from mountainash.core.dtypes import TimeDtype

    source = ibis.table({"clock": ibis.dtype("time")})
    declared = TimeDtype() if precision is None else TimeDtype(precision)
    result, errors = validate_match(source, TableSchema(fields={"clock": FieldDefinition(dtype=declared)}))
    assert result is valid
    assert bool(errors) is not valid


@pytest.mark.parametrize("kind", ["time", "timestamp", "duration"])
@pytest.mark.parametrize("same_family", [True, False])
def test_bare_temporal_evidence_does_not_invent_parameter_conflicts(kind, same_family):
    from mountainash.conform.contract import resolve_contract
    from mountainash.conform.errors import SchemaDriftError
    from mountainash.conform.expressions import resolve_conform_output
    from mountainash.core.dtypes import (
        DurationDtype, MountainashDtype as D, SchemaTypeStatus, TimeDtype, TimestampDtype,
    )
    from mountainash.typespec.converters import compare_resolved_type
    from mountainash.typespec.source_shape import SourceShape

    expected, family = {
        "time": (TimeDtype(6), D.TIME),
        "timestamp": (TimestampDtype(9, False, None), D.TIMESTAMP),
        "duration": (DurationDtype("ns", "fixed"), D.DURATION),
    }[kind]
    actual = family if same_family else D.STRING
    comparison = compare_resolved_type(expected, SourceShape(actual))
    assert comparison is (SchemaTypeStatus.UNKNOWN if same_family else False)
    schema = TableSchema(fields={"value": FieldDefinition(dtype=expected)})
    contract = resolve_contract("open", {"data_type": "freeze"})
    if not same_family:
        with pytest.raises(SchemaDriftError):
            resolve_conform_output(
                schema, ["value"], actual_dtypes={"value": actual}, contract=contract,
            )
        return
    resolved = resolve_conform_output(
        schema, ["value"], actual_dtypes={"value": actual}, contract=contract,
    )
    assert resolved.output_schema == {"value": expected}
    assert not (resolved.drift and resolved.drift.type_mismatches)
