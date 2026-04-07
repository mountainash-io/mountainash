"""Tests for RelationDAG.to_package() — Task 20."""
from __future__ import annotations

import pytest

from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag.errors import MissingResourceSchema
from mountainash.typespec.datapackage import DataPackage, DataResource


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


def test_dag_to_package_raises_on_missing_schema():
    import mountainash as ma
    dag = RelationDAG()
    dag.add("anon", ma.relation([{"x": 1}]))  # no schema, no source resource
    with pytest.raises(MissingResourceSchema, match="anon"):
        dag.to_package()


def test_dag_to_package_carries_assets_through(tmp_path):
    p = tmp_path / "logo.png"
    p.write_bytes(b"\x89PNG")
    pkg = DataPackage(resources=[
        DataResource(name="logo", path=str(p), format="png"),
    ])
    dag = pkg.to_relation_dag()
    pkg2 = dag.to_package()
    assert {r.name for r in pkg2.resources} == {"logo"}
