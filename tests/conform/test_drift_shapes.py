"""Tests for conform drift report shapes and SchemaDriftError.

Covers: TypeDrift, ColumnDrift, KeyDrift, ConformDrift, ConformCollection
(src/mountainash/conform/drift.py) and SchemaDriftError (conform/errors.py).

Key semantic under test: ConformDrift.key_changes distinguishes `None`
(NOT assessed — no DAG/FK context available) from `[]` (assessed, clean —
DAG/FK context was available and no drift was found). `.compatible` must
treat both as "no key drift" for the purposes of the item 17-P8 predicate,
since it only judges assessed dimensions.
"""
from __future__ import annotations

import pytest

from mountainash.conform.drift import (
    ColumnDrift,
    ConformCollection,
    ConformDrift,
    KeyDrift,
    TypeDrift,
)
from mountainash.conform.errors import ConformError, SchemaDriftError


class TestTypeDrift:
    def test_is_frozen(self):
        drift = TypeDrift(
            name="amount", declared="Int64", actual="Float64",
            safety="unsafe", action="coerce",
        )
        with pytest.raises(AttributeError):
            drift.name = "other"  # type: ignore[misc]

    def test_fields(self):
        drift = TypeDrift(
            name="amount", declared="Int64", actual="Float64",
            safety="unsafe", action="coerce",
        )
        assert drift.name == "amount"
        assert drift.declared == "Int64"
        assert drift.actual == "Float64"
        assert drift.safety == "unsafe"
        assert drift.action == "coerce"


class TestColumnDrift:
    def test_is_frozen(self):
        drift = ColumnDrift(name="extra_col", action="evolve")
        with pytest.raises(AttributeError):
            drift.action = "freeze"  # type: ignore[misc]

    def test_fields(self):
        drift = ColumnDrift(name="missing_col", action="null_fill")
        assert drift.name == "missing_col"
        assert drift.action == "null_fill"


class TestKeyDrift:
    def test_is_frozen(self):
        drift = KeyDrift(kind="fk_field_dropped", fields=["id"], reference="orders")
        with pytest.raises(AttributeError):
            drift.kind = "dangling_reference"  # type: ignore[misc]

    def test_defaults(self):
        drift = KeyDrift(kind="dangling_reference", fields=["customer_id"], reference="customers")
        assert drift.declared is None
        assert drift.actual is None
        assert drift.action == "ignore"

    def test_explicit_fields(self):
        drift = KeyDrift(
            kind="fk_type_mismatch",
            fields=["customer_id"],
            reference="customers",
            declared="Int64",
            actual="Utf8",
            action="freeze",
        )
        assert drift.declared == "Int64"
        assert drift.actual == "Utf8"
        assert drift.action == "freeze"


class TestConformDriftCompatible:
    """Every dimension of .compatible, one at a time, plus the None-vs-[] rule."""

    def _base_kwargs(self):
        return dict(node_id="n1", resource_name="orders", spec_name="orders_spec")

    def test_clean_drift_is_compatible(self):
        drift = ConformDrift(**self._base_kwargs())
        assert drift.compatible is True

    def test_extra_columns_trips_compatible(self):
        drift = ConformDrift(
            **self._base_kwargs(),
            extra_columns=[ColumnDrift(name="extra", action="evolve")],
        )
        assert drift.compatible is False

    def test_missing_columns_trips_compatible(self):
        drift = ConformDrift(
            **self._base_kwargs(),
            missing_columns=[ColumnDrift(name="missing", action="null_fill")],
        )
        assert drift.compatible is False

    def test_type_mismatches_trips_compatible(self):
        drift = ConformDrift(
            **self._base_kwargs(),
            type_mismatches=[
                TypeDrift(
                    name="amount", declared="Int64", actual="Float64",
                    safety="unsafe", action="coerce",
                )
            ],
        )
        assert drift.compatible is False

    def test_nonempty_key_changes_trips_compatible(self):
        drift = ConformDrift(
            **self._base_kwargs(),
            key_changes=[
                KeyDrift(kind="dangling_reference", fields=["customer_id"], reference="customers")
            ],
        )
        assert drift.compatible is False

    def test_key_changes_none_does_not_trip_compatible(self):
        """None means NOT ASSESSED (no DAG/FK context) — must not count as drift."""
        drift = ConformDrift(**self._base_kwargs(), key_changes=None)
        assert drift.compatible is True

    def test_key_changes_empty_list_does_not_trip_compatible(self):
        """[] means ASSESSED and clean — also must not count as drift."""
        drift = ConformDrift(**self._base_kwargs(), key_changes=[])
        assert drift.compatible is True

    def test_key_changes_none_vs_empty_are_distinguishable(self):
        not_assessed = ConformDrift(**self._base_kwargs(), key_changes=None)
        assessed_clean = ConformDrift(**self._base_kwargs(), key_changes=[])
        assert not_assessed.key_changes is None
        assert assessed_clean.key_changes == []
        assert not_assessed.key_changes is not assessed_clean.key_changes

    def test_is_frozen(self):
        drift = ConformDrift(**self._base_kwargs())
        with pytest.raises(AttributeError):
            drift.node_id = "other"  # type: ignore[misc]

    def test_default_field_lists_are_independent_instances(self):
        """Frozen dataclass with field(default_factory=list) must not share mutable state."""
        a = ConformDrift(**self._base_kwargs())
        b = ConformDrift(**self._base_kwargs())
        assert a.extra_columns is not b.extra_columns
        assert a.missing_columns is not b.missing_columns
        assert a.type_mismatches is not b.type_mismatches


class TestConformCollection:
    def _drift(self, node_id: str) -> ConformDrift:
        return ConformDrift(node_id=node_id, resource_name=None, spec_name=None)

    def test_drift_property_returns_single_drift(self):
        d = self._drift("n1")
        collection = ConformCollection(frame=None, drifts=[d], effective_schema={})
        assert collection.drift is d

    def test_drift_property_raises_on_zero_nodes(self):
        collection = ConformCollection(frame=None, drifts=[], effective_schema={})
        with pytest.raises(ValueError, match="0 conform nodes"):
            collection.drift

    def test_drift_property_raises_on_multiple_nodes(self):
        collection = ConformCollection(
            frame=None,
            drifts=[self._drift("n1"), self._drift("n2")],
            effective_schema={},
        )
        with pytest.raises(ValueError, match="2 conform nodes"):
            collection.drift

    def test_is_frozen(self):
        collection = ConformCollection(frame=None, drifts=[], effective_schema={})
        with pytest.raises(AttributeError):
            collection.frame = "other"  # type: ignore[misc]


class TestSchemaDriftError:
    def test_inherits_conform_error(self):
        assert issubclass(SchemaDriftError, ConformError)

    def test_carries_drift_payload(self):
        drift = ConformDrift(node_id="n1", resource_name="orders", spec_name="orders_spec")
        err = SchemaDriftError("schema drift detected under freeze policy", drift=drift)
        assert err.drift is drift
        assert "schema drift detected" in str(err)

    def test_raisable(self):
        drift = ConformDrift(node_id="n1", resource_name=None, spec_name=None)
        with pytest.raises(SchemaDriftError) as exc_info:
            raise SchemaDriftError("drift", drift=drift)
        assert exc_info.value.drift is drift


class TestFacadeExports:
    def test_schema_drift_error_exported_from_exceptions(self):
        from mountainash.exceptions import SchemaDriftError as FacadeSchemaDriftError

        assert FacadeSchemaDriftError is SchemaDriftError

    def test_drift_shapes_exported_from_conform_init(self):
        from mountainash.conform import (
            ColumnDrift as InitColumnDrift,
            ConformCollection as InitConformCollection,
            ConformDrift as InitConformDrift,
            KeyDrift as InitKeyDrift,
            TypeDrift as InitTypeDrift,
        )

        assert InitTypeDrift is TypeDrift
        assert InitColumnDrift is ColumnDrift
        assert InitKeyDrift is KeyDrift
        assert InitConformDrift is ConformDrift
        assert InitConformCollection is ConformCollection
