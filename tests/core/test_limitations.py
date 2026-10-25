"""Attribution requires a bound scope and operation as well as a native issue."""

from __future__ import annotations

import narwhals as nw
import pandas as pd
import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
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
        CapabilityRegistry.register_segment(
            BoundSegment(
                "mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_pandas.substrait.string",
                Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-pandas")),
                CapabilitySegment(
                    Domain.STRING,
                    policies=(
                        CapabilityPolicyRule(
                            key=CapabilityKey(FK.SPLIT, "*"),
                            level=CapabilityLevel.UNSUPPORTED,
                            message="Arrow-backed pandas strings are required.",
                            consumer=PolicyConsumer.MATERIALIZATION_ERROR,
                            action=PolicyAction.ENRICH,
                            native_errors=(TypeError,),
                            native_issue="narwhals:arrow-string-storage",
                            applicability=unbounded,
                        ),
                    ),
                ),
            )
        )
        dataframe = nw.from_native(
            pd.DataFrame(
                {
                    "text": pd.Series(["a,b"], dtype=object),
                }
            )
        )
        yield NarwhalsBaseRelationSystem(dialect="narwhals-pandas"), dataframe
    finally:
        CapabilityRegistry.restore(snapshot)


def _capture_native_failure(operation, captured):
    try:
        return operation()
    except Exception as error:
        captured.append((error, error.__context__, error.__traceback__))
        raise


@pytest.mark.parametrize("binding", ["unknown-dialect", "unbound-operation", "unrelated-error"])
def test_unmatched_materialization_preserves_native_exception_identity(single_split_policy, binding):
    """Real native errors retain identity, context and their original traceback."""
    backend, dataframe = single_split_policy
    captured = []
    options = {}
    if binding == "unknown-dialect":
        options = {"dialect": None, "prefer_operation_keys": frozenset({FK.SPLIT})}
    def operation():
        if binding == "unrelated-error":
            import polars as pl

            return pl.DataFrame({"x": [1]}).select(pl.col("x").replace_strict({0: 0}))
        return dataframe.select(nw.col("text").str.split(","))
    with pytest.raises(Exception) as raised:
        enrich_materialization(
            backend, lambda: _capture_native_failure(operation, captured), **options,
        )
    original, context, traceback = captured[0]
    assert raised.value is original
    assert raised.value.__context__ is context
    chain = raised.value.__traceback__
    while chain is not None and chain is not traceback:
        chain = chain.tb_next
    assert chain is traceback


def test_matching_materialization_policy_enriches_the_captured_native_failure(single_split_policy):
    from mountainash.core.types import BackendCapabilityError

    backend, dataframe = single_split_policy
    captured = []
    with pytest.raises(BackendCapabilityError) as raised:
        enrich_materialization(
            backend,
            lambda: _capture_native_failure(
                lambda: dataframe.select(nw.col("text").str.split(",")), captured,
            ),
            prefer_operation_keys=frozenset({FK.SPLIT}),
        )
    assert raised.value.function_key is FK.SPLIT
    assert raised.value.__cause__ is captured[0][0]


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


@pytest.mark.parametrize("last_marker", [False, None, True])
def test_arrow_residue_uses_boolean_values_across_chunks(last_marker):
    """False/null markers pass; a true marker cannot silently evade attribution."""
    from types import SimpleNamespace

    import pyarrow as pa

    from mountainash.core.errors import CapabilityResidueInvariantError

    table = pa.table({
        "id": [1, 2, 3],
        "__ma_residue_x": pa.chunked_array([[False, None], [last_marker]], type=pa.bool_()),
    })
    backend = SimpleNamespace(backend_type=CONST_BACKEND.IBIS, dialect=None)
    check = SimpleNamespace(marker="__ma_residue_x", function_key=FK.SPLIT, field_name="id")
    if last_marker is True:
        with pytest.raises(CapabilityResidueInvariantError, match="no declared fact"):
            enrich_materialization(backend, lambda: table, residue_checks=(check,))
    else:
        result = enrich_materialization(backend, lambda: table, residue_checks=(check,))
        assert result.to_pydict() == {"id": [1, 2, 3]}
