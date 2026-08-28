"""Logical terminal snapshot resolution tests."""
from __future__ import annotations

from types import MappingProxyType

import pytest

from mountainash.conform.errors import ConformTransformError
from mountainash.conform.structured_transport import (
    StructuredCarrier,
    StructuredFieldPlan,
    StructuredRoot,
)
from mountainash.core.capabilities.identity import BackendIdentity
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.logical_snapshot import (
    LOGICAL_SNAPSHOT_ADAPTERS,
    LogicalTerminalSnapshot,
    resolve_logical_snapshot,
    resolved_snapshot_to_pandas,
    resolved_snapshot_to_polars,
)


def plan(name: str, *, action: str = "coerce", root: StructuredRoot = StructuredRoot.ARRAY):
    return StructuredFieldPlan(
        field_name=name,
        root=root,
        carrier=StructuredCarrier.JSON_TEXT,
        configured_action=action,
        apply_value_transforms=True,
        missing_values=(),
        null_fill=None,
        declaration_fingerprint="schema",
        origin_node_id="conform",
    )


def snapshot(columns):
    return LogicalTerminalSnapshot(
        columns=MappingProxyType(columns),
        row_ordinals=(10, 11),
        source_identity=BackendIdentity(CONST_BACKEND.POLARS, "polars"),
    )


def test_resolution_decodes_transport_fields_and_preserves_ordinary_sequences(monkeypatch):
    """One snapshot resolves tagged physical fields without coercing ordinary columns."""
    import mountainash.conform.structured_transport as structured_transport

    calls: list[tuple[object, StructuredRoot]] = []
    original = structured_transport.decode_structured_value

    def spy(value, *, expected_root):
        calls.append((value, expected_root))
        return original(value, expected_root=expected_root)

    monkeypatch.setattr(structured_transport, "decode_structured_value", spy)
    ordinary = (1, 2)

    resolved = resolve_logical_snapshot(
        snapshot({"left": ("[1]", "[2]"), "right": ("{}", "{}"), "plain": ordinary}),
        MappingProxyType({"left": plan("left"), "right": plan("right", root=StructuredRoot.OBJECT)}),
    )

    assert resolved.logical_columns["left"] == ([1], [2])
    assert resolved.logical_columns["right"] == ({}, {})
    assert resolved.logical_columns["plain"] is ordinary
    assert calls == [
        ("[1]", StructuredRoot.ARRAY),
        ("[2]", StructuredRoot.ARRAY),
        ("{}", StructuredRoot.OBJECT),
        ("{}", StructuredRoot.OBJECT),
    ]


def test_discard_row_masks_combine_before_logical_output():
    """Rows rejected by independent transported fields are removed together."""
    resolved = resolve_logical_snapshot(
        snapshot({"left": ("[1]", "bad"), "right": ("{}", "bad")}),
        MappingProxyType({"left": plan("left", action="discard_row"), "right": plan("right", action="discard_row", root=StructuredRoot.OBJECT)}),
    )

    assert resolved.keep_ordinals == (10,)
    assert resolved.logical_columns["left"] == ([1],)
    assert resolved.logical_columns["right"] == ({},)


def test_coerce_error_is_selected_by_declaration_then_row_ordinal():
    """Logical terminal errors do not leak input values or backend evaluation order."""
    with pytest.raises(ConformTransformError, match="left.*row ordinal 11"):
        resolve_logical_snapshot(
            snapshot({"left": ("[1]", "bad"), "right": ("bad", "{}")}),
            MappingProxyType({"left": plan("left"), "right": plan("right", root=StructuredRoot.OBJECT)}),
        )


def test_coerce_raise_is_gated_to_logical_egress_not_validation():
    """Task 7 spec 12.2/12.3: a logical egress raises `ConformTransformError`
    for an invalid `coerce` value; validation never raises here -- it
    reports the same invalid source through the `logical_value`, letting
    TYPE_FORMAT fail the row instead of crashing check execution."""
    from mountainash.conform.structured_transport import (
        INVALID_STRUCTURED_VALUE,
        StructuredActionConsumer,
    )

    with pytest.raises(ConformTransformError, match="left.*row ordinal 11"):
        resolve_logical_snapshot(
            snapshot({"left": ("[1]", "bad")}),
            MappingProxyType({"left": plan("left")}),
            consumer=StructuredActionConsumer.LOGICAL_EGRESS,
        )

    resolved = resolve_logical_snapshot(
        snapshot({"left": ("[1]", "bad")}),
        MappingProxyType({"left": plan("left")}),
        consumer=StructuredActionConsumer.VALIDATION,
    )
    assert resolved.logical_columns["left"] == ([1], INVALID_STRUCTURED_VALUE)
    assert resolved.keep_ordinals == (10, 11)


def test_snapshot_registry_closes_over_backend_family_and_known_dialects():
    """Every supported family and declared dialect has exactly one adapter route."""
    from mountainash.core.capabilities.identity import KNOWN_DIALECTS
    from mountainash.relations.core.logical_snapshot import LOGICAL_SNAPSHOT_ADAPTERS

    assert set(LOGICAL_SNAPSHOT_ADAPTERS) == set(CONST_BACKEND)
    for family, dialects in KNOWN_DIALECTS.items():
        assert family in LOGICAL_SNAPSHOT_ADAPTERS
        for dialect in dialects:
            assert LOGICAL_SNAPSHOT_ADAPTERS[family].family is family, dialect


def test_snapshot_rejects_unregistered_identity_before_extracting_native_value():
    """A forged identity cannot fall through to an undeclared conversion route."""
    from mountainash.core.errors import BackendConversionError
    from mountainash.relations.core.logical_snapshot import logical_terminal_snapshot

    class ForgedFamily:
        pass

    class Native:
        value = object()
        value_identity = BackendIdentity(ForgedFamily(), None)
        compiler_identity = value_identity
        form = object()

    with pytest.raises(BackendConversionError) as error:
        logical_terminal_snapshot(Native())

    assert error.value.reason == "unregistered logical snapshot adapter"


class _Native:
    """Minimal `NativeExecutionValue`-shaped stand-in for direct adapter tests."""

    def __init__(self, value, identity):
        self.value = value
        self.value_identity = identity
        self.compiler_identity = identity


def test_pyarrow_snapshot_captures_columns_directly():
    """Direct behavior evidence for the PyArrow adapter (spec Task 4 step 1)."""
    import pyarrow as pa

    table = pa.table({"age": [30, -1, None]})
    identity = BackendIdentity(CONST_BACKEND.PYARROW, "pyarrow")
    adapter = LOGICAL_SNAPSHOT_ADAPTERS[CONST_BACKEND.PYARROW]

    result = adapter.snapshot(_Native(table, identity))

    assert result.row_ordinals == (0, 1, 2)
    assert result.columns["age"].to_pylist() == [30, -1, None]


@pytest.mark.parametrize("dialect", ["narwhals-polars", "narwhals-pandas"])
def test_narwhals_snapshot_captures_every_declared_dialect_directly(dialect):
    """Direct behavior evidence for every supported Narwhals dialect (spec Task 4 step 1)."""
    import narwhals as nw
    import pandas as pd
    import polars as pl

    native_frame = (
        pl.DataFrame({"age": [30, -1, None]})
        if dialect == "narwhals-polars"
        else pd.DataFrame({"age": [30, -1, None]})
    )
    frame = nw.from_native(native_frame, eager_only=True)
    identity = BackendIdentity(CONST_BACKEND.NARWHALS, dialect)
    adapter = LOGICAL_SNAPSHOT_ADAPTERS[CONST_BACKEND.NARWHALS]

    result = adapter.snapshot(_Native(frame, identity))

    assert result.row_ordinals == (0, 1, 2)
    assert result.columns["age"].to_pylist() == [30, -1, None]


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_ibis_snapshot_reads_cache_once_and_never_touches_pandas(
    backend_name, backend_factory, monkeypatch
):
    """Spec Task 4 step 2: one cache(), one to_pyarrow() for one snapshot, zero to_pandas()."""
    from mountainash.core.backend_detection import identify_backend_identity
    from mountainash.relations.core.materialization import (
        MaterializationPurpose,
        MaterializationScope,
        materialize_native,
    )
    from mountainash.relations.core.logical_snapshot import logical_terminal_snapshot

    table = backend_factory.create({"age": [30, -1, None], "name": ["a", "b", "c"]}, backend_name)
    identity = identify_backend_identity(table)

    cache_calls = []
    to_pyarrow_calls = []
    to_pandas_calls = []
    original_cache = type(table).cache

    def spy_cache(self, *a, **kw):
        cache_calls.append(1)
        cached = original_cache(self, *a, **kw)
        original_to_pyarrow = type(cached).to_pyarrow
        original_to_pandas = type(cached).to_pandas

        def spy_to_pyarrow(inner_self, *ia, **ikw):
            to_pyarrow_calls.append(1)
            return original_to_pyarrow(inner_self, *ia, **ikw)

        def spy_to_pandas(inner_self, *ia, **ikw):
            to_pandas_calls.append(1)
            return original_to_pandas(inner_self, *ia, **ikw)

        monkeypatch.setattr(type(cached), "to_pyarrow", spy_to_pyarrow)
        monkeypatch.setattr(type(cached), "to_pandas", spy_to_pandas)
        return cached

    monkeypatch.setattr(type(table), "cache", spy_cache)

    with MaterializationScope() as scope:
        native = materialize_native(
            table, identity, MaterializationPurpose.LOGICAL_TERMINAL, scope=scope
        )
        result = logical_terminal_snapshot(native)

    assert cache_calls == [1]
    assert to_pyarrow_calls == [1]
    assert to_pandas_calls == []
    assert result.row_ordinals == (0, 1, 2)
    assert set(result.columns) == {"age", "name"}


def test_resolved_snapshot_to_polars_retains_untagged_dtype_and_tags_object_column():
    """Spec Task 4 step 6: Polars output keeps untagged dtypes; transported column is pl.Object."""
    import polars as pl

    physical = pl.DataFrame({"left": ["[1]", "bad"], "plain": pl.Series([1, 2], dtype=pl.Int8)})
    identity = BackendIdentity(CONST_BACKEND.POLARS, "polars")
    native = _Native(physical, identity)
    adapter = LOGICAL_SNAPSHOT_ADAPTERS[CONST_BACKEND.POLARS]
    physical_snapshot = adapter.snapshot(native)

    resolved = resolve_logical_snapshot(
        physical_snapshot,
        MappingProxyType({"left": plan("left", action="discard_row")}),
    )

    frame = resolved_snapshot_to_polars(resolved)
    assert frame["plain"].dtype == pl.Int8
    assert frame["plain"].to_list() == [1]
    assert frame["left"].dtype == pl.Object
    assert frame["left"].to_list() == [[1]]


def test_resolved_snapshot_to_pandas_retains_untagged_dtype_and_tags_object_column():
    """Spec Task 4 step 6: pandas output keeps untagged dtypes; transported column is object dtype."""
    import pandas as pd

    physical = pd.DataFrame({"left": ["[1]", "bad"], "plain": pd.array([1, 2], dtype="Int8")})
    identity = BackendIdentity(CONST_BACKEND.PANDAS, "pandas")
    native = _Native(physical, identity)
    adapter = LOGICAL_SNAPSHOT_ADAPTERS[CONST_BACKEND.PANDAS]
    physical_snapshot = adapter.snapshot(native)

    resolved = resolve_logical_snapshot(
        physical_snapshot,
        MappingProxyType({"left": plan("left", action="discard_row")}),
    )

    frame = resolved_snapshot_to_pandas(resolved)
    assert str(frame["plain"].dtype) == "Int8"
    assert frame["plain"].tolist() == [1]
    assert frame["left"].dtype == object
    assert frame["left"].tolist() == [[1]]
