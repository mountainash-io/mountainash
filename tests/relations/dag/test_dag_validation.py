"""Tests for RelationDAG.validate() and validate_quick()."""
from __future__ import annotations

import pytest
import polars as pl

import mountainash as ma
from mountainash.typespec.spec import (
    TypeSpec, FieldSpec, FieldConstraints,
    ForeignKey, ForeignKeyReference,
)
from mountainash.typespec.universal_types import UniversalType
from mountainash.relations.dag import RelationDAG
from mountainash.relations.dag.validation import DAGValidationResult, FKViolation
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.compiler import compile_datacontract


def _build_dag(tables: dict[str, pl.DataFrame]) -> RelationDAG:
    dag = RelationDAG()
    for name, df in tables.items():
        dag.add(name, ma.relation(df))
    return dag


class TestPerTableValidation:
    def test_valid_data_passes(self):
        dag = _build_dag({"users": pl.DataFrame({"name": ["alice"], "age": [30]})})
        spec = TypeSpec(fields=[
            FieldSpec(name="name", type=UniversalType.STRING),
            FieldSpec(name="age", type=UniversalType.INTEGER, constraints=FieldConstraints(minimum=0)),
        ])
        result = dag.validate(specs={"users": spec})
        assert isinstance(result, DAGValidationResult)
        assert result.passes is True
        assert "users" in result.table_results
        assert result.table_results["users"].passes is True

    def test_invalid_data_fails(self):
        dag = _build_dag({"users": pl.DataFrame({"age": [-1, 5]})})
        spec = TypeSpec(fields=[
            FieldSpec(name="age", type=UniversalType.INTEGER, constraints=FieldConstraints(minimum=0)),
        ])
        result = dag.validate(specs={"users": spec})
        assert result.passes is False
        assert result.table_results["users"].passes is False

    def test_accepts_base_data_contract(self):
        class UserContract(BaseDataContract):
            name: str

        dag = _build_dag({"users": pl.DataFrame({"name": ["alice"]})})
        result = dag.validate(specs={"users": UserContract})
        assert result.passes is True

    def test_missing_relation_raises(self):
        dag = _build_dag({})
        spec = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.STRING)])
        with pytest.raises(KeyError, match="not_here"):
            dag.validate(specs={"not_here": spec})


class TestFKValidation:
    def _make_fk_dag(self, *, orphans: bool = False, nulls: bool = False):
        parents = pl.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        if orphans:
            child_ids = [1, 2, 99]
        elif nulls:
            child_ids = [1, 2, None]
        else:
            child_ids = [1, 2, 3]
        children = pl.DataFrame({"order_id": [10, 20, 30], "customer_id": child_ids})
        dag = _build_dag({"customers": parents, "orders": children})
        dag.constraint_edges.add(("customers", "orders"))
        return dag

    def _make_specs(self):
        customer_spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="name", type=UniversalType.STRING),
        ])
        order_spec = TypeSpec(
            fields=[
                FieldSpec(name="order_id", type=UniversalType.INTEGER),
                FieldSpec(name="customer_id", type=UniversalType.INTEGER),
            ],
            foreign_keys=[
                ForeignKey(
                    fields=["customer_id"],
                    reference=ForeignKeyReference(resource="customers", fields=["id"]),
                ),
            ],
        )
        return {"customers": customer_spec, "orders": order_spec}

    def test_valid_fk_passes(self):
        dag = self._make_fk_dag(orphans=False)
        specs = self._make_specs()
        result = dag.validate(specs=specs)
        assert result.passes is True
        assert len(result.fk_violations) == 0

    def test_orphan_fk_fails(self):
        dag = self._make_fk_dag(orphans=True)
        specs = self._make_specs()
        result = dag.validate(specs=specs)
        assert result.passes is False
        assert len(result.fk_violations) == 1
        v = result.fk_violations[0]
        assert v.child_table == "orders"
        assert v.parent_table == "customers"
        assert v.orphan_count == 1
        assert 99 in v.orphan_sample["customer_id"].to_list()

    def test_null_fk_excluded_from_check(self):
        dag = self._make_fk_dag(nulls=True)
        specs = self._make_specs()
        result = dag.validate(specs=specs)
        assert result.passes is True
        assert len(result.fk_violations) == 0

    def test_fk_only_edge_no_dependency_edge(self):
        parents = pl.DataFrame({"id": [1, 2]})
        children = pl.DataFrame({"parent_id": [1, 99]})
        dag = _build_dag({"parents": parents, "children": children})
        dag.constraint_edges.add(("parents", "children"))

        parent_spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
        ])
        child_spec = TypeSpec(
            fields=[FieldSpec(name="parent_id", type=UniversalType.INTEGER)],
            foreign_keys=[
                ForeignKey(
                    fields=["parent_id"],
                    reference=ForeignKeyReference(resource="parents", fields=["id"]),
                ),
            ],
        )
        result = dag.validate(specs={"parents": parent_spec, "children": child_spec})
        assert result.passes is False
        assert len(result.fk_violations) == 1

    def test_fk_skipped_when_parent_not_in_specs(self):
        parents = pl.DataFrame({"id": [1]})
        children = pl.DataFrame({"parent_id": [99]})
        dag = _build_dag({"parents": parents, "children": children})
        dag.constraint_edges.add(("parents", "children"))

        child_spec = TypeSpec(
            fields=[FieldSpec(name="parent_id", type=UniversalType.INTEGER)],
            foreign_keys=[
                ForeignKey(
                    fields=["parent_id"],
                    reference=ForeignKeyReference(resource="parents", fields=["id"]),
                ),
            ],
        )
        result = dag.validate(specs={"children": child_spec})
        assert result.passes is True
        assert len(result.fk_violations) == 0


class TestFastMode:
    def test_fast_stops_on_first_table_failure(self):
        dag = _build_dag({
            "good": pl.DataFrame({"x": [1]}),
            "bad": pl.DataFrame({"y": [-1]}),
        })
        good_spec = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.INTEGER)])
        bad_spec = TypeSpec(fields=[
            FieldSpec(name="y", type=UniversalType.INTEGER, constraints=FieldConstraints(minimum=0)),
        ])
        result = dag.validate_quick(specs={"good": good_spec, "bad": bad_spec})
        assert result.passes is False
        assert len(result.fk_violations) == 0

    def test_fast_stops_on_first_fk_violation(self):
        parents = pl.DataFrame({"id": [1]})
        children = pl.DataFrame({"pid": [99]})
        dag = _build_dag({"p": parents, "c": children})
        dag.constraint_edges.add(("p", "c"))

        p_spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
        c_spec = TypeSpec(
            fields=[FieldSpec(name="pid", type=UniversalType.INTEGER)],
            foreign_keys=[
                ForeignKey(fields=["pid"], reference=ForeignKeyReference(resource="p", fields=["id"])),
            ],
        )
        result = dag.validate_quick(specs={"p": p_spec, "c": c_spec})
        assert result.passes is False
        assert len(result.fk_violations) == 1
