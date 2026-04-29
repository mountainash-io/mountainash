"""Tests for Polars-compatible Relation method aliases."""
import polars as pl
import mountainash as ma


class TestRelationAliases:
    def _make_relation(self):
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        return ma.relation(df)

    def test_limit_is_head(self):
        r = self._make_relation()
        assert r.limit(2).to_dicts() == r.head(2).to_dicts()

    def test_melt_is_unpivot(self):
        r = self._make_relation()
        assert r.melt(on="b", index="a").to_dicts() == r.unpivot(on="b", index="a").to_dicts()

    def test_bottom_k(self):
        r = self._make_relation()
        assert r.bottom_k(2, by="a").to_dicts() == r.top_k(2, by="a", descending=False).to_dicts()

    def test_cross_join(self):
        r1 = self._make_relation()
        r2 = ma.relation(pl.DataFrame({"c": [10, 20]}))
        assert r1.cross_join(r2).to_dicts() == r1.join(r2, how="cross").to_dicts()

    def test_first_is_head_1(self):
        r = self._make_relation()
        assert r.first().to_dicts() == r.head(1).to_dicts()

    def test_last_is_tail_1(self):
        r = self._make_relation()
        assert r.last().to_dicts() == r.tail(1).to_dicts()

    def test_remove(self):
        r = self._make_relation()
        assert r.remove(ma.col("a").gt(2)).to_dicts() == r.filter(ma.col("a").le(2)).to_dicts()
