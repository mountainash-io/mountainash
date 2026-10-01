"""Tests for RelationDAG.to_package() — Task 5 (emit-not-gate + strict= mode)."""
from __future__ import annotations

import pytest
import polars as pl

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag.errors import MissingResourceSchema
from mountainash.typespec.datapackage import DataPackage, DataResource
from fixtures.backend_registry import ALL_BACKENDS


def test_dag_to_package_with_resource_read_node(tmp_path):
    p = tmp_path / "orders.csv"
    p.write_text("id\n1\n2\n")
    schema = {"fields": [{"name": "id", "type": "integer"}]}
    pkg = DataPackage(resources=[
        DataResource(
            name="orders", path=str(p),
            table_schema=schema, type="table", format="csv",
        ),
    ])
    dag = pkg.to_relation_dag()
    pkg2 = dag.to_package()
    assert {r.name for r in pkg2.resources} == {"orders"}
    # Schema preserved
    out_schema = pkg2.resources[0].table_schema
    assert out_schema == schema


def test_dag_to_package_emits_inline_relation():
    """Default to_package() emits a resource for an inline relation (no raise).

    Relies on Task 2 inline inference: pl.DataFrame([{"x": 1}]) → x: Int32
    which maps to Frictionless "integer". Replaces the old
    test_dag_to_package_raises_on_missing_schema — under the new ref-resolved
    to_package the premise inverts: a RefRelNode now resolves and emits.
    """
    dag = RelationDAG()
    dag.add("anon", ma.relation([{"x": 1}]))
    # Must NOT raise
    pkg = dag.to_package()
    names = {r.name for r in pkg.resources}
    assert "anon" in names
    anon_res = next(r for r in pkg.resources if r.name == "anon")
    schema = anon_res.table_schema
    assert schema is not None, "inline relation should have an inferred schema"
    fields = {f["name"]: f["type"] for f in schema["fields"]}
    assert "x" in fields
    assert fields["x"] == "integer"


def test_dag_to_package_strict_raises_on_unknown():
    """strict=True raises for a genuinely-UNKNOWN column; default emits it.

    Aggregate measure columns infer to SchemaTypeStatus.UNKNOWN (the type
    cannot be determined pre-compile from the plan alone — only the group
    keys are typed), whether or not the measure carries an explicit alias.
    See test_dag_to_package_strict_catches_unaliased_measure (item 46 a) for
    the un-aliased case specifically: since item 46 (a), un-aliased measures
    are inferred under their source-column name as UNKNOWN too, so they are
    no longer silently absent from strict='s view.
    """
    dag = RelationDAG()
    dag.add(
        "grouped",
        ma.relation(pl.DataFrame({"k": [1, 1, 2], "v": [10, 20, 30]}))
        .group_by("k")
        .agg(ma.col("v").sum().alias("v_sum")),
    )

    # Default must NOT raise — it emits best-effort
    pkg = dag.to_package()
    names = {r.name for r in pkg.resources}
    assert "grouped" in names, "default to_package() must emit the relation even with UNKNOWN columns"

    # strict=True must raise naming the relation
    with pytest.raises(MissingResourceSchema, match="grouped"):
        dag.to_package(strict=True)


def test_dag_to_package_strict_catches_unaliased_measure():
    """Item 46 (a): the un-aliased measure is now present-as-UNKNOWN, so
    strict= sees it (was: silently absent, strict passed)."""
    dag = RelationDAG()
    dag.add("src", ma.relation(pl.DataFrame({"k": ["a"], "v": [1]})))
    dag.add("agg", dag.ref("src").group_by("k").agg(ma.col("v").sum()))
    with pytest.raises(MissingResourceSchema, match="agg"):
        dag.to_package(strict=True)


def test_dag_to_package_default_emits_unaliased_measure_as_any():
    """R3: default export still emits, with the measure typeless."""
    dag = RelationDAG()
    dag.add("src", ma.relation(pl.DataFrame({"k": ["a"], "v": [1]})))
    dag.add("agg", dag.ref("src").group_by("k").agg(ma.col("v").sum()))
    pkg = dag.to_package()
    agg_res = next(r for r in pkg.resources if r.name == "agg")
    fields = {f["name"]: f["type"] for f in agg_res.table_schema["fields"]}
    assert fields["v"] == "any"


def test_dag_to_package_ref_relation_exports_real_schema():
    """to_package() uses dag.schema(name) (ref-resolved) not relation.output_schema.

    A ref-filter chain over a typed resource should export the full typed schema
    for the derived relation — NOT be schema-less — proving the ref-resolved
    code path is taken. strict=True must NOT falsely flag it.
    """
    dag = RelationDAG()
    # orders: typed resource with known schema
    df_orders = pl.DataFrame({"id": [1, 2, 3], "status": ["active", "inactive", "active"]})
    dag.add("orders", ma.relation(df_orders))

    # active: a filter over the ref — schema should resolve through the ref
    dag.add("active", dag.ref("orders").filter(ma.col("status").eq("active")))

    pkg = dag.to_package()
    names = {r.name for r in pkg.resources}
    assert "active" in names

    active_res = next(r for r in pkg.resources if r.name == "active")
    schema = active_res.table_schema
    assert schema is not None, "ref-filter relation should have a resolved schema"
    field_names = [f["name"] for f in schema["fields"]]
    assert "id" in field_names
    assert "status" in field_names

    # strict=True must NOT raise for a relation with a fully-resolved schema
    pkg_strict = dag.to_package(strict=True)
    names_strict = {r.name for r in pkg_strict.resources}
    assert "active" in names_strict


def test_dag_to_package_conformed_relation_exports():
    """A DAG with a resource-read and a conformed relation exports both.

    The conformed relation must carry its inferred conform schema in the output.
    """
    from mountainash.typespec.spec import TypeSpec, FieldSpec

    dag = RelationDAG()
    df = pl.DataFrame({"id": [1, 2], "value": ["10", "20"]})
    dag.add("raw", ma.relation(df))

    spec = TypeSpec(fields=[
        FieldSpec(name="id", type="integer"),
        FieldSpec(name="value", type="integer"),
    ])
    dag.add("conformed", ma.relation(df).conform(spec))

    pkg = dag.to_package()
    names = {r.name for r in pkg.resources}
    assert "raw" in names
    assert "conformed" in names

    conformed_res = next(r for r in pkg.resources if r.name == "conformed")
    schema = conformed_res.table_schema
    assert schema is not None, "conformed relation should carry inferred schema"
    field_names = [f["name"] for f in schema["fields"]]
    assert "id" in field_names
    assert "value" in field_names


def test_dag_to_package_carries_assets_through(tmp_path):
    p = tmp_path / "logo.png"
    p.write_bytes(b"\x89PNG")
    pkg = DataPackage(resources=[
        DataResource(name="logo", path=str(p), format="png"),
    ])
    dag = pkg.to_relation_dag()
    pkg2 = dag.to_package()
    assert {r.name for r in pkg2.resources} == {"logo"}


def _fk(fields, resource, ref_fields):
    from mountainash.typespec.spec import ForeignKey, ForeignKeyReference
    return ForeignKey(
        fields=list(fields),
        reference=ForeignKeyReference(resource=resource, fields=list(ref_fields)),
    )


def test_to_package_emits_foreign_keys_for_derived_resource():
    """Item 46 (c): a declared constraint on a derived relation exports."""
    dag = RelationDAG()
    dag.add("customers", ma.relation(pl.DataFrame({"id": [1]})))
    dag.add(
        "active_orders",
        ma.relation(pl.DataFrame({"id": [1], "customer_id": [1], "status": ["active"]})),
    )
    dag.add_constraint("active_orders", _fk(["customer_id"], "customers", ["id"]))
    pkg = dag.to_package()
    res = next(r for r in pkg.resources if r.name == "active_orders")
    assert res.table_schema["foreignKeys"] == [
        {
            "fields": ["customer_id"],
            "reference": {"resource": "customers", "fields": ["id"]},
        }
    ]


def test_to_package_topology_only_edge_emits_no_foreign_keys():
    dag = RelationDAG()
    dag.add("customers", ma.relation(pl.DataFrame({"id": [1]})))
    dag.add("orders", ma.relation(pl.DataFrame({"customer_id": [1]})))
    dag.constraint_edges.add(("customers", "orders"))  # edge, no metadata
    pkg = dag.to_package()
    res = next(r for r in pkg.resources if r.name == "orders")
    assert "foreignKeys" not in (res.table_schema or {})


def test_to_package_multiple_targets_concatenate_in_insertion_order():
    dag = RelationDAG()
    dag.add("customers", ma.relation(pl.DataFrame({"id": [1]})))
    dag.add("orders", ma.relation(pl.DataFrame({"id": [1]})))
    dag.add("items", ma.relation(pl.DataFrame({"order_id": [1], "customer_id": [1]})))
    dag.add_constraint("items", _fk(["order_id"], "orders", ["id"]))
    dag.add_constraint("items", _fk(["customer_id"], "customers", ["id"]))
    pkg = dag.to_package()
    res = next(r for r in pkg.resources if r.name == "items")
    fk_fields = [fk["fields"] for fk in res.table_schema["foreignKeys"]]
    assert fk_fields == [["order_id"], ["customer_id"]]


def test_fk_round_trip_descriptor_dag_descriptor(tmp_path):
    """Descriptor -> DAG -> descriptor is FK-faithful for pass-through AND
    derived resources; no duplicates."""
    order_schema = {
        "fields": [
            {"name": "id", "type": "integer"},
            {"name": "customer_id", "type": "integer"},
        ],
        "foreignKeys": [
            {
                "fields": ["customer_id"],
                "reference": {"resource": "customers", "fields": ["id"]},
            }
        ],
    }
    from mountainash.typespec.datapackage import DataPackage, DataResource
    pkg = DataPackage(resources=[
        DataResource(
            name="customers", path="customers.csv", type="table",
            table_schema={"fields": [{"name": "id", "type": "integer"}]},
        ),
        DataResource(name="orders", path="orders.csv", type="table", table_schema=order_schema),
    ])
    dag = pkg.to_relation_dag()
    dag.add("recent_orders", ma.relation(pl.DataFrame({"id": [1], "customer_id": [1]})))
    dag.add_constraint("recent_orders", _fk(["customer_id"], "customers", ["id"]))

    pkg2 = dag.to_package()
    # Pass-through: byte-identical FK block from lossless table_schema.
    orders = next(r for r in pkg2.resources if r.name == "orders")
    assert orders.table_schema["foreignKeys"] == order_schema["foreignKeys"]
    # Derived: declared constraint exported once.
    recent = next(r for r in pkg2.resources if r.name == "recent_orders")
    assert len(recent.table_schema["foreignKeys"]) == 1

    # Reload: metadata is captured again, no duplicate entries.
    dag2 = pkg2.to_relation_dag()
    assert len(dag2.constraint_metadata[("customers", "orders")]) == 1
    assert len(dag2.constraint_metadata[("customers", "recent_orders")]) == 1


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("operation", ["aggregate", "projection"])
def test_incomplete_export_omits_only_optional_schema(backend_name, backend_factory, operation):
    import ibis

    source = backend_factory.create({"x": [2, 4]}, backend_name)
    native = ma.col("x").sum().compile(source)
    if isinstance(native, ibis.Deferred):
        native = native.resolve(source)
    base = ma.relation(source)
    expr = ma.native(native).alias("total")
    opaque = base.group_by().agg(expr) if operation == "aggregate" else base.select(expr)
    dag = RelationDAG()
    dag.add("known", base)
    dag.add("opaque", opaque)
    resources = {r.name: r for r in dag.to_package().resources}
    assert set(resources) == {"known", "opaque"}
    assert resources["known"].table_schema["fields"] == [{"name": "x", "type": "integer"}]
    assert resources["opaque"].table_schema is None
    with pytest.raises(MissingResourceSchema, match="opaque"):
        dag.to_package(strict=True)


@pytest.mark.parametrize("strict", [False, True])
def test_incomplete_aggregate_export_cannot_discard_declared_foreign_keys(strict):
    """Opaque native cardinality must not silently erase declared constraints."""
    dag = RelationDAG()
    dag.add("customers", ma.relation([{"id": 1}]))
    dag.add("orders", ma.relation([{"customer_id": 1, "amount": 2}]).group_by("customer_id").agg(
        ma.native(object()).alias("total"),
    ))
    dag.add_constraint("orders", _fk(["customer_id"], "customers", ["id"]))
    with pytest.raises(MissingResourceSchema, match="orders.*foreign keys"):
        dag.to_package(strict=strict)


def test_named_aggregate_foreign_keys_round_trip():
    dag = RelationDAG()
    dag.add("customers", ma.relation([{"id": 1}]))
    dag.add("orders", ma.relation([{"customer_id": 1, "amount": 2}]).group_by("customer_id").agg(
        ma.col("amount").sum(),
    ))
    fk = _fk(["customer_id"], "customers", ["id"])
    dag.add_constraint("orders", fk)
    restored = dag.to_package().to_relation_dag()
    assert restored.constraints_for("orders") == [fk]


def test_aggregate_export_preserves_collision_errors():
    from mountainash.relations.core.projection_names import ProjectionNameError
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes import AggregateRelNode

    dag = RelationDAG()
    base = ma.relation([{"x": 1}])
    dag.add("bad", Relation(AggregateRelNode(input=base._node, keys=["x"], measures=[ma.col("x").sum()])))
    with pytest.raises(ProjectionNameError, match="duplicate.*x"):
        dag.to_package()
