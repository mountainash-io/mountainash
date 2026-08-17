"""BaseDataContract — native contract declaration layer (no Pandera).

Declaration style is unchanged for users: `age: int = Field(ge=0)`.
Contracts compile to validation checks; execution belongs to
mountainash.validation.ValidationRunner (spec §9.2).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from mountainash.datacontracts.field import Field

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec
    from mountainash.validation.checks import ValidationCheck
    from mountainash.validation.result import ValidationResult


class BaseDataContract:
    """Base class for native data contracts."""

    _contract_fields: ClassVar["dict[str, Field]"] = {}
    _contract_annotations: ClassVar["dict[str, Any]"] = {}
    __typespec__: ClassVar["TypeSpec | None"] = None

    class Config:
        name: str | None = None
        coerce: bool = True
        natural_key: "list[str] | None" = None
        primary_key: Any = None
        strict = None  # reserved

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        annotations: dict[str, Any] = {}
        for klass in reversed(cls.__mro__):
            annotations.update(getattr(klass, "__annotations__", {}))
        cls._contract_annotations = {
            name: annotation
            for name, annotation in annotations.items()
            if not name.startswith("_") and name != "Config"
        }
        fields: dict[str, Field] = {}
        for name in cls._contract_annotations:
            value = getattr(cls, name, None)
            if isinstance(value, Field):
                fields[name] = value
        cls._contract_fields = fields

    @classmethod
    def contract_name(cls) -> str:
        return getattr(cls.Config, "name", None) or cls.__name__

    @classmethod
    def to_typespec(cls) -> "TypeSpec":
        if cls.__typespec__ is not None:
            return cls.__typespec__
        from mountainash.typespec.extraction import python_type_to_universal
        from mountainash.typespec.spec import FieldSpec, TypeSpec
        from mountainash.typespec.universal_types import parse_universal

        fields = []
        for name, annotation in cls._contract_annotations.items():
            contract_field = cls._contract_fields.get(name)
            fields.append(
                FieldSpec(
                    name=name,
                    type=parse_universal(python_type_to_universal(annotation)),
                    title=contract_field.title if contract_field else None,
                    description=contract_field.description if contract_field else None,
                    constraints=contract_field.to_constraints() if contract_field else None,
                )
            )
        # primary_key falls back to natural_key so keyed identity survives the
        # TypeSpec round-trip (DAG validation resolves identity from
        # TypeSpec.primary_key; a natural_key-only contract must not lose it).
        return TypeSpec(
            fields=fields,
            title=cls.contract_name(),
            primary_key=(
                getattr(cls.Config, "primary_key", None)
                or getattr(cls.Config, "natural_key", None)
            ),
        )

    @classmethod
    def to_checks(cls) -> "list[ValidationCheck]":
        from mountainash.datacontracts.compiler import primary_key_check

        checks: "list[ValidationCheck]" = []
        for name, contract_field in cls._contract_fields.items():
            checks.extend(contract_field.to_checks(name))
        pk_check = primary_key_check(cls.to_typespec())
        if pk_check is not None:
            checks.append(pk_check)
        return checks

    @classmethod
    def validate_datacontract(
        cls,
        data: Any,
        *,
        context: "dict[str, Any] | None" = None,
        head: int | None = None,
        tail: int | None = None,
        sample: int | None = None,
        random_seed: int | None = None,
    ) -> "ValidationResult":
        """Validate data against this contract; returns (never raises)."""
        from mountainash.datacontracts.validator import Validator

        return Validator(name=cls.contract_name(), contract=cls).validate(
            data, context=context, head=head, tail=tail, sample=sample,
            random_seed=random_seed,
        )

    @classmethod
    def validate_datacontract_quick(
        cls,
        data: Any,
        *,
        context: "dict[str, Any] | None" = None,
        head: int | None = None,
        tail: int | None = None,
        sample: int | None = None,
        random_seed: int | None = None,
    ) -> "ValidationResult":
        """Quick validation — same runner, fail_fast=True (item 18 subsumed)."""
        from mountainash.datacontracts.validator import Validator

        return Validator(name=cls.contract_name(), contract=cls).validate_quick(
            data, context=context, head=head, tail=tail, sample=sample,
            random_seed=random_seed,
        )
