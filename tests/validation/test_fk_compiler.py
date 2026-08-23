"""build_fk_checks: canonicalisation, dedup, validation, error summaries."""
import polars as pl

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG
from mountainash.typespec.spec import ForeignKey, ForeignKeyReference, TypeSpec, FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.fk import build_fk_checks


def _dag():
    dag = RelationDAG()
    dag.add("customers", ma.relation(pl.DataFrame({"id": [1]})))
    dag.add("orders", ma.relation(pl.DataFrame({"customer_id": [1]})))
    # derived relation so add_constraint() is legal (pass-through resources reject it)
    dag.add("orders_clean", dag.ref("orders").filter(ma.col("customer_id").is_not_null()))
    return dag


def _fk(child_field="customer_id", parent="customers", parent_field="id"):
    return ForeignKey(
        fields=[child_field],
        reference=ForeignKeyReference(resource=parent, fields=[parent_field]),
    )


def test_metadata_fk_becomes_rule():
    dag = _dag()
    dag.add_constraint("orders_clean", _fk())
    rules, errors = build_fk_checks(dag)
    assert errors == []
    assert len(rules) == 1
    assert rules[0].child == "orders_clean"
    assert rules[0].parent == "customers"
    assert rules[0].child_fields == ["customer_id"]


def test_spec_fk_union_and_dedup():
    dag = _dag()
    dag.add_constraint("orders_clean", _fk())
    spec = TypeSpec(
        fields=[FieldSpec(name="customer_id", type=UniversalType.ANY)],
        foreign_keys=[_fk()],  # duplicate of the metadata declaration
    )
    rules, errors = build_fk_checks(dag, {"orders_clean": spec})
    assert len(rules) == 1  # deduplicated on (child, parent, child_fields, parent_fields)
    assert errors == []


def test_spec_only_fk_is_emitted():
    dag = _dag()
    spec = TypeSpec(fields=[], foreign_keys=[_fk()])
    rules, errors = build_fk_checks(dag, {"orders": spec})
    assert len(rules) == 1
    assert rules[0].child == "orders"


def test_unresolvable_parent_is_error_summary_not_skip():
    dag = _dag()
    spec = TypeSpec(fields=[], foreign_keys=[_fk(parent="warehouse")])
    rules, errors = build_fk_checks(dag, {"orders": spec})
    assert rules == []
    assert len(errors) == 1
    assert errors[0].status == "error"
    assert "warehouse" in errors[0].error


def test_arity_mismatch_is_error_summary():
    dag = _dag()
    fk = ForeignKey(
        fields=["customer_id", "extra"],
        reference=ForeignKeyReference(resource="customers", fields=["id"]),
    )
    spec = TypeSpec(fields=[], foreign_keys=[fk])
    rules, errors = build_fk_checks(dag, {"orders": spec})
    assert rules == []
    assert len(errors) == 1
    assert "arity" in errors[0].error


def test_missing_field_is_error_summary():
    dag = _dag()
    spec = TypeSpec(fields=[], foreign_keys=[_fk(child_field="ghost")])
    rules, errors = build_fk_checks(dag, {"orders": spec})
    assert rules == []
    assert len(errors) == 1
    assert "ghost" in errors[0].error


def test_self_reference_normalises_to_child():
    dag = RelationDAG()
    dag.add("employees", ma.relation(pl.DataFrame({"id": [1], "manager_id": [1]})))
    fk = ForeignKey(fields=["manager_id"], reference=ForeignKeyReference(resource=None, fields=["id"]))
    spec = TypeSpec(fields=[], foreign_keys=[fk])
    rules, errors = build_fk_checks(dag, {"employees": spec})
    assert errors == []
    assert rules[0].parent == "employees"


def test_spec_fields_validate_without_schema_inference(monkeypatch):
    # Spec-declared fields are evidence in their own right: a missing FK field
    # must surface as an error summary even when DAG schema inference is
    # unavailable (never silently deferred when evidence exists).
    dag = _dag()
    monkeypatch.setattr(
        type(dag), "schema",
        lambda self, name: (_ for _ in ()).throw(RuntimeError("inference unavailable")),
    )
    spec = TypeSpec(
        fields=[FieldSpec(name="customer_id", type=UniversalType.ANY)],  # declares fields; "ghost" absent
        foreign_keys=[_fk(child_field="ghost")],
    )
    rules, errors = build_fk_checks(dag, {"orders": spec})
    assert rules == []
    assert len(errors) == 1
    assert "ghost" in errors[0].error


def test_no_evidence_defers_to_execution(monkeypatch):
    # Neither spec fields nor schema inference available: the declaration is
    # emitted and the missing column fails at execution inside the runner's
    # isolation guard (status="error") — deferred, never silently dropped.
    dag = _dag()
    monkeypatch.setattr(
        type(dag), "schema",
        lambda self, name: (_ for _ in ()).throw(RuntimeError("inference unavailable")),
    )
    spec = TypeSpec(fields=[], foreign_keys=[_fk(child_field="ghost")])
    rules, errors = build_fk_checks(dag, {"orders": spec})
    assert errors == []
    assert len(rules) == 1  # execution-time guard owns the failure
