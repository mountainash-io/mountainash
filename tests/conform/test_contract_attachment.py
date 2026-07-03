"""Contract attachment surface: `Relation.conform(spec, contract=...)`.

Item 48 PR-B, Task 8. This module tests only the *attachment* surface —
that the raw contract override is validated eagerly at build time and
stored unresolved on `ConformRelNode.contract`. Resolution against
`TypeSpec.contract` / the `fields_match` preset (via `resolve_contract`)
happens inside `apply_conform` in a later task and is NOT exercised here.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.conform.errors import ConformError
from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_conform import (
    ConformRelNode,
)
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def _spec(**kwargs):
    return TypeSpec(
        fields=[FieldSpec(name="a", type=UniversalType.STRING)],
        **kwargs,
    )


# --- ConformRelNode: new optional field --------------------------------


def test_conform_rel_node_contract_defaults_to_none():
    node = ConformRelNode(input=ma.relation({"a": [1]})._node, spec=_spec())
    assert node.contract is None


def test_conform_rel_node_existing_construction_without_contract_unaffected():
    """Pre-existing call sites that never pass contract= keep working."""
    node = ConformRelNode(input=ma.relation({"a": [1]})._node, spec={})
    assert node.contract is None


def test_conform_rel_node_stores_raw_dict_contract():
    node = ConformRelNode(
        input=ma.relation({"a": [1]})._node,
        spec=_spec(),
        contract={"data_type": "freeze"},
    )
    assert node.contract == {"data_type": "freeze"}


def test_conform_rel_node_stores_raw_scalar_contract():
    node = ConformRelNode(
        input=ma.relation({"a": [1]})._node,
        spec=_spec(),
        contract="freeze",
    )
    assert node.contract == "freeze"


# --- Relation.conform(spec, contract=...) -------------------------------


def test_conform_without_contract_stores_none():
    r = ma.relation({"a": [1]}).conform(_spec())
    assert r._node.contract is None


def test_conform_with_dict_contract_stores_raw_override():
    r = ma.relation({"a": [1]}).conform(_spec(), contract={"keys": "freeze"})
    assert r._node.contract == {"keys": "freeze"}


def test_conform_with_scalar_contract_stores_raw_override():
    r = ma.relation({"a": [1]}).conform(_spec(), contract="freeze")
    assert r._node.contract == "freeze"


def test_conform_spec_untouched_by_contract_kwarg():
    """contract= is stored on the node, not written back onto spec."""
    spec = _spec()
    r = ma.relation({"a": [1]}).conform(spec, contract={"data_type": "freeze"})
    assert r._node.spec is spec
    assert spec.contract is None


# --- Eager build-time validation -----------------------------------------


def test_conform_dict_contract_unknown_dimension_raises_at_build_time():
    with pytest.raises(ConformError, match="unknown contract dimension"):
        ma.relation({"a": [1]}).conform(_spec(), contract={"bogus": "freeze"})


def test_conform_dict_contract_invalid_mode_raises_at_build_time():
    with pytest.raises(ConformError, match="invalid mode"):
        ma.relation({"a": [1]}).conform(_spec(), contract={"keys": "discard_row"})


def test_conform_scalar_contract_invalid_for_extension_dims_raises_at_build_time():
    """"null_fill" is valid for missing_columns but not for the extension
    dimensions (data_type, keys) the scalar shorthand expands into."""
    with pytest.raises(ConformError, match="invalid mode"):
        ma.relation({"a": [1]}).conform(_spec(), contract="null_fill")


def test_conform_scalar_contract_valid_for_both_extension_dims_succeeds():
    # "freeze" is a valid mode for both data_type and keys.
    r = ma.relation({"a": [1]}).conform(_spec(), contract="freeze")
    assert r._node.contract == "freeze"
