"""Cross-family coercion for derived/transitive DAG dependency refs (item 97).

Item 92 coerces only *bare* foreign-family refs (root is a ReadRelNode).
A *derived* ref whose own root tree contains an INLINE foreign ReadRelNode
(e.g. ma.relation(pandas_df).filter(...)) is left on the anchor pair and
raises `TypeError: <Family> backend cannot read DataFrame.` This item
materialises each ref once in its own family and coerces at resolver time.

Design: mountainash-central
2026-08-14-dag-cross-family-derived-dependency-coercion-design.md
(Revision 6, 6 GLM-5.2 adversarial review rounds -- SOUND_WITH_CONCERNS).
"""
from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.dag import RelationDAG

import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


def _pl(data: dict):
    return pl.DataFrame(data)


def _pd(data: dict):
    return pd.DataFrame(data)


class TestShapeBDerivedInlineRead:
    def test_filter_rooted_inline_pandas_read_coerces_to_polars_anchor(self):
        dag = RelationDAG()
        dag.add("a_pol", ma.relation(_pl({"id": [1, 2], "name": ["a", "b"]})))
        # Shape B: the foreign ReadRelNode(pandas) is INLINE in m_der's tree.
        dag.add(
            "m_der",
            ma.relation(_pd({"id": [2, 3], "name": ["c", "d"]})).filter(
                ma.col("id").gt(0)
            ),
        )
        dag.add("target", dag.ref("a_pol").join(dag.ref("m_der"), on="id"))

        result = dag.collect("target")  # Polars LazyFrame for a Polars anchor

        assert result.collect().to_dict(as_series=False) == {
            "id": [2],
            "name": ["b"],
            "name_right": ["c"],
        }


class TestBoundariesAndRegressions:
    def test_project_rooted_inline_pandas_read_in_union(self):
        dag = RelationDAG()
        dag.add("a_pol", ma.relation(_pl({"id": [1], "name": ["a"]})))
        dag.add(
            "m_proj",
            ma.relation(_pd({"id": [2], "name": ["c"]})).select("id", "name"),
        )
        dag.add("target", ma.concat([dag.ref("a_pol"), dag.ref("m_proj")]))
        result = dag.collect("target")
        assert sorted(result.collect().to_dict(as_series=False)["id"]) == [1, 2]

    def test_transitive_ref_chain(self):
        dag = RelationDAG()
        # Names chosen so "a_pol" sorts alphabetically before "n_sel" among
        # target's own direct refs, keeping the anchor-detection walk
        # (item 89's deterministic "first ref alphabetically") on the
        # Polars anchor -- this test targets the transitive-chain
        # materialisation path, not anchor-selection order.
        dag.add("m_raw", ma.relation(_pd({"id": [2], "name": ["c"]})).filter(ma.col("id").gt(0)))
        dag.add("n_sel", dag.ref("m_raw").select("id"))
        dag.add("a_pol", ma.relation(_pl({"id": [1, 2]})))
        dag.add("target", dag.ref("a_pol").join(dag.ref("n_sel"), on="id"))
        result = dag.collect("target")
        assert result.collect().to_dict(as_series=False)["id"] == [2]

    def test_no_leaf_ref_key_context_preserved(self):
        # A pure inline-data (SourceRelNode) ref materialises with the anchor
        # pair and is still key-assessed -- no key_context leak into the target.
        dag = RelationDAG()
        dag.add("inline", ma.relation({"id": [1]}))
        dag.add("target", dag.ref("inline").select("id"))
        result = dag.collect("target")
        assert result.collect().to_dict(as_series=False)["id"] == [1]
