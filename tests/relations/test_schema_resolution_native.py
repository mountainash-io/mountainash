"""Backend-native inference contracts, distinct from ordinary expression results."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D


def test_polars_native_udf_inference_is_allowed_without_collection(monkeypatch):
    """Polars-specific dummy-input inference; no equivalent generic callback API."""
    callbacks = []
    collections = []

    def double(series):
        callbacks.append(series.to_list())
        return series * 2

    source = pl.LazyFrame({"n": [901, 902]}).select(pl.col("n").map_batches(double))
    relation = ma.relation(source).select(ma.col("n").add(1).alias("next"))
    native_collect = pl.LazyFrame.collect

    def observe_collect(frame, *args, **kwargs):
        collections.append(True)
        return native_collect(frame, *args, **kwargs)

    monkeypatch.setattr(pl.LazyFrame, "collect", observe_collect)
    expected = {"next": D.I64}
    assert relation.schema == expected
    assert relation.collect_schema() == expected
    assert relation.collect_schema(allow_execution=True) == expected
    assert callbacks
    assert all(901 not in values and 902 not in values for values in callbacks)
    assert not collections
    assert relation.to_dict() == {"next": [1803, 1805]}
    assert [901, 902] in callbacks
    assert collections


def test_native_inference_error_is_not_retried_by_executing(monkeypatch):
    """Polars must expose its own unresolved-column failure even with permission."""
    source = pl.LazyFrame({"n": [901]}).select(pl.col("absent"))
    relation = ma.relation(source)
    collections = []
    native_collect = pl.LazyFrame.collect

    def observe_collect(frame, *args, **kwargs):
        collections.append(True)
        return native_collect(frame, *args, **kwargs)

    monkeypatch.setattr(pl.LazyFrame, "collect", observe_collect)
    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        relation.collect_schema(allow_execution=True)
    assert not collections


def test_eager_callback_does_not_certify_empty_input_dtype():
    """pandas apply(str) keeps int64 on empty data but changes populated output."""
    import narwhals as nw
    import pandas as pd
    from mountainash.core.dtypes import dtype_family
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
    from mountainash.exceptions import IncompleteSchemaError

    inputs = []

    def stringify(series):
        native = pd.Series(series.to_list(), dtype="int64")
        inputs.append(native.tolist())
        return native.apply(str).to_numpy()

    expression = ma.native(nw.col("n").map_batches(stringify)).alias("text")
    relation = ma.relation(pd.DataFrame({"n": [901, 902]})).select(expression)
    with pytest.raises(IncompleteProjectionSchemaError):
        _ = relation.schema
    with pytest.raises(IncompleteSchemaError):
        relation.collect_schema()
    assert inputs == []
    assert dtype_family(relation.collect_schema(allow_execution=True)["text"]) is D.STRING
    assert inputs == [[901, 902]]
    assert relation.to_dict() == {"text": ["901", "902"]}


def test_pivot_requires_permission_before_discovering_value_dependent_names(monkeypatch):
    from mountainash.exceptions import IncompleteSchemaError

    relation = ma.relation(pl.LazyFrame({
        "id": [1, 1], "category": ["a", "b"], "amount": [10, 20],
    })).pivot(on="category", index="id", values="amount")
    collections = []
    native_collect = pl.LazyFrame.collect

    def observe_collect(frame, *args, **kwargs):
        collections.append(True)
        return native_collect(frame, *args, **kwargs)

    monkeypatch.setattr(pl.LazyFrame, "collect", observe_collect)
    with pytest.raises(IncompleteSchemaError):
        relation.collect_schema()
    assert not collections
    assert relation.collect_schema(allow_execution=True) == {"id": D.I64, "a": D.I64, "b": D.I64}
    assert collections


@pytest.mark.parametrize("allow_execution", [False, True])
def test_known_zero_column_schema_is_complete(allow_execution):
    relation = ma.relation(pl.DataFrame())

    assert relation.collect_schema(allow_execution=allow_execution) == {}


@pytest.mark.parametrize("allow_execution", [False, True])
def test_unbound_reference_is_not_a_known_zero_column_schema(allow_execution):
    from mountainash.exceptions import IncompleteSchemaError
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
    from mountainash.relations.core.relation_api.relation import Relation

    relation = Relation(RefRelNode(name="missing"))

    with pytest.raises(IncompleteSchemaError, match="missing"):
        relation.collect_schema(allow_execution=allow_execution)


def test_recursive_unknown_dtype_does_not_certify_complete_schema():
    import ibis
    from mountainash.core.dtypes import ListDtype, SchemaTypeStatus, dtype_is_complete
    from mountainash.exceptions import IncompleteSchemaError

    relation = ma.relation(ibis.table({"items": "array<timestamp>"}, name="partial"))

    assert isinstance(relation.schema["items"], ListDtype)
    assert relation.schema["items"].element.precision is SchemaTypeStatus.UNKNOWN
    assert not dtype_is_complete(relation.schema["items"])
    with pytest.raises(IncompleteSchemaError):
        relation.collect_schema()
