"""Frictionless serialization of contract attachment (item 48 PR-B, Task 8).

Covers:
- `TypeSpec.contract` field + `{}` -> `None` normalisation (carry-forward
  warning from Task 4: an empty dict must never reach `resolve_contract`,
  since a non-None layer -- even an empty one -- flips `from_preset=False`).
- Standard `fieldsMatch` values write byte-identical to today.
- `open` moves under `x-mountainash.fields_match`; standard `fieldsMatch`
  key no longer carries "open".
- Legacy descriptors with `fieldsMatch: "open"` still read as open.
- `contract` round-trips through `x-mountainash.contract`, validated on
  read via `validate_contract_dict`.
"""
from __future__ import annotations

import pytest

from mountainash.conform.errors import ConformError
from mountainash.typespec.frictionless import (
    typespec_from_frictionless,
    typespec_to_frictionless,
)
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def _spec(**kwargs):
    return TypeSpec(
        fields=[FieldSpec(name="a", type=UniversalType.STRING)],
        **kwargs,
    )


# --- TypeSpec.contract field + {} -> None normalisation --------------------


def test_typespec_contract_defaults_to_none():
    assert _spec().contract is None


def test_typespec_contract_stores_dict():
    spec = _spec(contract={"data_type": "freeze"})
    assert spec.contract == {"data_type": "freeze"}


def test_typespec_empty_dict_contract_normalises_to_none():
    """An explicitly-empty dict must never be stored as {} -- it would
    flip resolve_contract's from_preset provenance flag despite carrying
    zero explicit values."""
    spec = _spec(contract={})
    assert spec.contract is None


def test_typespec_equality_unaffected_when_contract_none():
    assert _spec() == _spec()
    assert _spec(contract={}) == _spec()  # both normalise to None


# --- Write: standard fieldsMatch values byte-identical ----------------------


@pytest.mark.parametrize("fields_match", ["exact", "equal", "subset", "superset", "partial"])
def test_write_standard_fields_match_values(fields_match):
    spec = _spec(fields_match=fields_match)
    descriptor = typespec_to_frictionless(spec)
    if fields_match == "exact":
        assert "fieldsMatch" not in descriptor
    else:
        assert descriptor["fieldsMatch"] == fields_match
    assert "x-mountainash" not in descriptor


def test_write_open_fields_match_does_not_appear_in_standard_key():
    spec = _spec(fields_match="open")
    descriptor = typespec_to_frictionless(spec)
    assert "fieldsMatch" not in descriptor


def test_write_open_fields_match_moves_under_x_mountainash():
    spec = _spec(fields_match="open")
    descriptor = typespec_to_frictionless(spec)
    assert descriptor["x-mountainash"] == {"fields_match": "open"}


def test_write_contract_under_x_mountainash():
    spec = _spec(contract={"data_type": "freeze", "keys": "freeze"})
    descriptor = typespec_to_frictionless(spec)
    assert descriptor["x-mountainash"]["contract"] == {
        "data_type": "freeze",
        "keys": "freeze",
    }


def test_write_open_and_contract_together():
    spec = _spec(fields_match="open", contract={"keys": "freeze"})
    descriptor = typespec_to_frictionless(spec)
    assert descriptor["x-mountainash"] == {
        "fields_match": "open",
        "contract": {"keys": "freeze"},
    }


def test_write_no_x_mountainash_when_neither_open_nor_contract():
    spec = _spec(fields_match="subset")
    descriptor = typespec_to_frictionless(spec)
    assert "x-mountainash" not in descriptor


def test_write_empty_contract_emits_no_x_mountainash():
    spec = _spec(contract={})
    descriptor = typespec_to_frictionless(spec)
    assert "x-mountainash" not in descriptor


# --- Read: legacy + new form -------------------------------------------------


def test_read_legacy_fields_match_open_still_works():
    """Old descriptors written before this change used the standard
    fieldsMatch key for "open" -- must still parse correctly."""
    descriptor = {
        "fields": [{"name": "a", "type": "string"}],
        "fieldsMatch": "open",
    }
    spec = typespec_from_frictionless(descriptor)
    assert spec.fields_match == "open"


def test_read_new_form_x_mountainash_fields_match_open():
    descriptor = {
        "fields": [{"name": "a", "type": "string"}],
        "x-mountainash": {"fields_match": "open"},
    }
    spec = typespec_from_frictionless(descriptor)
    assert spec.fields_match == "open"


def test_read_x_mountainash_fields_match_takes_precedence_over_legacy_key():
    """If both are somehow present, the new namespaced form wins."""
    descriptor = {
        "fields": [{"name": "a", "type": "string"}],
        "fieldsMatch": "subset",
        "x-mountainash": {"fields_match": "open"},
    }
    spec = typespec_from_frictionless(descriptor)
    assert spec.fields_match == "open"


def test_read_contract_round_trips():
    descriptor = {
        "fields": [{"name": "a", "type": "string"}],
        "x-mountainash": {"contract": {"data_type": "freeze"}},
    }
    spec = typespec_from_frictionless(descriptor)
    assert spec.contract == {"data_type": "freeze"}


def test_read_no_x_mountainash_yields_none_contract_and_exact_fields_match():
    descriptor = {"fields": [{"name": "a", "type": "string"}]}
    spec = typespec_from_frictionless(descriptor)
    assert spec.contract is None
    assert spec.fields_match == "exact"


def test_read_empty_contract_in_descriptor_normalises_to_none():
    descriptor = {
        "fields": [{"name": "a", "type": "string"}],
        "x-mountainash": {"contract": {}},
    }
    spec = typespec_from_frictionless(descriptor)
    assert spec.contract is None


def test_read_invalid_contract_dimension_raises():
    descriptor = {
        "fields": [{"name": "a", "type": "string"}],
        "x-mountainash": {"contract": {"bogus": "freeze"}},
    }
    with pytest.raises(ConformError, match="unknown contract dimension"):
        typespec_from_frictionless(descriptor)


def test_read_invalid_contract_mode_raises():
    descriptor = {
        "fields": [{"name": "a", "type": "string"}],
        "x-mountainash": {"contract": {"keys": "discard_row"}},
    }
    with pytest.raises(ConformError, match="invalid mode"):
        typespec_from_frictionless(descriptor)


# --- Round trip ---------------------------------------------------------


@pytest.mark.parametrize("fields_match", ["exact", "equal", "subset", "superset", "partial", "open"])
def test_round_trip_fields_match_all_six_values(fields_match):
    spec = _spec(fields_match=fields_match)
    descriptor = typespec_to_frictionless(spec)
    restored = typespec_from_frictionless(descriptor)
    assert restored.fields_match == fields_match


def test_round_trip_contract_survives_descriptor_to_typespec_to_descriptor():
    spec = _spec(contract={"extra_columns": "discard", "data_type": "evolve"})
    descriptor = typespec_to_frictionless(spec)
    restored = typespec_from_frictionless(descriptor)
    assert restored.contract == {"extra_columns": "discard", "data_type": "evolve"}
    descriptor2 = typespec_to_frictionless(restored)
    assert descriptor2 == descriptor
