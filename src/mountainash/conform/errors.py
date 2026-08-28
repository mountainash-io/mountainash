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


class ExactFieldsMismatchError(ConformError):
    """Ordered exact-field mismatch with a stable machine-readable reason."""

    def __init__(
        self,
        *,
        expected: list[str] | tuple[str, ...],
        actual: list[str] | tuple[str, ...],
        reason: str,
    ) -> None:
        self.expected = tuple(expected)
        self.actual = tuple(actual)
        self.reason = reason
        super().__init__(
            f"fieldsMatch='exact': {reason} mismatch; expected "
            f"{self.expected!r}, actual {self.actual!r}"
        )


class UnresolvedSourceTypeError(ConformError):
    """The source representation is required but schema evidence is unknown."""

    def __init__(self, *, field_name: str, requirement: str) -> None:
        self.field_name = field_name
        self.requirement = requirement
        super().__init__(
            f"field {field_name!r} requires resolved source type evidence: "
            f"{requirement}"
        )


class IncompatibleSourceTypeError(ConformError):
    """The source representation cannot satisfy a field operation."""

    def __init__(
        self,
        *,
        field_name: str,
        source_detail: str,
        requirement: str,
    ) -> None:
        self.field_name = field_name
        self.source_detail = source_detail
        self.requirement = requirement
        super().__init__(
            f"field {field_name!r} has incompatible source type "
            f"{source_detail!r}; requires {requirement}"
        )


class UnsupportedStructuredTransportUse(ConformError):
    """A transported structured physical carrier reached an unsafe relation use."""

    def __init__(
        self, *, field_name: str, root: str, node_type: str, consumer: str
    ) -> None:
        self.field_name = field_name
        self.root = root
        self.node_type = node_type
        self.consumer = consumer
        super().__init__(
            f"Transported {root} field {field_name!r} cannot be used by "
            f"{consumer} in {node_type} before logical decoding"
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
