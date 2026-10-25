"""Selected lazy registries for native schema adapters and interchange codecs.

Registrations are ``"module:attribute"`` locations (or ready objects). The
implementation module is imported, and the stateless instance created, only
when its key is first requested, so importing declarations or one codec never
imports every optional library.
"""
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from mountainash.core.dtypes.targets import TypeTarget
from mountainash.core.registries import KeyedRegistry

if TYPE_CHECKING:
    from mountainash.typespec.protocols import NativeSchemaAdapter, SchemaCodec

_NATIVE_SCHEMA = "mountainash.typespec.native_schema"


def _register_native_schema_adapters() -> None:
    for target, name in (
        (TypeTarget.POLARS, "PolarsSchemaAdapter"),
        (TypeTarget.PANDAS, "PandasSchemaAdapter"),
        (TypeTarget.PYARROW, "ArrowSchemaAdapter"),
        (TypeTarget.IBIS, "IbisSchemaAdapter"),
        (TypeTarget.NARWHALS, "NarwhalsSchemaAdapter"),
    ):
        NATIVE_SCHEMA_ADAPTERS.register(target, f"{_NATIVE_SCHEMA}:{name}")


def _register_schema_codecs() -> None:
    SCHEMA_CODECS.register("frictionless", "mountainash.typespec.frictionless:FrictionlessSchemaCodec")


NATIVE_SCHEMA_ADAPTERS: KeyedRegistry[TypeTarget, Any] = KeyedRegistry(
    "native schema adapter", initializer=_register_native_schema_adapters,
)
SCHEMA_CODECS: KeyedRegistry[str, Any] = KeyedRegistry(
    "schema codec", initializer=_register_schema_codecs,
)

_instances: dict[tuple[int, Any], Any] = {}


def _instance(registry: KeyedRegistry, key: Any) -> Any:
    entry = registry.get(key)
    if not isinstance(entry, str):
        return entry
    cache_key = (id(registry), key)
    if cache_key not in _instances:
        module, _, attribute = entry.partition(":")
        _instances[cache_key] = getattr(importlib.import_module(module), attribute)()
    return _instances[cache_key]


def get_native_schema_adapter(target: TypeTarget) -> "NativeSchemaAdapter":
    """The stateless native schema adapter for a type target."""
    return _instance(NATIVE_SCHEMA_ADAPTERS, target)


def get_schema_codec(format_name: str) -> "SchemaCodec":
    """The typed interchange codec registered under a format name."""
    return _instance(SCHEMA_CODECS, format_name)


__all__ = [
    "NATIVE_SCHEMA_ADAPTERS", "SCHEMA_CODECS",
    "get_native_schema_adapter", "get_schema_codec",
]
