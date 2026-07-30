"""NW-LIST-01 capability fact relocation unit tests (Task 7).

Verifies that NW-LIST-01 capability facts are properly registered on list ops
(CONTAINS and T_CONTAINS) as item GATE/BUILD facts and narwhals-pandas
MATERIALIZE_RESIDUE storage facts, and absent from membership ops.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.capabilities import (
    Boundary,
    CapabilityLevel,
    CapabilityRegistry,
    Enforcement,
    WILDCARD_PARAM,
    load_all_capability_declarations,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_MOUNTAINASH_SCALAR_TERNARY as FK_MA_TERN,
)


@pytest.fixture(autouse=True)
def _ensure_capabilities_loaded():
    load_all_capability_declarations()


def test_nw_list_01_item_gate_facts_present():
    """(LIST.CONTAINS, "item") and (LIST.T_CONTAINS, "item") are GATE/BUILD facts."""
    for op in (FK_LIST.CONTAINS, FK_LIST.T_CONTAINS):
        fact = CapabilityRegistry.capability_for(
            op, "item", CONST_BACKEND.NARWHALS
        )
        assert fact is not None
        assert fact.level is CapabilityLevel.LITERAL_ONLY
        assert fact.enforcement is Enforcement.GATE
        assert fact.boundary is Boundary.BUILD
        assert fact.upstream_ref == "NW-LIST-01"


def test_nw_list_01_storage_residue_facts_present():
    """(LIST.CONTAINS, WILDCARD_PARAM) and (LIST.T_CONTAINS, WILDCARD_PARAM) are MATERIALIZE_RESIDUE facts on narwhals-pandas."""
    for op in (FK_LIST.CONTAINS, FK_LIST.T_CONTAINS):
        fact = CapabilityRegistry.capability_for(
            op, WILDCARD_PARAM, CONST_BACKEND.NARWHALS, "narwhals-pandas"
        )
        assert fact is not None
        assert fact.enforcement is Enforcement.MATERIALIZE_RESIDUE
        assert fact.boundary is Boundary.MATERIALIZE
        assert fact.native_errors == (TypeError,)
        assert fact.upstream_ref == "NW-LIST-01"


def test_membership_op_facts_absent():
    """T_IS_IN / T_IS_NOT_IN facts for collection on Narwhals are absent."""
    for op in (FK_MA_TERN.T_IS_IN, FK_MA_TERN.T_IS_NOT_IN):
        fact = CapabilityRegistry.capability_for(
            op, "collection", CONST_BACKEND.NARWHALS
        )
        assert fact is None


def test_dynamic_item_expr_raises_backend_capability_error(backend_factory):
    """Dynamic item Expr on .list.contains and .list.t_contains raises BackendCapabilityError via BUILD gate."""
    data = {"tags": [[1, 2, 3]], "other": [2]}
    df = backend_factory.create(data, "narwhals-polars")

    # Dynamic item on list.contains
    expr_contains = ma.col("tags").list.contains(ma.col("other"))
    with pytest.raises(BackendCapabilityError) as exc_info1:
        expr_contains.compile(df)
    assert "NW-LIST-01" in str(exc_info1.value) or "literal item" in str(exc_info1.value).lower()

    # Dynamic item on list.t_contains
    expr_t_contains = ma.col("tags").list.t_contains(ma.col("other"))
    with pytest.raises(BackendCapabilityError) as exc_info2:
        expr_t_contains.compile(df)
    assert "NW-LIST-01" in str(exc_info2.value) or "literal item" in str(exc_info2.value).lower()
