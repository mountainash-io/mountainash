"""Shared helpers for expression argument/option coverage guards."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import importlib
from typing import Any, Iterable

from cross_backend.argument_types._introspection import ProtocolParam, introspect_protocols
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)


@dataclass(frozen=True)
class KnownGap:
    reason: str
    since: str


@dataclass(frozen=True)
class ProtocolMethodRef:
    protocol_name: str
    op_name: str


@dataclass(frozen=True)
class TestedParamRef:
    module_name: str
    category: str
    original_key: Any
    protocol_name: str | None
    op_name: str
    param_name: str
    registry_wired: bool

    @property
    def protocol_param_key(self) -> tuple[str, str, str] | None:
        if self.protocol_name is None:
            return None
        return (self.protocol_name, self.op_name, self.param_name)

    @property
    def operation_key(self) -> tuple[str, str] | None:
        if self.protocol_name is None:
            return None
        return (self.protocol_name, self.op_name)


def category_from_module_name(module_name: str) -> str:
    if module_name.startswith("test_arg_types_"):
        return module_name.removeprefix("test_arg_types_")
    return module_name


def registry_protocol_ref(function_key: object) -> ProtocolMethodRef | None:
    if not isinstance(function_key, Enum):
        return None
    try:
        func_def = ExpressionFunctionRegistry.get(function_key)
    except KeyError:
        return None
    protocol_method = func_def.protocol_method
    if protocol_method is None:
        return None
    qualname = getattr(protocol_method, "__qualname__", "")
    if "." not in qualname:
        return None
    protocol_name, op_name = qualname.rsplit(".", 1)
    return ProtocolMethodRef(protocol_name=protocol_name, op_name=op_name)


def protocol_params_by_category() -> dict[str, list[ProtocolParam]]:
    by_category: dict[str, list[ProtocolParam]] = {}
    for param in introspect_protocols():
        by_category.setdefault(param.category, []).append(param)
    return by_category


def resolve_string_protocol_ref(
    op_name: str,
    category: str,
    params_by_category: dict[str, list[ProtocolParam]] | None = None,
) -> ProtocolMethodRef | None:
    params_by_category = params_by_category or protocol_params_by_category()
    matches = {
        (param.protocol_name, param.op_name)
        for param in params_by_category.get(category, [])
        if param.op_name == op_name
    }
    if len(matches) != 1:
        return None
    protocol_name, resolved_op_name = next(iter(matches))
    return ProtocolMethodRef(protocol_name=protocol_name, op_name=resolved_op_name)


def canonicalize_tested_param(
    module_name: str,
    original_key: object,
    param_name: str,
    params_by_category: dict[str, list[ProtocolParam]] | None = None,
) -> TestedParamRef:
    category = category_from_module_name(module_name)
    registry_ref = registry_protocol_ref(original_key)
    if registry_ref is not None:
        return TestedParamRef(
            module_name=module_name,
            category=category,
            original_key=original_key,
            protocol_name=registry_ref.protocol_name,
            op_name=registry_ref.op_name,
            param_name=param_name,
            registry_wired=True,
        )

    if isinstance(original_key, Enum):
        op_name = original_key.name.lower()
    else:
        op_name = str(original_key)
    protocol_ref = resolve_string_protocol_ref(op_name, category, params_by_category)
    return TestedParamRef(
        module_name=module_name,
        category=category,
        original_key=original_key,
        protocol_name=protocol_ref.protocol_name if protocol_ref else None,
        op_name=protocol_ref.op_name if protocol_ref else op_name,
        param_name=param_name,
        registry_wired=False,
    )


def collect_tested_params(module_names: Iterable[str]) -> set[TestedParamRef]:
    tested: set[TestedParamRef] = set()
    params_by_category = protocol_params_by_category()
    for module_name in module_names:
        try:
            mod = importlib.import_module(f"cross_backend.argument_types.{module_name}")
        except ImportError:
            continue
        for original_key, param_name in getattr(mod, "TESTED_PARAMS", []):
            tested.add(
                canonicalize_tested_param(
                    module_name=module_name,
                    original_key=original_key,
                    param_name=param_name,
                    params_by_category=params_by_category,
                )
            )
    return tested
