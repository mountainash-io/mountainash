"""ConformContract, fields_match preset expansion, and mode x dimension validation.

The preset table is LOCKED to current fields_match behaviour (see
conform-contract.md "fields_match preset expansion (locked to current
behaviour)"). `resolve_contract` layers TypeSpec.contract and
conform(contract=) overrides on top of the preset, flipping `from_preset`
to False on any explicit layer — that flag is the provenance mechanism
distinguishing legacy fields_match errors from SchemaDriftError.
"""
from __future__ import annotations

import dataclasses

import pytest

from mountainash.conform.contract import (
    FIELDS_MATCH_PRESETS,
    ConformContract,
    resolve_contract,
    validate_contract_dict,
)
from mountainash.conform.errors import ConformError, MissingFieldsError


# --- Preset table matrix (locked to current fields_match behaviour) -------

PRESET_TABLE = {
    "open": {
        "extra_columns": "evolve",
        "missing_columns": "skip",
        "mapping": "by_name",
        "count_must_match": False,
        "minimum_overlap": 0,
    },
    "exact": {
        "extra_columns": "freeze",
        "missing_columns": "freeze",
        "mapping": "positional",
        "count_must_match": True,
        "minimum_overlap": 0,
    },
    "equal": {
        "extra_columns": "freeze",
        "missing_columns": "freeze",
        "mapping": "by_name",
        "count_must_match": False,
        "minimum_overlap": 0,
    },
    "subset": {
        "extra_columns": "discard",
        "missing_columns": "freeze",
        "mapping": "by_name",
        "count_must_match": False,
        "minimum_overlap": 0,
    },
    "superset": {
        "extra_columns": "freeze",
        "missing_columns": "skip",
        "mapping": "by_name",
        "count_must_match": False,
        "minimum_overlap": 0,
    },
    "partial": {
        "extra_columns": "discard",
        "missing_columns": "skip",
        "mapping": "by_name",
        "count_must_match": False,
        "minimum_overlap": 1,
    },
}


def test_preset_table_has_exactly_six_entries():
    assert set(FIELDS_MATCH_PRESETS) == set(PRESET_TABLE)


@pytest.mark.parametrize("fields_match", sorted(PRESET_TABLE))
def test_preset_expansion_field_by_field(fields_match):
    contract = FIELDS_MATCH_PRESETS[fields_match]
    expected = PRESET_TABLE[fields_match]
    assert contract.extra_columns == expected["extra_columns"]
    assert contract.missing_columns == expected["missing_columns"]
    assert contract.mapping == expected["mapping"]
    assert contract.count_must_match == expected["count_must_match"]
    assert contract.minimum_overlap == expected["minimum_overlap"]


@pytest.mark.parametrize("fields_match", sorted(PRESET_TABLE))
def test_preset_extension_dimensions_default(fields_match):
    """Presets only ever touch the column dimensions; extension dims stay default."""
    contract = FIELDS_MATCH_PRESETS[fields_match]
    assert contract.data_type == "coerce"
    assert contract.keys == "ignore"


@pytest.mark.parametrize("fields_match", sorted(PRESET_TABLE))
def test_preset_contracts_are_preset_provenance(fields_match):
    assert FIELDS_MATCH_PRESETS[fields_match].from_preset is True


def test_all_presets_are_frozen_conform_contract_instances():
    for contract in FIELDS_MATCH_PRESETS.values():
        assert isinstance(contract, ConformContract)
        with pytest.raises(dataclasses.FrozenInstanceError):
            contract.extra_columns = "freeze"


# --- validate_contract_dict -------------------------------------------------


def test_validate_contract_dict_rejects_unknown_dimension():
    with pytest.raises(ConformError, match="unknown contract dimension"):
        validate_contract_dict({"nope": "x"})


def test_validate_contract_dict_rejects_invalid_mode_for_dimension():
    with pytest.raises(ConformError, match="invalid mode"):
        validate_contract_dict({"keys": "discard_row"})


def test_validate_contract_dict_accepts_valid_pairs():
    # Should not raise.
    validate_contract_dict(
        {
            "extra_columns": "discard",
            "missing_columns": "null_fill",
            "data_type": "discard_row",
            "keys": "freeze",
        }
    )


@pytest.mark.parametrize(
    "dim,valid_modes",
    [
        ("extra_columns", {"evolve", "freeze", "discard"}),
        ("missing_columns", {"skip", "freeze", "null_fill"}),
        ("data_type", {"coerce", "evolve", "freeze", "discard_value", "discard_row"}),
        ("keys", {"ignore", "freeze"}),
    ],
)
def test_validate_contract_dict_rejects_modes_from_other_dimensions(dim, valid_modes):
    all_modes = {
        "evolve", "freeze", "discard", "skip", "null_fill", "coerce",
        "discard_value", "discard_row", "ignore",
    }
    for mode in all_modes - valid_modes:
        with pytest.raises(ConformError, match="invalid mode"):
            validate_contract_dict({dim: mode})


# --- resolve_contract: scalar shorthand -------------------------------------


def test_scalar_override_sets_only_extension_dimensions():
    contract = resolve_contract("open", override="freeze")
    assert contract.data_type == "freeze"
    assert contract.keys == "freeze"
    # Column dimensions untouched by the scalar shorthand.
    assert contract.extra_columns == "evolve"
    assert contract.missing_columns == "skip"


def test_scalar_spec_contract_sets_only_extension_dimensions():
    contract = resolve_contract("open", spec_contract="freeze")
    assert contract.data_type == "freeze"
    assert contract.keys == "freeze"
    # Column dimensions untouched by the scalar shorthand.
    assert contract.extra_columns == "evolve"
    assert contract.missing_columns == "skip"


def test_scalar_override_invalid_mode_raises():
    # "freeze" is invalid for... actually valid for both extension dims;
    # use a mode that's invalid for data_type/keys instead.
    with pytest.raises(ConformError, match="invalid mode"):
        resolve_contract("open", override="null_fill")


# --- resolve_contract: dict layering + precedence ---------------------------


def test_resolve_contract_with_no_layers_returns_preset_unchanged():
    contract = resolve_contract("subset")
    assert contract == FIELDS_MATCH_PRESETS["subset"]
    assert contract.from_preset is True


def test_resolve_contract_spec_contract_layer_applies():
    contract = resolve_contract("open", spec_contract={"data_type": "evolve"})
    assert contract.data_type == "evolve"
    assert contract.extra_columns == "evolve"  # untouched preset value


def test_resolve_contract_override_precedence_over_spec_contract():
    """spec_contract < override: override wins on a dimension both set."""
    contract = resolve_contract(
        "open",
        spec_contract={"data_type": "evolve"},
        override={"data_type": "freeze"},
    )
    assert contract.data_type == "freeze"


def test_resolve_contract_override_layer_preserves_spec_contract_dims_not_overridden():
    contract = resolve_contract(
        "open",
        spec_contract={"data_type": "evolve", "keys": "freeze"},
        override={"data_type": "freeze"},
    )
    assert contract.data_type == "freeze"       # overridden
    assert contract.keys == "freeze"             # preserved from spec_contract layer


def test_resolve_contract_dict_layer_can_set_column_dimensions():
    contract = resolve_contract(
        "open",
        override={"extra_columns": "freeze"},
    )
    assert contract.extra_columns == "freeze"
    assert contract.missing_columns == "skip"  # untouched


def test_resolve_contract_layer_rejects_invalid_mode():
    with pytest.raises(ConformError, match="invalid mode"):
        resolve_contract("open", spec_contract={"extra_columns": "null_fill"})


def test_resolve_contract_layer_rejects_unknown_dimension():
    with pytest.raises(ConformError, match="unknown contract dimension"):
        resolve_contract("open", override={"bogus": "freeze"})


# --- resolve_contract: from_preset provenance flag --------------------------


def test_from_preset_true_with_no_explicit_layers():
    assert resolve_contract("exact").from_preset is True


def test_from_preset_flips_false_on_spec_contract_layer():
    assert resolve_contract("open", spec_contract={"keys": "freeze"}).from_preset is False


def test_from_preset_flips_false_on_override_layer():
    assert resolve_contract("open", override="freeze").from_preset is False


def test_from_preset_flips_false_on_dict_override_layer():
    assert resolve_contract("open", override={"data_type": "freeze"}).from_preset is False


def test_from_preset_flips_false_even_when_layer_matches_preset_values():
    """Provenance tracks *explicitness*, not value divergence from the preset."""
    contract = resolve_contract(
        "open", spec_contract={"extra_columns": "evolve", "missing_columns": "skip"}
    )
    assert contract.extra_columns == "evolve"
    assert contract.missing_columns == "skip"
    assert contract.from_preset is False


def test_original_preset_dict_entry_not_mutated_by_resolve_contract():
    """resolve_contract must not mutate the shared FIELDS_MATCH_PRESETS singletons."""
    before = dataclasses.replace(FIELDS_MATCH_PRESETS["open"])
    resolve_contract("open", override={"data_type": "freeze"})
    assert FIELDS_MATCH_PRESETS["open"] == before


# --- fields_match key errors -------------------------------------------------


def test_resolve_contract_unknown_fields_match_raises_keyerror():
    with pytest.raises(KeyError):
        resolve_contract("nonexistent")


# --- resolve_conform_output: contract provenance (item 48 Task 5) -----------
#
# Task 5 replaced the five literal fields_match guard branches in
# resolve_conform_output with a single preset-driven guard keyed off
# ConformContract. These tests exercise the new `contract` parameter and
# its provenance (`from_preset`) directly; tests/conform/test_fields_match.py
# remains the behaviour-parity gate for the fields_match-level API.

from mountainash.conform.expressions import resolve_conform_output
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def _spec(fields_match, field_names):
    return TypeSpec(
        fields=[FieldSpec(name=n, type=UniversalType.STRING) for n in field_names],
        fields_match=fields_match,
    )


def test_resolve_conform_output_default_contract_derived_from_fields_match():
    """contract=None -> derived internally via resolve_contract(fields_match)."""
    spec = _spec("equal", ["a", "b"])
    out = resolve_conform_output(spec, available_columns=["a", "b"])
    assert out.fields_match == "equal"
    assert {em.source_name for em in out.emitted} == {"a", "b"}


def test_resolve_conform_output_default_contract_raises_legacy_fields_match_error():
    """The internally-derived contract is preset provenance, so a frozen-
    dimension violation still raises the legacy fields_match error, not
    SchemaDriftError."""
    spec = _spec("equal", ["a", "b"])
    with pytest.raises(MissingFieldsError):
        resolve_conform_output(spec, available_columns=["a"])


def test_resolve_conform_output_explicit_preset_contract_matches_default():
    """Passing the resolved preset contract explicitly is equivalent to
    leaving contract=None (same preset, same provenance). "subset" allows
    extra columns to be discarded, so a", "b", "extra" is a valid source."""
    spec = _spec("subset", ["a", "b"])
    default_out = resolve_conform_output(
        spec, available_columns=["a", "b", "extra"],
    )
    explicit_out = resolve_conform_output(
        spec,
        available_columns=["a", "b", "extra"],
        contract=resolve_contract("subset"),
    )
    assert [em.source_name for em in default_out.emitted] == [
        em.source_name for em in explicit_out.emitted
    ]


def test_resolve_conform_output_non_preset_contract_missing_columns_defers_to_drift_stub():
    """A non-preset (from_preset=False) contract with a missing_columns=freeze
    violation takes the Task-6 `_raise_drift` branch, which is a stub
    (NotImplementedError) until Task 6 lands."""
    spec = _spec("equal", ["a", "b"])
    contract = dataclasses.replace(resolve_contract("equal"), from_preset=False)
    with pytest.raises(NotImplementedError, match="item 48 Task 6"):
        resolve_conform_output(spec, available_columns=["a"], contract=contract)


def test_resolve_conform_output_non_preset_contract_extra_columns_defers_to_drift_stub():
    """Same as above but for the extra_columns=freeze branch (superset preset)."""
    spec = _spec("superset", ["a"])
    contract = dataclasses.replace(resolve_contract("superset"), from_preset=False)
    with pytest.raises(NotImplementedError, match="item 48 Task 6"):
        resolve_conform_output(
            spec, available_columns=["a", "extra"], contract=contract,
        )


def test_resolve_conform_output_non_preset_contract_without_violation_does_not_raise():
    """A non-preset contract that doesn't trip a frozen dimension passes
    through cleanly -- the drift stub is never reached."""
    spec = _spec("equal", ["a", "b"])
    contract = dataclasses.replace(resolve_contract("equal"), from_preset=False)
    out = resolve_conform_output(
        spec, available_columns=["a", "b"], contract=contract,
    )
    assert {em.source_name for em in out.emitted} == {"a", "b"}


def test_resolve_conform_output_positional_mapping_skips_column_dimension_guards():
    """mapping="positional" (exact preset) only runs the count guard, even
    when passed explicitly as a non-preset contract -- matches today's
    'exact' behaviour (parity gate, brief step 1)."""
    spec = _spec("exact", ["a", "b"])
    contract = dataclasses.replace(resolve_contract("exact"), from_preset=False)
    # Count matches, so no guard fires despite extra_columns/missing_columns
    # both being "freeze" on this preset.
    out = resolve_conform_output(
        spec, available_columns=["x", "y"], contract=contract,
    )
    assert [em.source_name for em in out.emitted] == ["x", "y"]
