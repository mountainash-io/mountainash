"""Protocol walker that classifies parameters as arguments vs options."""
from __future__ import annotations

import inspect
import typing
from dataclasses import dataclass
from typing import Any, Literal, get_type_hints

from mountainash.expressions.core.expression_protocols.expression_systems import (
    extensions_mountainash as _ext_mod,
)
from mountainash.expressions.core.expression_protocols.expression_systems import (
    substrait as _substrait_mod,
)

Kind = Literal["argument", "option", "unclassified"]


@dataclass(frozen=True)
class ProtocolParam:
    op_name: str
    function_key: Any | None
    param_name: str
    kind: Kind
    category: str
    protocol_name: str
    annotation: str


_CATEGORY_MAP = {
    "SubstraitScalarStringExpressionSystemProtocol": "string",
    "SubstraitScalarArithmeticExpressionSystemProtocol": "arithmetic",
    "SubstraitScalarComparisonExpressionSystemProtocol": "comparison",
    "SubstraitScalarBooleanExpressionSystemProtocol": "boolean",
    "SubstraitScalarDatetimeExpressionSystemProtocol": "datetime",
    "SubstraitScalarRoundingExpressionSystemProtocol": "rounding",
    "SubstraitScalarLogarithmicExpressionSystemProtocol": "logarithmic",
    "SubstraitScalarSetExpressionSystemProtocol": "set",
    "SubstraitScalarGeometryExpressionSystemProtocol": "geometry",
    "SubstraitWindowArithmeticExpressionSystemProtocol": "window",
    "SubstraitAggregateArithmeticExpressionSystemProtocol": "aggregate",
    "SubstraitAggregateStringExpressionSystemProtocol": "aggregate",
    "SubstraitAggregateBooleanExpressionSystemProtocol": "aggregate",
    "SubstraitAggregateGenericExpressionSystemProtocol": "aggregate",
    "SubstraitCastExpressionSystemProtocol": "cast",
    "SubstraitConditionalExpressionSystemProtocol": "conditional",
    "SubstraitFieldReferenceExpressionSystemProtocol": "field_reference",
    "SubstraitLiteralExpressionSystemProtocol": "literal",
    "MountainAshNameExpressionSystemProtocol": "name",
    "MountainAshNullExpressionSystemProtocol": "null",
    "MountainAshScalarDatetimeExpressionSystemProtocol": "datetime",
    "MountainAshScalarArithmeticExpressionSystemProtocol": "arithmetic",
    "MountainAshScalarBooleanExpressionSystemProtocol": "boolean",
    "MountainAshScalarTernaryExpressionSystemProtocol": "boolean",
    "MountainAshScalarSetExpressionSystemProtocol": "set",
    "MountainAshScalarListExpressionSystemProtocol": "list",
    "MountainAshScalarStructExpressionSystemProtocol": "struct",
    "MountainAshScalarStringExpressionSystemProtocol": "string",
    "MountainashWindowExpressionSystemProtocol": "window",
    "MountainashExtensionAggregateExpressionSystemProtocol": "aggregate",
}

_EXCLUDED_PARAMS = {"self", "input"}


def _iter_protocol_classes():
    for mod in (_substrait_mod, _ext_mod):
        for name in dir(mod):
            obj = getattr(mod, name)
            if inspect.isclass(obj) and name.endswith("Protocol"):
                yield name, obj


def _classify_annotation(ann: Any) -> Kind:
    s = str(ann)
    if "ExpressionT" in s:
        return "argument"
    import types as _types

    origin = typing.get_origin(ann)
    if origin is typing.Union or isinstance(ann, _types.UnionType):
        args = typing.get_args(ann)
        if any("ExpressionT" in str(a) for a in args):
            return "argument"
        non_none = [a for a in args if a is not type(None)]
        if all(a in (int, str, bool, float, bytes, object) for a in non_none):
            return "option"
    if ann in (int, str, bool, float, bytes, object):
        return "option"
    # Optional[concrete] and unions of concrete literal types
    if s.startswith("typing.Optional[") and any(t in s for t in ("int", "str", "bool", "float", "bytes", "object")):
        return "option"
    # Literal collections (frozenset, set, list, tuple, Collection) carrying literal values
    if any(tok in s for tok in ("FrozenSet", "frozenset", "typing.Collection", "collections.abc.Collection")):
        return "option"
    if ann is typing.Any or s == "typing.Any":
        return "unclassified"
    return "unclassified"


def introspect_protocols() -> list[ProtocolParam]:
    results: list[ProtocolParam] = []
    for proto_name, proto_cls in _iter_protocol_classes():
        category = _CATEGORY_MAP.get(proto_name)
        if category is None:
            continue
        for op_name, method in inspect.getmembers(proto_cls, predicate=inspect.isfunction):
            if op_name.startswith("_"):
                continue
            try:
                hints = get_type_hints(method)
            except Exception:
                hints = {}
            sig = inspect.signature(method)
            for param_name, param in sig.parameters.items():
                if param_name in _EXCLUDED_PARAMS:
                    continue
                ann = hints.get(param_name, param.annotation)
                kind = _classify_annotation(ann)
                results.append(
                    ProtocolParam(
                        op_name=op_name,
                        function_key=None,
                        param_name=param_name,
                        kind=kind,
                        category=category,
                        protocol_name=proto_name,
                        annotation=str(ann),
                    )
                )
    return results
