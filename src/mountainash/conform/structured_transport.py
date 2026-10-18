"""Portable physical-to-logical transport for structured conform fields."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
import json
import math
from types import MappingProxyType
from typing import Any, Literal, NoReturn


class StructuredRoot(str, Enum):
    """The declared top-level JSON shape."""

    ARRAY = "array"
    OBJECT = "object"


class StructuredCarrier(str, Enum):
    """The physical representation selected from source schema evidence."""

    NATIVE = "native"
    JSON_TEXT = "json_text"
    OPAQUE = "opaque"


StructuredAction = Literal["coerce", "discard_value", "discard_row", "evolve", "freeze"]


@dataclass(frozen=True)
class StructuredFieldPlan:
    """Immutable structured-field execution facts for one conform application."""

    field_name: str
    root: StructuredRoot
    carrier: StructuredCarrier
    configured_action: StructuredAction
    apply_value_transforms: bool
    missing_values: tuple[str, ...]
    null_fill: Any | None
    declaration_fingerprint: str
    origin_node_id: str
    target_dtype: Any = None
    declaration: Any = None

    @property
    def requires_logical_terminal(self) -> bool:
        """Whether native egress must resolve the field through a logical snapshot."""
        return (
            self.apply_value_transforms
            and self.configured_action in {"coerce", "discard_value", "discard_row"}
            and self.carrier in {StructuredCarrier.JSON_TEXT, StructuredCarrier.OPAQUE}
        )


StructuredFieldPlanMap = Mapping[str, StructuredFieldPlan]


class StructuredActionConsumer(str, Enum):
    """Consumer-specific action semantics for a structured physical cell."""

    VALIDATION = "validation"
    LOGICAL_EGRESS = "logical_egress"


@dataclass(frozen=True)
class InvalidStructuredValue:
    """Identity sentinel for a physical value that cannot satisfy a structured declaration."""


INVALID_STRUCTURED_VALUE = InvalidStructuredValue()


@dataclass(frozen=True)
class StructuredCellResolution:
    """One resolved logical cell and its row-retention decision."""

    logical_value: Any
    post_missing_is_null: bool
    keep: bool


def freeze_structured_field_plans(
    plans: Mapping[str, StructuredFieldPlan],
) -> StructuredFieldPlanMap:
    """Make one structured-field plan mapping immutable at its producer boundary."""
    return MappingProxyType(dict(plans))

def freeze_structured_value(value: Any) -> Any:
    """Freeze a null-fill value without changing its decoder-visible shape."""
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: freeze_structured_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(freeze_structured_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze_structured_value(item) for item in value)
    return value


def _reject_constant(token: str) -> NoReturn:
    raise ValueError(f"non-finite JSON number: {token}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate object name")
        result[name] = value
    return result


def _normalize_native(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int, Decimal, date, datetime, time, timedelta)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite native number")
        return value
    if isinstance(value, (list, tuple)):
        return [_normalize_native(item) for item in value]
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("structured mapping keys must be strings")
            normalized[key] = _normalize_native(item)
        return normalized
    raise TypeError(f"unsupported structured native value: {type(value)!r}")


def _is_native_null_scalar(value: Any) -> bool:
    """Recognize backend null scalars only at the physical-cell boundary."""
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value)
    value_type = type(value)
    return value_type.__module__.startswith("pandas.") and value_type.__name__ in {
        "NAType",
        "NaTType",
    }


def _all_numbers_are_finite(value: Any) -> None:
    """Reject non-finite numeric leaves in a decoded JSON tree."""
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite JSON number")
    elif isinstance(value, list):
        for item in value:
            _all_numbers_are_finite(item)
    elif isinstance(value, dict):
        for item in value.values():
            _all_numbers_are_finite(item)


def decode_structured_value(
    value: Any, *, expected_root: StructuredRoot
) -> list[Any] | dict[str, Any] | None | InvalidStructuredValue:
    """Decode one physical carrier without accepting ambiguous JSON or Python values."""
    try:
        decoded = (
            json.loads(value, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
            if isinstance(value, str)
            else _normalize_native(value)
        )
        if isinstance(value, str):
            _all_numbers_are_finite(decoded)
        if decoded is None:
            return None
        if expected_root is StructuredRoot.ARRAY and isinstance(decoded, list):
            return decoded
        if expected_root is StructuredRoot.OBJECT and isinstance(decoded, dict):
            return decoded
    except (json.JSONDecodeError, RecursionError, TypeError, ValueError):
        return INVALID_STRUCTURED_VALUE
    return INVALID_STRUCTURED_VALUE


def transport_arrow_dtype(dtype: Any) -> Any:
    """Translate an effective execution type to its Arrow transport representation."""
    import pyarrow as pa
    from mountainash.core.dtypes import (
        DecimalDtype, MountainashDtype, NativeDtype, SchemaTypeStatus, TypeTarget, registry,
    )
    from mountainash.core.dtypes.target_pyarrow import to_native_parameterized

    if dtype is None:
        return None
    if dtype is SchemaTypeStatus.UNKNOWN:
        return pa.null()
    native = dtype if isinstance(dtype, NativeDtype) else getattr(dtype, "native", None)
    if native is not None:
        value = registry.to_native_schema(native, native.target)
        if native.target is TypeTarget.PYARROW:
            return value
        if native.target is TypeTarget.POLARS:
            import polars as pl
            return pl.Series("", [], dtype=value).to_arrow().type
        if native.target is TypeTarget.PANDAS:
            import pandas as pd
            return pa.Array.from_pandas(pd.Series([], dtype=value)).type
        if native.target is TypeTarget.NARWHALS:
            from narwhals._arrow.utils import narwhals_to_native_dtype
            from narwhals._utils import Version
            return narwhals_to_native_dtype(value, Version.MAIN)
        if native.target is TypeTarget.IBIS:
            from ibis.formats.pyarrow import PyArrowType
            return PyArrowType.from_ibis(value)
        return registry.to_native_schema(dtype, TypeTarget.PYARROW)
    if isinstance(dtype, (MountainashDtype, DecimalDtype)):
        return registry.to_native_schema(dtype, TypeTarget.PYARROW)
    return to_native_parameterized(dtype, child_lowerer=transport_arrow_dtype)


def _convert_struct_mapping(value: Mapping[str, Any], children: Any, dtypes: Any = None) -> dict[str, Any]:
    by_name = {child.name: child for child in children}
    names = value if dtypes is None else dtypes
    result = {}
    for name in names:
        item = value.get(name)
        child = by_name.get(name)
        if child is None and dtypes is not None:
            from mountainash.typespec.spec import FieldSpec
            child = FieldSpec(name=name)
        if child is not None:
            if isinstance(item, str) and child.missing_values is not None:
                from mountainash.typespec._categorical import categorical_values
                if item in categorical_values(list(child.missing_values)):
                    item = None
            if item is None and child.null_fill is not None:
                item = child.null_fill
            item = _convert_declared_value(item, child, None if dtypes is None else dtypes[name])
        result[name] = item
    return result


def _convert_declared_value(value: Any, field: Any, dtype: Any = None) -> Any:
    """Apply retained nested FieldSpec conversion instructions to decoded cells."""
    if value is None:
        return None
    from mountainash.core.dtypes import (
        ArrayDtype, DecimalDtype, ListDtype, StructDtype, MountainashDtype,
        NativeDtype, SchemaTypeStatus, TypeTarget, dtype_family, registry,
    )
    from mountainash.typespec.converters import effective_child_fields, resolve_field_canonical

    if dtype is None:
        dtype = field.dtype
        if dtype is None or dtype is SchemaTypeStatus.UNKNOWN:
            dtype = resolve_field_canonical(field)
    if dtype is SchemaTypeStatus.UNKNOWN:
        return value
    native = dtype if isinstance(dtype, NativeDtype) else getattr(dtype, "native", None)
    if native is not None:
        decoded = registry.from_native(native.value, native.target)
        if dtype_family(decoded) in {MountainashDtype.STRUCT, MountainashDtype.LIST}:
            dtype = decoded
        elif isinstance(decoded, NativeDtype):
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                f"Structured transport cannot faithfully convert opaque native dtype {native.value!s}.",
                backend=native.target.value,
                function_key=None,
            )
        else:
            dtype = decoded
    family = dtype_family(dtype)
    unsupported_metadata = (
        (family is MountainashDtype.BOOL and (field.true_values is not None or field.false_values is not None))
        or field.decimal_char is not None
        or field.group_char is not None
        or field.bare_number is False
        or field.rounding is not None
        or field.categories is not None
    )
    if unsupported_metadata:
        from mountainash.core.types import BackendCapabilityError

        raise BackendCapabilityError(
            f"Structured conversion metadata for {field.name!r} cannot be honored by direct Arrow casting.",
            backend="pyarrow",
            function_key=None,
        )
    if family is MountainashDtype.STRUCT and isinstance(value, Mapping):
        fields = dict(dtype.fields) if isinstance(dtype, StructDtype) and dtype.fields is not SchemaTypeStatus.UNKNOWN else None
        return _convert_struct_mapping(value, effective_child_fields(field), fields)
    if family is MountainashDtype.LIST and isinstance(value, list):
        element = dtype.element if isinstance(dtype, (ListDtype, ArrayDtype)) else SchemaTypeStatus.UNKNOWN
        if isinstance(dtype, ArrayDtype) and dtype.dimensions is not SchemaTypeStatus.UNKNOWN and len(dtype.dimensions) > 1:
            element = ArrayDtype(dtype.element, dtype.dimensions[1:])
        if dtype_family(element) is MountainashDtype.STRUCT:
            children = effective_child_fields(field)
            fields = dict(element.fields) if element.fields is not SchemaTypeStatus.UNKNOWN else None
            return [
                None if item is None else _convert_struct_mapping(item, children, fields)
                for item in value
            ]
        return [_convert_declared_value(item, field, element) for item in value]
    if family in {MountainashDtype.TIMESTAMP, MountainashDtype.TIME, MountainashDtype.DATE}:
        if not isinstance(value, str):
            return value
        import pyarrow as pa
        import pyarrow.compute as pc

        native = transport_arrow_dtype(dtype)
        if field.format not in (None, "default", "any"):
            parsed_python = datetime.strptime(value, field.format)
            if family is MountainashDtype.DATE:
                parsed_python = parsed_python.date()
            elif family is MountainashDtype.TIME:
                parsed_python = parsed_python.time()
            return pa.scalar(parsed_python, type=native)
        if field.format == "any":
            from mountainash.typespec.temporal import parse_temporal_any
            kind = "datetime" if family is MountainashDtype.TIMESTAMP else (
                "date" if family is MountainashDtype.DATE else "time"
            )
            try:
                return pc.cast(pa.scalar(value), native)
            except pa.ArrowInvalid:
                return pa.scalar(parse_temporal_any(value, kind=kind), type=native)
        try:
            return pc.cast(pa.scalar(value), native)
        except pa.ArrowNotImplementedError as error:
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                "Structured temporal conversion is not supported by direct Arrow casts.",
                backend="pyarrow",
                function_key=None,
            ) from error
    if isinstance(dtype, (MountainashDtype, DecimalDtype)):
        import pyarrow as pa
        import pyarrow.compute as pc

        try:
            return pc.cast(pa.scalar(value), transport_arrow_dtype(dtype))
        except pa.ArrowNotImplementedError as error:
            from mountainash.core.types import BackendCapabilityError

            raise BackendCapabilityError(
                f"Structured conversion to {dtype!s} is unsupported by direct Arrow casting.",
                backend="pyarrow",
                function_key=None,
            ) from error
    return value


def _convert_declared_structured(value: Any, plan: StructuredFieldPlan, native_dtype: Any = None) -> Any:
    field = plan.declaration
    if field is None or value is None:
        return value
    import pyarrow as pa
    from mountainash.core.dtypes import (
        MountainashDtype, SchemaTypeStatus, TypeTarget, dtype_is_complete, registry, resolve_dtype_parameters,
    )

    target = plan.target_dtype
    if target is SchemaTypeStatus.UNKNOWN or target in (MountainashDtype.LIST, MountainashDtype.STRUCT):
        target = None
    if target is not None and not dtype_is_complete(target):
        source = registry.from_native(pa.scalar(value).type, TypeTarget.PYARROW)
        target = resolve_dtype_parameters(target, source)
    native = transport_arrow_dtype(target) if native_dtype is None else native_dtype
    effective = target
    converted = _convert_declared_value(value, field, effective)
    # Range/shape failures must participate in discard policies, not surface
    # later while constructing a terminal's output column.
    return pa.scalar(converted, type=native) if native is not None else converted

def _apply_missing_value(value: Any, plan: StructuredFieldPlan) -> tuple[Any, bool]:
    post_missing = None if _is_native_null_scalar(value) or (
        isinstance(value, str) and value in plan.missing_values
    ) else value
    return post_missing, post_missing is None
def _decode_or_null(
    value: Any, *, plan: StructuredFieldPlan, post_missing_is_null: bool
) -> Any:
    decoded = decode_structured_value(value, expected_root=plan.root)
    if post_missing_is_null and decoded is INVALID_STRUCTURED_VALUE:
        return None
    return decoded


def resolve_structured_cell(
    value: Any,
    *,
    plan: StructuredFieldPlan,
    consumer: StructuredActionConsumer,
    native_dtype: Any = None,
) -> StructuredCellResolution:
    """Apply missing-value, fill, decoding, and consumer action semantics in order."""
    post_missing, post_missing_is_null = _apply_missing_value(value, plan)
    materialized = plan.null_fill if post_missing_is_null and plan.null_fill is not None else post_missing

    if consumer is StructuredActionConsumer.LOGICAL_EGRESS and not plan.apply_value_transforms:
        return StructuredCellResolution(
            logical_value=value,
            post_missing_is_null=post_missing_is_null,
            keep=True,
        )

    decoded = _decode_or_null(
        materialized,
        plan=plan,
        post_missing_is_null=post_missing_is_null,
    )
    if (
        decoded is not INVALID_STRUCTURED_VALUE
        and consumer is StructuredActionConsumer.LOGICAL_EGRESS
        and plan.requires_logical_terminal
    ):
        try:
            decoded = _convert_declared_structured(decoded, plan, native_dtype)
        except (TypeError, ValueError, OverflowError):
            decoded = INVALID_STRUCTURED_VALUE
    action = plan.configured_action
    if (
        plan.apply_value_transforms
        and action == "discard_value"
        and decoded is INVALID_STRUCTURED_VALUE
    ):
        logical_value = None
    elif (
        plan.apply_value_transforms
        and action == "discard_row"
        and decoded is INVALID_STRUCTURED_VALUE
    ):
        logical_value = decoded
    elif consumer is StructuredActionConsumer.LOGICAL_EGRESS and action in {"evolve", "freeze"}:
        logical_value = value
    else:
        logical_value = decoded

    keep = not (
        plan.apply_value_transforms
        and action == "discard_row"
        and not post_missing_is_null
        and decoded is INVALID_STRUCTURED_VALUE
    )
    return StructuredCellResolution(
        logical_value=logical_value,
        post_missing_is_null=post_missing_is_null,
        keep=keep,
    )


