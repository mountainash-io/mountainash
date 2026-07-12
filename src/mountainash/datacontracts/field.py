"""Native Field descriptor — constraint metadata compiling to validation checks.

Replaces pa.Field(); keeps its kwargs verbatim so contract declarations
migrate by changing only the import (acceptance 10).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mountainash.typespec.spec import FieldConstraints

if TYPE_CHECKING:
    from mountainash.validation.checks import ValidationCheck


@dataclass(frozen=True)
class Field:
    nullable: bool = True
    eq: Any = None
    ne: Any = None
    gt: Any = None
    ge: Any = None
    lt: Any = None
    le: Any = None
    isin: "list[Any] | None" = None
    notin: "list[Any] | None" = None
    str_matches: str | None = None
    str_contains: str | None = None
    str_startswith: str | None = None
    str_endswith: str | None = None
    str_length: "dict[str, int] | None" = None
    unique: bool = False
    severity: str = "blocking"
    title: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        from mountainash.validation.checks import validate_severity

        validate_severity("Field", self.severity)

    def to_constraints(self) -> FieldConstraints:
        # Frictionless-shaped subset only (frictionless-structural-fidelity);
        # the beyond-Frictionless kwargs compile directly in to_checks.
        length = self.str_length or {}
        return FieldConstraints(
            required=not self.nullable,
            unique=self.unique,
            minimum=self.ge,
            maximum=self.le,
            min_length=length.get("min_value"),
            max_length=length.get("max_value"),
            pattern=self.str_matches,
            enum=list(self.isin) if self.isin is not None else None,
        )

    def to_checks(self, col_name: str) -> "list[ValidationCheck]":
        from mountainash.datacontracts.compiler import constraint_checks, extra_field_checks

        return constraint_checks(
            col_name, self.to_constraints(), severity=self.severity
        ) + extra_field_checks(col_name, self, severity=self.severity)
