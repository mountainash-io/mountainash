"""Public façade for the mountainash error hierarchy.

Mirrors the `polars.exceptions` convention: one import home for every typed
error mountainash raises. This module defines nothing — it only re-exports the
classes from their owning modules' `errors.py` (single source of truth).

    from mountainash.exceptions import MissingResourceSchema

For broad catches, `mountainash.MountainashError` is also available at the top
level (the root is the only error exported from the package `__init__`).
"""
from __future__ import annotations

from mountainash.core.errors import (
    BackendConversionError,
    CapabilityResidueInvariantError,
    InvalidOptionValueError,
    MountainashError,
)
from mountainash.conform.errors import (
    ConformError,
    MissingFieldsError,
    ExtraFieldsError,
    ExactFieldsMismatchError,
    NoMatchingFieldsError,
    ConformTransformError,
    SchemaDriftError,
    UnresolvedSourceTypeError,
    IncompatibleSourceTypeError,
    UnsupportedStructuredTransportUse,
)
from mountainash.relations.core.errors import InvalidSampleArgumentsError, LogicalTerminalRequired
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
from mountainash.typespec.errors import (
    DescriptorError,
    InvalidDescriptorSyntax,
    InvalidDescriptorStructure,
    UnsupportedDescriptorVersion,
    MissingDescriptorBase,
    DescriptorReferenceNotFound,
    DescriptorReferenceInvalid,
    DescriptorReferenceSchemeDenied,
    InvalidDescriptorRelationship,
    UnsupportedResourceDialect,
    TypeSpecError,
    InvalidTypeSpecSemantics,
    InvalidConstraintDeclaration,
    InvalidJSONSchemaConstraint,
    JSONSchemaReferenceDenied,
    AmbiguousFieldName,
    InvalidFieldIdentifier,
    AmbiguousGeospatialTypeError,
    InvalidGeospatialFormatError,
    InvalidKeyShapeError,
    IncompatibleFieldPropertiesError,
    InvalidFieldMatchDeclaration,
)
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
    "BackendConversionError",
    "InvalidOptionValueError",
    "InvalidSampleArgumentsError",
    "LogicalTerminalRequired",
    "BareExpressionCollectionError",
    "ConformError",
    "MissingFieldsError",
    "ExtraFieldsError",
    "ExactFieldsMismatchError",
    "MembershipArgumentError",
    "NativeExprMemberError",
    "NestedCollectionError",
    "NoMatchingFieldsError",
    "ConformTransformError",
    "SchemaDriftError",
    "UnresolvedSourceTypeError",
    "IncompatibleSourceTypeError",
    "UnsupportedStructuredTransportUse",
    "DAGError",
    "RelationDAGRequired",
    "MissingResourceSchema",
    "UnsupportedResourceFormat",
    "CapabilityResidueInvariantError",
    "DtypeError",
    "UnknownDtypeError",
    "DtypeMappingError",
    "BackendCapabilityError",
    "SchemaValidationError",
    "DescriptorError",
    "InvalidDescriptorSyntax",
    "InvalidDescriptorStructure",
    "UnsupportedDescriptorVersion",
    "MissingDescriptorBase",
    "DescriptorReferenceNotFound",
    "DescriptorReferenceInvalid",
    "DescriptorReferenceSchemeDenied",
    "InvalidDescriptorRelationship",
    "UnsupportedResourceDialect",
    "TypeSpecError",
    "InvalidTypeSpecSemantics",
    "InvalidConstraintDeclaration",
    "InvalidJSONSchemaConstraint",
    "JSONSchemaReferenceDenied",
    "AmbiguousFieldName",
    "InvalidFieldIdentifier",
    "AmbiguousGeospatialTypeError",
    "InvalidGeospatialFormatError",
    "InvalidKeyShapeError",
    "IncompatibleFieldPropertiesError",
    "InvalidFieldMatchDeclaration",
    "StepEmptyError",
    "UnsupportedCollectionError",
    "ValidationError",
    "CheckDeclarationError",
    "IdentityRequiredError",
    "IdentityInvalidError",
    "UnknownCheckTypeError",
]
