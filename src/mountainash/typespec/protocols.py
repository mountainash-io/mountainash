"""Schema-boundary contracts: native schema adapters and interchange codecs.

These protocols depend on the shared declaration and evidence vocabulary only;
never on a concrete backend library or a consumer compiler. Native *type*
adapters live with the dtype system (``core/dtypes/protocols.py``).
"""
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from collections.abc import Mapping
    from mountainash.core.dtypes.protocols import ResolvedType
    from mountainash.typespec.source_shape import SourceShape
    from mountainash.typespec.spec import TableSchema

CarrierT = TypeVar("CarrierT", contravariant=True)
NativeSchemaT = TypeVar("NativeSchemaT")
DescriptorT = TypeVar("DescriptorT")

DeclarationPath = tuple["str | None", ...]
"""Diagnostic location: literal member names, ``None`` for a collection
element scope, the empty tuple for the root. Never split on dots."""


class NativeSchemaAdapter(Protocol[CarrierT, NativeSchemaT]):
    """Acquire schema evidence from a carrier and construct native schemas.

    Acquisition returns shared evidence directly; only ``decode_schema`` and
    ``encode_schema`` bind the implementation-specific ``NativeSchemaT``.
    Neither fabricates evidence or claims constraints are natively enforced.
    """

    @abstractmethod
    def extract_schema(self, carrier: CarrierT) -> dict[str, SourceShape]: ...

    @abstractmethod
    def decode_schema(self, schema: NativeSchemaT) -> dict[str, SourceShape]: ...

    @abstractmethod
    def encode_schema(
        self, schema: TableSchema, *, resolved_types: Mapping[str, ResolvedType],
    ) -> NativeSchemaT: ...


class SchemaCodec(Protocol[DescriptorT]):
    """Import/export of complete supported declarations for one wire format."""

    def decode(self, descriptor: DescriptorT) -> TableSchema: ...

    def encode(self, schema: TableSchema) -> DescriptorT: ...


__all__ = ["DeclarationPath", "NativeSchemaAdapter", "SchemaCodec"]
