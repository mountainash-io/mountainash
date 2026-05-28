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
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1, -1, 3]

    def test_conform_produces_only_spec_fields(self, backend_name, backend_factory):
        df = backend_factory.create({"keep": ["a", "b"], "drop": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="keep", type=UniversalType.STRING)],
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
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["score"].to_list() == [1.5, 0.0, 3.5]
        assert result["label"].to_list() == ["foo", "bar", "n/a"]
        assert "extra" not in result.columns


class TestRelationConformEdgeCases:
    def test_empty_spec_produces_no_columns(self):
        import polars as pl

        df = pl.DataFrame({"a": [1], "b": [2]})
        spec = TypeSpec(fields=[])
        result = ma.relation(df).conform(spec).to_polars()
        assert len(result.columns) == 0

    def test_type_any_skips_cast(self):
        import polars as pl

        df = pl.DataFrame({"val": ["hello", "world"]})
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.ANY)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["hello", "world"]


class TestRelationConformMissingColumns:
    """Tests for conform with available_columns — skipping missing source columns."""

    def test_available_columns_skips_missing(self):
        import polars as pl

        df = pl.DataFrame({"keep": [1, 2], "extra": [10, 20]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="keep", type=UniversalType.INTEGER),
                FieldSpec(name="gone", type=UniversalType.STRING),
            ],
        )
        result = ma.relation(df).conform(
            spec, available_columns={"keep", "extra"},
        ).to_polars()
        assert list(result.columns) == ["keep"]
        assert result["keep"].to_list() == [1, 2]

    def test_available_columns_skips_missing_rename_from(self):
        import polars as pl

        df = pl.DataFrame({"raw_id": ["1", "2"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw_id"),
                FieldSpec(name="duration", type=UniversalType.NUMBER, rename_from="stress_duration"),
            ],
        )
        result = ma.relation(df).conform(
            spec, available_columns={"raw_id"},
        ).to_polars()
        assert list(result.columns) == ["id"]
        assert result["id"].to_list() == [1, 2]

    def test_available_columns_skips_dotted_source(self):
        import polars as pl

        df = pl.DataFrame({"id": [1, 2]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="strain", type=UniversalType.NUMBER, rename_from="score.strain"),
            ],
        )
        result = ma.relation(df).conform(
            spec, available_columns={"id"},
        ).to_polars()
        assert list(result.columns) == ["id"]

    def test_available_columns_none_is_strict(self):
        """Without available_columns, missing columns still raise."""
        import polars as pl

        df = pl.DataFrame({"a": [1]})
        spec = TypeSpec(
            fields=[FieldSpec(name="missing", type=UniversalType.STRING)],
        )
        with pytest.raises(Exception):
            ma.relation(df).conform(spec).to_polars()

    def test_all_columns_missing_produces_empty(self):
        import polars as pl

        df = pl.DataFrame({"a": [1, 2]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="x", type=UniversalType.INTEGER),
                FieldSpec(name="y", type=UniversalType.STRING),
            ],
        )
        result = ma.relation(df).conform(
            spec, available_columns={"a"},
        ).to_polars()
        assert len(result.columns) == 0


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRelationConformKeepUnmapped:
    """Tests for keep_unmapped=True — preserving columns not in the TypeSpec."""

    def test_unmapped_columns_preserved(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"raw_id": ["1", "2"], "extra": [10, 20]}, backend_name,
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw_id")],
        )
        result = ma.relation(df).conform(spec, keep_unmapped=True).to_polars()
        assert "id" in result.columns
        assert "extra" in result.columns
        assert "raw_id" not in result.columns
        assert result["id"].to_list() == [1, 2]
        assert result["extra"].to_list() == [10, 20]

    def test_keep_unmapped_false_drops_extra(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"raw_id": ["1", "2"], "extra": [10, 20]}, backend_name,
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw_id")],
        )
        result = ma.relation(df).conform(spec, keep_unmapped=False).to_polars()
        assert list(result.columns) == ["id"]

    def test_same_name_field_overwrites_in_place(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"val": ["1", "2"], "other": ["a", "b"]}, backend_name,
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER)],
        )
        result = ma.relation(df).conform(spec, keep_unmapped=True).to_polars()
        assert result["val"].to_list() == [1, 2]
        assert result["other"].to_list() == ["a", "b"]

    def test_null_fill_with_keep_unmapped(self, backend_name, backend_factory):
        if backend_name.startswith("ibis"):
            pytest.xfail("Ibis coalesce cannot mix column type with different literal type")
        df = backend_factory.create(
            {"val": [1, None, 3], "tag": ["a", "b", "c"]}, backend_name,
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER, null_fill=-1)],
        )
        result = ma.relation(df).conform(spec, keep_unmapped=True).to_polars()
        assert result["val"].to_list() == [1, -1, 3]
        assert result["tag"].to_list() == ["a", "b", "c"]

    def test_multiple_renames_with_unmapped(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"src_a": [1, 2], "src_b": ["x", "y"], "keep": [10, 20]},
            backend_name,
        )
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER, rename_from="src_a"),
                FieldSpec(name="b", type=UniversalType.STRING, rename_from="src_b"),
            ],
        )
        result = ma.relation(df).conform(spec, keep_unmapped=True).to_polars()
        assert "a" in result.columns
        assert "b" in result.columns
        assert "keep" in result.columns
        assert "src_a" not in result.columns
        assert "src_b" not in result.columns


class TestRelationConformKeepUnmappedStructAccess:
    def test_dotted_source_preserves_parent_struct(self):
        import polars as pl

        df = pl.DataFrame([
            {"id": 1, "score": {"strain": 10.5, "recovery": 80}},
            {"id": 2, "score": {"strain": 8.2, "recovery": 90}},
        ])
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="strain", type=UniversalType.NUMBER, rename_from="score.strain"),
            ],
        )
        result = ma.relation(df).conform(spec, keep_unmapped=True).to_polars()
        assert "id" in result.columns
        assert "strain" in result.columns
        assert "score" in result.columns
