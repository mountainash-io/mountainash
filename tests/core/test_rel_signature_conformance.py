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
