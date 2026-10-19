"""Declaration fingerprint compatibility tests."""
from __future__ import annotations

import pytest
from mountainash.typespec._fingerprint import declaration_fingerprint
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.plan import build_compiled_plan, freeze_typespec


def test_shared_fingerprint_matches_compiled_validation_plan():
    """A frozen TypeSpec has one canonical fingerprint at every consumer boundary."""
    spec = TypeSpec(fields={"payload": FieldSpec(type=UniversalType.OBJECT)})

    plan = build_compiled_plan(spec, ())

    assert declaration_fingerprint(freeze_typespec(spec)) == plan.declaration_fingerprint


def test_equivalent_typespec_declarations_have_matching_fingerprints():
    """Reconstructed equivalent declarations retain their stable identity."""
    first = TypeSpec(fields={"payload": FieldSpec(type=UniversalType.ARRAY)})
    second = TypeSpec(fields={"payload": FieldSpec(type=UniversalType.ARRAY)})

    assert declaration_fingerprint(freeze_typespec(first)) == declaration_fingerprint(
        freeze_typespec(second)
    )


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
        spec = TypeSpec(fields={"value": FieldSpec(backend_type=constructors[backend](changed))})
        return build_compiled_plan(spec, ()).declaration_fingerprint

    first = fingerprint(False)
    assert fingerprint(False) == first
    assert fingerprint(True) != first


def test_declared_field_order_changes_identity_but_metadata_key_order_does_not():
    quantity = FieldSpec(type=UniversalType.INTEGER, minimum=0)
    first = TypeSpec(fields={"left": quantity, "right": quantity})
    reversed_fields = TypeSpec(fields={"right": quantity, "left": quantity})
    assert declaration_fingerprint(freeze_typespec(first)) != declaration_fingerprint(
        freeze_typespec(reversed_fields)
    )
    first.fields["left"] = quantity.variant(json_schema={"type": "integer", "minimum": 0})
    equivalent = TypeSpec(fields={
        "left": quantity.variant(json_schema={"minimum": 0, "type": "integer"}),
        "right": quantity,
    })
    assert declaration_fingerprint(freeze_typespec(first)) == declaration_fingerprint(
        freeze_typespec(equivalent)
    )


def test_temporal_and_decimal_requirements_participate_in_identity():
    from datetime import date, datetime, time
    from decimal import Decimal

    fields = {
        "day": FieldSpec(type=UniversalType.DATE, minimum=date(2026, 1, 1)),
        "instant": FieldSpec(type=UniversalType.DATETIME, minimum=datetime(2026, 1, 1)),
        "clock": FieldSpec(type=UniversalType.TIME, minimum=time(12, 30)),
        "amount": FieldSpec(type=UniversalType.NUMBER, minimum=Decimal("1.25")),
    }
    original = declaration_fingerprint(freeze_typespec(TypeSpec(fields=fields)))
    fields["amount"] = fields["amount"].variant(minimum=Decimal("1.26"))
    assert declaration_fingerprint(freeze_typespec(TypeSpec(fields=fields))) != original
