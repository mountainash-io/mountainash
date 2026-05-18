"""Relation signature conformance tests — closed-by-default wiring verification.

R-A1: Protocol vs backend method signatures (arity)
R-A2: Visitor dispatch coverage (nodes + extension ops)
R-A3: Extension enum ↔ protocol consistency
"""
from __future__ import annotations

import inspect
import re

import pytest

from mountainash.relations.core.relation_protocols.relsys_base import RelationSystem

# Trigger backend registration
import mountainash.relations.backends  # noqa: F401

from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem
from mountainash.relations.backends.relation_systems.narwhals import NarwhalsRelationSystem
from mountainash.relations.backends.relation_systems.ibis import IbisRelationSystem

BACKEND_LEAF_CLASSES = {
    "polars": PolarsRelationSystem,
    "ibis": IbisRelationSystem,
    "narwhals": NarwhalsRelationSystem,
}


def _iter_relation_protocols() -> list[tuple[str, type]]:
    protocols = []
    for cls in RelationSystem.__mro__:
        if not cls.__name__.endswith("Protocol"):
            continue
        if not getattr(cls, "__module__", "").startswith("mountainash"):
            continue
        protocols.append((cls.__name__, cls))
    return protocols


def _get_protocol_methods(proto_cls: type) -> list[tuple[str, inspect.Signature]]:
    methods = []
    for name, obj in sorted(proto_cls.__dict__.items()):
        if name.startswith("_"):
            continue
        if name == "backend_type":
            continue
        if callable(obj):
            sig = inspect.signature(obj)
            methods.append((name, sig))
    return methods


def _resolve_backend_method(
    backend_cls: type, method_name: str
) -> tuple[type, object] | None:
    for cls in type.mro(backend_cls):
        if cls.__name__.endswith("Protocol"):
            continue
        if method_name in cls.__dict__:
            return cls, cls.__dict__[method_name]
    return None


def _get_positional_params(sig: inspect.Signature) -> list[tuple[str, str]]:
    result = []
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            result.append((f"*{pname}", "variadic"))
            continue
        if param.kind in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD):
            continue
        result.append((pname, "positional"))
    return result


# ── R-A1 Exception set ──────────────────────────────────────────────────
_KNOWN_REL_SIGNATURE_DIVERGENCES: dict[tuple[str, str, str], str] = {}


def _collect_ra1_cases() -> (
    list[tuple[str, str, str, inspect.Signature, inspect.Signature]]
):
    cases = []
    for proto_name, proto_cls in _iter_relation_protocols():
        for method_name, proto_sig in _get_protocol_methods(proto_cls):
            for backend_name, backend_cls in BACKEND_LEAF_CLASSES.items():
                resolved = _resolve_backend_method(backend_cls, method_name)
                if resolved is None:
                    continue
                defining_cls, backend_method = resolved
                assert not defining_cls.__name__.endswith("Protocol"), (
                    f"MRO resolution returned protocol class {defining_cls.__name__} "
                    f"for {method_name} on {backend_name}"
                )
                backend_sig = inspect.signature(backend_method)
                cases.append(
                    (proto_name, method_name, backend_name, proto_sig, backend_sig)
                )
    return cases


_RA1_CASES = _collect_ra1_cases()


class TestRelProtocolVsBackendSignatures:
    """R-A1: Every backend method must match its protocol's positional param count."""

    @pytest.mark.parametrize(
        ("proto_name", "method_name", "backend_name", "proto_sig", "backend_sig"),
        _RA1_CASES,
        ids=[f"{p}/{m}/{b}" for p, m, b, _, _ in _RA1_CASES],
    )
    def test_signature_matches(
        self,
        proto_name: str,
        method_name: str,
        backend_name: str,
        proto_sig: inspect.Signature,
        backend_sig: inspect.Signature,
    ) -> None:
        key = (proto_name, method_name, backend_name)
        if key in _KNOWN_REL_SIGNATURE_DIVERGENCES:
            pytest.xfail(_KNOWN_REL_SIGNATURE_DIVERGENCES[key])

        proto_params = _get_positional_params(proto_sig)
        backend_params = _get_positional_params(backend_sig)

        proto_variadic = any(k == "variadic" for _, k in proto_params)
        backend_variadic = any(k == "variadic" for _, k in backend_params)

        if proto_variadic or backend_variadic:
            return

        assert len(proto_params) == len(backend_params), (
            f"{proto_name}.{method_name} on {backend_name}: "
            f"protocol has {len(proto_params)} positional params "
            f"{[n for n, _ in proto_params]}, "
            f"backend has {len(backend_params)} "
            f"{[n for n, _ in backend_params]}"
        )

    def test_divergences_still_diverge(self) -> None:
        for proto_name, method_name, backend_name, proto_sig, backend_sig in _RA1_CASES:
            key = (proto_name, method_name, backend_name)
            if key not in _KNOWN_REL_SIGNATURE_DIVERGENCES:
                continue
            proto_params = _get_positional_params(proto_sig)
            backend_params = _get_positional_params(backend_sig)
            if any(k == "variadic" for _, k in proto_params):
                continue
            assert len(proto_params) != len(backend_params), (
                f"Stale divergence: {key} — signatures now match! "
                f"Remove from _KNOWN_REL_SIGNATURE_DIVERGENCES."
            )

    def test_no_stale_divergence_entries(self) -> None:
        all_keys = {(p, m, b) for p, m, b, _, _ in _RA1_CASES}
        for key in _KNOWN_REL_SIGNATURE_DIVERGENCES:
            assert key in all_keys, (
                f"Stale _KNOWN_REL_SIGNATURE_DIVERGENCES entry: {key}"
            )

    def test_every_divergence_has_reason_and_date(self) -> None:
        for key, reason in _KNOWN_REL_SIGNATURE_DIVERGENCES.items():
            assert "since" in reason.lower(), (
                f"_KNOWN_REL_SIGNATURE_DIVERGENCES[{key}] missing date: {reason!r}"
            )
            assert re.search(r"\d{4}-\d{2}-\d{2}", reason), (
                f"_KNOWN_REL_SIGNATURE_DIVERGENCES[{key}] has no date: {reason!r}"
            )


from mountainash.relations.core.relation_nodes.reln_base import RelationNode
from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor
from mountainash.relations.core.unified_visitor.visit_registry import RelationVisitRegistry
from mountainash.core.constants import ExtensionRelOperation


def _camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


_REGISTRY_HANDLED_OPS = {"REF", "READ_RESOURCE"}


# ── R-A2a: Node type → visitor ──────────────────────────────────────────


def _collect_all_node_types() -> set[type]:
    import mountainash.relations.core.relation_nodes.substrait  # noqa: F401
    import mountainash.relations.core.relation_nodes.extensions_mountainash  # noqa: F401

    all_nodes: set[type] = set()

    def collect(cls: type) -> None:
        for sub in cls.__subclasses__():
            if not inspect.isabstract(sub):
                mod = getattr(sub, "__module__", "") or ""
                if not mod.startswith("test") and "test_" not in mod:
                    all_nodes.add(sub)
            collect(sub)

    collect(RelationNode)
    return all_nodes


_ALL_NODE_TYPES = _collect_all_node_types()

# node_class_name → "reason. Since YYYY-MM-DD."
_KNOWN_UNHANDLED_NODES: dict[str, str] = {}


def _collect_ra2a_cases() -> list[tuple[str, type]]:
    return [(cls.__name__, cls) for cls in sorted(_ALL_NODE_TYPES, key=lambda c: c.__name__)]


_RA2A_CASES = _collect_ra2a_cases()


class TestRelVisitorDispatchCoverage:
    """R-A2a: Every concrete RelationNode subclass must be handled."""

    @pytest.mark.parametrize(
        ("node_name", "node_cls"),
        _RA2A_CASES,
        ids=[name for name, _ in _RA2A_CASES],
    )
    def test_node_has_visitor_handler(self, node_name: str, node_cls: type) -> None:
        if node_name in _KNOWN_UNHANDLED_NODES:
            pytest.xfail(_KNOWN_UNHANDLED_NODES[node_name])

        stem = node_name.removesuffix("Node")
        method_name = f"visit_{_camel_to_snake(stem)}"

        has_visitor_method = hasattr(UnifiedRelationVisitor, method_name)
        has_registry_handler = RelationVisitRegistry.get(node_cls) is not None

        assert has_visitor_method or has_registry_handler, (
            f"{node_name} has no visit method ({method_name}) on "
            f"UnifiedRelationVisitor and no RelationVisitRegistry handler"
        )

    def test_no_stale_unhandled_entries(self) -> None:
        all_names = {name for name, _ in _RA2A_CASES}
        for key in _KNOWN_UNHANDLED_NODES:
            assert key in all_names, (
                f"Stale _KNOWN_UNHANDLED_NODES entry: {key}"
            )


# ── R-A2b: Extension ops → backend methods ──────────────────────────────


def _collect_ra2b_cases() -> list[tuple[str, str]]:
    cases = []
    for op in ExtensionRelOperation:
        if op.name in _REGISTRY_HANDLED_OPS:
            continue
        method_name = op.name.lower()
        for backend_name in BACKEND_LEAF_CLASSES:
            cases.append((method_name, backend_name))
    return cases


_RA2B_CASES = _collect_ra2b_cases()

# (operation_name, backend_name) → "reason. Since YYYY-MM-DD."
_KNOWN_DISPATCH_GAPS: dict[tuple[str, str], str] = {}


class TestRelExtensionDispatch:
    """R-A2b: Every ExtensionRelOperation must dispatch to a backend method."""

    @pytest.mark.parametrize(
        ("method_name", "backend_name"),
        _RA2B_CASES,
        ids=[f"{m}/{b}" for m, b in _RA2B_CASES],
    )
    def test_extension_op_resolves(
        self, method_name: str, backend_name: str
    ) -> None:
        key = (method_name, backend_name)
        if key in _KNOWN_DISPATCH_GAPS:
            pytest.xfail(_KNOWN_DISPATCH_GAPS[key])

        backend_cls = BACKEND_LEAF_CLASSES[backend_name]
        assert hasattr(backend_cls, method_name), (
            f"ExtensionRelOperation.{method_name.upper()} has no method "
            f"'{method_name}' on {backend_name} ({backend_cls.__name__})"
        )

    def test_no_stale_dispatch_gap_entries(self) -> None:
        all_keys = set(_RA2B_CASES)
        for key in _KNOWN_DISPATCH_GAPS:
            assert key in all_keys, (
                f"Stale _KNOWN_DISPATCH_GAPS entry: {key}"
            )
