"""Tests enforcing bidirectional method alignment between relation protocols and backends.

Verifies:
1. Every protocol method exists on every composed backend class.
2. Method signatures (parameter names and order) match between protocol and backend.
3. No backend methods exist that aren't declared in any protocol ("rogue" methods).
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import pytest

import mountainash.relations.backends  # noqa: F401

from mountainash.relations.backends.relation_systems.ibis import IbisRelationSystem
from mountainash.relations.backends.relation_systems.narwhals import NarwhalsRelationSystem
from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem
from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitAggregateRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitReadRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
)

# ---------------------------------------------------------------------------
# Fixtures / constants
# ---------------------------------------------------------------------------

PROTOCOLS: list[type] = [
    SubstraitReadRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitAggregateRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
    MountainashExtensionRelationSystemProtocol,
]

BACKENDS: list[tuple[str, type]] = [
    ("polars", PolarsRelationSystem),
    ("ibis", IbisRelationSystem),
    ("narwhals", NarwhalsRelationSystem),
]


def _protocol_methods(protocol_cls: type) -> list[str]:
    """Return public method names directly defined on a protocol class."""
    return [
        name
        for name in protocol_cls.__dict__
        if not name.startswith("_") and callable(protocol_cls.__dict__[name])
    ]


def _all_protocol_methods() -> set[str]:
    """Collect all method names across all protocols."""
    methods: set[str] = set()
    for proto in PROTOCOLS:
        methods.update(_protocol_methods(proto))
    return methods


def _get_method_params(cls: type, method_name: str) -> list[str]:
    """Get parameter names (excluding 'self') for a method, walking MRO."""
    for klass in cls.__mro__:
        if klass is object:
            continue
        if method_name in klass.__dict__:
            method = klass.__dict__[method_name]
            sig = inspect.signature(method)
            return [p for p in sig.parameters if p != "self"]
    msg = f"{cls.__name__} has no method {method_name} in MRO"
    raise AttributeError(msg)


# Pre-compute for parametrization
_PROTOCOL_METHOD_BACKEND_COMBOS: list[tuple[type, str, type, str]] = []
for _proto in PROTOCOLS:
    for _method in _protocol_methods(_proto):
        for _backend_name, _backend_cls in BACKENDS:
            _PROTOCOL_METHOD_BACKEND_COMBOS.append((_proto, _method, _backend_cls, _backend_name))


def _combo_id(combo: tuple[type, str, type, str]) -> str:
    proto, method, _, backend_name = combo
    return f"{proto.__name__}::{method}::{backend_name}"


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestProtocolMethodAlignment:
    """Every protocol method must exist on every composed backend."""

    @pytest.mark.parametrize(
        "combo",
        _PROTOCOL_METHOD_BACKEND_COMBOS,
        ids=[_combo_id(c) for c in _PROTOCOL_METHOD_BACKEND_COMBOS],
    )
    def test_method_exists(self, combo: tuple[type, str, type, str]) -> None:
        proto, method_name, backend_cls, backend_name = combo
        assert hasattr(backend_cls, method_name), (
            f"{backend_name} ({backend_cls.__name__}) is missing method "
            f"'{method_name}' required by {proto.__name__}"
        )


class TestSignatureAlignment:
    """Method signatures must match between protocol and backend."""

    @pytest.mark.parametrize(
        "combo",
        _PROTOCOL_METHOD_BACKEND_COMBOS,
        ids=[_combo_id(c) for c in _PROTOCOL_METHOD_BACKEND_COMBOS],
    )
    def test_signature_matches(self, combo: tuple[type, str, type, str]) -> None:
        proto, method_name, backend_cls, backend_name = combo
        proto_params = _get_method_params(proto, method_name)
        backend_params = _get_method_params(backend_cls, method_name)
        assert proto_params == backend_params, (
            f"Signature mismatch for '{method_name}' on {backend_name}:\n"
            f"  Protocol ({proto.__name__}): {proto_params}\n"
            f"  Backend  ({backend_cls.__name__}): {backend_params}"
        )


class TestBackendMethodsHaveProtocols:
    """No backend method should exist without a corresponding protocol declaration."""

    def test_no_rogue_methods(self) -> None:
        """Collect all public methods from individual backend classes and verify
        each appears in some protocol."""
        all_protocol_methods = _all_protocol_methods()
        rogue: dict[str, list[str]] = {}

        backend_packages = [
            "mountainash.relations.backends.relation_systems.polars",
            "mountainash.relations.backends.relation_systems.ibis",
            "mountainash.relations.backends.relation_systems.narwhals",
        ]

        for pkg_path in backend_packages:
            for sub in ["substrait", "extensions_mountainash"]:
                sub_pkg_path = f"{pkg_path}.{sub}"
                try:
                    sub_pkg = importlib.import_module(sub_pkg_path)
                except ImportError:
                    continue

                for _, modname, _ in pkgutil.iter_modules(sub_pkg.__path__):
                    if not modname.startswith("relsys_"):
                        continue
                    full_mod_path = f"{sub_pkg_path}.{modname}"
                    mod = importlib.import_module(full_mod_path)

                    for attr_name in dir(mod):
                        obj = getattr(mod, attr_name)
                        if (
                            inspect.isclass(obj)
                            and obj.__module__ == full_mod_path
                        ):
                            # Get methods defined directly on this class
                            class_methods = [
                                m
                                for m in obj.__dict__
                                if not m.startswith("_") and callable(obj.__dict__[m])
                            ]
                            for method in class_methods:
                                if method not in all_protocol_methods:
                                    key = f"{modname}.{attr_name}"
                                    rogue.setdefault(key, []).append(method)

        if rogue:
            lines = ["Rogue methods found (not declared in any protocol):"]
            for cls_name, methods in sorted(rogue.items()):
                lines.append(f"  {cls_name}: {methods}")
            pytest.fail("\n".join(lines))
