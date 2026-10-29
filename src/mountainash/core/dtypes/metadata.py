"""Declarative metadata for expression operand representations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, get_args


LogicalKind = Literal[
    "boolean",
    "integer",
    "float",
    "text",
    "null",
    "other",
    "unknown",
]
StorageKind = Literal[
    "native",
    "pandas_numpy",
    "pandas_nullable",
    "pandas_arrow",
    "pandas_object",
    "polars_object",
    "sql_dynamic",
]

LOGICAL_KINDS: Final = frozenset(get_args(LogicalKind))
STORAGE_KINDS: Final = frozenset(get_args(StorageKind))
_UNKNOWN_STORAGE_KINDS: Final = frozenset(
    {"pandas_object", "polars_object", "sql_dynamic"}
)


def _validate_logical_kind(logical_kind: str) -> None:
    if logical_kind not in LOGICAL_KINDS:
        raise ValueError(
            f"logical_kind must be one of {sorted(LOGICAL_KINDS)}, got {logical_kind!r}"
        )


def _validate_nullable(nullable: bool | None) -> None:
    nullable_type = type(nullable)
    if nullable is not None and nullable_type is not bool:
        raise TypeError(f"nullable must be bool or None, got {type(nullable).__name__}")


@dataclass(frozen=True)
class OperandType:
    """A resolved expression representation without native dtype details."""

    logical_kind: LogicalKind
    storage_kind: StorageKind
    nullable: bool | None

    def __post_init__(self) -> None:
        _validate_logical_kind(self.logical_kind)
        if self.storage_kind not in STORAGE_KINDS:
            raise ValueError(
                f"storage_kind must be one of {sorted(STORAGE_KINDS)}, got {self.storage_kind!r}"
            )
        _validate_nullable(self.nullable)
        if (
            self.logical_kind == "unknown"
            and self.storage_kind not in _UNKNOWN_STORAGE_KINDS
        ):
            raise ValueError(
                "logical_kind='unknown' is valid only for object or dynamic storage"
            )


@dataclass(frozen=True)
class FixedResultType:
    """A result rule whose logical kind is independent of operand metadata."""

    logical_kind: LogicalKind
    nullable: bool | None

    def __post_init__(self) -> None:
        _validate_logical_kind(self.logical_kind)
        _validate_nullable(self.nullable)


@dataclass(frozen=True)
class PreserveResultType:
    """A result rule that preserves a named expression operand's descriptor."""

    argument: str
    require_kind: LogicalKind | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.argument, str):
            raise TypeError(
                f"argument must be a protocol parameter name, got {type(self.argument).__name__}"
            )
        if not self.argument:
            raise ValueError("argument must be a non-empty protocol parameter name")
        if self.require_kind is not None:
            _validate_logical_kind(self.require_kind)
