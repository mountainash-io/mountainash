"""Public behavior for validated lexical numeric expression lineage."""
from __future__ import annotations

import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.core.dtypes.errors import LexicalNumericUseError


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_lexical_cast_blocks_arithmetic_before_backend_dispatch(backend_name, backend_factory):
    source = backend_factory.create({"text": ["20", "100"]}, backend_name)
    expression = ma.col("text").cast(ma.MountainashDtype.LEXICAL_INTEGER) + 1

    with pytest.raises(LexicalNumericUseError):
        ma.relation(source).select(expression.alias("result")).to_dict()


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_lexical_cast_lineage_survives_projection_rename_and_sort(backend_name, backend_factory):
    source = backend_factory.create({"text": ["20", "100", None]}, backend_name)
    relation = (
        ma.relation(source)
        .select(ma.col("text").cast(ma.MountainashDtype.LEXICAL_INTEGER).alias("value"))
        .rename({"value": "number"})
    )

    assert relation.to_dict()["number"] == ["20", "100", None]
    with pytest.raises(LexicalNumericUseError):
        relation.sort("number").to_dict()

    # STRING is an intentional opt-out, so ordinary textual ordering applies.
    text = relation.select(ma.col("number").cast("string"))
    assert text.filter(ma.col("number").is_not_null()).sort("number").to_dict()["number"] == [
        "100", "20"
    ]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_explicit_numeric_cast_consumes_lexical_evidence(backend_name, backend_factory):
    source = backend_factory.create({"text": ["20", "100"]}, backend_name)
    relation = ma.relation(source).select(
        ma.col("text").cast(ma.MountainashDtype.LEXICAL_INTEGER).alias("value")
    )

    assert relation.select(ma.col("value").cast("i64").alias("number")).sort("number").to_dict() == {
        "number": [20, 100]
    }


def _declared_relation(backend_name, backend_factory):
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

    source = backend_factory.create({"id": [1, 2], "n": ["+00020", "100"]}, backend_name)
    return ma.relation(source).conform(TypeSpec(fields_match="open", fields=[
        FieldSpec(name="n", type=UniversalType.STRING, dtype=ma.MountainashDtype.LEXICAL_INTEGER),
    ]))


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("path", ["filter", "prefix", "regex", "union", "join", "dag"])
def test_lexical_protection_survives_relation_boundaries(backend_name, backend_factory, path):
    rel = _declared_relation(backend_name, backend_factory)
    column = "n"
    if path == "filter":
        rel = rel.filter(ma.col("n").is_not_null()).head(1)
    elif path == "prefix":
        rel = rel.select(ma.col("*").name.prefix("v_"))
        column = "v_n"
    elif path == "regex":
        rel = rel.select(ma.col("^n$").name.suffix("_value"))
        column = "n_value"
    elif path == "union":
        rel = ma.concat([rel, rel])
    elif path == "join":
        rel = rel.join(rel, on="id")
        column = "n_right"
    else:
        dag = ma.RelationDAG()
        dag.add("values", rel)
        rel = dag.ref("values").rename({"n": "value"})
        column = "value"
    with pytest.raises(LexicalNumericUseError):
        rel.sort(column).to_dict()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_canonical_lexical_equality_grouping_and_join(backend_name, backend_factory):
    rel = _declared_relation(backend_name, backend_factory)
    key = ma.lit("20").cast(ma.MountainashDtype.LEXICAL_INTEGER)
    assert rel.filter(ma.col("n").eq(key)).to_dict()["id"] == [1]
    assert rel.join(rel, on="n").to_dict()["n"] == ["20", "100"]
    renamed = rel.rename({"n": "key"})
    assert rel.join(renamed, left_on="n", right_on="key").to_dict()["n"] == ["20", "100"]
    grouped = rel.group_by("n").agg(ma.col("id").count().alias("count")).to_dict()
    assert dict(zip(grouped["n"], grouped["count"])) == {"20": 1, "100": 1}
    assert set(ma.concat([rel, rel]).unique().to_dict()["n"]) == {"20", "100"}


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("consumer", ["join", "union", "coalesce", "conditional"])
def test_mixed_lexical_plain_domains_require_conversion(backend_name, backend_factory, consumer):
    rel = _declared_relation(backend_name, backend_factory)
    plain = ma.relation(backend_factory.create({"id": [1, 2], "n": ["20", "100"]}, backend_name))
    if consumer == "join":
        result = rel.join(plain, on="n")
    elif consumer == "union":
        result = ma.concat([rel, plain])
    elif consumer == "coalesce":
        result = rel.select(ma.coalesce(ma.col("n"), ma.lit("20")))
    else:
        result = rel.select(ma.when(ma.col("id").eq(1)).then(ma.col("n")).otherwise(ma.lit("20")))
    with pytest.raises(LexicalNumericUseError):
        result.to_dict()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_native_export_deliberately_ends_lexical_protection(backend_name, backend_factory):
    rel = _declared_relation(backend_name, backend_factory)
    native = rel.to_polars()
    assert ma.relation(native).sort("n").to_dict()["n"] == ["100", "20"]
    with pytest.raises(LexicalNumericUseError):
        rel.sort("n").to_dict()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_nested_numeric_projection_keeps_child_domain(backend_name, backend_factory):
    from mountainash.conform.errors import UnsupportedStructuredTransportUse
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

    values = [{"n": "+00020"}, {"n": "100"}]
    if backend_name == "ibis-sqlite":
        import json
        values = [json.dumps(value) for value in values]
    source = backend_factory.create({"record": values}, backend_name)
    spec = TypeSpec(fields=[FieldSpec(
        name="record", type=UniversalType.OBJECT, object_fields=[
            FieldSpec(name="n", type=UniversalType.STRING, dtype=ma.MountainashDtype.LEXICAL_INTEGER),
        ],
    )])
    rel = ma.relation(source).conform(spec).select(ma.col("record").struct.field("n"))
    if backend_name in {"pandas", "narwhals-pandas", "ibis-sqlite"}:
        with pytest.raises(UnsupportedStructuredTransportUse):
            rel.to_dict()
        return
    assert rel.to_dict()["n"] == ["20", "100"]
    with pytest.raises(LexicalNumericUseError):
        rel.sort("n").to_dict()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_lexical_conditional_predicate_is_refused_before_dispatch(backend_name, backend_factory):
    rel = _declared_relation(backend_name, backend_factory)
    with pytest.raises(LexicalNumericUseError):
        rel.select(ma.when(ma.col("n")).then(1).otherwise(0)).to_dict()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_null_equality_does_not_depend_on_operand_order(backend_name, backend_factory):
    rel = _declared_relation(backend_name, backend_factory)
    expected = {"id": [], "n": []}
    assert rel.filter(ma.col("n").eq(ma.lit(None))).to_dict() == expected
    assert rel.filter(ma.lit(None).eq(ma.col("n"))).to_dict() == expected


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_lexical_window_order_requires_conversion(backend_name, backend_factory):
    rel = _declared_relation(backend_name, backend_factory)
    with pytest.raises(LexicalNumericUseError):
        rel.select(ma.col("id").sum().over(order_by="n")).to_dict()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_opaque_native_predicate_cannot_bypass_lexical_protection(backend_name, backend_factory):
    source = backend_factory.create({"n": ["20", "100"]}, backend_name)
    if backend_name.startswith("ibis-"):
        import ibis
        predicate = ibis._["n"] > "30"
    elif backend_name in {"polars", "polars-lazy"}:
        import polars as pl
        predicate = pl.col("n") > "30"
    else:
        import narwhals as nw
        predicate = nw.col("n") > "30"
    rel = ma.relation(source).with_columns(ma.col("n").cast(ma.MountainashDtype.LEXICAL_INTEGER))
    with pytest.raises(LexicalNumericUseError):
        rel.filter(ma.native(predicate)).to_dict()
