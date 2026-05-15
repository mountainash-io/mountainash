"""Cross-backend parametrized tests for Relation.conform()."""
from __future__ import annotations

import pytest
import mountainash as ma

from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.typespec.universal_types import UniversalType


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformCast:
    def test_cast_string_to_integer(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1", "2", "3"]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER)],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1, 2, 3]

    def test_cast_string_to_number(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1.5", "2.5", "3.5"]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.NUMBER)],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1.5, 2.5, 3.5]

    def test_cast_string_to_string(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["hello", "world"]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.STRING)],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["hello", "world"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformRename:
    def test_rename_column(self, backend_name, backend_factory):
        df = backend_factory.create({"old_name": ["a", "b", "c"]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="new_name", type=UniversalType.STRING, rename_from="old_name")],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["new_name"].to_list() == ["a", "b", "c"]

    def test_rename_preserves_other_columns(self, backend_name, backend_factory):
        df = backend_factory.create({"old": ["a", "b"], "keep": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="new", type=UniversalType.STRING, rename_from="old")],
            keep_only_mapped=False,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "new" in result.columns
        assert "keep" in result.columns
        assert "old" not in result.columns


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformNullFill:
    def test_null_fill_integer(self, backend_name, backend_factory):
        df = backend_factory.create({"val": [1, None, 3]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER, null_fill=-1)],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1, -1, 3]

    def test_null_fill_string(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["x", None, "z"]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.STRING, null_fill="unknown")],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["x", "unknown", "z"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformKeepOnlyMapped:
    def test_keep_only_mapped_drops_extra(self, backend_name, backend_factory):
        df = backend_factory.create({"keep": ["a", "b"], "drop": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="keep", type=UniversalType.STRING)],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "keep" in result.columns
        assert "drop" not in result.columns

    def test_keep_only_mapped_false_preserves_extra(self, backend_name, backend_factory):
        df = backend_factory.create({"mapped": ["a", "b"], "extra": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="mapped", type=UniversalType.STRING)],
            keep_only_mapped=False,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "mapped" in result.columns
        assert "extra" in result.columns


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformMultiTransform:
    def test_cast_and_rename(self, backend_name, backend_factory):
        df = backend_factory.create({"raw_id": ["1", "2", "3"]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="user_id", type=UniversalType.INTEGER, rename_from="raw_id")],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["user_id"].to_list() == [1, 2, 3]

    def test_full_pipeline(self, backend_name, backend_factory):
        if backend_name.startswith("ibis"):
            pytest.xfail("Ibis coalesce cannot mix string column with numeric literal fill")
        df = backend_factory.create({
            "raw_score": ["1.5", None, "3.5"],
            "raw_label": ["foo", "bar", None],
            "extra": [10, 20, 30],
        }, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="score", type=UniversalType.NUMBER, rename_from="raw_score", null_fill=0.0),
                FieldSpec(name="label", type=UniversalType.STRING, rename_from="raw_label", null_fill="n/a"),
            ],
            keep_only_mapped=False,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["score"].to_list() == [1.5, 0.0, 3.5]
        assert result["label"].to_list() == ["foo", "bar", "n/a"]
        assert "extra" in result.columns


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformFromFrictionless:
    def test_from_frictionless_dict(self, backend_name, backend_factory):
        df = backend_factory.create({"raw_id": ["1", "2"]}, backend_name)
        frictionless_data = {
            "fields": [
                {"name": "user_id", "type": "integer", "x-mountainash": {"rename_from": "raw_id"}},
            ],
            "x-mountainash": {"keep_only_mapped": True},
        }
        spec = TypeSpec.from_frictionless(frictionless_data)
        result = ma.relation(df).conform(spec).to_polars()
        assert result["user_id"].to_list() == [1, 2]
