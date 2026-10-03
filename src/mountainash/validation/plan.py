"""Immutable snapshots used by validation compilation and execution."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass, replace
from types import MappingProxyType
from typing import Any, TYPE_CHECKING
from mountainash.typespec._fingerprint import (
    declaration_fingerprint,
    freeze_declaration as freeze_value,
    freeze_typespec,
)


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




def _foreign_key_declaration_key(
    child_fields: tuple[str, ...], parent_resource: str | None, parent_fields: tuple[str, ...]
) -> bytes:
    return declaration_fingerprint((child_fields, parent_resource, parent_fields)).encode()

def _copy_expression_value(value: Any, memo: dict[int, Any]) -> Any:
    """Copy Mountainash expression declaration structure, keeping opaque leaves.

    Only AST nodes, window declarations, sort fields and the plain containers
    holding them are rebuilt. Native literal values, callbacks, dtypes, enums
    and other leaves are retained without inspection.
    """
    from mountainash.core.constants import SortField
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import ExpressionNode
    from mountainash.expressions.core.expression_nodes.substrait.exn_literal import (
        LiteralNode,
    )
    from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import (
        WindowBound,
        WindowSpec,
    )

    key = id(value)
    if key in memo:
        return memo[key]

    if isinstance(value, BaseExpressionAPI):
        copied: Any = type(value).create(_copy_expression_value(value._node, memo))
    elif isinstance(value, (ExpressionNode, WindowSpec, WindowBound)):
        # Native literal payloads are opaque; diagnostic_context is already an
        # immutable mapping.
        skip = {"diagnostic_context"}
        if isinstance(value, LiteralNode) and value.is_native:
            skip.add("value")
        update = {
            name: _copy_expression_value(getattr(value, name), memo)
            for name in type(value).model_fields
            if name not in skip
        }
        copied = value.model_copy(update=update)
    elif isinstance(value, SortField):
        copied = replace(
            value,
            **{
                item.name: _copy_expression_value(getattr(value, item.name), memo)
                for item in fields(value)
            },
        )
    elif type(value) is dict:
        copied = {}
        memo[key] = copied
        for name, item in value.items():
            copied[name] = _copy_expression_value(item, memo)
    elif isinstance(value, MappingProxyType):
        copied = MappingProxyType(
            {name: _copy_expression_value(item, memo) for name, item in value.items()}
        )
    elif type(value) is list:
        copied = []
        memo[key] = copied
        copied.extend(_copy_expression_value(item, memo) for item in value)
    elif type(value) is tuple:
        copied = tuple(_copy_expression_value(item, memo) for item in value)
    elif type(value) in (set, frozenset):
        copied = type(value)(_copy_expression_value(item, memo) for item in value)
    else:
        return value

    memo[key] = copied
    return copied


def _freeze_check(check: Any) -> Any:
    """Copy check declarations into the immutable compiled-plan snapshot."""
    if not is_dataclass(check) or isinstance(check, type):
        return check
    replacements = {
        item.name: freeze_value(getattr(check, item.name))
        for item in fields(check)
        if item.name not in {"expr", "plan", "validator"}
    }
    if hasattr(check, "expr"):
        replacements["expr"] = _copy_expression_value(check.expr, {})
    return replace(check, **replacements)


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
    fingerprint = declaration_fingerprint(declaration)
    return CompiledValidationPlan(
        checks=tuple(_freeze_check(check) for check in checks),
        field_plan=field_plan,
        foreign_keys=foreign_keys,
        declaration=declaration,
        declaration_fingerprint=fingerprint,
    )


__all__ = ["CompiledValidationPlan"]


def _thaw_dataclass_type(identifier: str) -> type[Any]:
    """Resolve only the closed TypeSpec declaration vocabulary."""
    from mountainash.typespec.spec import (
        FieldConstraints,
        FieldSpec,
        ForeignKey,
        ForeignKeyReference,
        LabeledValue,
        TypeSpec,
    )

    allowed = {
        f"{cls.__module__}:{cls.__qualname__}": cls
        for cls in (
            FieldConstraints,
            FieldSpec,
            ForeignKey,
            ForeignKeyReference,
            LabeledValue,
            TypeSpec,
        )
    }
    try:
        return allowed[identifier]
    except KeyError:
        raise ValueError(
            f"unsupported frozen dataclass declaration {identifier!r}"
        ) from None


def _thaw_enum(module_name: str, class_name: str, value: Any) -> Any:
    """Resolve only TypeSpec's closed universal-type enum."""
    from mountainash.typespec.universal_types import UniversalType

    if (module_name, class_name) != (
        UniversalType.__module__,
        UniversalType.__qualname__,
    ):
        raise ValueError(
            f"unsupported frozen enum declaration {module_name}:{class_name}"
        )
    return UniversalType(value)


def thaw_value(value: Any) -> Any:
    """Reconstruct one private mutable declaration copy from a frozen snapshot."""
    if isinstance(value, Mapping) and "__dataclass__" in value:
        cls = _thaw_dataclass_type(value["__dataclass__"])
        return cls(**{name: thaw_value(item) for name, item in value["fields"].items()})
    if (
        isinstance(value, tuple)
        and len(value) == 4
        and value[0] == "__enum__"
    ):
        return _thaw_enum(value[1], value[2], value[3])
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
