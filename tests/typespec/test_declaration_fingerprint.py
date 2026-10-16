"""Declaration fingerprint compatibility tests."""
from __future__ import annotations

import pytest
from mountainash.typespec._fingerprint import declaration_fingerprint
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.plan import build_compiled_plan, freeze_typespec


def test_shared_fingerprint_matches_compiled_validation_plan():
    """A frozen TypeSpec has one canonical fingerprint at every consumer boundary."""
    spec = TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.OBJECT)])

    plan = build_compiled_plan(spec, ())

    assert declaration_fingerprint(freeze_typespec(spec)) == plan.declaration_fingerprint


def test_equivalent_typespec_declarations_have_matching_fingerprints():
    """Reconstructed equivalent declarations retain their stable identity."""
    first = TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    second = TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])

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
        spec = TypeSpec(fields=[FieldSpec(name="value", backend_type=constructors[backend](changed))])
        return build_compiled_plan(spec, ()).declaration_fingerprint

    first = fingerprint(False)
    assert fingerprint(False) == first
    assert fingerprint(True) != first
