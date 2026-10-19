"""BaseDataContract declaration discovery and validation entrypoints."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from mountainash.typespec.spec import FieldSpec

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec
    from mountainash.validation.checks import ValidationCheck
    from mountainash.validation.result import ValidationResult


class BaseDataContract:
    """Base for classes whose FieldSpec members declare validation policy."""

    _contract_fields: ClassVar[dict[str, FieldSpec]] = {}
    __typespec__: ClassVar["TypeSpec | None"] = None

    class Config:
        name: str | None = None
        coerce: bool = True
        natural_key: list[str] | None = None
        primary_key: Any = None
        strict = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        members: dict[str, Any] = {}
        for base in reversed(cls.__mro__[1:]):
            members.update({
                name: value for name, value in vars(base).items()
                if isinstance(value, FieldSpec)
            })
        for name, value in vars(cls).items():
            if isinstance(value, FieldSpec):
                members[name] = value
            elif name in members and not name.startswith("__"):
                members.pop(name)
        cls._contract_fields = members

    @classmethod
    def contract_name(cls) -> str:
        return getattr(cls.Config, "name", None) or cls.__name__

    @classmethod
    def to_typespec(cls) -> "TypeSpec":
        if cls.__typespec__ is not None:
            return cls.__typespec__
        from mountainash.typespec.spec import TypeSpec

        return TypeSpec(
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

        return list(compile_datacontract(cls.to_typespec()).checks)

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

        See validate_datacontract for the allow_imperfect_key contract.
        """
        from mountainash.datacontracts.validator import Validator

        return Validator(name=cls.contract_name(), contract=cls).validate_quick(
            data, context=context, head=head, tail=tail, sample=sample,
            random_seed=random_seed, allow_imperfect_key=allow_imperfect_key,
        )
