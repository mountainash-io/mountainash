"""Automated wiring audit for the relational system."""

import inspect
import pytest

from mountainash.relations.core.relation_nodes.reln_base import RelationNode
from mountainash.relations.core.relation_protocols.relsys_base import RelationSystem

# Trigger backend registration
import mountainash.relations.backends  # noqa

from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem
from mountainash.relations.backends.relation_systems.narwhals import NarwhalsRelationSystem
from mountainash.relations.backends.relation_systems.ibis import IbisRelationSystem


class TestVisitorCoversAllNodes:
    """Every concrete RelationNode subclass must be dispatchable (spec §3.5):
    either via a RelationVisitRegistry handler (third-party extension surface)
    or via operation_key + a RelationOperationRegistry definition."""

    def test_all_node_types_dispatchable(self):
        # Import node packages to trigger subclass registration
        import mountainash.relations.core.relation_nodes.substrait  # noqa: F401
        import mountainash.relations.core.relation_nodes.extensions_mountainash  # noqa: F401

        # Recursively collect all concrete RelationNode subclasses
        # (excluding test helpers defined in test modules)
        all_nodes: set[type] = set()

        def collect(cls: type) -> None:
            for sub in cls.__subclasses__():
                if not inspect.isabstract(sub):
                    mod = getattr(sub, "__module__", "") or ""
                    if not mod.startswith("test") and "test_" not in mod:
                        all_nodes.add(sub)
                collect(sub)

        collect(RelationNode)
        assert all_nodes, "No RelationNode subclasses found — registration may have failed"

        from mountainash.relations.core.unified_visitor.visit_registry import RelationVisitRegistry
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            RelationOperationRegistry,
        )

        covered_by_visit_registry = {
            node_cls for node_cls in all_nodes
            if RelationVisitRegistry.get(node_cls) is not None
        }
        covered_by_operation_registry = {
            RelationOperationRegistry.get(key).node_type
            for key in RelationOperationRegistry.list_all()
            if RelationOperationRegistry.get(key).node_type is not None
        }

        missing = all_nodes - covered_by_visit_registry - covered_by_operation_registry
        assert not missing, (
            f"Unregistered relation node types (no visit handler, no "
            f"operation_key def): {sorted(n.__name__ for n in missing)}"
        )


class TestAllBackendsImplementProtocols:
    """Every protocol method must be implemented by all 3 backends."""

    def _get_protocol_methods(self):
        """Get all non-private, non-dunder method names from protocol bases."""
        methods = set()
        # Walk through RelationSystem's bases (the protocol classes)
        for base in RelationSystem.__mro__:
            for name in dir(base):
                if name.startswith("_"):
                    continue
                attr = getattr(base, name, None)
                if callable(attr) or isinstance(attr, property):
                    methods.add(name)
        # Remove non-protocol items
        methods.discard("backend_type")
        return methods

    @pytest.mark.parametrize("backend_cls,backend_name", [
        (PolarsRelationSystem, "Polars"),
        (NarwhalsRelationSystem, "Narwhals"),
        (IbisRelationSystem, "Ibis"),
    ])
    def test_backend_has_all_protocol_methods(self, backend_cls, backend_name):
        protocol_methods = self._get_protocol_methods()
        missing = []
        for method_name in protocol_methods:
            if not hasattr(backend_cls, method_name):
                missing.append(method_name)
        assert not missing, (
            f"{backend_name} missing protocol methods: {missing}"
        )

    @pytest.mark.parametrize("backend_cls,backend_name", [
        (PolarsRelationSystem, "Polars"),
        (NarwhalsRelationSystem, "Narwhals"),
        (IbisRelationSystem, "Ibis"),
    ])
    def test_backend_methods_are_callable(self, backend_cls, backend_name):
        """Verify methods are real implementations, not just inherited stubs."""
        instance = backend_cls()
        for method_name in ["read", "filter", "sort", "project_select", "join", "aggregate", "distinct", "union_all"]:
            method = getattr(instance, method_name, None)
            assert method is not None, f"{backend_name}.{method_name} is None"
            assert callable(method), f"{backend_name}.{method_name} is not callable"


class TestBackendRegistration:
    """All backends are properly registered."""

    def test_polars_registered(self):
        from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
        from mountainash.core.constants import CONST_BACKEND
        cls = get_relation_system(CONST_BACKEND.POLARS)
        assert cls is PolarsRelationSystem

    def test_narwhals_registered(self):
        from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
        from mountainash.core.constants import CONST_BACKEND
        cls = get_relation_system(CONST_BACKEND.NARWHALS)
        assert cls is NarwhalsRelationSystem

    def test_ibis_registered(self):
        from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
        from mountainash.core.constants import CONST_BACKEND
        cls = get_relation_system(CONST_BACKEND.IBIS)
        assert cls is IbisRelationSystem


class TestExtensionDispatchValidation:
    """Verify that every method in MountainashExtensionRelationSystemProtocol
    exists on all 3 backend extension classes.

    ExtensionRelNode ops dispatch via _dispatch()'s
    getattr(self.backend, op.protocol_method.__name__), so each protocol
    method must be implemented by every backend.
    """

    def _get_protocol_methods(self) -> set[str]:
        """Get public method names defined directly on the extension protocol."""
        from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
            MountainashExtensionRelationSystemProtocol,
        )
        return {
            name
            for name, val in MountainashExtensionRelationSystemProtocol.__dict__.items()
            if not name.startswith("_") and callable(val)
        }

    @pytest.mark.parametrize("backend_module,backend_name", [
        (
            "mountainash.relations.backends.relation_systems.polars.extensions_mountainash",
            "Polars",
        ),
        (
            "mountainash.relations.backends.relation_systems.ibis.extensions_mountainash",
            "Ibis",
        ),
        (
            "mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash",
            "Narwhals",
        ),
    ])
    def test_backend_implements_all_extension_methods(self, backend_module, backend_name):
        import importlib
        mod = importlib.import_module(backend_module)
        # The module's __all__ should contain exactly one class
        backend_cls = getattr(mod, mod.__all__[0])

        protocol_methods = self._get_protocol_methods()
        assert protocol_methods, "No protocol methods found — check protocol class"

        missing = [
            method for method in sorted(protocol_methods)
            if not hasattr(backend_cls, method)
        ]
        assert not missing, (
            f"{backend_name} extension backend missing methods: {missing}"
        )
