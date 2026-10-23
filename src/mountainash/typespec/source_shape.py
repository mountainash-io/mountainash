"""Schema-only structural evidence and its generic portable projection.

Concrete carrier inspection is owned by the registered native schema adapters
(``typespec/native_schema.py``); this module is the shared evidence model and the
acquisition facade consumers call.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mountainash.core.dtypes import DecimalDtype, MountainashDtype, NativeDtype, TypeTarget
from mountainash.core.types import detect_schema_carrier



@dataclass(frozen=True)
class SourceShape:
    """Recursive type evidence exposed by a native schema."""

    canonical_type: MountainashDtype | None
    item_shape: SourceShape | None = None
    struct_fields: tuple[tuple[str, SourceShape], ...] = ()
    decimal: DecimalDtype | None = None
    native_dtype: NativeDtype | None = field(default=None, compare=False)
    detailed_dtype: Any = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if self.decimal is not None and (
            self.canonical_type is not None or self.item_shape is not None or self.struct_fields
        ):
            raise ValueError("a decimal shape is a scalar leaf")
        if self.item_shape is not None and self.canonical_type is not MountainashDtype.LIST:
            raise ValueError("only LIST can have item_shape")
        if self.struct_fields and self.canonical_type is not MountainashDtype.STRUCT:
            raise ValueError("only STRUCT can have struct_fields")
        if self.item_shape is not None and self.struct_fields:
            raise ValueError("one source shape cannot have item and struct children")
        names = tuple(name for name, _ in self.struct_fields)
        if len(names) != len(set(names)):
            raise ValueError("struct field names must be unique")


def shape_from_dtype(dtype: Any) -> SourceShape:
    """Project an already-decoded canonical dtype to the evidence consumers need."""
    from mountainash.core.dtypes import (
        ArrayDtype,
        ListDtype,
        StructDtype,
        dtype_family,
    )

    if dtype is None:
        return SourceShape(None, detailed_dtype=dtype)
    if isinstance(dtype, DecimalDtype):
        return SourceShape(None, decimal=dtype, detailed_dtype=dtype)
    family = dtype_family(dtype)
    canonical = family if isinstance(family, MountainashDtype) else None
    if isinstance(dtype, (ListDtype, ArrayDtype)):
        child = shape_from_dtype(dtype.element)
        if isinstance(dtype, ArrayDtype) and isinstance(dtype.dimensions, tuple):
            for _ in dtype.dimensions[1:]:
                child = SourceShape(MountainashDtype.LIST, child)
        return SourceShape(canonical, child, detailed_dtype=dtype)
    if isinstance(dtype, StructDtype):
        fields = (
            ()
            if not isinstance(dtype.fields, tuple)
            else tuple((name, shape_from_dtype(child)) for name, child in dtype.fields)
        )
        return SourceShape(canonical, struct_fields=fields, detailed_dtype=dtype)
    return SourceShape(canonical, detailed_dtype=dtype)


def extract_source_shapes(native: Any, *, target: TypeTarget | None = None) -> dict[str, SourceShape]:
    """Extract recursive source shapes using schema metadata only.

    The carrier's schema adapter is selected by central recognition. An
    execution placement of ``NARWHALS`` selects the Narwhals schema adapter for
    any carrier it can wrap; the carrier's own representation is not rewritten.
    """
    from mountainash.typespec.adapter_registry import get_native_schema_adapter

    schema_target = TypeTarget.NARWHALS if target is TypeTarget.NARWHALS else detect_schema_carrier(native)
    if schema_target is None:
        raise TypeError(
            "extract_source_shapes: unsupported schema carrier "
            f"{type(native).__module__}.{type(native).__qualname__}"
        )
    return get_native_schema_adapter(schema_target).extract_schema(native)


def shape_type_evidence(shape: SourceShape) -> Any:
    """The detailed type a shape evidences, or UNKNOWN when its decode was unrecognised.

    Nested children are already part of the detailed dtype; the result is the
    portable/native/UNKNOWN vocabulary of ``ResolvedType``, never a new model.
    """
    from mountainash.core.dtypes import SchemaTypeStatus

    return SchemaTypeStatus.UNKNOWN if shape.detailed_dtype is None else shape.detailed_dtype


__all__ = ["SourceShape", "extract_source_shapes", "shape_from_dtype", "shape_type_evidence"]
