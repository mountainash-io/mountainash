"""Test that apply_conform works via the shared helper."""
from __future__ import annotations

import polars as pl
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestVisitorApplyConform:
    def test_apply_conform_polars(self):
        """apply_conform on a Polars LazyFrame returns a LazyFrame with conformed schema."""
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )
        from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor
        from mountainash.expressions.core.expression_system.expsys_base import (
            get_expression_system,
        )
        from mountainash.relations.core.relation_protocols.relsys_base import (
            get_relation_system,
        )
        from mountainash.core.constants import CONST_BACKEND

        backend = CONST_BACKEND.POLARS
        rel_sys = get_relation_system(backend)()
        expr_sys = get_expression_system(backend)()
        expr_visitor = UnifiedExpressionVisitor(expr_sys)
        visitor = UnifiedRelationVisitor(rel_sys, expr_visitor)

        lf = pl.DataFrame({"raw_id": ["1", "2"], "extra": [10, 20]}).lazy()
        spec = TypeSpec(
            fields=[
                FieldSpec(name="user_id", type=UniversalType.INTEGER, rename_from="raw_id"),
            ],
        )

        result = visitor.apply_conform(lf, spec)
        assert hasattr(result, "collect")
        df = result.collect()
        assert df["user_id"].to_list() == [1, 2]
        assert "extra" in df.columns
        assert "raw_id" not in df.columns

    def test_apply_conform_from_dict(self):
        """apply_conform accepts a raw Frictionless schema dict."""
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )
        from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor
        from mountainash.expressions.core.expression_system.expsys_base import (
            get_expression_system,
        )
        from mountainash.relations.core.relation_protocols.relsys_base import (
            get_relation_system,
        )
        from mountainash.core.constants import CONST_BACKEND

        backend = CONST_BACKEND.POLARS
        rel_sys = get_relation_system(backend)()
        expr_sys = get_expression_system(backend)()
        expr_visitor = UnifiedExpressionVisitor(expr_sys)
        visitor = UnifiedRelationVisitor(rel_sys, expr_visitor)

        lf = pl.DataFrame({"raw_id": ["1", "2"]}).lazy()
        schema_dict = {
            "fields": [
                {"name": "user_id", "type": "integer", "x-mountainash": {"rename_from": "raw_id"}},
            ],
        }

        result = visitor.apply_conform(lf, schema_dict)
        df = result.collect()
        assert df["user_id"].to_list() == [1, 2]


def _make_visitor():
    from mountainash.relations.core.unified_visitor.relation_visitor import (
        UnifiedRelationVisitor,
    )
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor
    from mountainash.expressions.core.expression_system.expsys_base import (
        get_expression_system,
    )
    from mountainash.relations.core.relation_protocols.relsys_base import (
        get_relation_system,
    )
    from mountainash.core.constants import CONST_BACKEND

    backend = CONST_BACKEND.POLARS
    rel_sys = get_relation_system(backend)()
    expr_sys = get_expression_system(backend)()
    expr_visitor = UnifiedExpressionVisitor(expr_sys)
    return UnifiedRelationVisitor(rel_sys, expr_visitor)


class TestVisitorDriftReports:
    """item 48 Task 7: visitor.drift_reports accumulation."""

    def test_drift_reports_starts_empty(self):
        visitor = _make_visitor()
        assert visitor.drift_reports == []

    def test_drift_reports_accumulates_in_traversal_order(self):
        """Sequential apply_conform() calls on one visitor append in order,
        each with a deterministic node_id derived from the running count."""
        visitor = _make_visitor()
        spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])

        lf1 = pl.DataFrame({"n": ["1", "2"]}).lazy()
        visitor.apply_conform(lf1, spec).collect()
        assert len(visitor.drift_reports) == 1
        assert visitor.drift_reports[0].node_id == "conform:0"

        lf2 = pl.DataFrame({"n": ["3", "4"]}).lazy()
        visitor.apply_conform(lf2, spec).collect()
        assert len(visitor.drift_reports) == 2
        assert visitor.drift_reports[1].node_id == "conform:1"

    def test_drift_report_carries_resource_name_when_supplied(self):
        visitor = _make_visitor()
        spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])
        lf = pl.DataFrame({"n": ["1", "2"]}).lazy()

        visitor.apply_conform(lf, spec, resource_name="orders").collect()

        assert len(visitor.drift_reports) == 1
        assert visitor.drift_reports[0].resource_name == "orders"

    def test_drift_report_resource_name_none_by_default(self):
        """A bare Relation.conform() call (no resource context) leaves
        resource_name None -- matches apply_conform's default param."""
        visitor = _make_visitor()
        spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])
        lf = pl.DataFrame({"n": ["1", "2"]}).lazy()

        visitor.apply_conform(lf, spec).collect()

        assert visitor.drift_reports[0].resource_name is None
