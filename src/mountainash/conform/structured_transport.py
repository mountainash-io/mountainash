"""Portable physical-to-logical transport for structured conform fields."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
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
    if value is None or isinstance(value, (str, bool, int)):
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
        if decoded is None:
            return None
        if expected_root is StructuredRoot.ARRAY and isinstance(decoded, list):
            return decoded
        if expected_root is StructuredRoot.OBJECT and isinstance(decoded, dict):
            return decoded
    except (json.JSONDecodeError, RecursionError, TypeError, ValueError):
        return INVALID_STRUCTURED_VALUE
    return INVALID_STRUCTURED_VALUE


def _apply_missing_value(value: Any, plan: StructuredFieldPlan) -> tuple[Any, bool]:
    post_missing = None if value is None or value in plan.missing_values else value
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
