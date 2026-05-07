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


# ═════════════════════════════════════════════════════════════════════════
# Test Class 5: Relation API Protocol Inheritance
# ═════════════════════════════════════════════════════════════════════════


class TestRelationAPIProtocolInheritance:
    """Relation and GroupedRelation must inherit from their API protocols."""

    def test_relation_has_builder_dispatch(self) -> None:
        from mountainash.relations.core.relation_api.relation import Relation

        assert hasattr(Relation, "_FLAT_NAMESPACES"), (
            "Relation must define _FLAT_NAMESPACES for builder dispatch"
        )
        assert len(Relation._FLAT_NAMESPACES) > 0, (
            "Relation._FLAT_NAMESPACES must contain at least one builder"
        )

    def test_grouped_relation_inherits_api_protocol(self) -> None:
        from mountainash.relations.core.relation_api.grouped_relation import (
            GroupedRelation,
        )
        from mountainash.relations.core.relation_protocols import (
            GroupedRelationAPIProtocol,
        )

        mro_names = [cls.__name__ for cls in type.mro(GroupedRelation)]
        assert "GroupedRelationAPIProtocol" in mro_names, (
            f"GroupedRelation does not inherit from GroupedRelationAPIProtocol.\n"
            f"MRO: {mro_names}"
        )


# ═════════════════════════════════════════════════════════════════════════
# Test Class 6: Relation API Protocol Method Coverage
# ═════════════════════════════════════════════════════════════════════════


class TestRelationAPIProtocolMethodCoverage:
    """API protocols must cover all public methods on Relation/GroupedRelation."""

    @staticmethod
    def _get_public_methods(cls: type) -> set[str]:
        """Get public methods including those dispatched via _FLAT_NAMESPACES."""
        object_attrs = set(dir(object))
        methods = set()
        for name in dir(cls):
            if name.startswith("_"):
                continue
            if name in object_attrs:
                continue
            methods.add(name)
        for ns_cls in getattr(cls, "_FLAT_NAMESPACES", ()):
            for name, value in ns_cls.__dict__.items():
                if not name.startswith("_") and callable(value):
                    methods.add(name)
        return methods

    @staticmethod
    def _get_protocol_methods(protocol_cls: type) -> set[str]:
        """Get public method/property names defined directly on a protocol class."""
        return {
            name
            for name, value in protocol_cls.__dict__.items()
            if not name.startswith("_")
            and (callable(value) or isinstance(value, property))
        }

    def test_relation_methods_covered_by_protocol(self) -> None:
        from mountainash.relations.core.relation_api.relation import Relation
        from mountainash.relations.core.relation_protocols import RelationAPIProtocol

        class_methods = self._get_public_methods(Relation)
        protocol_methods = self._get_protocol_methods(RelationAPIProtocol)

        missing = class_methods - protocol_methods
        assert not missing, (
            f"Relation has public methods not covered by RelationAPIProtocol:\n"
            f"  {sorted(missing)}\n"
            f"Add these to the protocol or exclude them explicitly."
        )

    def test_protocol_methods_exist_on_relation(self) -> None:
        from mountainash.relations.core.relation_api.relation import Relation
        from mountainash.relations.core.relation_protocols import RelationAPIProtocol

        protocol_methods = self._get_protocol_methods(RelationAPIProtocol)
        class_methods = self._get_public_methods(Relation)

        missing = protocol_methods - class_methods
        assert not missing, (
            f"RelationAPIProtocol declares methods not found on Relation:\n"
            f"  {sorted(missing)}\n"
            f"Either implement them on Relation or remove from protocol."
        )

    def test_grouped_relation_methods_covered_by_protocol(self) -> None:
        from mountainash.relations.core.relation_api.grouped_relation import (
            GroupedRelation,
        )
        from mountainash.relations.core.relation_protocols import (
            GroupedRelationAPIProtocol,
        )

        class_methods = self._get_public_methods(GroupedRelation)
        protocol_methods = self._get_protocol_methods(GroupedRelationAPIProtocol)

        missing = class_methods - protocol_methods
        assert not missing, (
            f"GroupedRelation has public methods not covered by "
            f"GroupedRelationAPIProtocol:\n"
            f"  {sorted(missing)}\n"
            f"Add these to the protocol or exclude them explicitly."
        )

    def test_grouped_protocol_methods_exist_on_class(self) -> None:
        from mountainash.relations.core.relation_api.grouped_relation import (
            GroupedRelation,
        )
        from mountainash.relations.core.relation_protocols import (
            GroupedRelationAPIProtocol,
        )

        protocol_methods = self._get_protocol_methods(GroupedRelationAPIProtocol)
        class_methods = self._get_public_methods(GroupedRelation)

        missing = protocol_methods - class_methods
        assert not missing, (
            f"GroupedRelationAPIProtocol declares methods not found on "
            f"GroupedRelation:\n"
            f"  {sorted(missing)}\n"
            f"Either implement them on GroupedRelation or remove from protocol."
        )


# ═════════════════════════════════════════════════════════════════════════
# Test Class 7: Relation Builder Protocol Completeness
# ═════════════════════════════════════════════════════════════════════════


class TestRelationBuilderProtocolCompleteness:
    """Every rel_bldr_*.py must have a prtcl_rel_bldr_*.py and inherit from it."""

    def _collect_builder_classes(self) -> list[tuple[str, type]]:
        from mountainash.relations.core.relation_api.api_builders import (
            RelationProjectionBuilder,
        )

        return [
            ("RelationProjectionBuilder", RelationProjectionBuilder),
        ]

    def test_builder_inherits_protocol(self):
        for name, cls in self._collect_builder_classes():
            assert _has_protocol_in_mro(cls), (
                f"{name} does not inherit from any Protocol class.\n"
                f"MRO: {[c.__name__ for c in type.mro(cls)]}"
            )

    def test_builder_protocol_file_exists(self):
        protocol_dir = (
            Path(__file__).resolve().parents[2]
            / "src"
            / "mountainash"
            / "relations"
            / "core"
            / "relation_protocols"
            / "api_builders"
        )
        builder_dir = (
            Path(__file__).resolve().parents[2]
            / "src"
            / "mountainash"
            / "relations"
            / "core"
            / "relation_api"
            / "api_builders"
        )
        for f in sorted(builder_dir.glob("rel_bldr_*.py")):
            expected_protocol = f"prtcl_{f.name}"
            assert (protocol_dir / expected_protocol).exists(), (
                f"Builder '{f.name}' has no protocol file.\n"
                f"Expected: {protocol_dir / expected_protocol}"
            )

    def test_dispatch_routes_to_concrete_methods(self):
        """Verify _FLAT_NAMESPACES dispatch only exposes concrete implementations."""
        import inspect

        from mountainash.relations.core.relation_api.relation import Relation

        for ns_cls in Relation._FLAT_NAMESPACES:
            for name, value in ns_cls.__dict__.items():
                if name.startswith("_"):
                    continue
                if not callable(value):
                    continue
                assert inspect.isfunction(value), (
                    f"{ns_cls.__name__}.{name} is not a function — "
                    f"got {type(value).__name__}. "
                    "Dispatch would expose a protocol stub."
                )
