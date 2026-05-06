"""
Tests for relation protocol completeness — structural enforcement.

Ensures every relation backend implementation has a corresponding protocol file,
every backend class inherits from its protocol, every composed RelationSystem
implements all protocols, and every protocol class is exported in __init__.py __all__.

Mirrors tests/unit/test_protocol_completeness.py but adapted for the relations module.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest


# ── Path constants ──────────────────────────────────────────────────────
_REL_ROOT = Path(__file__).resolve().parents[2] / "src" / "mountainash" / "relations"
_BACKEND_IMPL_ROOT = _REL_ROOT / "backends" / "relation_systems"
_PROTOCOL_ROOT = _REL_ROOT / "core" / "relation_protocols" / "relation_systems"

_BACKEND_PREFIXES = {"pl": "polars", "ib": "ibis", "nw": "narwhals"}
_NAMESPACES = ("substrait", "extensions_mountainash")


# ── Helpers ─────────────────────────────────────────────────────────────


def _collect_backend_impl_files() -> list[tuple[str, str, str]]:
    """Return (backend_prefix, namespace, filename) for every relsys_{prefix}_*.py."""
    triples = []
    for prefix, backend_dir_name in _BACKEND_PREFIXES.items():
        for ns in _NAMESPACES:
            d = _BACKEND_IMPL_ROOT / backend_dir_name / ns
            if not d.exists():
                continue
            for f in sorted(d.glob(f"relsys_{prefix}_*.py")):
                triples.append((prefix, ns, f.name))
    return triples


def _expected_protocol_filename(backend_prefix: str, impl_filename: str) -> str:
    """relsys_pl_filter.py → prtcl_relsys_filter.py"""
    stem = impl_filename.removeprefix(f"relsys_{backend_prefix}_")
    return f"prtcl_relsys_{stem}"


def _has_protocol_in_mro(cls: type) -> bool:
    """Check if any class in the MRO (excluding the class itself) has 'Protocol' in its name."""
    for parent in type.mro(cls)[1:]:
        if parent.__name__.endswith("Protocol"):
            return True
    return False


def _import_backend_classes_from_file(
    backend_prefix: str, namespace: str, filename: str
) -> list[type]:
    """Import a relsys_*.py module and return classes defined in it."""
    backend_dir = _BACKEND_PREFIXES[backend_prefix]
    dotted = (
        f"mountainash.relations.backends.relation_systems"
        f".{backend_dir}.{namespace}.{Path(filename).stem}"
    )
    mod = importlib.import_module(dotted)
    classes = []
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if obj.__module__ == mod.__name__ and not name.startswith("_"):
            classes.append(obj)
    return classes


def _collect_all_backend_classes() -> list[tuple[str, type]]:
    """Return (label, cls) for every backend class across all files."""
    results = []
    for prefix, ns, filename in _collect_backend_impl_files():
        for cls in _import_backend_classes_from_file(prefix, ns, filename):
            label = f"{_BACKEND_PREFIXES[prefix]}/{ns}/{cls.__name__}"
            results.append((label, cls))
    return results


def _extract_protocol_class_name(filepath: Path) -> str | None:
    """Find the class name ending with 'Protocol' defined in a protocol file."""
    with open(filepath) as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith("class ") and "Protocol" in stripped:
                class_name = stripped.split("(")[0].replace("class ", "").strip()
                if class_name.endswith("Protocol"):
                    return class_name
    return None


def _collect_protocol_files_and_packages() -> list[tuple[Path, str]]:
    """Return (protocol_file_path, dotted_package_path) for all protocol files."""
    results = []
    package_base = "mountainash.relations.core.relation_protocols.relation_systems"

    for ns in _NAMESPACES:
        ns_dir = _PROTOCOL_ROOT / ns
        if not ns_dir.exists():
            continue
        dotted_pkg = f"{package_base}.{ns}"
        for f in sorted(ns_dir.glob("prtcl_*.py")):
            results.append((f, dotted_pkg))

    return results


def _collect_all_protocol_classes() -> list[type]:
    """Import and return all protocol classes from __all__ in both namespace packages."""
    protocols = []
    package_base = "mountainash.relations.core.relation_protocols.relation_systems"

    for ns in _NAMESPACES:
        dotted_pkg = f"{package_base}.{ns}"
        try:
            pkg = importlib.import_module(dotted_pkg)
        except ImportError:
            continue
        all_exports = getattr(pkg, "__all__", [])
        for name in all_exports:
            obj = getattr(pkg, name, None)
            if obj is not None and inspect.isclass(obj) and name.endswith("Protocol"):
                protocols.append(obj)

    return protocols


# ═════════════════════════════════════════════════════════════════════════
# Test Class 1: Relation Backend Protocol File Completeness
# ═════════════════════════════════════════════════════════════════════════


class TestRelationBackendProtocolFileCompleteness:
    """Every relsys_{pl,ib,nw}_*.py must have a corresponding prtcl_relsys_*.py."""

    @pytest.mark.parametrize(
        ("backend_prefix", "namespace", "impl_filename"),
        _collect_backend_impl_files(),
        ids=[
            f"{_BACKEND_PREFIXES[bp]}/{ns}/{fn}"
            for bp, ns, fn in _collect_backend_impl_files()
        ],
    )
    def test_protocol_file_exists(
        self, backend_prefix: str, namespace: str, impl_filename: str
    ) -> None:
        expected_protocol = _expected_protocol_filename(backend_prefix, impl_filename)
        protocol_dir = _PROTOCOL_ROOT / namespace
        protocol_path = protocol_dir / expected_protocol

        assert protocol_path.exists(), (
            f"Backend impl '{_BACKEND_PREFIXES[backend_prefix]}/{namespace}/"
            f"{impl_filename}' has no corresponding protocol.\n"
            f"Expected: {protocol_path}\n"
            f"Either create the protocol or move the impl to the correct namespace."
        )


# ═════════════════════════════════════════════════════════════════════════
# Test Class 2: Relation Backend Protocol Inheritance
# ═════════════════════════════════════════════════════════════════════════


class TestRelationBackendProtocolInheritance:
    """Every concrete relation backend class must inherit from a Protocol."""

    @pytest.mark.parametrize(
        ("label", "backend_cls"),
        _collect_all_backend_classes(),
        ids=[label for label, _ in _collect_all_backend_classes()],
    )
    def test_backend_inherits_protocol(self, label: str, backend_cls: type) -> None:
        assert _has_protocol_in_mro(backend_cls), (
            f"{backend_cls.__name__} does not inherit from any Protocol class.\n"
            f"MRO: {[c.__name__ for c in type.mro(backend_cls)]}\n"
            f"Add the corresponding *RelationSystemProtocol to the class bases."
        )


# ═════════════════════════════════════════════════════════════════════════
# Test Class 3: Relation System Completeness
# ═════════════════════════════════════════════════════════════════════════


class TestRelationSystemCompleteness:
    """Each composed RelationSystem must have every protocol in its MRO."""

    @pytest.fixture()
    def all_protocols(self) -> list[type]:
        return _collect_all_protocol_classes()

    @pytest.mark.parametrize(
        "system_import_path",
        [
            "mountainash.relations.backends.relation_systems.polars.PolarsRelationSystem",
            "mountainash.relations.backends.relation_systems.ibis.IbisRelationSystem",
            "mountainash.relations.backends.relation_systems.narwhals.NarwhalsRelationSystem",
        ],
        ids=["PolarsRelationSystem", "IbisRelationSystem", "NarwhalsRelationSystem"],
    )
    def test_system_implements_all_protocols(
        self, system_import_path: str, all_protocols: list[type]
    ) -> None:
        module_path, class_name = system_import_path.rsplit(".", 1)
        mod = importlib.import_module(module_path)
        system_cls = getattr(mod, class_name)

        mro_set = set(type.mro(system_cls))
        missing = []
        for protocol_cls in all_protocols:
            if protocol_cls not in mro_set:
                missing.append(protocol_cls.__name__)

        assert not missing, (
            f"{class_name} is missing protocol inheritance for:\n"
            + "\n".join(f"  - {name}" for name in missing)
            + "\nEnsure the composed class includes mixins that inherit from these protocols."
        )


# ═════════════════════════════════════════════════════════════════════════
# Test Class 4: Relation Protocol Export Completeness
# ═════════════════════════════════════════════════════════════════════════


class TestRelationProtocolExportCompleteness:
    """Every protocol class must be exported in its package __init__.py __all__."""

    @pytest.mark.parametrize(
        ("protocol_file", "package_path"),
        _collect_protocol_files_and_packages(),
        ids=[
            f"{pf.parent.name}/{pf.name}"
            for pf, _ in _collect_protocol_files_and_packages()
        ],
    )
    def test_protocol_in_package_all(
        self, protocol_file: Path, package_path: str
    ) -> None:
        class_name = _extract_protocol_class_name(protocol_file)
        if class_name is None:
            pytest.skip(f"No Protocol class found in {protocol_file.name}")

        pkg = importlib.import_module(package_path)
        all_exports = getattr(pkg, "__all__", [])

        assert class_name in all_exports or any(
            getattr(obj, "__name__", None) == class_name
            for attr in all_exports
            if (obj := getattr(pkg, attr, None)) is not None
        ), (
            f"Protocol class '{class_name}' from {protocol_file.name} "
            f"is not exported in {package_path}.__all__.\n"
            f"Current __all__: {all_exports}"
        )
