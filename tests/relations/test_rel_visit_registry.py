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
