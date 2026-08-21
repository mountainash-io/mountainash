from __future__ import annotations

from typing import Any

from mountainash.core.errors import MountainashError


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
]
