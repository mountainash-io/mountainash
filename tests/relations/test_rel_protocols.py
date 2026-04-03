"""Tests for relation system protocols, base class, and registry."""

from __future__ import annotations

from typing import Any, Optional

import pytest

from mountainash.core.constants import CONST_BACKEND, JoinType, SortField

# --- Substrait protocols ---------------------------------------------------
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitReadRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitAggregateRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
)

# --- Extension protocol ----------------------------------------------------
from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol,
)

# --- Base & registry -------------------------------------------------------
from mountainash.relations.core.relation_protocols.relsys_base import (
    RelationSystem,
    register_relation_system,
    get_relation_system,
    _relation_system_registry,
)


# ===========================================================================
# Protocol method expectations
# ===========================================================================

class TestSubstraitReadProtocol:
    def test_has_read(self):
        assert hasattr(SubstraitReadRelationSystemProtocol, "read")


class TestSubstraitProjectProtocol:
    @pytest.mark.parametrize("method", [
        "project_select",
        "project_with_columns",
        "project_drop",
        "project_rename",
    ])
    def test_has_method(self, method: str):
        assert hasattr(SubstraitProjectRelationSystemProtocol, method)


class TestSubstraitFilterProtocol:
    def test_has_filter(self):
        assert hasattr(SubstraitFilterRelationSystemProtocol, "filter")


class TestSubstraitSortProtocol:
    def test_has_sort(self):
        assert hasattr(SubstraitSortRelationSystemProtocol, "sort")


class TestSubstraitFetchProtocol:
    @pytest.mark.parametrize("method", ["fetch", "fetch_from_end"])
    def test_has_method(self, method: str):
        assert hasattr(SubstraitFetchRelationSystemProtocol, method)


class TestSubstraitJoinProtocol:
    @pytest.mark.parametrize("method", ["join", "join_asof"])
    def test_has_method(self, method: str):
        assert hasattr(SubstraitJoinRelationSystemProtocol, method)


class TestSubstraitAggregateProtocol:
    @pytest.mark.parametrize("method", ["aggregate", "distinct"])
    def test_has_method(self, method: str):
        assert hasattr(SubstraitAggregateRelationSystemProtocol, method)


class TestSubstraitSetProtocol:
    def test_has_union_all(self):
        assert hasattr(SubstraitSetRelationSystemProtocol, "union_all")


class TestMountainashExtensionProtocol:
    @pytest.mark.parametrize("method", [
        "drop_nulls",
        "with_row_index",
        "explode",
        "sample",
        "unpivot",
        "pivot",
        "top_k",
    ])
    def test_has_method(self, method: str):
        assert hasattr(MountainashExtensionRelationSystemProtocol, method)


# ===========================================================================
# RelationSystem base class
# ===========================================================================

ALL_PROTOCOLS = (
    SubstraitReadRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitAggregateRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
    MountainashExtensionRelationSystemProtocol,
)


class TestRelationSystemInheritance:
    @pytest.mark.parametrize("protocol", ALL_PROTOCOLS, ids=lambda p: p.__name__)
    def test_inherits_protocol(self, protocol):
        assert protocol in RelationSystem.__mro__


# ===========================================================================
# Registry
# ===========================================================================

class _DummyRelationSystem(RelationSystem):
    """Minimal concrete subclass used only for registry tests."""

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.POLARS

    # --- Substrait: read ---
    def read(self, dataframe, /):
        return dataframe

    # --- Substrait: project ---
    def project_select(self, relation, columns, /):
        return relation
    def project_with_columns(self, relation, expressions, /):
        return relation
    def project_drop(self, relation, columns, /):
        return relation
    def project_rename(self, relation, mapping, /):
        return relation

    # --- Substrait: filter ---
    def filter(self, relation, predicate, /):
        return relation

    # --- Substrait: sort ---
    def sort(self, relation, sort_fields, /):
        return relation

    # --- Substrait: fetch ---
    def fetch(self, relation, offset, count, /):
        return relation
    def fetch_from_end(self, relation, count, /):
        return relation

    # --- Substrait: join ---
    def join(self, left, right, *, join_type, on=None, left_on=None, right_on=None, suffix="_right"):
        return left
    def join_asof(self, left, right, *, on, by=None, strategy="backward", tolerance=None):
        return left

    # --- Substrait: aggregate ---
    def aggregate(self, relation, keys, measures, /):
        return relation
    def distinct(self, relation, columns, /):
        return relation

    # --- Substrait: set ---
    def union_all(self, relations, /):
        return relations[0]

    # --- Extension: mountainash ---
    def drop_nulls(self, relation, /, *, subset=None):
        return relation
    def with_row_index(self, relation, /, *, name="index"):
        return relation
    def explode(self, relation, /, *, columns):
        return relation
    def sample(self, relation, /, *, n=None, fraction=None):
        return relation
    def unpivot(self, relation, /, *, on, index=None, variable_name="variable", value_name="value"):
        return relation
    def pivot(self, relation, /, *, on, index=None, values=None, aggregate_function="first"):
        return relation
    def top_k(self, relation, /, *, k, by, descending=True):
        return relation


class TestRelationSystemRegistry:
    """Test register / get lifecycle."""

    def setup_method(self):
        # Snapshot and restore registry around each test
        self._snapshot = dict(_relation_system_registry)

    def teardown_method(self):
        _relation_system_registry.clear()
        _relation_system_registry.update(self._snapshot)

    def test_register_and_retrieve(self):
        register_relation_system(CONST_BACKEND.POLARS)(_DummyRelationSystem)
        result = get_relation_system(CONST_BACKEND.POLARS)
        assert result is _DummyRelationSystem

    def test_get_unknown_backend_raises(self):
        with pytest.raises(KeyError, match="No RelationSystem registered"):
            get_relation_system(CONST_BACKEND.PYARROW)

    def test_register_decorator_returns_class(self):
        decorated = register_relation_system(CONST_BACKEND.IBIS)(_DummyRelationSystem)
        assert decorated is _DummyRelationSystem
