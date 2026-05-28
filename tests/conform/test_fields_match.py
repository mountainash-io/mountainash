"""Tests for fieldsMatch schema-level guard in _build_conform_exprs."""
from __future__ import annotations

import pytest

from mountainash.conform.expressions import ConformResult, _build_conform_exprs
from mountainash.conform.errors import (
    ConformError,
    ExactFieldCountError,
    ExtraFieldsError,
    MissingFieldsError,
    NoMatchingFieldsError,
)
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestConformResultType:
    def test_returns_conform_result(self):
        spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.STRING)])
        result = _build_conform_exprs(spec)
        assert isinstance(result, ConformResult)
        assert len(result.exprs) == 1
        assert isinstance(result.fields_match, str)
        assert isinstance(result.renamed_sources, set)

    def test_none_resolves_to_open(self):
        spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.STRING)])
        result = _build_conform_exprs(spec)
        assert result.fields_match == "open"

    def test_explicit_mode_preserved(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.STRING)],
            fields_match="partial",
        )
        result = _build_conform_exprs(spec, available_columns=["a", "b"])
        assert result.fields_match == "partial"


class TestFieldsMatchOpen:
    def test_open_skips_missing_fields(self):
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(name="missing", type=UniversalType.STRING),
            ],
        )
        result = _build_conform_exprs(spec, available_columns=["a", "b"])
        assert len(result.exprs) == 1

    def test_open_tracks_renamed_sources(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="new_name", type=UniversalType.STRING, rename_from="old_name")],
        )
        result = _build_conform_exprs(spec, available_columns=["old_name", "other"])
        assert "old_name" in result.renamed_sources

    def test_open_without_available_columns_builds_all_fields(self):
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(name="b", type=UniversalType.INTEGER),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 2


class TestFieldsMatchPartial:
    def test_partial_skips_missing_fields(self):
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(name="missing", type=UniversalType.STRING),
            ],
            fields_match="partial",
        )
        result = _build_conform_exprs(spec, available_columns=["a", "b"])
        assert len(result.exprs) == 1

    def test_partial_raises_on_zero_overlap(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="x", type=UniversalType.STRING)],
            fields_match="partial",
        )
        with pytest.raises(NoMatchingFieldsError):
            _build_conform_exprs(spec, available_columns=["a", "b"])


class TestFieldsMatchSubset:
    def test_subset_allows_extra_fields(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.STRING)],
            fields_match="subset",
        )
        result = _build_conform_exprs(spec, available_columns=["a", "b", "c"])
        assert len(result.exprs) == 1

    def test_subset_raises_on_missing_field(self):
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(name="missing", type=UniversalType.STRING),
            ],
            fields_match="subset",
        )
        with pytest.raises(MissingFieldsError) as exc_info:
            _build_conform_exprs(spec, available_columns=["a", "b"])
        assert "missing" in exc_info.value.missing_fields


class TestFieldsMatchSuperset:
    def test_superset_allows_missing_fields(self):
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(name="missing", type=UniversalType.STRING),
            ],
            fields_match="superset",
        )
        result = _build_conform_exprs(spec, available_columns=["a"])
        assert len(result.exprs) == 1

    def test_superset_raises_on_extra_field(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.STRING)],
            fields_match="superset",
        )
        with pytest.raises(ExtraFieldsError) as exc_info:
            _build_conform_exprs(spec, available_columns=["a", "extra"])
        assert "extra" in exc_info.value.extra_fields


class TestFieldsMatchEqual:
    def test_equal_passes_when_fields_match(self):
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(name="b", type=UniversalType.INTEGER),
            ],
            fields_match="equal",
        )
        result = _build_conform_exprs(spec, available_columns=["b", "a"])
        assert len(result.exprs) == 2

    def test_equal_raises_on_missing(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.STRING)],
            fields_match="equal",
        )
        with pytest.raises(MissingFieldsError):
            _build_conform_exprs(spec, available_columns=["b"])

    def test_equal_raises_on_extra(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.STRING)],
            fields_match="equal",
        )
        with pytest.raises(ExtraFieldsError):
            _build_conform_exprs(spec, available_columns=["a", "extra"])


class TestFieldsMatchExact:
    def test_exact_maps_by_position(self):
        spec = TypeSpec(
            fields=[
                FieldSpec(name="first", type=UniversalType.STRING),
                FieldSpec(name="second", type=UniversalType.INTEGER),
            ],
            fields_match="exact",
        )
        result = _build_conform_exprs(spec, available_columns=["col_x", "col_y"])
        assert len(result.exprs) == 2

    def test_exact_raises_on_count_mismatch(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.STRING)],
            fields_match="exact",
        )
        with pytest.raises(ExactFieldCountError) as exc_info:
            _build_conform_exprs(spec, available_columns=["a", "b", "c"])
        assert exc_info.value.expected_count == 1
        assert exc_info.value.actual_count == 3

    def test_exact_ignores_rename_from(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="target", type=UniversalType.STRING, rename_from="ignored")],
            fields_match="exact",
        )
        result = _build_conform_exprs(spec, available_columns=["actual_col"])
        assert len(result.exprs) == 1


class TestFieldsMatchRequiresColumns:
    def test_strict_mode_without_columns_raises(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.STRING)],
            fields_match="equal",
        )
        with pytest.raises(ConformError):
            _build_conform_exprs(spec)

    def test_open_mode_without_columns_ok(self):
        spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.STRING)])
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1
