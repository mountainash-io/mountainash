"""Conform error hierarchy.

All errors raised during TypeSpec conformance — fieldsMatch violations,
field count mismatches, and transform compilation failures.

See: https://datapackage.org/standard/table-schema/#fieldsMatch
"""
from typing import TYPE_CHECKING, Any, List

from mountainash.core.errors import MountainashError

if TYPE_CHECKING:
    from mountainash.conform.diagnostics import OperationDiagnostic


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
        self,
        *,
        original_error: Exception,
        candidates: tuple["OperationDiagnostic", ...] = (),
        spec_summary: str | None = None,
    ) -> None:
        self.original_error = original_error
        self.candidates = tuple(
            sorted(candidates, key=lambda item: (item.field_name, item.logical_type, item.format))
        )
        # Kept while older callers migrate to the diagnostic trace contract.
        self.spec_summary = spec_summary
        if len(self.candidates) == 1:
            candidate = self.candidates[0]
            detail = (
                f"field {candidate.field_name!r}, logical type "
                f"{candidate.logical_type!r}, format {candidate.format!r}"
            )
        elif self.candidates:
            fields = sorted({candidate.field_name for candidate in self.candidates})
            detail = f"candidate fields {fields!r}"
        elif spec_summary is not None:
            detail = f"Check TypeSpec parsing properties: {spec_summary}"
        else:
            detail = "no matching conform operation diagnostic"
        super().__init__(f"Conform transform failed: {original_error}; {detail}")


class SchemaDriftError(ConformError):
    """A freeze policy detected declared-vs-actual schema drift.

    Carries the tripping node's `ConformDrift` (see conform/drift.py) so
    callers can inspect exactly which columns/types/keys diverged.
    """

    def __init__(self, message: str, *, drift: Any) -> None:
        self.drift = drift
        super().__init__(message)
