"""Immediate native attribution requires the actual failing call, not prose."""
from __future__ import annotations

import narwhals as nw
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST as FK,
)


def test_negative_list_index_attribution_without_information():
    """Narwhals-specific: other backends implement native negative indexing.

    The policy has no information record. Valid indices still execute, and an
    unrelated native argument-type failure is not attributed to negative indexing.
    """
    dataframe = nw.from_native(pl.DataFrame({"values": [[1, 2], [3, 4]]}))
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_polars.extensions_mountainash.list",
            Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-polars")),
            CapabilitySegment(Domain.LIST, policies=(
                CapabilityPolicyRule(
                    key=CapabilityKey(FK.GET, "index"),
                    level=CapabilityLevel.UNSUPPORTED,
                    since="2026-09-18",
                    message="Negative list indices are unsupported by Narwhals.",
                    consumer=PolicyConsumer.IMMEDIATE_ERROR,
                    action=PolicyAction.ENRICH,
                    native_errors=(ValueError,),
                    native_issue="narwhals:list-negative-index",
                ),
            )),
        ))
        with pytest.raises(BackendCapabilityError) as raised:
            ma.col("values").list.get(-1).compile(dataframe)
        assert type(raised.value.__cause__) is ValueError

        with ma.capability_policy(ma.CapabilityPolicy.native_debugging()):
            with pytest.raises(ValueError) as native:
                ma.col("values").list.get(-1).compile(dataframe)
            assert type(native.value) is ValueError
            compiled = ma.col("values").list.get(0).compile(dataframe)
            assert dataframe.select(compiled.alias("result"))["result"].to_list() == [1, 3]

        with ma.capability_policy(ma.CapabilityPolicy.trusted()):
            with pytest.raises(ValueError) as native:
                ma.col("values").list.get(-1).compile(dataframe)
            assert type(native.value) is ValueError

        compiled = ma.col("values").list.get(0).compile(dataframe)
        assert dataframe.select(compiled.alias("result"))["result"].to_list() == [1, 3]

        with pytest.raises(TypeError):
            ma.col("values").list.get("not-an-index").compile(dataframe)
    finally:
        CapabilityRegistry.restore(snapshot)
