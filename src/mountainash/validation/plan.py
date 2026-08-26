"""Immutable snapshots used by validation compilation and execution."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import importlib
from types import MappingProxyType
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash.datacontracts.field import Field
    from mountainash.typespec.universal_types import UniversalType
    from mountainash.typespec.spec import TypeSpec


@dataclass(frozen=True)
class ValidationField:
    name: str
    type: UniversalType
    format: str


@dataclass(frozen=True)
class ValidationFieldPlan:
    fields: tuple[ValidationField, ...]
    by_name: Mapping[str, ValidationField]


@dataclass(frozen=True)
class FrozenForeignKey:
    child_fields: tuple[str, ...]
    parent_resource: str | None
    parent_fields: tuple[str, ...]
    declaration_key: bytes
    declaration_path: str


@dataclass(frozen=True)
class FieldValidationExtension:
    severity: str
    eq: Any = None
    ne: Any = None
    gt: Any = None
    lt: Any = None
    notin: tuple[Any, ...] | None = None
    str_contains: str | None = None
    str_startswith: str | None = None
    str_endswith: str | None = None



def freeze_field_extension(field: "Field") -> FieldValidationExtension:
    """Freeze native-contract-only rules at the compiler boundary."""
    return FieldValidationExtension(
        severity=field.severity,
        eq=freeze_value(field.eq),
        ne=freeze_value(field.ne),
        gt=freeze_value(field.gt),
        lt=freeze_value(field.lt),
        notin=(
            tuple(freeze_value(value) for value in field.notin)
            if field.notin is not None
            else None
        ),
        str_contains=field.str_contains,
        str_startswith=field.str_startswith,
        str_endswith=field.str_endswith,
    )

@dataclass(frozen=True)
class CompiledValidationPlan:
    checks: tuple[Any, ...]
    field_plan: ValidationFieldPlan
    foreign_keys: tuple[FrozenForeignKey, ...]
    declaration: Mapping[str, Any]
    declaration_fingerprint: str


def freeze_value(value: Any) -> Any:
    """Recursively replace mutable declaration values with immutable tagged data."""
    if isinstance(value, Enum):
        return ("__enum__", value.__class__.__module__, value.__class__.__qualname__, value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return MappingProxyType(
            {
                "__dataclass__": f"{value.__class__.__module__}:{value.__class__.__qualname__}",
                "fields": MappingProxyType(
                    {item.name: freeze_value(getattr(value, item.name)) for item in fields(value)}
                ),
            }
        )
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze_value(item) for item in value)
    return value


def _canonical_bytes(value: Any) -> bytes:
    if value is None:
        return b"n"
    if type(value) is bool:
        return b"b1" if value else b"b0"
    if type(value) is int:
        return f"i{value}".encode()
    if type(value) is float:
        return f"f{value.hex()}".encode()
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return b"s" + str(len(encoded)).encode() + b":" + encoded
    if isinstance(value, bytes):
        return b"y" + str(len(value)).encode() + b":" + value
    if isinstance(value, Mapping):
        parts = sorted(
            (_canonical_bytes(key), _canonical_bytes(item)) for key, item in value.items()
        )
        return b"m" + b"".join(
            str(len(key)).encode() + b":" + key + str(len(item)).encode() + b":" + item
            for key, item in parts
        )
    if isinstance(value, (tuple, list, frozenset, set)):
        parts = sorted(_canonical_bytes(item) for item in value) if isinstance(value, (frozenset, set)) else [_canonical_bytes(item) for item in value]
        return b"q" + b"".join(str(len(item)).encode() + b":" + item for item in parts)
    raise TypeError(f"unsupported frozen declaration value: {type(value)!r}")


def freeze_typespec(spec: TypeSpec) -> Mapping[str, Any]:
    """Freeze every TypeSpec field before compiling any executable metadata."""
    frozen = freeze_value(spec)
    assert isinstance(frozen, Mapping)
    return frozen


def _foreign_key_declaration_key(
    child_fields: tuple[str, ...], parent_resource: str | None, parent_fields: tuple[str, ...]
) -> bytes:
    return _canonical_bytes((child_fields, parent_resource, parent_fields))


def build_compiled_plan(spec: TypeSpec, checks: Sequence[Any]) -> CompiledValidationPlan:
    declaration = freeze_typespec(spec)
    fields_snapshot = tuple(
        ValidationField(name=field.name, type=field.type, format=field.format)
        for field in spec.fields
    )
    field_plan = ValidationFieldPlan(
        fields=fields_snapshot,
        by_name=MappingProxyType({field.name: field for field in fields_snapshot}),
    )
    foreign_keys = tuple(
        FrozenForeignKey(
            child_fields=tuple(foreign_key.fields),
            parent_resource=foreign_key.reference.resource,
            parent_fields=tuple(foreign_key.reference.fields),
            declaration_key=_foreign_key_declaration_key(
                tuple(foreign_key.fields),
                foreign_key.reference.resource,
                tuple(foreign_key.reference.fields),
            ),
            declaration_path=f"/foreign_keys/{index}",
        )
        for index, foreign_key in enumerate(spec.foreign_keys or ())
    )
    fingerprint = hashlib.sha256(_canonical_bytes(declaration)).hexdigest()
    return CompiledValidationPlan(
        checks=tuple(checks),
        field_plan=field_plan,
        foreign_keys=foreign_keys,
        declaration=declaration,
        declaration_fingerprint=fingerprint,
    )


__all__ = ["CompiledValidationPlan"]


def thaw_value(value: Any) -> Any:
    """Reconstruct one private mutable declaration copy from a frozen snapshot."""
    if isinstance(value, Mapping) and "__dataclass__" in value:
        module_name, class_name = value["__dataclass__"].split(":", maxsplit=1)
        cls = getattr(importlib.import_module(module_name), class_name)
        return cls(**{name: thaw_value(item) for name, item in value["fields"].items()})
    if (
        isinstance(value, tuple)
        and len(value) == 4
        and value[0] == "__enum__"
    ):
        cls = getattr(importlib.import_module(value[1]), value[2])
        return cls(value[3])
    if isinstance(value, Mapping):
        return {thaw_value(key): thaw_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_value(item) for item in value]
    if isinstance(value, frozenset):
        return {thaw_value(item) for item in value}
    return value


def thaw_typespec(plan: CompiledValidationPlan) -> TypeSpec:
    """Build a fresh TypeSpec for runner-owned conform from a compiled plan."""
    from mountainash.typespec.spec import TypeSpec

    thawed = thaw_value(plan.declaration)
    assert isinstance(thawed, TypeSpec)
    return thawed
