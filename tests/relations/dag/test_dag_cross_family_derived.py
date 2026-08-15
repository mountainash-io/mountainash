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
