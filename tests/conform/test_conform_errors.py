"""Tests for conform error hierarchy."""
from __future__ import annotations

import pytest

from mountainash.conform.errors import (
    ConformError,
    MissingFieldsError,
    ExtraFieldsError,
    ExactFieldsMismatchError,
    NoMatchingFieldsError,
    ConformTransformError,
)


class TestConformErrorHierarchy:
    def test_all_errors_inherit_from_conform_error(self):
        assert issubclass(MissingFieldsError, ConformError)
        assert issubclass(ExactFieldsMismatchError, ConformError)

    def test_missing_fields_error_attributes(self):
        err = MissingFieldsError(
            missing_fields=["col_a", "col_b"],
            fields_match="subset",
        )
        assert err.missing_fields == ["col_a", "col_b"]
        assert err.fields_match == "subset"
        assert "col_a" in str(err)
        assert "subset" in str(err)

    def test_extra_fields_error_attributes(self):
        err = ExtraFieldsError(
            extra_fields=["unknown_col"],
            fields_match="superset",
        )
        assert err.extra_fields == ["unknown_col"]
        assert err.fields_match == "superset"
        assert "unknown_col" in str(err)

    def test_exact_fields_mismatch_error_attributes(self):
        err = ExactFieldsMismatchError(expected=("a",), actual=("b",), reason="name")
        assert err.expected == ("a",)
        assert err.actual == ("b",)
        assert err.reason == "name"
        assert "name" in str(err)

    def test_no_matching_fields_error_attributes(self):
        err = NoMatchingFieldsError(
            spec_fields=["a", "b"],
            available_columns=["x", "y"],
        )
        assert err.spec_fields == ["a", "b"]
        assert err.available_columns == ["x", "y"]

    def test_conform_transform_error_wraps_original(self):
        original = TypeError("cannot compare Boolean to Utf8")
        err = ConformTransformError(
            original_error=original,
            spec_summary="decimalChar=',', bareNumber=false",
        )
        assert err.original_error is original
        assert "decimalChar" in err.spec_summary
        assert "cannot compare" in str(err)

    def test_conform_error_catchable_as_base(self):
        err = MissingFieldsError(missing_fields=["a"], fields_match="equal")
        with pytest.raises(ConformError):
            raise err
