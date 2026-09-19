"""Attribution requires a bound scope and operation as well as a native issue."""
from __future__ import annotations

import narwhals as nw
import pandas as pd
import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.limitations import enrich_materialization
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK,
)
from mountainash.relations.backends.relation_systems.narwhals.base import NarwhalsBaseRelationSystem


@pytest.fixture
def single_split_policy():
    """Narwhals-specific storage signal; no other backend has this native boundary."""
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_pandas.substrait.string",
            Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-pandas")),
            CapabilitySegment(Domain.STRING, policies=(
                CapabilityPolicyRule(
                    key=CapabilityKey(FK.SPLIT, "*"),
                    level=CapabilityLevel.UNSUPPORTED,
                    since="2026-09-18",
                    message="Arrow-backed pandas strings are required.",
                    consumer=PolicyConsumer.MATERIALIZATION_ERROR,
                    action=PolicyAction.ENRICH,
                    native_errors=(TypeError,),
                    native_issue="narwhals:arrow-string-storage",
                ),
            )),
        ))
        dataframe = nw.from_native(pd.DataFrame({
            "text": pd.Series(["a,b"], dtype=object),
        }))
        yield NarwhalsBaseRelationSystem(dialect="narwhals-pandas"), dataframe
    finally:
        CapabilityRegistry.restore(snapshot)


def test_explicit_unknown_dialect_does_not_borrow_backend_policy(single_split_policy):
    backend, dataframe = single_split_policy
    with pytest.raises(TypeError):
        enrich_materialization(
            backend,
            lambda: dataframe.select(nw.col("text").str.split(",")),
            dialect=None,
            prefer_operation_keys=frozenset({FK.SPLIT}),
        )


def test_native_issue_without_bound_operation_does_not_guess(single_split_policy):
    backend, dataframe = single_split_policy
    with pytest.raises(TypeError):
        enrich_materialization(
            backend,
            lambda: dataframe.select(nw.col("text").str.split(",")),
        )


def test_enrich_materialization_does_not_execute_successful_ibis_table():
    from types import SimpleNamespace

    import ibis

    table = ibis.memtable({"x": [1]})
    backend = SimpleNamespace(
        backend_type=CONST_BACKEND.IBIS,
        dialect=None,
        BACKEND_NAME="ibis",
    )
    trace = SimpleNamespace(records=())
    result = enrich_materialization(
        backend,
        lambda: table,
        diagnostic_trace=trace,
    )
    assert result is table
