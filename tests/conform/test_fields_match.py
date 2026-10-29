"""Tests for fieldsMatch schema-level guard in _build_conform_exprs."""
from __future__ import annotations

import pytest

from mountainash.conform.expressions import _build_conform_exprs
from mountainash.conform.errors import (
    ConformError,
    ExactFieldsMismatchError,
    ExtraFieldsError,
    MissingFieldsError,
    NoMatchingFieldsError,
)
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType


class TestFieldsMatchPartial:
    def test_partial_raises_on_zero_overlap(self):
        spec = TableSchema(
            fields={"x": FieldDefinition(type=UniversalType.STRING)},
            fields_match="partial",
        )
        with pytest.raises(NoMatchingFieldsError):
            _build_conform_exprs(spec, available_columns=["a", "b"])


class TestFieldsMatchSubset:
    def test_subset_raises_on_missing_field(self):
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.STRING),
                "missing": FieldDefinition(type=UniversalType.STRING),},
            fields_match="subset",
        )
        with pytest.raises(MissingFieldsError) as exc_info:
            _build_conform_exprs(spec, available_columns=["a", "b"])
        assert "missing" in exc_info.value.missing_fields


class TestFieldsMatchSuperset:
    def test_superset_raises_on_extra_field(self):
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.STRING)},
            fields_match="superset",
        )
        with pytest.raises(ExtraFieldsError) as exc_info:
            _build_conform_exprs(spec, available_columns=["a", "extra"])
        assert "extra" in exc_info.value.extra_fields


class TestFieldsMatchEqual:
    def test_equal_raises_on_missing(self):
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.STRING)},
            fields_match="equal",
        )
        with pytest.raises(MissingFieldsError):
            _build_conform_exprs(spec, available_columns=["b"])

    def test_equal_raises_on_extra(self):
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.STRING)},
            fields_match="equal",
        )
        with pytest.raises(ExtraFieldsError):
            _build_conform_exprs(spec, available_columns=["a", "extra"])


class TestFieldsMatchExact:
    def test_exact_raises_on_count_mismatch(self):
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.STRING)},
            fields_match="exact",
        )
        with pytest.raises(ExactFieldsMismatchError) as exc_info:
            _build_conform_exprs(spec, available_columns=["a", "b", "c"])
        assert exc_info.value.reason == "count"

class TestFieldsMatchRequiresColumns:
    def test_strict_mode_without_columns_raises(self):
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.STRING)},
            fields_match="equal",
        )
        with pytest.raises(ConformError):
            _build_conform_exprs(spec)

class TestFieldsMatchDottedSources:
    """Item 46 (b): dotted (struct) sources validate on their ROOT column.

    The guard must agree with the skip/extract logic: both compare dotted
    roots. Guard missing/extra sets are root-collapsed; full dotted paths
    stay on EmittedField.source_name.
    """

    def _spec(self, mode):
        return TableSchema(
            fields={"pid": FieldDefinition(type=UniversalType.INTEGER, rename_from="payload.id")},
            fields_match=mode,
        )

    def test_equal_dotted_root_absent_raises_missing_root(self):
        with pytest.raises(MissingFieldsError) as exc_info:
            _build_conform_exprs(self._spec("equal"), available_columns=["other"])
        # Root-collapsed guard surface: the missing entry is the ROOT
        assert exc_info.value.missing_fields == ["payload"]

    def test_subset_dotted_root_absent_raises(self):
        with pytest.raises(MissingFieldsError) as exc_info:
            _build_conform_exprs(self._spec("subset"), available_columns=["other"])
        assert exc_info.value.missing_fields == ["payload"]

    def test_superset_flat_extra_still_raises(self):
        with pytest.raises(ExtraFieldsError) as exc_info:
            _build_conform_exprs(
                self._spec("superset"), available_columns=["payload", "stray"]
            )
        assert exc_info.value.extra_fields == ["stray"]

    def test_partial_dotted_root_absent_raises(self):
        with pytest.raises(NoMatchingFieldsError):
            _build_conform_exprs(self._spec("partial"), available_columns=["x"])
