"""BaseDataContract — native contract declaration layer (no Pandera).

Members are shared ``FieldDefinition`` declarations:
``age: int = FieldDefinition(dtype=D.I64, minimum=0)``. Contracts compile to
validation checks; execution belongs to mountainash.validation.ValidationRunner
(spec §9.2).
"""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, ClassVar

from mountainash.typespec.spec import FieldDefinition, TableSchema

if TYPE_CHECKING:
    from mountainash.validation.checks import ValidationCheck
    from mountainash.validation.result import ValidationResult

def _is_class_variable(annotation: Any) -> bool:
    """True for a ``ClassVar`` annotation (evaluated or deferred-string form)."""
    if isinstance(annotation, str):
        return annotation.lstrip().startswith(("ClassVar", "typing.ClassVar"))
    return annotation is ClassVar or getattr(annotation, "__origin__", None) is ClassVar



class BaseDataContract:
    """Base class for native data contracts."""

    _contract_fields: ClassVar["dict[str, FieldDefinition]"] = {}
    __table_schema__: ClassVar["TableSchema | None"] = None

    class Config:
        name: str | None = None
        coerce: bool = True
        natural_key: "list[str] | None" = None
        primary_key: Any = None
        strict = None  # reserved

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Base-class order first; a subclass redeclaration keeps the base
        # position (dict update semantics) and its own definition replaces it.
        names: dict[str, Any] = {}
        for klass in reversed(cls.__mro__):
            for name, annotation in getattr(klass, "__annotations__", {}).items():
                names[name] = annotation
            for name, value in vars(klass).items():
                if isinstance(value, FieldDefinition):
                    names.setdefault(name, None)
        members: dict[str, FieldDefinition] = {}
        for name, annotation in names.items():
            if name.startswith("_") or name == "Config" or _is_class_variable(annotation):
                continue
            value = getattr(cls, name, None)
            if not isinstance(value, FieldDefinition):
                raise TypeError(
                    f"{cls.__name__}.{name} is annotated but not declared as a "
                    f"FieldDefinition; contract members are explicit definitions: "
                    f"`{name}: ... = FieldDefinition(...)`"
                )
            # The attached definition is authoritative, whatever the annotation says.
            members[name] = value
        cls._contract_fields = members

    @classmethod
    def contract_name(cls) -> str:
        return getattr(cls.Config, "name", None) or cls.__name__

    @classmethod
    def to_table_schema(cls) -> "TableSchema":
        if "__table_schema__" in vars(cls):
            # The class's own schema is authoritative (schema-generated contracts
            # and explicit assignment).
            return deepcopy(cls.__table_schema__)
        if cls.__table_schema__ is not None:
            # A subclass of a schema-generated contract keeps the inherited
            # table-level declaration; members it redeclares replace in place and
            # new members append.
            schema = deepcopy(cls.__table_schema__)
            for name, definition in cls._contract_fields.items():
                schema.fields[name] = deepcopy(definition)
            return schema
        # primary_key falls back to natural_key so keyed identity survives the
        # TableSchema round-trip (DAG validation resolves identity from
        # TableSchema.primary_key; a natural_key-only contract must not lose it).
        return TableSchema(
            fields=dict(cls._contract_fields),
            title=cls.contract_name(),
            primary_key=(
                getattr(cls.Config, "primary_key", None)
                or getattr(cls.Config, "natural_key", None)
            ),
        )

    @classmethod
    def to_checks(cls) -> "list[ValidationCheck]":
        from mountainash.datacontracts.compiler import compile_datacontract

        return list(compile_datacontract(cls.to_table_schema()).checks)

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
        allow_imperfect_key: bool = False,
    ) -> "ValidationResult":
        """Validate data against this contract; returns a ValidationResult.

        ``sample`` selects an exact-count native snapshot shared by validation
        and failure reporting. Omitting ``random_seed`` leaves sampling unseeded;
        supplying it requires backend support for seeded exact-count sampling.

        Raises IdentityInvalidError if this contract declares a keyed identity
        (Config.primary_key / Config.natural_key) and the data does not honour
        it: always for key fields missing from the data (declaration-phase,
        spec §7); for null-key rows or duplicate key tuples, unless
        allow_imperfect_key=True — which lets the run proceed and reports the
        duplicates via the primary_key_unique check instead (spec §9.3).
        """
        from mountainash.datacontracts.validator import Validator

        return Validator(name=cls.contract_name(), contract=cls).validate(
            data, context=context, head=head, tail=tail, sample=sample,
            random_seed=random_seed, allow_imperfect_key=allow_imperfect_key,
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
        allow_imperfect_key: bool = False,
    ) -> "ValidationResult":
        """Quick validation — same runner, fail_fast=True (item 18 subsumed).

        See validate_datacontract for sampling and allow_imperfect_key contracts.
        """
        from mountainash.datacontracts.validator import Validator

        return Validator(name=cls.contract_name(), contract=cls).validate_quick(
            data, context=context, head=head, tail=tail, sample=sample,
            random_seed=random_seed, allow_imperfect_key=allow_imperfect_key,
        )
