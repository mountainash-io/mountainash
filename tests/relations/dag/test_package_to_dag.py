"""Tests for DataPackage.to_relation_dag() — Task 19."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.typespec.datapackage import DataPackage, DataResource


def _csv_pkg(tmp_path):
    p = tmp_path / "orders.csv"
    p.write_text("id,amount\n1,10\n2,20\n")
    return DataPackage(resources=[
        DataResource(name="orders", path=str(p), format="csv", type="table"),
    ])


def test_package_to_dag_basic(tmp_path):
    pkg = _csv_pkg(tmp_path)
    dag = pkg.to_relation_dag()
    assert "orders" in dag.relations
    result = dag.collect("orders")
    df = result.collect() if hasattr(result, "collect") else result
    assert df["amount"].sum() == 30


def test_package_to_dag_overrides(tmp_path):
    pkg = _csv_pkg(tmp_path)
    override_df = pl.DataFrame({"id": [99], "amount": [999]})
    dag = pkg.to_relation_dag(overrides={"orders": override_df})
    result = dag.collect("orders")
    df = result.collect() if hasattr(result, "collect") else result
    assert df["amount"].to_list() == [999]


def test_constraint_edges_from_foreign_keys():
    cust_schema = {
        "fields": [{"name": "id", "type": "integer"}],
    }
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
    pkg = DataPackage(resources=[
        DataResource(name="customers", path="customers.csv", table_schema=cust_schema, type="table"),
        DataResource(name="orders", path="orders.csv", table_schema=order_schema, type="table"),
    ])
    dag = pkg.to_relation_dag()
    assert ("customers", "orders") in dag.constraint_edges
    # Foreign keys must NOT be promoted to dependency edges
    assert dag.dependency_edges == set()


def test_non_tabular_resource_becomes_asset(tmp_path):
    p = tmp_path / "logo.png"
    p.write_bytes(b"\x89PNG...")
    pkg = DataPackage(resources=[
        DataResource(name="logo", path=str(p), format="png"),
    ])
    dag = pkg.to_relation_dag()
    assert "logo" in dag.assets
    assert "logo" not in dag.relations
