"""Shared recipes reuse real lowering work, never a previous terminal's rows."""

import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.relations.core.execution.transport import TransportSession


@pytest.mark.parametrize("backend_name", [
    name for name, spec in REGISTRY.items() if spec.family == "ibis"
])
def test_shared_request_lowering_and_transfer_are_execution_local(backend_name, monkeypatch):
    payload = {"id": [1, 3]}
    request = ma.relation(payload).filter(ma.col("id") > 0)
    frame = REGISTRY[backend_name].build({"id": [1, 2]}, "stored")
    branch = ma.relation(frame).join(request, on="id")
    query = ma.concat([branch] * 4)
    calls = {"lower": 0, "transfer": 0}
    node_type = type(request._node)
    accept = node_type.accept
    convert = TransportSession._convert

    def observe_accept(node, visitor):
        if node is request._node and visitor.execution_phase.name == "EXECUTE":
            calls["lower"] += 1
        return accept(node, visitor)

    def observe_convert(session, source, requirement):
        calls["transfer"] += 1
        return convert(session, source, requirement)

    monkeypatch.setattr(node_type, "accept", observe_accept)
    monkeypatch.setattr(TransportSession, "_convert", observe_convert)
    assert query.to_dicts() == [{"id": 1}] * 4
    assert calls == {"lower": 1, "transfer": 1}
    payload["id"] = [2]
    assert query.to_dicts() == [{"id": 2}] * 4
    assert calls == {"lower": 2, "transfer": 2}


@pytest.mark.parametrize("backend_name", list(REGISTRY))
def test_shared_local_branch_lowers_once(backend_name, monkeypatch):
    frame = REGISTRY[backend_name].build({"id": [1, 2]}, "local_source")
    branch = ma.relation(frame).filter(ma.col("id") > 1).select("id")
    query = ma.concat([branch] * 4)
    calls = []
    node_type = type(branch._node)
    accept = node_type.accept

    def observe_accept(node, visitor):
        if node is branch._node and visitor.execution_phase.name == "EXECUTE":
            calls.append(node)
        return accept(node, visitor)

    monkeypatch.setattr(node_type, "accept", observe_accept)
    assert query.to_dicts() == [{"id": 2}] * 4
    assert len(calls) == 1


@pytest.mark.parametrize("backend_name", list(REGISTRY))
@pytest.mark.parametrize("payload", [
    {"id": [1, 3]}, [{"id": 1}, {"id": 3}], ({"id": 1}, {"id": 3}),
])
def test_raw_ingress_shared_by_distinct_parents(backend_name, payload, monkeypatch):
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes import ReadRelNode

    raw = Relation(ReadRelNode(dataframe=payload))
    frame = REGISTRY[backend_name].build({"id": [1, 2]}, "raw_target")
    target = ma.relation(frame)
    left = target.filter(ma.col("id") > 0).join(raw, on="id")
    right = target.filter(ma.col("id") < 2).join(raw, on="id")
    from mountainash.relations.core.execution import transport
    from mountainash.relations.core.errors import UnsupportedRelationTransportError
    from mountainash.relations.core import materialization

    conversions = []
    adapter_name = (
        "coerce_to_ibis" if REGISTRY[backend_name].family == "ibis"
        else "coerce_to_polars" if backend_name.startswith("polars")
        else "coerce_to_narwhals"
    )
    adapter = getattr(materialization, adapter_name)

    def observe_adapter(target, value):
        conversions.append(value)
        return adapter(target, value)

    monkeypatch.setattr(materialization, adapter_name, observe_adapter)
    monkeypatch.setattr(transport, adapter_name, observe_adapter)
    if backend_name == "narwhals-lazy":
        # This destination has no declared raw-input transport on baseline.
        with pytest.raises(UnsupportedRelationTransportError):
            ma.concat([left, right]).to_dicts()
        return
    assert ma.concat([left, right]).to_dicts() == [{"id": 1}] * 2
    assert len(conversions) == 1


def test_replaced_lowering_cannot_borrow_copied_builtin_permission(monkeypatch):
    from functools import wraps
    import polars as pl
    from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem

    original = PolarsRelationSystem.filter
    calls = 0

    @wraps(original)
    def replacement(self, relation, predicate):
        nonlocal calls
        calls += 1
        return original(self, relation, predicate).with_columns(pl.lit(calls).alias("call"))

    monkeypatch.setattr(PolarsRelationSystem, "filter", replacement)
    branch = ma.relation({"id": [1]}).filter(ma.col("id") > 0)
    result = ma.concat([branch] * 4).to_dicts()
    assert result == [{"id": 1, "call": n} for n in range(1, 5)]


def test_replaced_expression_argument_lowering_remains_occurrence_wise(monkeypatch):
    from functools import wraps
    import polars as pl
    from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem

    original = PolarsExpressionSystem.prepare_coalesce_arguments
    calls = 0

    @wraps(original)
    def replacement(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        return [pl.lit(calls)]

    monkeypatch.setattr(PolarsExpressionSystem, "prepare_coalesce_arguments", replacement)
    branch = ma.relation({"id": [1]}).select(ma.coalesce(ma.lit(None), ma.col("id")).alias("call"))
    assert ma.concat([branch] * 4).to_dicts() == [{"call": n} for n in range(1, 5)]


def test_independent_equal_requests_keep_distinct_lowerings(monkeypatch):
    requests = [ma.relation({"id": [1]}).filter(ma.col("id") > 0) for _ in range(2)]
    target = ma.relation(REGISTRY["ibis-duckdb"].build({"id": [1]}, "independent"))
    branches = [target.join(request, on="id") for request in requests]
    calls = []
    node_type = type(requests[0]._node)
    original = node_type.accept

    def observe(node, visitor):
        if any(node is request._node for request in requests):
            calls.append(node)
        return original(node, visitor)

    monkeypatch.setattr(node_type, "accept", observe)
    assert ma.concat(branches * 2).to_dicts() == [{"id": 1}] * 4
    assert len(calls) == 2
    assert calls[0] is not calls[1]


@pytest.mark.parametrize("wrapper", ["conditional", "cast", "window"])
@pytest.mark.parametrize("seed", [None, 42])
def test_nested_list_sample_keeps_occurrence_transfers(wrapper, seed, monkeypatch):
    expression = ma.col("items").list.sample(n=1, seed=seed)
    if wrapper == "conditional":
        expression = ma.when(ma.col("id") > 0).then(expression).otherwise(ma.col("items"))
    elif wrapper == "cast":
        from mountainash.core.dtypes import ListDtype

        expression = expression.cast(ListDtype(ma.MountainashDtype.I64))
    else:
        expression = expression.over("group")
    request = ma.relation({"id": [1], "items": [[7]], "group": [0]}).select(
        "id", expression.alias("sample"),
    )
    stored = ma.relation(REGISTRY["ibis-duckdb"].build({"id": [1]}, "list_target"))
    branch = stored.join(request, on="id")
    conversions = []
    convert = TransportSession._convert

    def observe(session, source, requirement):
        conversions.append(source.value)
        return convert(session, source, requirement)

    monkeypatch.setattr(TransportSession, "_convert", observe)
    assert ma.concat([branch] * 4).to_dicts() == [{"id": 1, "sample": [7]}] * 4
    assert len(conversions) == 4


@pytest.mark.parametrize("dtype,values", [
    ("category", ["a", "b"]), ("Int64", [1, None]), ("string", ["a", None]),
])
def test_pandas_extension_series_ingress_remains_supported(dtype, values):
    import pandas as pd

    source = ma.relation({"value": pd.Series(values, dtype=dtype)})
    assert ma.concat([source] * 2).to_dicts() == [
        {"value": value} for value in values
    ] * 2


def test_raw_native_expression_keeps_occurrence_evaluation():
    import polars as pl

    calls = []

    def alternating(series):
        calls.append(True)
        return pl.Series([len(calls) % 2 == 1] * len(series))

    predicate = pl.col("id").map_batches(alternating, return_dtype=pl.Boolean)
    request = ma.relation({"id": [1]}).filter(predicate)
    stored = ma.relation(REGISTRY["ibis-duckdb"].build({"id": [1]}, "native_target"))
    branch = stored.join(request, on="id")
    assert ma.concat([branch] * 4).to_dicts() == [{"id": 1}] * 2
    assert len(calls) == 4


@pytest.mark.parametrize("backend_name, snapshot", [
    (name, snapshot)
    for name, spec in REGISTRY.items()
    for snapshot in ("today", "now")
    if snapshot == "today" or spec.family != "ibis"
])
@pytest.mark.parametrize("shared_projection", [False, True])
def test_host_clock_snapshots_are_evaluated_per_occurrence(
    backend_name, snapshot, shared_projection, monkeypatch,
):
    from datetime import date, datetime, timedelta
    from importlib import import_module

    family = (
        "ibis" if REGISTRY[backend_name].family == "ibis"
        else "polars" if backend_name.startswith("polars")
        else "narwhals"
    )
    prefix = {"polars": "pl", "narwhals": "nw", "ibis": "ib"}[family]
    module = import_module(
        f"mountainash.expressions.backends.expression_systems.{family}"
        f".extensions_mountainash.expsys_{prefix}_ext_ma_scalar_datetime"
    )
    values = []
    start = date(2026, 1, 1) if snapshot == "today" else datetime(2026, 1, 1)

    class Clock:
        @staticmethod
        def read():
            value = start + timedelta(days=len(values))
            values.append(value)
            return value

        today = read
        now = read

    monkeypatch.setattr(module, "date" if snapshot == "today" else "datetime", Clock)
    frame = REGISTRY[backend_name].build({"id": [1]}, "clock_source")
    stamp = getattr(ma, snapshot)()
    expressions = [stamp.alias("stamp")]
    if shared_projection:
        expressions.append(stamp.alias("again"))
    branch = ma.relation(frame).select(*expressions)
    result = ma.concat([branch] * 4).to_dicts()
    assert sorted(value for row in result for value in row.values()) == [
        start + timedelta(days=index) for index in range(8 if shared_projection else 4)
    ]


def test_native_window_partition_keeps_occurrence_evaluation():
    import polars as pl
    from mountainash.expressions.core.expression_nodes.mountainash_extensions.exn_ext_ma_over import OverNode
    from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import WindowSpec

    calls = []

    def alternating_groups(series):
        calls.append(True)
        return pl.Series([0] * len(series)) if len(calls) % 2 else series

    partition = pl.col("id").map_batches(alternating_groups, return_dtype=pl.Int64)
    total = ma.col("id").sum()
    windowed = total.create(OverNode(
        expression=total._node, window_spec=WindowSpec(partition_by=[partition]),
    ))
    request = ma.relation({"id": [1, 2]}).select("id", windowed.alias("total"))
    stored = ma.relation(REGISTRY["ibis-duckdb"].build({"id": [1, 2]}, "window_target"))
    branch = stored.join(request, on="id")
    rows = ma.concat([branch] * 4).to_dicts()
    assert sorted(row["total"] for row in rows) == [1, 1, 2, 2, 3, 3, 3, 3]
    assert len(calls) == 4


@pytest.mark.parametrize("backend_name", [
    name for name, spec in REGISTRY.items() if spec.family == "ibis"
])
def test_trusted_multiarm_conditional_retains_qualified_transfer(backend_name, monkeypatch):
    expression = (
        ma.when(ma.col("id") == 1).then(10)
        .when(ma.col("id") == 2).then(20).otherwise(30)
    )
    request = ma.relation({"id": [1, 2, 3]}).select("id", expression.alias("value"))
    stored = ma.relation(REGISTRY[backend_name].build({"id": [1, 2, 3]}, "conditional_target"))
    branch = stored.join(request, on="id")
    conversions = []
    convert = TransportSession._convert

    def observe(session, source, requirement):
        conversions.append(source.value)
        return convert(session, source, requirement)

    monkeypatch.setattr(TransportSession, "_convert", observe)
    with ma.capability_policy(ma.CapabilityPolicy.trusted()):
        rows = ma.concat([branch] * 4).to_dicts()
    assert sorted((row["id"], row["value"]) for row in rows) == sorted(
        [(1, 10), (2, 20), (3, 30)] * 4
    )
    assert len(conversions) == 1
