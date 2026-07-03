"""Tests for RelationVisitRegistry."""
import pytest

from mountainash.relations.core.unified_visitor.visit_registry import (
    RelationVisitRegistry,
    RelationVisitHandler,
    _PROTECTED_NODE_TYPES,
    _protect,
)
from mountainash.relations.core.unified_visitor import visit_registry as vr


@pytest.fixture(autouse=True)
def _snapshot_registry():
    """Snapshot registry before test, restore after."""
    snapshot = dict(vr._registry._store)
    entries = list(vr._registry._entries)
    was_initialized = vr._registry._initialized
    yield
    vr._registry._store.clear()
    vr._registry._store.update(snapshot)
    vr._registry._entries[:] = entries
    vr._registry._initialized = was_initialized


class _FakeNode:
    """Minimal stand-in for a RelationNode subclass."""
    pass


class _AnotherFakeNode:
    pass


class TestRegister:
    def test_register_and_get(self):
        handler = lambda node, visitor: "result"
        RelationVisitRegistry.register(_FakeNode, handler)
        assert RelationVisitRegistry.get(_FakeNode) is handler

    def test_get_unregistered_returns_none(self):
        assert RelationVisitRegistry.get(_AnotherFakeNode) is None

    def test_duplicate_registration_raises(self):
        RelationVisitRegistry.register(_FakeNode, lambda n, v: None)
        with pytest.raises(ValueError, match="already has a registered"):
            RelationVisitRegistry.register(_FakeNode, lambda n, v: None)

    def test_unregister(self):
        RelationVisitRegistry.register(_FakeNode, lambda n, v: None)
        RelationVisitRegistry.unregister(_FakeNode)
        assert RelationVisitRegistry.get(_FakeNode) is None

    def test_unregister_nonexistent_is_silent(self):
        RelationVisitRegistry.unregister(_FakeNode)  # should not raise


class TestProtection:
    def test_protected_node_type_raises_on_register(self):
        _protect(_FakeNode)
        try:
            with pytest.raises(TypeError, match="protected Substrait-aligned"):
                RelationVisitRegistry.register(_FakeNode, lambda n, v: None)
        finally:
            _PROTECTED_NODE_TYPES.discard(_FakeNode)

    def test_unprotected_node_type_registers_normally(self):
        RelationVisitRegistry.register(_AnotherFakeNode, lambda n, v: "ok")
        assert RelationVisitRegistry.get(_AnotherFakeNode) is not None

    def test_substrait_nodes_are_protected(self):
        from mountainash.relations.core.relation_nodes import (
            ReadRelNode, ProjectRelNode, FilterRelNode, SortRelNode,
            FetchRelNode, JoinRelNode, AggregateRelNode, SetRelNode,
        )
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            ConformRelNode, ExtensionRelNode, RefRelNode, ResourceReadRelNode,
            SourceRelNode,
        )
        for node_type in [
            ReadRelNode, ProjectRelNode, FilterRelNode, SortRelNode,
            FetchRelNode, JoinRelNode, AggregateRelNode, SetRelNode,
            ExtensionRelNode, ConformRelNode, RefRelNode, ResourceReadRelNode,
            SourceRelNode,
        ]:
            assert node_type in _PROTECTED_NODE_TYPES, f"{node_type.__name__} not protected"


from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_nodes.reln_base import RelationNode


class _LeafNodeWithBackend(RelationNode):
    """Test subclass verifying _leaf_backend ClassVar override.

    Intentionally left abstract (accept not implemented) so the wiring audit
    skips it via inspect.isabstract().
    """
    _leaf_backend = CONST_BACKEND.POLARS


class TestLeafBackend:
    def test_leaf_backend_default_is_none(self):
        assert RelationNode._leaf_backend is None

    def test_leaf_backend_subclass_override(self):
        assert _LeafNodeWithBackend._leaf_backend == CONST_BACKEND.POLARS


from pydantic import ConfigDict
from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor
from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem


class _RegistryTestNode(RelationNode):
    """No RelationVisitRegistry handler, no operation_key — deliberately
    undispatchable (spec §3.5): accept() is a compatibility shim only,
    visit() never falls back to it."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    value: str = "test"


class TestVisitorDispatch:
    def test_visitor_dispatches_to_registered_handler(self):
        called_with = []

        def handler(node, visitor):
            called_with.append(node)
            return "from_registry"

        RelationVisitRegistry.register(_RegistryTestNode, handler)
        try:
            visitor = UnifiedRelationVisitor(
                relation_system=PolarsRelationSystem(),
                expression_visitor=None,
            )
            result = visitor.visit(_RegistryTestNode())
            assert result == "from_registry"
            assert len(called_with) == 1
        finally:
            RelationVisitRegistry.unregister(_RegistryTestNode)

    def test_visitor_raises_for_unregistered_node_without_operation_key(self):
        from mountainash.relations.core.errors import UnregisteredRelationNodeError

        visitor = UnifiedRelationVisitor(
            relation_system=PolarsRelationSystem(),
            expression_visitor=None,
        )
        node = _RegistryTestNode()
        with pytest.raises(UnregisteredRelationNodeError, match="_RegistryTestNode"):
            visitor.visit(node)

    def test_accept_shim_delegates_to_visit(self):
        """accept() no longer participates in dispatch — it's a pure shim
        that always calls visitor.visit(self)."""
        called_with = []

        def handler(node, visitor):
            called_with.append(node)
            return "from_registry"

        RelationVisitRegistry.register(_RegistryTestNode, handler)
        try:
            visitor = UnifiedRelationVisitor(
                relation_system=PolarsRelationSystem(),
                expression_visitor=None,
            )
            node = _RegistryTestNode()
            assert node.accept(visitor) == "from_registry"
            assert called_with == [node]
        finally:
            RelationVisitRegistry.unregister(_RegistryTestNode)

    def test_handler_exception_includes_node_type(self):
        def bad_handler(node, visitor):
            raise RuntimeError("something broke")

        RelationVisitRegistry.register(_RegistryTestNode, bad_handler)
        try:
            visitor = UnifiedRelationVisitor(
                relation_system=PolarsRelationSystem(),
                expression_visitor=None,
            )
            with pytest.raises(RuntimeError, match="_RegistryTestNode"):
                visitor.visit(_RegistryTestNode())
        finally:
            RelationVisitRegistry.unregister(_RegistryTestNode)


from mountainash.relations.core.relation_system.relation_mapping import handlers
from mountainash.relations.dag.errors import RelationDAGRequired


class TestCoreHandlers:
    """RefRelNode/ResourceReadRelNode/SourceRelNode no longer register via
    RelationVisitRegistry (Task 4): they dispatch through operation_key ->
    RelationOperationRegistry -> handlers module. Exercise the handlers
    directly, as the pre-Task-4 suite did for _core_handlers."""

    def test_visit_ref_no_resolver_raises(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_ref import RefRelNode
        node = RefRelNode(name="orders")
        visitor = UnifiedRelationVisitor(
            relation_system=PolarsRelationSystem(),
            expression_visitor=None,
        )
        with pytest.raises(RelationDAGRequired):
            handlers.visit_ref(node, visitor)

    def test_visit_ref_with_resolver(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_ref import RefRelNode
        node = RefRelNode(name="orders")
        visitor = UnifiedRelationVisitor(
            relation_system=PolarsRelationSystem(),
            expression_visitor=None,
            ref_resolver=lambda name: f"resolved:{name}",
        )
        result = handlers.visit_ref(node, visitor)
        assert result == "resolved:orders"

    def test_ref_and_resource_read_dispatch_via_operation_registry(self):
        """RefRelNode/ResourceReadRelNode have no RelationVisitRegistry
        handler; visitor.visit() must route them through operation_key."""
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_ref import RefRelNode
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_resource_read import ResourceReadRelNode

        assert RelationVisitRegistry.get(RefRelNode) is None
        assert RelationVisitRegistry.get(ResourceReadRelNode) is None

        visitor = UnifiedRelationVisitor(
            relation_system=PolarsRelationSystem(),
            expression_visitor=None,
            ref_resolver=lambda name: f"resolved:{name}",
        )
        assert visitor.visit(RefRelNode(name="orders")) == "resolved:orders"
