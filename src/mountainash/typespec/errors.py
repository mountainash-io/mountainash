from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.errors import MountainashError

if TYPE_CHECKING:
    from mountainash.typespec.universal_types import UniversalType


class DescriptorError(MountainashError):
    """Base for descriptor decoding, encoding, and reference errors."""

    def __init__(
        self,
        message: str,
        *,
        descriptor_kind: str | None = None,
        descriptor_path: str | None = None,
        resource_name: str | None = None,
        reference: str | None = None,
        normalized_reference: str | None = None,
        expected_kind: str | None = None,
        rejected_value: Any = None,
        required_form: str | None = None,
    ) -> None:
        super().__init__(message)
        self.descriptor_kind = descriptor_kind
        self.descriptor_path = descriptor_path
        self.resource_name = resource_name
        self.reference = reference
        self.normalized_reference = normalized_reference
        self.expected_kind = expected_kind
        self.rejected_value = rejected_value
        self.required_form = required_form


class InvalidDescriptorSyntax(DescriptorError, ValueError):
    """The descriptor text is not valid JSON."""


class InvalidDescriptorStructure(DescriptorError, ValueError):
    """A descriptor property or container has an invalid shape."""


class UnsupportedDescriptorVersion(DescriptorError, ValueError):
    """The descriptor contains an explicit v1 marker."""


class MissingDescriptorBase(DescriptorError, ValueError):
    """A relative reference has no base URI."""


class DescriptorReferenceNotFound(DescriptorError, FileNotFoundError):
    """The normalized descriptor reference does not exist."""


class DescriptorReferenceInvalid(DescriptorError, ValueError):
    """The resolved descriptor is malformed or has the wrong kind."""


class DescriptorReferenceSchemeDenied(DescriptorError, PermissionError):
    """The resolver policy denies the reference scheme."""


class InvalidDescriptorRelationship(DescriptorError, ValueError):
    """A descriptor relationship targets an unknown resource or field."""


class UnsupportedResourceDialect(DescriptorError, ValueError):
    """A dialect combines incompatible format-family properties."""


class TypeSpecError(MountainashError, ValueError):
    """Base for field-value/type-shape structural errors (sibling to DescriptorError)."""


class AmbiguousGeospatialTypeError(TypeSpecError):
    def __init__(self, universal_type: "UniversalType") -> None:
        self.universal_type = universal_type
        super().__init__(
            f"{universal_type.value!r} has no single canonical mapping without field "
            f"context; use converters.resolve_field_canonical(field), not to_canonical() directly"
        )


class InvalidGeospatialFormatError(TypeSpecError):
    def __init__(
        self,
        field_name: str,
        universal_type: "UniversalType",
        rejected_format: str,
        allowed_formats: list[str],
    ) -> None:
        self.field_name = field_name
        self.universal_type = universal_type
        self.rejected_format = rejected_format
        self.allowed_formats = allowed_formats
        super().__init__(
            f"field {field_name!r}: format {rejected_format!r} is not valid for "
            f"{universal_type.value!r}; allowed: {allowed_formats}"
        )


class InvalidKeyShapeError(TypeSpecError):
    def __init__(self, label: str, rejected_value: Any, required_form: str) -> None:
        self.field_name = label
        self.rejected_value = rejected_value
        self.required_form = required_form
        super().__init__(
            f"{label}: {rejected_value!r} is not a valid key shape; required: {required_form}"
        )


class IncompatibleFieldPropertiesError(TypeSpecError):
    def __init__(
        self,
        field_name: str,
        property_name: str,
        actual_type: "UniversalType",
        required_types: tuple["UniversalType", ...],
    ) -> None:
        self.field_name = field_name
        self.property_name = property_name
        self.actual_type = actual_type
        self.required_types = required_types
        allowed = " or ".join(t.value for t in required_types)
        super().__init__(
            f"field {field_name!r}: {property_name!r} requires type in ({allowed}), "
            f"got {actual_type.value!r}"
        )


class InvalidFieldMatchDeclaration(TypeSpecError):
    def __init__(
        self,
        standard_value: Any,
        extension_value: Any,
        reason: str,
    ) -> None:
        self.standard_value = standard_value
        self.extension_value = extension_value
        self.reason = reason
        super().__init__(
            "invalid fieldsMatch declaration "
            f"({reason}): standard={standard_value!r}, "
            f"x-mountainash={extension_value!r}"
        )


__all__ = [
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
    "AmbiguousGeospatialTypeError",
    "InvalidGeospatialFormatError",
    "InvalidKeyShapeError",
    "IncompatibleFieldPropertiesError",
    "InvalidFieldMatchDeclaration",
]
