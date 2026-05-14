"""Tests for RelationVisitRegistry."""
import pytest

from mountainash.relations.core.unified_visitor.visit_registry import (
    RelationVisitRegistry,
    RelationVisitHandler,
    _PROTECTED_NODE_TYPES,
    _protect,
)


@pytest.fixture(autouse=True)
def _snapshot_registry():
    """Snapshot registry before test, restore after."""
    snapshot = dict(RelationVisitRegistry._handlers)
    was_initialized = RelationVisitRegistry._initialized
    yield
    RelationVisitRegistry._handlers.clear()
    RelationVisitRegistry._handlers.update(snapshot)
    RelationVisitRegistry._initialized = was_initialized


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
        from mountainash.relations.core.relation_nodes.extensions_mountainash import ExtensionRelNode
        for node_type in [
            ReadRelNode, ProjectRelNode, FilterRelNode, SortRelNode,
            FetchRelNode, JoinRelNode, AggregateRelNode, SetRelNode,
            ExtensionRelNode,
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
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    value: str = "test"

    def accept(self, visitor):
        return "accept_fallback"


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

    def test_visitor_falls_back_to_accept_when_not_registered(self):
        visitor = UnifiedRelationVisitor(
            relation_system=PolarsRelationSystem(),
            expression_visitor=None,
        )
        node = _RegistryTestNode()
        result = visitor.visit(node)
        assert result == "accept_fallback"

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


from mountainash.relations.core.unified_visitor._core_handlers import (
    _visit_ref_rel,
    _visit_resource_read_rel,
    _visit_source_rel,
)
from mountainash.relations.dag.errors import RelationDAGRequired


class TestCoreHandlers:
    def test_visit_ref_rel_no_resolver_raises(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_ref import RefRelNode
        node = RefRelNode(name="orders")
        visitor = UnifiedRelationVisitor(
            relation_system=PolarsRelationSystem(),
            expression_visitor=None,
        )
        with pytest.raises(RelationDAGRequired):
            _visit_ref_rel(node, visitor)

    def test_visit_ref_rel_with_resolver(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_ref import RefRelNode
        node = RefRelNode(name="orders")
        visitor = UnifiedRelationVisitor(
            relation_system=PolarsRelationSystem(),
            expression_visitor=None,
            ref_resolver=lambda name: f"resolved:{name}",
        )
        result = _visit_ref_rel(node, visitor)
        assert result == "resolved:orders"

    def test_core_handlers_registered_on_first_get(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_ref import RefRelNode
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_resource_read import ResourceReadRelNode
        handler = RelationVisitRegistry.get(RefRelNode)
        assert handler is _visit_ref_rel
        handler2 = RelationVisitRegistry.get(ResourceReadRelNode)
        assert handler2 is _visit_resource_read_rel
