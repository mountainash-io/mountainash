"""Conform error hierarchy.

All errors raised during TypeSpec conformance — fieldsMatch violations,
field count mismatches, and transform compilation failures.

See: https://datapackage.org/standard/table-schema/#fieldsMatch
"""
from __future__ import annotations

from typing import List

from mountainash.core.errors import MountainashError


class ConformError(MountainashError):
    """Base error for conformance failures."""


class MissingFieldsError(ConformError):
    """Spec declares fields not present in the data source."""

    def __init__(self, *, missing_fields: List[str], fields_match: str) -> None:
        self.missing_fields = missing_fields
        self.fields_match = fields_match
        super().__init__(
            f"fieldsMatch={fields_match!r}: spec fields not found in data: "
            f"{missing_fields}. Set fields_match='open' or 'partial' to skip "
            f"missing fields."
        )


class ExtraFieldsError(ConformError):
    """Data source has fields not declared in the spec."""

    def __init__(self, *, extra_fields: List[str], fields_match: str) -> None:
        self.extra_fields = extra_fields
        self.fields_match = fields_match
        super().__init__(
            f"fieldsMatch={fields_match!r}: data has undeclared fields: "
            f"{extra_fields}. Set fields_match='open' or 'partial' to allow "
            f"extra fields."
        )


class ExactFieldCountError(ConformError):
    """Field count mismatch in exact mode (positional mapping)."""

    def __init__(self, *, expected_count: int, actual_count: int) -> None:
        self.expected_count = expected_count
        self.actual_count = actual_count
        super().__init__(
            f"fieldsMatch='exact': spec has {expected_count} fields but data "
            f"has {actual_count} columns. Exact mode requires identical count."
        )


class NoMatchingFieldsError(ConformError):
    """No overlap between spec fields and data source columns."""

    def __init__(
        self, *, spec_fields: List[str], available_columns: List[str]
    ) -> None:
        self.spec_fields = spec_fields
        self.available_columns = available_columns
        super().__init__(
            f"fieldsMatch='partial': no spec fields found in data. "
            f"Spec fields: {spec_fields}, data columns: {available_columns}."
        )


class ConformTransformError(ConformError):
    """The conform pipeline failed due to incompatible source data types."""

    def __init__(
        self, *, original_error: Exception, spec_summary: str
    ) -> None:
        self.original_error = original_error
        self.spec_summary = spec_summary
        super().__init__(
            f"Conform transform failed: {original_error}. "
            f"Check TypeSpec parsing properties: {spec_summary}"
        )
