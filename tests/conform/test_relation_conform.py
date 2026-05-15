"""Cross-backend tests for Relation.conform()."""
from __future__ import annotations

import pytest
import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
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
class TestRelationConformBasic:
    def test_rename_and_cast(self, backend_name, backend_factory):
        df = backend_factory.create({"raw_id": ["1", "2", "3"]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="user_id", type=UniversalType.INTEGER, rename_from="raw_id")],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["user_id"].to_list() == [1, 2, 3]
        assert list(result.columns) == ["user_id"]

    def test_null_fill_and_cast(self, backend_name, backend_factory):
        if backend_name.startswith("ibis"):
            pytest.xfail("Ibis coalesce cannot mix column type with different literal type")
        df = backend_factory.create({"val": [1, None, 3]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER, null_fill=-1)],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1, -1, 3]

    def test_keep_only_mapped_false(self, backend_name, backend_factory):
        df = backend_factory.create({"mapped": ["a", "b"], "extra": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="mapped", type=UniversalType.STRING)],
            keep_only_mapped=False,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "mapped" in result.columns
        assert "extra" in result.columns

    def test_keep_only_mapped_true(self, backend_name, backend_factory):
        df = backend_factory.create({"keep": ["a", "b"], "drop": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="keep", type=UniversalType.STRING)],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "keep" in result.columns
        assert "drop" not in result.columns


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRelationConformComposition:
    def test_conform_then_filter(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1", "2", "3"]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER)],
            keep_only_mapped=True,
        )
        result = (
            ma.relation(df)
            .conform(spec)
            .filter(ma.col("val").gt(1))
            .to_polars()
        )
        assert result["val"].to_list() == [2, 3]

    def test_conform_then_sort(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["3", "1", "2"]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER)],
            keep_only_mapped=True,
        )
        result = (
            ma.relation(df)
            .conform(spec)
            .sort("val")
            .to_polars()
        )
        assert result["val"].to_list() == [1, 2, 3]


class TestRelationConformStructAccess:
    def test_dotted_source_name(self):
        import polars as pl

        df = pl.DataFrame([
            {"id": 1, "score": {"strain": 10.5, "kilojoule": 500.0}},
            {"id": 2, "score": {"strain": 8.2, "kilojoule": 350.0}},
        ])
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="strain", type=UniversalType.NUMBER, rename_from="score.strain"),
            ],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["strain"].to_list() == [10.5, 8.2]
        assert list(result.columns) == ["id", "strain"]


class TestRelationConformFullPipeline:
    def test_full_pipeline(self):
        import polars as pl

        df = pl.DataFrame({
            "raw_score": ["1.5", None, "3.5"],
            "raw_label": ["foo", "bar", None],
            "extra": [10, 20, 30],
        })
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


class TestRelationConformEdgeCases:
    def test_empty_spec_keep_only_mapped_true(self):
        import polars as pl

        df = pl.DataFrame({"a": [1], "b": [2]})
        spec = TypeSpec(fields=[], keep_only_mapped=True)
        result = ma.relation(df).conform(spec).to_polars()
        assert len(result.columns) == 0

    def test_empty_spec_keep_only_mapped_false(self):
        import polars as pl

        df = pl.DataFrame({"a": [1], "b": [2]})
        spec = TypeSpec(fields=[], keep_only_mapped=False)
        result = ma.relation(df).conform(spec).to_polars()
        assert set(result.columns) == {"a", "b"}

    def test_type_any_skips_cast(self):
        import polars as pl

        df = pl.DataFrame({"val": ["hello", "world"]})
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.ANY)],
            keep_only_mapped=True,
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["hello", "world"]
