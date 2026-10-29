"""Tests for Polars-compatible free function aliases."""
import mountainash.expressions as ma
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
)


class TestHorizontalAliases:
    def test_min_horizontal_is_least(self):
        canonical = ma.least(ma.col("a"), ma.col("b"))._node
        alias = ma.min_horizontal(ma.col("a"), ma.col("b"))._node
        assert canonical.function_key == alias.function_key

    def test_max_horizontal_is_greatest(self):
        canonical = ma.greatest(ma.col("a"), ma.col("b"))._node
        alias = ma.max_horizontal(ma.col("a"), ma.col("b"))._node
        assert canonical.function_key == alias.function_key

    def test_all_horizontal(self):
        expr = ma.all_horizontal(ma.col("a"), ma.col("b"))
        assert expr._node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND

    def test_any_horizontal(self):
        expr = ma.any_horizontal(ma.col("a"), ma.col("b"))
        assert expr._node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR


class TestLenAlias:
    def test_len_is_count_records(self):
        canonical = ma.count_records()._node
        alias = ma.len()._node
        assert canonical.function_key == alias.function_key
