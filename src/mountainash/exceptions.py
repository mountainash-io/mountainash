"""Public façade for the mountainash error hierarchy.

Mirrors the `polars.exceptions` convention: one import home for every typed
error mountainash raises. This module defines nothing — it only re-exports the
classes from their owning modules' `errors.py` (single source of truth).

    from mountainash.exceptions import MissingResourceSchema

For broad catches, `mountainash.MountainashError` is also available at the top
level (the root is the only error exported from the package `__init__`).
"""
from __future__ import annotations

from mountainash.core.errors import InvalidOptionValueError, MountainashError
from mountainash.conform.errors import (
    ConformError,
    MissingFieldsError,
    ExtraFieldsError,
    ExactFieldCountError,
    NoMatchingFieldsError,
    ConformTransformError,
    SchemaDriftError,
)
from mountainash.relations.core.errors import InvalidSampleArgumentsError
from mountainash.relations.dag.errors import (
    DAGError,
    RelationDAGRequired,
    MissingResourceSchema,
    UnsupportedResourceFormat,
)
from mountainash.core.dtypes.errors import (
    DtypeError,
    UnknownDtypeError,
    DtypeMappingError,
)
from mountainash.core.types import BackendCapabilityError
from mountainash.typespec.validation import SchemaValidationError
from mountainash.pipelines.errors import StepEmptyError
from mountainash.expressions.membership.errors import (
    BareExpressionCollectionError,
    MembershipArgumentError,
    NativeExprMemberError,
    NestedCollectionError,
    UnsupportedCollectionError,
)
from mountainash.validation.errors import (
    CheckDeclarationError,
    IdentityInvalidError,
    IdentityRequiredError,
    UnknownCheckTypeError,
    ValidationError,
)

__all__ = [
    "MountainashError",
    "InvalidOptionValueError",
    "InvalidSampleArgumentsError",
    "BareExpressionCollectionError",
    "ConformError",
    "MissingFieldsError",
    "ExtraFieldsError",
    "ExactFieldCountError",
    "MembershipArgumentError",
    "NativeExprMemberError",
    "NestedCollectionError",
    "NoMatchingFieldsError",
    "ConformTransformError",
    "SchemaDriftError",
    "DAGError",
    "RelationDAGRequired",
    "MissingResourceSchema",
    "UnsupportedResourceFormat",
    "DtypeError",
    "UnknownDtypeError",
    "DtypeMappingError",
    "BackendCapabilityError",
    "SchemaValidationError",
    "StepEmptyError",
    "UnsupportedCollectionError",
    "ValidationError",
    "CheckDeclarationError",
    "IdentityRequiredError",
    "IdentityInvalidError",
    "UnknownCheckTypeError",
]
