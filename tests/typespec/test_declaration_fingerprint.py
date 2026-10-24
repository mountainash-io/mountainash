"""Declaration fingerprint compatibility tests."""
from __future__ import annotations

import pytest
from mountainash.typespec._fingerprint import declaration_fingerprint, freeze_table_schema
from mountainash.typespec.spec import FieldConstraints, FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.plan import build_compiled_plan


def _fingerprint(schema):
    return declaration_fingerprint(freeze_table_schema(schema))


def test_shared_fingerprint_matches_compiled_validation_plan():
    """A frozen TableSchema has one canonical fingerprint at every consumer boundary."""
    schema = TableSchema(fields={"payload": FieldDefinition(type=UniversalType.OBJECT)})

    plan = build_compiled_plan(schema, ())

    assert _fingerprint(schema) == plan.declaration_fingerprint


def test_equivalent_table_schema_declarations_have_matching_fingerprints():
    """Reconstructed equivalent declarations retain their stable identity."""
    first = TableSchema(fields={"payload": FieldDefinition(type=UniversalType.ARRAY)})
    second = TableSchema(fields={"payload": FieldDefinition(type=UniversalType.ARRAY)})

    assert _fingerprint(first) == _fingerprint(second)


def test_fingerprint_is_order_sensitive_for_named_fields_only():
    """Declared field order is identity; generic constraint metadata order is not."""
    a, b = FieldDefinition(type=UniversalType.STRING), FieldDefinition(type=UniversalType.INTEGER)
    assert _fingerprint(TableSchema(fields={"a": a, "b": b})) != _fingerprint(
        TableSchema(fields={"b": b, "a": a})
    )
    nested_ab = FieldDefinition(fields={"a": a, "b": b})
    nested_ba = FieldDefinition(fields={"b": b, "a": a})
    assert _fingerprint(TableSchema(fields={"n": nested_ab})) != _fingerprint(
        TableSchema(fields={"n": nested_ba})
    )
    one = FieldDefinition(constraints=FieldConstraints(json_schema={"x": 1, "y": 2}))
    two = FieldDefinition(constraints=FieldConstraints(json_schema={"y": 2, "x": 1}))
    assert _fingerprint(TableSchema(fields={"v": one})) == _fingerprint(TableSchema(fields={"v": two}))


def test_snapshot_is_isolated_from_later_schema_mutation():
    """An acquired plan keeps the schema it was built from after the caller edits the map."""
    schema = TableSchema(fields={"a": FieldDefinition(type=UniversalType.STRING)})
    plan = build_compiled_plan(schema, ())
    before = plan.declaration_fingerprint

    schema.fields["b"] = FieldDefinition(type=UniversalType.INTEGER)

    assert plan.declaration_fingerprint == before
    assert _fingerprint(schema) != before


@pytest.mark.parametrize("backend", ["polars", "narwhals", "arrow", "pandas", "ibis"])
def test_native_parameter_identity_is_stable_and_distinguishes_changes(backend):
    import polars as pl
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa
    import ibis.expr.datatypes as dt

    constructors = {
        "polars": lambda changed: pl.Struct({"at": pl.Datetime("us" if changed else "ns", "UTC")}),
        "narwhals": lambda changed: nw.Datetime("us" if changed else "ns", "UTC"),
        "arrow": lambda changed: pa.list_(pa.int16() if changed else pa.int8()),
        "pandas": lambda changed: pd.CategoricalDtype(
            [f"category-{i}" for i in range(100)] + ["changed" if changed else "original"], ordered=True,
        ),
        "ibis": lambda changed: dt.Array(dt.int16 if changed else dt.int8),
    }

    def fingerprint(changed):
        schema = TableSchema(fields={"value": FieldDefinition(backend_type=constructors[backend](changed))})
        return build_compiled_plan(schema, ()).declaration_fingerprint

    first = fingerprint(False)
    assert fingerprint(False) == first
    assert fingerprint(True) != first


def test_decimal_values_survive_snapshots_without_losing_precision():
    from decimal import Decimal
    from mountainash.validation.plan import thaw_table_schema

    value = Decimal("1.000000000000000001")
    field = FieldDefinition(type=UniversalType.NUMBER, null_fill=value, minimum=value)
    schema = TableSchema(fields={"amount": field})
    plan = build_compiled_plan(schema, ())
    restored = thaw_table_schema(plan).fields["amount"]
    assert restored.null_fill.as_tuple() == value.as_tuple()
    assert restored.constraints.minimum.as_tuple() == value.as_tuple()
    schema.fields["amount"] = field.variant(null_fill=Decimal("1.000000000000000002"))
    assert _fingerprint(schema) != plan.declaration_fingerprint
