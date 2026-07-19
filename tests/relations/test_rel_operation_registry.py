"""RelationOperationRegistry: registration validation + lookup (spec §3.5).

Uses a PRIVATE test enum for keys — real RKEYs get registered by
definitions.py at lazy init (Task 4), so tests registering real keys would
collide with duplicate-registration errors once get() triggers init.
"""
from __future__ import annotations

from enum import Enum, auto

import pytest

from mountainash.relations.core.relation_nodes import FilterRelNode
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitFilterRelationSystemProtocol,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
    MountainashRelExtension,
)
from mountainash.relations.core.relation_system.relation_mapping.registry import (
    ArgBinding,
    ArgKind,
    RelationOperationDef,
    RelationOperationRegistry,
    classify_relation_def,
)


class _TKEY(Enum):
    """Private test-only operation keys (never in definitions.py)."""

    FAKE_FILTER = auto()
    FAKE_MISSING = auto()


def _filter_def(**overrides):
    base = dict(
        operation_key=_TKEY.FAKE_FILTER,
        node_type=FilterRelNode,
        substrait_rel="FilterRel",
        protocol_method=SubstraitFilterRelationSystemProtocol.filter,
        args=(
            ArgBinding("input", ArgKind.INPUT),
            ArgBinding("predicate", ArgKind.EXPRESSION),
        ),
    )
    base.update(overrides)
    return RelationOperationDef(**base)


class TestRegistration:
    def setup_method(self):
        RelationOperationRegistry.reset()

    def teardown_method(self):
        RelationOperationRegistry.reset()

    def test_register_and_get(self):
        d = _filter_def()
        RelationOperationRegistry.register(d)
        assert RelationOperationRegistry.get(_TKEY.FAKE_FILTER) is d

    def test_get_unknown_key_raises_with_available(self):
        RelationOperationRegistry.register(_filter_def())
        with pytest.raises(KeyError) as exc:
            RelationOperationRegistry.get(_TKEY.FAKE_MISSING)
        assert "FAKE_FILTER" in str(exc.value)

    def test_arg_count_mismatch_fails_at_registration(self):
        bad = _filter_def(args=(ArgBinding("input", ArgKind.INPUT),))  # filter needs 2
        with pytest.raises(ValueError, match="positional"):
            RelationOperationRegistry.register(bad)

    def test_unknown_node_field_fails_at_registration(self):
        bad = _filter_def(
            args=(
                ArgBinding("input", ArgKind.INPUT),
                ArgBinding("no_such_field", ArgKind.EXPRESSION),
            )
        )
        with pytest.raises(ValueError, match="no_such_field"):
            RelationOperationRegistry.register(bad)

    def test_def_needs_method_or_handler(self):
        bad = _filter_def(protocol_method=None)
        with pytest.raises(ValueError, match="protocol_method or handler"):
            RelationOperationRegistry.register(bad)

    def test_handler_def_skips_arg_validation(self):
        d = _filter_def(args=(), handler=lambda node, visitor: None)
        RelationOperationRegistry.register(d)  # no raise

    def test_metadata_only_def_skips_arg_validation(self):
        # EMPTY_FRAME shape: no node_type, protocol_method only (spec §3.5)
        from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
            MountainashExtensionRelationSystemProtocol,
        )
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_MOUNTAINASH_REL,
        )
        d = RelationOperationDef(
            operation_key=RKEY_MOUNTAINASH_REL.EMPTY_FRAME,
            node_type=None,
            substrait_rel=None,
            is_extension=True,
            extension_uri=MountainashRelExtension.CONFORM,
            protocol_method=MountainashExtensionRelationSystemProtocol.empty_frame,
        )
        RelationOperationRegistry.register(d)  # no raise

    def test_duplicate_key_raises(self):
        RelationOperationRegistry.register(_filter_def())
        with pytest.raises(ValueError, match="already registered"):
            RelationOperationRegistry.register(_filter_def())


def test_relation_def_has_lowers_to_default_none():
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationDef,
    )
    from enum import Enum, auto

    class _K(Enum):
        A = auto()

    d = RelationOperationDef(operation_key=_K.A, substrait_rel="ProjectRel")
    assert d.lowers_to is None


class TestLazyInit:
    def test_registry_self_initializes_from_definitions(self):
        RelationOperationRegistry.reset()
        d = RelationOperationRegistry.get(RKEY_SUBSTRAIT_REL.READ)
        assert d.operation_key is RKEY_SUBSTRAIT_REL.READ
        RelationOperationRegistry.reset()


class _K(Enum):
    A = auto()


def _def(**kw):
    return RelationOperationDef(operation_key=_K.A, **kw)


class TestClassifyRelationDef:
    def test_classify_direct(self):
        assert classify_relation_def(_def(substrait_rel="ProjectRel")) == "direct"

    def test_classify_lowered(self):
        assert classify_relation_def(_def(lowers_to="ProjectRel")) == "lowered"

    def test_classify_extension(self):
        d = _def(is_extension=True, extension_uri=MountainashRelExtension.UTIL)
        assert classify_relation_def(d) == "extension"

    def test_invalid_both_rel_and_lowers(self):
        assert classify_relation_def(_def(substrait_rel="ProjectRel", lowers_to="ProjectRel")) is None

    def test_invalid_both_none_not_extension(self):
        assert classify_relation_def(_def()) is None

    def test_invalid_direct_carrying_extension_flag(self):
        d = _def(substrait_rel="ReadRel", is_extension=True, extension_uri=MountainashRelExtension.UTIL)
        assert classify_relation_def(d) is None

    def test_invalid_extension_without_uri(self):
        assert classify_relation_def(_def(is_extension=True)) is None
