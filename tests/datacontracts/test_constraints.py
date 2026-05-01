"""Tests for reusable FieldConstraints constants and combinators."""
from __future__ import annotations

from mountainash.typespec.spec import FieldConstraints
from mountainash.datacontracts.constraints import (
    SINGLE_CHAR, ISO_DATE, ISO_DATETIME, POSITIVE_INT, PERCENTAGE,
    required, with_enum, with_range, with_length,
)


class TestConstraintConstants:

    def test_single_char(self):
        assert SINGLE_CHAR.min_length == 1
        assert SINGLE_CHAR.max_length == 1
        assert SINGLE_CHAR.required is False

    def test_iso_date(self):
        assert ISO_DATE.min_length == 10
        assert ISO_DATE.max_length == 10
        assert ISO_DATE.pattern == r"\d{4}-\d{2}-\d{2}"

    def test_iso_datetime(self):
        assert ISO_DATETIME.min_length == 19
        assert ISO_DATETIME.max_length == 19

    def test_positive_int(self):
        assert POSITIVE_INT.required is True
        assert POSITIVE_INT.minimum == 0

    def test_percentage(self):
        assert PERCENTAGE.minimum == 0
        assert PERCENTAGE.maximum == 100


class TestConstraintCombinators:

    def test_required_adds_required(self):
        result = required(SINGLE_CHAR)
        assert result.required is True
        assert result.min_length == 1

    def test_required_does_not_mutate_original(self):
        _ = required(SINGLE_CHAR)
        assert SINGLE_CHAR.required is False

    def test_with_enum(self):
        result = with_enum(SINGLE_CHAR, ["Y", "N"])
        assert result.enum == ["Y", "N"]
        assert result.min_length == 1

    def test_with_range(self):
        result = with_range(FieldConstraints(), minimum=0, maximum=999)
        assert result.minimum == 0
        assert result.maximum == 999

    def test_with_length(self):
        result = with_length(FieldConstraints(), min_length=5, max_length=20)
        assert result.min_length == 5
        assert result.max_length == 20

    def test_chained_combinators(self):
        result = required(with_enum(SINGLE_CHAR, ["Y", "N"]))
        assert result.required is True
        assert result.enum == ["Y", "N"]
        assert result.min_length == 1
