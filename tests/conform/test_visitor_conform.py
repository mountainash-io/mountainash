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
        assert "extra" not in df.columns

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
