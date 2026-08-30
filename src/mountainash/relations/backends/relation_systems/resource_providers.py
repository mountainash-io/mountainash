"""Lazy provider discovery and portable Arrow reads for DataResource nodes."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def read_provider_arrow(resource: Any, provider_binding: object | str):
    """Plan and execute one explicitly bound resource provider into Arrow."""
    from mountainash_resource_provider import DetectedResourceFormat, ResourceRequest, validate_provider
    from mountainash_resource_provider.discovery import load_provider_by_key

    provider = load_provider_by_key(provider_binding) if isinstance(provider_binding, str) else validate_provider(provider_binding)
    path = resource.path
    if not isinstance(path, str):
        raise ValueError("provider-bound resource path must be one string locator")
    format_name = (resource.format or Path(path).suffix.lstrip(".")).casefold()
    descriptor = next(
        (
            item
            for item in provider.formats
            if format_name == item.canonical_format or format_name in item.aliases
        ),
        None,
    )
    if descriptor is None:
        raise ValueError(f"provider {provider.key!r} does not support resource format {format_name!r}")
    dialect = resource.to_dialect()
    values = dialect.model_dump(by_alias=True, exclude_none=True) if dialect is not None else {}
    request = ResourceRequest(
        name=resource.name,
        locator=path,
        detected_format=DetectedResourceFormat(
            canonical_format=descriptor.canonical_format,
            dialect_family=descriptor.dialect_family,
            provider_format_key=descriptor.provider_format_key,
            detection_source="explicit",
        ),
        encoding=resource.encoding,
        dialect=values,
        dialect_context={},
        schema=None,
        metadata={},
    )
    return provider.read_arrow(provider.plan(request)).table
