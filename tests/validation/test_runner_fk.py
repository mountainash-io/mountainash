"""ForeignKeyRule execution over a RelationDAG (canonical logical keys,
MATCH SIMPLE; Task 9, spec 15.2)."""
import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG
from mountainash.validation import (
    CheckSummary,
    ForeignKeyRule,
    RowRule,
    ValidationRunner,
)


def _dag(child_rows, parent_rows):
    dag = RelationDAG()
    dag.add("customers", ma.relation(pl.DataFrame(parent_rows)))
    dag.add("orders", ma.relation(pl.DataFrame(child_rows)))
    return dag


def _fk(**overrides):
    kwargs = dict(
        id="fk__orders__customer_id__customers",
        child="orders",
        parent="customers",
        child_fields=["customer_id"],
        parent_fields=["id"],
    )
    kwargs.update(overrides)
    return ForeignKeyRule(**kwargs)


class TestForeignKeyRule:
    def test_all_resolve_passes(self):
        dag = _dag({"customer_id": [1, 2]}, {"id": [1, 2, 3]})
        result = ValidationRunner().validate_dag(dag, {"orders": [_fk()]})
        assert result.passes
        assert result.fk_result.passes

    def test_orphans_fail_with_row_structs(self):
        dag = _dag({"customer_id": [1, 99]}, {"id": [1, 2]})
        result = ValidationRunner().validate_dag(dag, {"orders": [_fk()]})
        assert not result.passes
        summary = result.fk_result.check_summaries.row(0, named=True)
        assert summary["check_kind"] == "foreign_key"
        assert summary["fail_count"] == 1
        assert summary["diagnostic"] == "1"  # orphan count
        assert result.fk_result.failure_cases["row"].dtype == pl.Struct

    def test_null_child_keys_excluded_by_default(self):
        dag = _dag({"customer_id": [1, None]}, {"id": [1]})
        result = ValidationRunner().validate_dag(dag, {"orders": [_fk()]})
        assert result.passes  # null child key is not an orphan

    def test_exclude_null_child_false_counts_nulls_as_orphans(self):
        dag = _dag({"customer_id": [1, None]}, {"id": [1]})
        result = ValidationRunner().validate_dag(
            dag, {"orders": [_fk(exclude_null_child=False)]}
        )
        assert not result.passes

    def test_composite_fk_match_simple(self):
        """Any-null component excludes the row; fully-non-null must resolve."""
        dag = RelationDAG()
        dag.add("parents", ma.relation(pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})))
        dag.add(
            "children",
            ma.relation(
                pl.DataFrame(
                    {
                        "pa": [1, 1, None, 9],
                        "pb": ["x", None, "y", "z"],
                    }
                )
            ),
        )
        fk = ForeignKeyRule(
            id="fk_comp", child="children", parent="parents",
            child_fields=["pa", "pb"], parent_fields=["a", "b"],
        )
        result = ValidationRunner().validate_dag(dag, {"children": [fk]})
        summary = result.fk_result.check_summaries.row(0, named=True)
        # (1,x) resolves; (1,NULL) and (NULL,y) excluded (MATCH SIMPLE); (9,z) orphan
        assert summary["fail_count"] == 1

    def test_intra_table_and_fk_phases_share_result_shape(self):
        dag = _dag({"customer_id": [1, -1]}, {"id": [1]})
        checks = {
            "orders": [
                RowRule(id="cid_pos", expr=ma.col("customer_id").ge(0)),
                _fk(),
            ]
        }
        result = ValidationRunner().validate_dag(dag, checks)
        assert set(result.results) == {"orders"}
        assert result.results["orders"].check_summaries["check_id"].to_list() == ["cid_pos"]
        assert result.fk_result.check_summaries["check_id"].to_list() == [
            "fk__orders__customer_id__customers"
        ]

    def test_fk_error_summaries_flow_into_fk_result(self):
        dag = _dag({"customer_id": [1]}, {"id": [1]})
        bad = CheckSummary(
            check_id="fk__orders__ghost__missing", check_kind="foreign_key",
            status="error", error="parent 'missing' not in DAG",
        )
        result = ValidationRunner().validate_dag(
            dag, {"orders": []}, fk_error_summaries=[bad]
        )
        assert not result.passes
        assert result.fk_result.check_summaries["status"].to_list() == ["error"]

    def test_fk_rule_outside_dag_context_errors_not_raises(self):
        df = pl.DataFrame({"customer_id": [1]})
        result = ValidationRunner().validate_relation(ma.relation(df), [_fk()])
        assert result.check_summaries["status"][0] == "error"
        assert "DAG" in result.check_summaries["error"][0]

    def test_no_backend_join_is_used(self, monkeypatch):
        """Task 9 step 1: every FK comparison uses canonical logical keys,
        never a backend join -- zero `Relation.join()` calls."""
        from mountainash.relations import Relation

        join_calls = 0
        original_join = Relation.join

        def counted_join(self, *args, **kwargs):
            nonlocal join_calls
            join_calls += 1
            return original_join(self, *args, **kwargs)

        monkeypatch.setattr(Relation, "join", counted_join)

        dag = _dag({"customer_id": [1, 99]}, {"id": [1, 2]})
        result = ValidationRunner().validate_dag(dag, {"orders": [_fk()]})
        assert not result.passes
        assert join_calls == 0
