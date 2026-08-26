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
from mountainash.relations.dag.validation import DAGValidationResult
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.exceptions import InvalidTypeSpecSemantics


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
        assert "users" in result.results
        assert result.results["users"].passes is True

    def test_invalid_data_fails(self):
        dag = _build_dag({"users": pl.DataFrame({"age": [-1, 5]})})
        spec = TypeSpec(fields=[
            FieldSpec(name="age", type=UniversalType.INTEGER, constraints=FieldConstraints(minimum=0)),
        ])
        result = dag.validate(specs={"users": spec})
        assert result.passes is False
        assert result.results["users"].passes is False

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


class TestDerivedRelationValidation:
    def test_validate_resolves_ref_relations_through_dag(self):
        dag = RelationDAG()
        dag.add(
            "raw",
            ma.relation(pl.DataFrame({"id": [1, 2], "age": [10, 20]})),
        )
        dag.add("adults", dag.ref("raw").filter(ma.col("age").ge(18)))

        spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(
                name="age",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(minimum=18),
            ),
        ])

        result = dag.validate(specs={"adults": spec})

        assert result.passes is True
        assert "adults" in result.results

    def test_validate_quick_resolves_ref_relations_through_dag(self):
        dag = RelationDAG()
        dag.add(
            "raw",
            ma.relation(pl.DataFrame({"id": [1, 2], "age": [10, 20]})),
        )
        dag.add("adults", dag.ref("raw").filter(ma.col("age").ge(18)))

        spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(
                name="age",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(minimum=18),
            ),
        ])

        result = dag.validate_quick(specs={"adults": spec})

        assert result.passes is True
        assert "adults" in result.results

    def test_dependency_edges_do_not_create_fk_checks(self):
        dag = RelationDAG()
        dag.add("parents", ma.relation(pl.DataFrame({"id": [1]})))
        dag.add("children", dag.ref("parents").select(ma.col("id").alias("parent_id")))

        child_spec = TypeSpec(fields=[
            FieldSpec(name="parent_id", type=UniversalType.INTEGER),
        ])

        result = dag.validate(specs={"children": child_spec})

        assert result.passes is True
        assert result.fk_result.passes is True
        assert result.fk_result.check_summaries.height == 0

    def test_constraint_edges_without_typespec_foreign_keys_do_not_create_fk_checks(self):
        dag = RelationDAG()
        dag.add("parents", ma.relation(pl.DataFrame({"id": [1]})))
        dag.add("children", ma.relation(pl.DataFrame({"parent_id": [99]})))
        dag.constraint_edges.add(("parents", "children"))

        parent_spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
        ])
        child_spec = TypeSpec(fields=[
            FieldSpec(name="parent_id", type=UniversalType.INTEGER),
        ])

        result = dag.validate(specs={"parents": parent_spec, "children": child_spec})

        assert result.passes is True
        assert result.fk_result.passes is True
        assert result.fk_result.check_summaries.height == 0


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
        assert result.fk_result.passes is True
        assert result.fk_result.check_summaries.height == 1
        assert result.fk_result.check_summaries.row(0, named=True)["status"] == "passed"

    def test_fk_uses_conformed_resource_columns(self):
        """FKs run against each resource's logical post-conform schema."""
        dag = _build_dag(
            {
                "customers": pl.DataFrame({"customer_key": ["1"]}),
                "orders": pl.DataFrame({"order_customer_key": ["1"]}),
            }
        )
        dag.constraint_edges.add(("customers", "orders"))
        customer_spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="id",
                    type=UniversalType.INTEGER,
                    rename_from="customer_key",
                )
            ]
        )
        order_spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="customer_id",
                    type=UniversalType.INTEGER,
                    rename_from="order_customer_key",
                )
            ],
            foreign_keys=[
                ForeignKey(
                    fields=["customer_id"],
                    reference=ForeignKeyReference(resource="customers", fields=["id"]),
                )
            ],
        )

        result = dag.validate(specs={"customers": customer_spec, "orders": order_spec})

        assert result.passes is True
        assert result.fk_result.passes is True
        assert result.fk_result.check_summaries.row(0, named=True)["status"] == "passed"

    def test_orphan_fk_fails(self):
        dag = self._make_fk_dag(orphans=True)
        specs = self._make_specs()
        result = dag.validate(specs=specs)
        assert result.passes is False
        assert result.fk_result.passes is False
        fk_summary = result.fk_result.check_summaries.row(0, named=True)
        assert fk_summary["check_kind"] == "foreign_key"
        assert fk_summary["check_id"] == "fk__orders__customer_id__customers"
        assert fk_summary["fail_count"] == 1
        orphan_rows = result.fk_result.failure_cases["row"].struct.unnest()
        assert 99 in orphan_rows["customer_id"].to_list()

    def test_null_fk_excluded_from_check(self):
        dag = self._make_fk_dag(nulls=True)
        specs = self._make_specs()
        result = dag.validate(specs=specs)
        assert result.passes is True
        assert result.fk_result.passes is True
        assert result.fk_result.check_summaries.row(0, named=True)["fail_count"] == 0

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
        assert result.fk_result.passes is False
        fk_summary = result.fk_result.check_summaries.row(0, named=True)
        assert fk_summary["check_id"] == "fk__children__parent_id__parents"
        assert fk_summary["fail_count"] == 1

    def test_fk_evaluated_when_parent_not_in_specs(self):
        """Behaviour change (closed-by-default): the FK parent resource is
        resolved against the DAG's relations, not the caller's `specs` dict —
        so a parent omitted from `specs` no longer causes the FK check to be
        silently skipped. The orphan is still detected and surfaces as a
        real failure (not merely a status="error" placeholder, since the
        parent relation itself is fully resolvable in the DAG)."""
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
        assert result.passes is False
        assert result.fk_result.passes is False
        fk_summary = result.fk_result.check_summaries.row(0, named=True)
        assert fk_summary["check_id"] == "fk__children__parent_id__parents"
        assert fk_summary["status"] == "failed"
        assert fk_summary["fail_count"] == 1


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
        assert result.fk_result.passes is True
        assert result.fk_result.check_summaries.height == 0

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
        assert result.fk_result.passes is False
        fk_summary = result.fk_result.check_summaries.row(0, named=True)
        assert fk_summary["check_id"] == "fk__c__pid__p"
        assert fk_summary["fail_count"] == 1


class TestIdentityIsolation:
    def _dup_pk_dag(self):
        return _build_dag({"users": pl.DataFrame({"id": [1, 1], "age": [30, 40]})})

    @pytest.mark.parametrize("spec_kind", ["typespec", "primary_key_contract", "natural_key_contract"])
    def test_allow_imperfect_key_reports_primary_key_unique(self, spec_kind):
        dag = self._dup_pk_dag()
        if spec_kind == "typespec":
            spec = TypeSpec(
                fields=[FieldSpec(name="id", type=UniversalType.INTEGER),
                        FieldSpec(name="age", type=UniversalType.INTEGER)],
                primary_key=["id"],
            )
        elif spec_kind == "primary_key_contract":
            class C(BaseDataContract):
                id: int
                age: int
                class Config:
                    primary_key = ["id"]
            spec = C
        else:
            class C(BaseDataContract):
                id: int
                age: int
                class Config:
                    natural_key = ["id"]
            spec = C

        result = dag.validate(specs={"users": spec}, allow_imperfect_key=True)
        assert result.passes is False
        failing = set(
            result.results["users"].check_summaries.filter(
                result.results["users"].check_summaries["status"] != "passed"
            )["check_id"].to_list()
        )
        assert "primary_key_unique" in failing

    def test_default_isolates_identity_failure_no_exception(self):
        dag = self._dup_pk_dag()
        dag.add("other", ma.relation(pl.DataFrame({"name": ["ok"]})))
        spec_users = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER),
                    FieldSpec(name="age", type=UniversalType.INTEGER)],
            primary_key=["id"],
        )
        spec_other = TypeSpec(fields=[FieldSpec(name="name", type=UniversalType.STRING)])

        result = dag.validate(specs={"users": spec_users, "other": spec_other})  # no allow_imperfect_key

        assert result.passes is False
        users_summary = result.results["users"].check_summaries.row(0, named=True)
        assert users_summary["check_id"] == "__identity__"
        assert users_summary["status"] == "error"
        assert result.results["other"].passes is True

    @pytest.mark.parametrize("order", [("users", "other"), ("other", "users")])
    def test_quick_fail_fast_ordering(self, order):
        dag = self._dup_pk_dag()
        dag.add("other", ma.relation(pl.DataFrame({"name": ["ok"]})))
        spec_users = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER),
                    FieldSpec(name="age", type=UniversalType.INTEGER)],
            primary_key=["id"],
        )
        spec_other = TypeSpec(fields=[FieldSpec(name="name", type=UniversalType.STRING)])
        specs = {order[0]: (spec_users if order[0] == "users" else spec_other),
                 order[1]: (spec_users if order[1] == "users" else spec_other)}

        result = dag.validate_quick(specs=specs)

        assert result.passes is False
        assert "users" in result.results
        if order == ("users", "other"):
            assert "other" not in result.results  # stopped before the second resource ran
        else:
            assert result.results["other"].passes is True  # ran and reported before the stop

    def test_single_resource_dict_does_not_raise(self):
        dag = self._dup_pk_dag()
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER),
                    FieldSpec(name="age", type=UniversalType.INTEGER)],
            primary_key=["id"],
        )
        result = dag.validate(specs={"users": spec})  # must not raise
        assert result.passes is False

    def test_missing_declared_key_field_fails_before_dag_execution(self):
        """A key naming no TypeSpec field is a declaration error, not bad data."""
        dag = _build_dag({"users": pl.DataFrame({"age": [30, 40]})})
        spec = TypeSpec(
            fields=[FieldSpec(name="age", type=UniversalType.INTEGER)],
            primary_key=["id"],
        )

        with pytest.raises(InvalidTypeSpecSemantics) as caught:
            dag.validate(specs={"users": spec}, allow_imperfect_key=True)

        assert tuple((issue.path, issue.code) for issue in caught.value.issues) == (
            ("/primary_key/0", "typespec.invalid_constraint_declaration"),
        )