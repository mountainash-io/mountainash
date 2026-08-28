"""Structured (ARRAY/OBJECT) foreign keys (Task 9, spec 15.2).

Every foreign-key comparison uses `canonical_value_key()` over each side's
prepared logical snapshot, never a backend join -- a JSON-text/opaque
carrier's raw physical bytes cannot define logical equality (whitespace,
object-name order differ between structurally-equal values). Scalar-key
mechanics (MATCH SIMPLE, orphan reporting, error isolation) are covered by
test_runner_fk.py; this file covers the structured-value-specific contract.
"""
from __future__ import annotations

import polars as pl

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation import ForeignKeyRule, ValidationRunner


def _structured_dag(
    *, child_rows: dict, parent_rows: dict, child_action: str = "coerce",
    parent_action: str = "coerce",
):
    dag = RelationDAG()

    def _fields(rows: dict) -> list[FieldSpec]:
        fields = []
        for name, values in rows.items():
            sample = next((v for v in values if v is not None), None)
            if isinstance(sample, str) and name.startswith("meta"):
                fields.append(FieldSpec(name=name, type=UniversalType.OBJECT))
            elif isinstance(sample, str) and name.startswith("tags"):
                fields.append(FieldSpec(name=name, type=UniversalType.ARRAY))
            else:
                fields.append(FieldSpec(name=name, type=UniversalType.INTEGER))
        return fields

    parent_spec = TypeSpec(fields_match="open", fields=_fields(parent_rows))
    child_spec = TypeSpec(fields_match="open", fields=_fields(child_rows))
    parent_rel = ma.relation(pl.DataFrame(parent_rows)).conform(
        parent_spec, contract={"data_type": parent_action}
    )
    child_rel = ma.relation(pl.DataFrame(child_rows)).conform(
        child_spec, contract={"data_type": child_action}
    )
    dag.add("parents", parent_rel)
    dag.add("children", child_rel)
    return dag


def _fk(*, child_fields, parent_fields, exclude_null_child=True):
    return ForeignKeyRule(
        id="fk__children__structured__parents",
        child="children",
        parent="parents",
        child_fields=child_fields,
        parent_fields=parent_fields,
        exclude_null_child=exclude_null_child,
    )


class TestObjectKeys:
    def test_object_key_ignores_whitespace_and_name_order(self):
        dag = _structured_dag(
            parent_rows={"meta": ['{"a":1,"b":2}']},
            child_rows={"meta": ['{ "b" : 2 , "a" : 1 }']},
        )
        result = ValidationRunner().validate_dag(
            dag, {"children": [_fk(child_fields=["meta"], parent_fields=["meta"])]}
        )
        assert result.fk_result.passes

    def test_object_key_structurally_different_is_an_orphan(self):
        dag = _structured_dag(
            parent_rows={"meta": ['{"a":1}']},
            child_rows={"meta": ['{"a":2}']},
        )
        result = ValidationRunner().validate_dag(
            dag, {"children": [_fk(child_fields=["meta"], parent_fields=["meta"])]}
        )
        assert not result.fk_result.passes
        summary = result.fk_result.check_summaries.row(0, named=True)
        assert summary["fail_count"] == 1


class TestArrayKeys:
    def test_array_key_matches_on_element_order(self):
        dag = _structured_dag(
            parent_rows={"tags": ["[1,2]"]},
            child_rows={"tags": ["[1, 2]"]},
        )
        result = ValidationRunner().validate_dag(
            dag, {"children": [_fk(child_fields=["tags"], parent_fields=["tags"])]}
        )
        assert result.fk_result.passes

    def test_array_key_different_order_is_an_orphan(self):
        dag = _structured_dag(
            parent_rows={"tags": ["[1,2]"]},
            child_rows={"tags": ["[2,1]"]},
        )
        result = ValidationRunner().validate_dag(
            dag, {"children": [_fk(child_fields=["tags"], parent_fields=["tags"])]}
        )
        assert not result.fk_result.passes


class TestMixedCompositeKeys:
    def test_composite_key_mixes_scalar_and_structured_fields(self):
        dag = _structured_dag(
            parent_rows={"id": [1, 2], "meta": ['{"a":1}', '{"a":2}']},
            child_rows={"id": [1, 1], "meta": ['{"a": 1}', '{"a":9}']},
        )
        result = ValidationRunner().validate_dag(
            dag,
            {
                "children": [
                    _fk(child_fields=["id", "meta"], parent_fields=["id", "meta"])
                ]
            },
        )
        summary = result.fk_result.check_summaries.row(0, named=True)
        # row 0: (1, {"a":1}) matches (whitespace-insensitive); row 1: (1, {"a":9}) orphan.
        assert summary["fail_count"] == 1


class TestNullAndInvalidComponents:
    def test_any_null_component_excludes_the_child_row_under_match_simple(self):
        dag = _structured_dag(
            parent_rows={"id": [1], "meta": ['{"a":1}']},
            child_rows={"id": [1, None], "meta": ['{"a":1}', '{"a":1}']},
        )
        result = ValidationRunner().validate_dag(
            dag,
            {
                "children": [
                    _fk(child_fields=["id", "meta"], parent_fields=["id", "meta"])
                ]
            },
        )
        assert result.fk_result.passes

    def test_invalid_child_component_is_unknown_not_a_failure(self):
        dag = _structured_dag(
            parent_rows={"meta": ['{"a":1}']},
            child_rows={"meta": ["{broken"]},
        )
        result = ValidationRunner().validate_dag(
            dag, {"children": [_fk(child_fields=["meta"], parent_fields=["meta"])]}
        )
        summary = result.fk_result.check_summaries.row(0, named=True)
        assert summary["fail_count"] == 0
        assert summary["unknown_count"] == 1
        assert result.fk_result.passes

    def test_invalid_parent_component_never_creates_a_target_key(self):
        """An invalid parent value can never legitimize a child match --
        a child whose key happens to canonicalize the same way as the
        parent's raw (unparseable) text is still an orphan."""
        dag = _structured_dag(
            parent_rows={"meta": ["{broken"]},
            child_rows={"meta": ['{"a":1}']},
        )
        result = ValidationRunner().validate_dag(
            dag, {"children": [_fk(child_fields=["meta"], parent_fields=["meta"])]}
        )
        assert not result.fk_result.passes
        summary = result.fk_result.check_summaries.row(0, named=True)
        assert summary["fail_count"] == 1


class TestDiscardRowExclusion:
    def test_discard_row_children_never_enter_fk_evaluation(self):
        dag = _structured_dag(
            parent_rows={"meta": ['{"a":1}']},
            child_rows={"meta": ['{"a":1}', "{broken", '{"a":9}']},
            child_action="discard_row",
        )
        result = ValidationRunner().validate_dag(
            dag, {"children": [_fk(child_fields=["meta"], parent_fields=["meta"])]}
        )
        summary = result.fk_result.check_summaries.row(0, named=True)
        # The malformed middle row is discarded before FK evaluation runs:
        # only 2 rows are ever evaluated (matches + 1 genuine orphan).
        assert summary["total_rows"] == 2
        assert summary["fail_count"] == 1


class TestDeterministicFailureRows:
    def test_failure_rows_are_deterministic_and_carry_the_orphan_ordinal(self):
        dag = _structured_dag(
            parent_rows={"meta": ['{"a":1}']},
            child_rows={"meta": ['{"a":1}', '{"a":2}', '{"a":3}']},
        )
        result = ValidationRunner().validate_dag(
            dag, {"children": [_fk(child_fields=["meta"], parent_fields=["meta"])]}
        )
        summary = result.fk_result.check_summaries.row(0, named=True)
        assert summary["fail_count"] == 2
        assert result.fk_result.failure_cases.height == 2
        assert result.fk_result.failure_cases["row"].dtype == pl.Struct
