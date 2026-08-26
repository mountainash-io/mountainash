"""mountainash.validation — backend-agnostic validation engine.

Checks compile through the existing expression/relation visitors; the
runner contains no backend-specific code. See the conform boundary:
conform owns structural schema conformance, validation owns value-level
checks (spec §3).
"""
from mountainash.validation.checks import (
    BOOLEANIZERS,
    SEVERITIES,
    VERDICT_PASSING,
    DistributionRule,
    ForeignKeyRule,
    RelationRule,
    RowRule,
    ScalarRule,
    ValidationCheck,
    check_kind,
    ValueRule,
    ValueValidatorKey,
    classify,
    require_as_of,
    validate_severity,
)
from mountainash.validation.errors import (
    CheckDeclarationError,
    IdentityInvalidError,
    IdentityRequiredError,
    UnknownCheckTypeError,
    ValidationError,
)
from mountainash.validation.fk import build_fk_checks, build_standalone_fk_checks
from mountainash.validation.identity import (
    RowIdentity,
    require_keyed,
    resolve_identity,
    validate_keyed_identity,
)
from mountainash.validation.result import (
    BLOCKING_STATUSES,
    VALID_STATUSES,
    CheckSummary,
    DAGValidationResult,
    ValidationResult,
    combine_failure_frames,
    empty_failure_frame,
    failure_case_schema,
    interpolate_message,
    is_blocking,
    passes_from_summaries,
    summaries_frame,
)
from mountainash.validation.runner import ROW_ORDINAL, ValidationRunner
from mountainash.validation.schema import (
    TypeSpecIssue,
    require_valid_typespec,
    validate_typespec_semantics,
)
from mountainash.validation.plan import CompiledValidationPlan

__all__ = [
    "BLOCKING_STATUSES",
    "BOOLEANIZERS",
    "ROW_ORDINAL",
    "SEVERITIES",
    "VALID_STATUSES",
    "VERDICT_PASSING",
    "CheckDeclarationError",
    "CheckSummary",
    "DAGValidationResult",
    "DistributionRule",
    "ForeignKeyRule",
    "IdentityInvalidError",
    "IdentityRequiredError",
    "RelationRule",
    "RowIdentity",
    "RowRule",
    "ScalarRule",
    "UnknownCheckTypeError",
    "ValidationCheck",
    "ValidationError",
    "ValidationResult",
    "ValidationRunner",
    "TypeSpecIssue",
    "CompiledValidationPlan",
    "ValueRule",
    "ValueValidatorKey",
    "build_fk_checks",
    "build_standalone_fk_checks",
    "check_kind",
    "classify",
    "combine_failure_frames",
    "empty_failure_frame",
    "failure_case_schema",
    "interpolate_message",
    "is_blocking",
    "passes_from_summaries",
    "require_as_of",
    "require_keyed",
    "resolve_identity",
    "summaries_frame",
    "validate_keyed_identity",
    "validate_severity",
    "require_valid_typespec",
    "validate_typespec_semantics",
]
