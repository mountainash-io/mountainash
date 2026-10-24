# src/mountainash/core/dtypes/protocols.py
"""Contracts implemented by the per-target native dtype adapters.

Depends only on the canonical dtype vocabulary and generics: no native library
and no consumer (typespec/conform) is imported here. One stateless adapter per
:class:`TypeTarget` implements both protocols; ``DtypeRegistry`` selects and
retains it lazily.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar, Protocol, TypeVar, runtime_checkable

from .canonical import CastTarget, NativeDtype, PortableDtype, SchemaTypeStatus

if TYPE_CHECKING:
    from .targets import TypeTarget

# Annotation aliases over the existing vocabulary, not wrapper classes. Absent
# source evidence is ``None`` and UNKNOWN stays missing knowledge; a consumer
# still distinguishes the three members' meanings.
TypeEvidence = PortableDtype | NativeDtype | SchemaTypeStatus
ResolvedType = TypeEvidence

NativeTypeT = TypeVar("NativeTypeT")
ArrowTypeT = TypeVar("ArrowTypeT")


@runtime_checkable
class NativeTypeAdapter(Protocol[NativeTypeT]):
    """Native/canonical dtype translation for one type target.

    Methods receive resolved type intent, never a field declaration: precedence,
    evidence reconciliation and field diagnostics belong to shared resolution.
    """

    target: ClassVar[TypeTarget]

    @abstractmethod
    def from_native(self, value: NativeTypeT) -> TypeEvidence:
        """Decode a native dtype, retaining parameters and native refinements.

        Never returns None; unrecognised or invalid input raises the existing
        typed dtype error.
        """
        ...

    @abstractmethod
    def to_native_schema(self, dtype: CastTarget) -> NativeTypeT:
        """Lower ``dtype`` for schema construction (bare containers allowed)."""
        ...

    @abstractmethod
    def to_native_cast(self, dtype: CastTarget) -> NativeTypeT:
        """Lower ``dtype`` as an expression cast target (bare containers raise)."""
        ...

    @abstractmethod
    def parse_type_string(self, text: str) -> NativeTypeT | None:
        """Parse a native type spelling; None means an unrecognised spelling."""
        ...

    @abstractmethod
    def types_equal(self, left: NativeTypeT, right: NativeTypeT) -> bool:
        """Compare native types in their owning domain, retaining parameters."""
        ...


@runtime_checkable
class NativeArrowTransportAdapter(Protocol[NativeTypeT, ArrowTypeT]):
    """Native-owner conversion of one native dtype to its Arrow transport dtype.

    Returns a dtype, not a field: names, nullability and metadata stay with the
    schema adapters, and qualifiers reaching this dtype-only path are refused
    rather than stripped.
    """

    @abstractmethod
    def to_arrow_transport(self, value: NativeTypeT) -> ArrowTypeT:
        ...
