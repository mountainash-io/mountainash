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
