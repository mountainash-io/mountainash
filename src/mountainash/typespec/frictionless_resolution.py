"""Lazy resolution and validation of referenced Frictionless descriptors."""
from __future__ import annotations

from collections.abc import Mapping

from mountainash.typespec.descriptor_context import DescriptorContext, DescriptorKind
from mountainash.typespec.errors import (
    DescriptorError,
    DescriptorReferenceInvalid,
    DescriptorReferenceNotFound,
    DescriptorReferenceSchemeDenied,
    InvalidDescriptorStructure,
    MissingDescriptorBase,
)
from mountainash.typespec.frictionless_codec import (
    _structure_error,
    _validate_dialect,
    _validate_schema,
)
from mountainash.typespec.frictionless_invariants import (
    InvariantLocation,
    reject_v1_markers_at,
)


def validate_resolved_kind(
    raw: object,
    *,
    expected_kind: DescriptorKind,
    location: InvariantLocation,
) -> None:
    """Validate the shape of one resolved schema or dialect document."""
    if not isinstance(raw, Mapping):
        raise _structure_error(
            "resolved descriptor must have a mapping root",
            descriptor_path=location.descriptor_path,
            rejected_value=raw,
            required_form=f"{expected_kind.value} mapping",
            descriptor_kind=expected_kind.value,
            resource_name=location.resource_name,
        )

    nested_key = expected_kind.value
    if isinstance(raw.get(nested_key), str):
        raise _structure_error(
            f"resolved {nested_key} must not be another reference",
            descriptor_path=f"{location.descriptor_path}.{nested_key}",
            rejected_value=raw[nested_key],
            required_form=f"inline {nested_key} mapping",
            descriptor_kind=expected_kind.value,
            resource_name=location.resource_name,
        )

    if expected_kind is DescriptorKind.SCHEMA:
        _validate_schema(
            raw,
            path=location.descriptor_path,
            resource_name=location.resource_name,
        )
        return

    if not raw:
        raise _structure_error(
            "resolved dialect mapping must not be empty",
            descriptor_path=location.descriptor_path,
            rejected_value=raw,
            required_form="non-empty Table Dialect mapping",
            descriptor_kind=expected_kind.value,
            resource_name=location.resource_name,
        )
    _validate_dialect(
        raw,
        path=location.descriptor_path,
        resource_name=location.resource_name,
    )


def resolve_descriptor_mapping(
    value: Mapping[str, object] | str,
    *,
    context: DescriptorContext,
    expected_kind: DescriptorKind,
    location: InvariantLocation,
) -> Mapping[str, object]:
    """Resolve and validate one raw or referenced descriptor lazily."""
    if isinstance(value, str):
        try:
            raw = context.resolver.resolve(
                value,
                base_uri=context.base_uri,
                expected_kind=expected_kind,
            )
        except MissingDescriptorBase as exc:
            raise MissingDescriptorBase(
                str(exc),
                descriptor_kind=expected_kind.value,
                descriptor_path=location.descriptor_path,
                resource_name=location.resource_name,
                reference=exc.reference,
                rejected_value=value,
                required_form="absolute URI or relative reference with base URI",
            ) from exc
        except DescriptorReferenceNotFound as exc:
            raise DescriptorReferenceNotFound(
                str(exc),
                descriptor_kind=expected_kind.value,
                descriptor_path=location.descriptor_path,
                resource_name=location.resource_name,
                reference=exc.reference,
                normalized_reference=exc.normalized_reference,
                expected_kind=exc.expected_kind,
                rejected_value=value,
                required_form="existing descriptor document",
            ) from exc
        except DescriptorReferenceSchemeDenied as exc:
            raise DescriptorReferenceSchemeDenied(
                str(exc),
                descriptor_kind=expected_kind.value,
                descriptor_path=location.descriptor_path,
                resource_name=location.resource_name,
                reference=exc.reference,
                normalized_reference=exc.normalized_reference,
                expected_kind=exc.expected_kind,
                rejected_value=value,
                required_form="approved descriptor reference scheme",
            ) from exc
        except DescriptorError:
            raise
        except Exception as exc:
            raise DescriptorReferenceInvalid(
                "descriptor reference could not be resolved",
                descriptor_kind=expected_kind.value,
                descriptor_path=location.descriptor_path,
                resource_name=location.resource_name,
                reference=value,
                expected_kind=expected_kind.value,
                rejected_value=value,
                required_form=f"resolvable {expected_kind.value} JSON reference",
            ) from exc
        reference = value
    else:
        raw = value
        reference = None

    marker_location = InvariantLocation(
        "$" if reference is not None else location.descriptor_path,
        location.resource_name,
        reference,
    )
    if isinstance(raw, Mapping):
        reject_v1_markers_at(
            raw,
            descriptor_kind=expected_kind.value,
            location=marker_location,
        )

    try:
        validate_resolved_kind(
            raw,
            expected_kind=expected_kind,
            location=location,
        )
    except InvalidDescriptorStructure as exc:
        if reference is None:
            raise
        raise DescriptorReferenceInvalid(
            "resolved descriptor has an invalid structure",
            descriptor_kind=expected_kind.value,
            descriptor_path=location.descriptor_path,
            resource_name=location.resource_name,
            reference=reference,
            expected_kind=expected_kind.value,
            rejected_value=exc.rejected_value,
            required_form=exc.required_form,
        ) from exc
    return raw


__all__ = ["resolve_descriptor_mapping", "validate_resolved_kind"]
