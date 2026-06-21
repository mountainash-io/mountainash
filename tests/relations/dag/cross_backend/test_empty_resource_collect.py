"""Empty resource with a Table Schema collects as a typed-empty (0, N) frame."""
from __future__ import annotations

import json
import os
import tempfile

import polars as pl
import pytest

from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.datapackage import DataResource, DataPackage

CHILD = TypeSpec(
    fields=[
        FieldSpec(name="date", type=UniversalType.STRING),
        FieldSpec(name="v", type=UniversalType.INTEGER),
    ],
    primary_key=["date", "v"],
    fields_match="open",
)
PARENT = TypeSpec(
    fields=[
        FieldSpec(name="date", type=UniversalType.STRING),
        FieldSpec(name="total", type=UniversalType.INTEGER),
    ],
    primary_key=["date"],
    fields_match="open",
)


def _collect(dag, name):
    df = dag.collect(name)
    return df.collect() if hasattr(df, "collect") else df


def test_inline_empty_resource_reconstructs_schema():
    pkg = DataPackage(name="toy", resources=[
        DataResource(name="parent", type="table",
                     data=[{"date": "2026-06-19", "total": 20}], schema=PARENT),
        DataResource(name="child", type="table", data=[], schema=CHILD),
    ])
    dag = pkg.to_relation_dag()
    child = _collect(dag, "child")
    assert child.shape == (0, 2)
    assert child.columns == ["date", "v"]
    assert child.dtypes == [pl.String, pl.Int64]
    # non-empty sibling unchanged
    parent = _collect(dag, "parent")
    assert parent.shape == (1, 2)
    assert parent.columns == ["date", "total"]


def test_path_based_empty_json_reconstructs_schema():
    d = tempfile.mkdtemp()
    jp = os.path.join(d, "child.json")
    with open(jp, "w") as f:
        json.dump([], f)
    pkg = DataPackage(name="t", resources=[
        DataResource(name="child", type="table", path=jp, format="json", schema=CHILD),
    ])
    child = _collect(pkg.to_relation_dag(), "child")
    assert child.shape == (0, 2)
    assert child.columns == ["date", "v"]
    assert child.dtypes == [pl.String, pl.Int64]


def test_raw_dict_schema_via_from_descriptor():
    # table_schema is a RAW Frictionless dict, not an authored TypeSpec.
    descriptor = {
        "name": "t",
        "resources": [{
            "name": "child", "type": "table", "data": [],
            "schema": {
                "fields": [
                    {"name": "date", "type": "string"},
                    {"name": "v", "type": "integer"},
                ],
                "primaryKey": ["date", "v"],
                "fieldsMatch": "open",
            },
        }],
    }
    pkg = DataPackage.from_descriptor(descriptor)
    child = _collect(pkg.to_relation_dag(), "child")
    assert child.shape == (0, 2)
    assert child.columns == ["date", "v"]


@pytest.mark.parametrize("mode", ["exact", "equal", "subset", "partial"])
def test_strict_modes_still_raise_on_empty(mode):
    spec = TypeSpec(
        fields=[FieldSpec(name="date", type=UniversalType.STRING),
                FieldSpec(name="v", type=UniversalType.INTEGER)],
        primary_key=["date", "v"], fields_match=mode,
    )
    pkg = DataPackage(name="t", resources=[
        DataResource(name="child", type="table", data=[], schema=spec),
    ])
    with pytest.raises(Exception):
        _collect(pkg.to_relation_dag(), "child")


def test_parity_with_eager_conform():
    import mountainash as ma
    empty_typed = pl.DataFrame(schema={"date": pl.Utf8, "v": pl.Int64})
    eager = ma.relation(empty_typed).conform(CHILD).to_polars()
    eager = eager.collect() if hasattr(eager, "collect") else eager
    pkg = DataPackage(name="t", resources=[
        DataResource(name="child", type="table", data=[], schema=CHILD)])
    dag_result = _collect(pkg.to_relation_dag(), "child")
    assert dag_result.columns == eager.columns
    assert dag_result.dtypes == eager.dtypes
    assert dag_result.shape == eager.shape


# Canonical CONST_BACKEND names accepted by dag.collect(backend=...).
# These are the three relation-system-level backends (not the 7 factory sub-variants
# used by backend_factory.create()).  "polars" currently returns a SingleNodeQueryResult
# in pytest (pre-existing DAG-collect bug tracked in the 9 known failures); we test
# "narwhals" and "ibis" here to exercise the empty_from_schema reconstruction across
# all three *distinct* relation systems, and mark "polars" xfail so the suite stays
# honest — exactly as the sibling tests do for [polars].
_COLLECT_BACKENDS = [
    pytest.param("polars", marks=pytest.mark.xfail(
        reason="pre-existing: dag.collect returns SingleNodeQueryResult for polars backend",
        strict=True,
    )),
    "narwhals",
    "ibis",
]


def _columns(result) -> list[str]:
    """Return column names from a backend-native result as a sorted list.

    Handles: polars LazyFrame (.collect()), narwhals DataFrame (.columns),
    ibis expr (.execute() → pandas DataFrame).
    """
    if hasattr(result, "execute"):
        executed = result.execute()
        return sorted(executed.columns.tolist())
    if hasattr(result, "collect"):
        return sorted(result.collect().columns)
    return sorted(result.columns)


def _nrows(result) -> int:
    """Return row count from a backend-native result."""
    if hasattr(result, "execute"):
        return len(result.execute())
    if hasattr(result, "collect"):
        return result.collect().height
    return result.height if hasattr(result, "height") else len(result)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _COLLECT_BACKENDS)
def test_empty_resource_collect_cross_backend(backend_name):
    """Empty resource with a declared schema reconstructs typed-empty frame on every backend.

    Uses inline ``data=[]`` — the path that triggers
    ``apply_conform(empty_from_schema=True)`` inside the ResourceReadRelNode visitor.
    The DAG visitor is routed to the target relation system via the ``backend=`` kwarg
    on ``dag.collect()``, which accepts canonical CONST_BACKEND names (``"polars"``,
    ``"narwhals"``, ``"ibis"``).  This exercises the full schema-reconstruction code
    path for every relation-system backend without needing a pre-built backend-native
    empty frame — the frame is built from the TypeSpec, which is exactly the defect
    that Tasks 1-5 fix.
    """
    pkg = DataPackage(
        name="t",
        resources=[
            DataResource(name="child", type="table", data=[], schema=CHILD),
        ],
    )
    dag = pkg.to_relation_dag()
    result = dag.collect("child", backend=backend_name)
    assert _columns(result) == sorted(["date", "v"]), (
        f"[{backend_name}] expected columns ['date', 'v'], got {_columns(result)}"
    )
    assert _nrows(result) == 0, (
        f"[{backend_name}] expected 0 rows, got {_nrows(result)}"
    )


def test_uninspectable_columns_does_not_trigger_empty_frame():
    # available is None (no collect_schema/columns) must NOT build from schema.
    from mountainash.relations.core.unified_visitor.relation_visitor import (
        UnifiedRelationVisitor,
    )
    from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
        MountainashPolarsExtensionRelationSystem,
    )
    from mountainash.expressions.core.unified_visitor.visitor import (
        UnifiedExpressionVisitor,
    )
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.expsys_base import get_expression_system

    relation_system = MountainashPolarsExtensionRelationSystem()
    expression_system_cls = get_expression_system(CONST_BACKEND.POLARS)
    expr_visitor = UnifiedExpressionVisitor(expression_system_cls())

    class NoMetadata:
        """A native object exposing neither collect_schema nor columns."""

    visitor = UnifiedRelationVisitor(relation_system, expr_visitor)
    sentinel = NoMetadata()
    # Correct behaviour: with available=None (uninspectable), the zero-column
    # branch MUST NOT fire (trigger is `available == []`, not `is None`/falsy).
    # The call then falls through to normal conform dispatch, which operates on
    # the metadata-less sentinel and raises. A loosened trigger would instead
    # RETURN a typed-empty frame with the declared columns and NOT raise — so
    # "returned without raising" is exactly the regression this test catches.
    try:
        result = visitor.apply_conform(sentinel, CHILD, empty_from_schema=True)
    except Exception:
        return  # guard correctly did not reconstruct; fell through and raised
    pytest.fail(
        "apply_conform must not reconstruct from schema when columns are "
        f"uninspectable (available is None); it returned {result!r}, which "
        "means the zero-column trigger fired on a None (loosened from `== []`)."
    )
