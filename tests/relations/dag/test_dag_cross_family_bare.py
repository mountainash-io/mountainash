"""Cross-family coercion for bare DAG dependency refs (item 92)."""
from __future__ import annotations

import pandas as pd
import polars as pl

import mountainash as ma
from mountainash.relations.dag import RelationDAG

import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


class TestBareForeignDependencyCoercion:
    def test_polars_anchor_joins_bare_pandas_dependency(self):
        dag = RelationDAG()
        dag.add("a_anchor", ma.relation(pl.DataFrame({"id": [1, 2], "name": ["a", "b"]})))
        dag.add("z_dep", ma.relation(pd.DataFrame({"id": [2, 3], "name": ["c", "d"]})))
        dag.add("target", dag.ref("a_anchor").join(dag.ref("z_dep"), on="id"))

        result = dag.collect("target")

        assert result.collect().to_dict(as_series=False) == {
            "id": [2],
            "name": ["b"],
            "name_right": ["c"],
        }

class TestCoercionMatrixAndBoundaries:
    def test_ibis_anchor_coerces_bare_pandas_dependency(self):
        import ibis

        ib = ibis.memtable(pl.DataFrame({"id": [1, 2], "name": ["a", "b"]}))
        dag = RelationDAG()
        dag.add("a_anchor", ma.relation(ib))
        dag.add("z_dep", ma.relation(pd.DataFrame({"id": [2], "name": ["c"]})))
        dag.add("target", dag.ref("a_anchor").join(dag.ref("z_dep"), on="id"))
        result = dag.collect("target")
        assert result is not None

    def test_narwhals_anchor_coerces_bare_polars_dependency_to_exact_dialect(self):
        import narwhals as nw

        nw_pd = nw.from_native(pd.DataFrame({"id": [1, 2]}), eager_only=True)
        dag = RelationDAG()
        dag.add("a_anchor", ma.relation(nw_pd))  # narwhals-pandas
        dag.add("z_dep", ma.relation(pl.DataFrame({"id": [2]})))
        dag.add("target", dag.ref("a_anchor").join(dag.ref("z_dep"), on="id"))
        result = dag.collect("target")
        assert result is not None

    def test_derived_foreign_dependency_is_coerced(self):
        # Item 97 inverts this item-92 boundary: a FilterRelNode-rooted
        # foreign dependency is now materialised in its own family and
        # coerced at resolver time, rather than raising from the anchor's
        # read().
        dag = RelationDAG()
        dag.add("a_anchor", ma.relation(pl.DataFrame({"id": [1, 2]})))
        dag.add("z_dep", ma.relation(pd.DataFrame({"id": [2]})).filter(ma.col("id") > 0))
        dag.add("target", dag.ref("a_anchor").join(dag.ref("z_dep"), on="id"))
        result = dag.collect("target")
        assert result.collect().to_dict(as_series=False) == {"id": [2]}
