"""Closed JSON Schema declaration compilation.

Instance diagnostics are added with the ValueRule engine; this module owns the
shared declaration boundary so semantic validation and runtime execution agree.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for

from mountainash.typespec.errors import (
    InvalidJSONSchemaConstraint,
    JSONSchemaReferenceDenied,
)


@dataclass(frozen=True)
class JSONSchemaDiagnostic:
    """One deterministic data-quality error from a compiled schema."""

    instance_path: str
    schema_path: str
    validator: str
    message: str


def _json_pointer(parts: Iterable[Any]) -> str:
    """Render JSON Schema's path deque as an RFC 6901 pointer."""
    return "".join(
        "/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


@dataclass(frozen=True)
class CompiledJSONSchema:
    """A checked local JSON Schema declaration and its selected validator."""

    declaration: Mapping[str, Any]
    validator: Any

    def validate(self, instance: Any) -> tuple[JSONSchemaDiagnostic, ...]:
        """Return every instance error in stable pointer order."""
        diagnostics = [
            JSONSchemaDiagnostic(
                instance_path=_json_pointer(error.absolute_path),
                schema_path=_json_pointer(error.absolute_schema_path),
                validator=error.validator,
                message=error.message,
            )
            for error in self.validator.iter_errors(instance)
        ]
        return tuple(
            sorted(
                diagnostics,
                key=lambda item: (
                    item.instance_path,
                    item.schema_path,
                    item.validator,
                    item.message,
                ),
            )
        )

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
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for nested in value:
            _reject_remote_references(nested)


def _owned_json_value(value: Any) -> Any:
    """Copy frozen declaration snapshots into jsonschema's mutable-neutral data."""
    if isinstance(value, Mapping):
        return {key: _owned_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_owned_json_value(item) for item in value]
    return value


def compile_json_schema(declaration: Mapping[str, Any]) -> CompiledJSONSchema:
    """Validate a mapping declaration without allowing remote resolution."""
    if not isinstance(declaration, Mapping) or not all(
        isinstance(key, str) for key in declaration
    ):
        raise InvalidJSONSchemaConstraint("json_schema must be a mapping with string keys")

    _reject_remote_references(declaration)
    try:
        frozen_declaration = _owned_json_value(declaration)
        validator_type = validator_for(frozen_declaration, default=Draft202012Validator)
        validator_type.check_schema(frozen_declaration)
        return CompiledJSONSchema(
            declaration=frozen_declaration,
            validator=validator_type(frozen_declaration),
        )
    except JSONSchemaReferenceDenied:
        raise
    except Exception as error:
        raise InvalidJSONSchemaConstraint(str(error)) from error


__all__ = []
