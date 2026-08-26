"""Closed JSON Schema declaration compilation.

Instance diagnostics are added with the ValueRule engine; this module owns the
shared declaration boundary so semantic validation and runtime execution agree.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for

from mountainash.typespec.errors import (
    InvalidJSONSchemaConstraint,
    JSONSchemaReferenceDenied,
)


@dataclass(frozen=True)
class CompiledJSONSchema:
    """A checked local JSON Schema declaration and its selected validator."""

    declaration: Mapping[str, Any]
    validator: Any


def _reject_remote_references(value: Any) -> None:
    if isinstance(value, Mapping):
        for keyword in ("$ref", "$dynamicRef", "$recursiveRef"):
            reference = value.get(keyword)
            if isinstance(reference, str) and not reference.startswith("#"):
                raise JSONSchemaReferenceDenied(
                    f"JSON Schema reference {reference!r} is not a local fragment"
                )
        for nested in value.values():
            _reject_remote_references(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_remote_references(nested)


def compile_json_schema(declaration: Mapping[str, Any]) -> CompiledJSONSchema:
    """Validate a mapping declaration without allowing remote resolution."""
    if not isinstance(declaration, Mapping) or not all(
        isinstance(key, str) for key in declaration
    ):
        raise InvalidJSONSchemaConstraint("json_schema must be a mapping with string keys")

    _reject_remote_references(declaration)
    try:
        validator_type = validator_for(declaration, default=Draft202012Validator)
        validator_type.check_schema(declaration)
        return CompiledJSONSchema(declaration=dict(declaration), validator=validator_type)
    except JSONSchemaReferenceDenied:
        raise
    except Exception as error:
        raise InvalidJSONSchemaConstraint(str(error)) from error


__all__ = []
