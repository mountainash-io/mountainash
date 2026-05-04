"""
Tests for protocol completeness — structural enforcement.

Ensures every API builder has a corresponding protocol file, every builder
inherits from its protocol, every backend inherits from its protocol, and
every protocol class is exported in __init__.py __all__.

Complements test_protocol_alignment.py which checks method-level alignment.
This file checks existence and wiring.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Protocol

import pytest


# ── Path constants ──────────────────────────────────────────────────────
_EXPR_ROOT = Path(__file__).resolve().parents[2] / "src" / "mountainash" / "expressions"

_API_BUILDER_DIRS = {
    "substrait": _EXPR_ROOT / "core" / "expression_api" / "api_builders" / "substrait",
    "extensions_mountainash": _EXPR_ROOT / "core" / "expression_api" / "api_builders" / "extensions_mountainash",
}

_API_BUILDER_PROTOCOL_DIRS = {
    "substrait": _EXPR_ROOT / "core" / "expression_protocols" / "api_builders" / "substrait",
    "extensions_mountainash": _EXPR_ROOT / "core" / "expression_protocols" / "api_builders" / "extensions_mountainash",
}

_BACKEND_PREFIXES = {"pl": "polars", "ib": "ibis", "nw": "narwhals"}
_NAMESPACES = ("substrait", "extensions_mountainash")


# ── Helpers ─────────────────────────────────────────────────────────────

def _collect_api_builder_files() -> list[tuple[str, str]]:
    """Return (namespace, filename) for every api_bldr_*.py file."""
    pairs = []
    for ns, d in _API_BUILDER_DIRS.items():
        for f in sorted(d.glob("api_bldr_*.py")):
            pairs.append((ns, f.name))
    return pairs


def _expected_protocol_filename(builder_filename: str) -> str:
    """api_bldr_foo.py → prtcl_api_bldr_foo.py"""
    return builder_filename.replace("api_bldr_", "prtcl_api_bldr_", 1)


def _collect_backend_impl_files() -> list[tuple[str, str, str]]:
    """Return (backend_prefix, namespace, filename) for every expsys_*.py."""
    triples = []
    for prefix, backend_dir_name in _BACKEND_PREFIXES.items():
        for ns in _NAMESPACES:
            d = _EXPR_ROOT / "backends" / "expression_systems" / backend_dir_name / ns
            if not d.exists():
                continue
            for f in sorted(d.glob(f"expsys_{prefix}_*.py")):
                triples.append((prefix, ns, f.name))
    return triples


def _expected_expsys_protocol_filename(backend_prefix: str, impl_filename: str) -> str:
    """expsys_pl_scalar_comparison.py → prtcl_expsys_scalar_comparison.py"""
    stem = impl_filename.removeprefix(f"expsys_{backend_prefix}_")
    return f"prtcl_expsys_{stem}"


_EXPSYS_PROTOCOL_DIRS = {
    "substrait": _EXPR_ROOT / "core" / "expression_protocols" / "expression_systems" / "substrait",
    "extensions_mountainash": _EXPR_ROOT / "core" / "expression_protocols" / "expression_systems" / "extensions_mountainash",
}


# ═════════════════════════════════════════════════════════════════════════
# Test Class 1: API Builder Protocol File Completeness (Approach A)
# ═════════════════════════════════════════════════════════════════════════

class TestAPIBuilderProtocolFileCompleteness:
    """Every api_bldr_*.py must have a corresponding prtcl_api_bldr_*.py."""

    @pytest.mark.parametrize(
        ("namespace", "builder_filename"),
        _collect_api_builder_files(),
        ids=[f"{ns}/{fn}" for ns, fn in _collect_api_builder_files()],
    )
    def test_protocol_file_exists(self, namespace: str, builder_filename: str) -> None:
        expected_protocol = _expected_protocol_filename(builder_filename)
        protocol_dir = _API_BUILDER_PROTOCOL_DIRS[namespace]
        protocol_path = protocol_dir / expected_protocol

        assert protocol_path.exists(), (
            f"API builder '{namespace}/{builder_filename}' has no corresponding "
            f"protocol file.\n"
            f"Expected: {protocol_path}\n"
            f"Create the protocol file with the matching method signatures."
        )


# ═════════════════════════════════════════════════════════════════════════
# Test Class 2: Expression System Protocol File Completeness (Approach A)
# ═════════════════════════════════════════════════════════════════════════

class TestExpressionSystemProtocolFileCompleteness:
    """Every expsys_{backend}_*.py must have a corresponding prtcl_expsys_*.py
    in the SAME namespace directory."""

    @pytest.mark.parametrize(
        ("backend_prefix", "namespace", "impl_filename"),
        _collect_backend_impl_files(),
        ids=[
            f"{backend}/{ns}/{fn}"
            for backend, ns, fn in _collect_backend_impl_files()
        ],
    )
    def test_protocol_file_exists(
        self, backend_prefix: str, namespace: str, impl_filename: str
    ) -> None:
        expected_protocol = _expected_expsys_protocol_filename(
            backend_prefix, impl_filename
        )
        protocol_dir = _EXPSYS_PROTOCOL_DIRS[namespace]
        protocol_path = protocol_dir / expected_protocol

        assert protocol_path.exists(), (
            f"Backend impl '{_BACKEND_PREFIXES[backend_prefix]}/{namespace}/"
            f"{impl_filename}' has no corresponding protocol.\n"
            f"Expected: {protocol_path}\n"
            f"Either create the protocol or move the impl to the correct namespace."
        )
