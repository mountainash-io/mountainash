"""Cross-backend tests for Relation.conform()."""
from __future__ import annotations

import pytest
import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS

# ALL_BACKENDS = [
#     "polars",
#     "pandas",
#     "narwhals",
#     "ibis-polars",
#     "ibis-duckdb",
#     "ibis-sqlite",
# ]


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

    def test_default_keeps_unmapped(self, backend_name, backend_factory):
        """Unset fields_match defaults to open — unmapped columns preserved."""
        df = backend_factory.create({"keep": ["a", "b"], "extra": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="keep", type=UniversalType.STRING)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "keep" in result.columns
        assert "extra" in result.columns


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
        assert "id" in result.columns
        assert "strain" in result.columns
        assert "score" in result.columns


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
        assert "extra" in result.columns


class TestRelationConformEdgeCases:
    def test_empty_spec_default_keeps_all_columns(self):
        """Empty spec with default (open) keeps all original columns."""
        import polars as pl

        df = pl.DataFrame({"a": [1], "b": [2]})
        spec = TypeSpec(fields=[])
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a", "b"]

    def test_empty_spec_partial_raises(self):
        """Empty spec with partial raises NoMatchingFieldsError — zero fields match."""
        import polars as pl
        from mountainash.conform.errors import NoMatchingFieldsError

        df = pl.DataFrame({"a": [1], "b": [2]})
        spec = TypeSpec(fields=[], fields_match="partial")
        with pytest.raises(NoMatchingFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_type_any_skips_cast(self):
        import polars as pl

        df = pl.DataFrame({"val": ["hello", "world"]})
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.ANY)],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["hello", "world"]


class TestRelationConformMissingColumns:
    """Missing spec fields are silently skipped — the visitor auto-detects columns."""

    def test_missing_spec_field_skipped(self):
        """Missing spec fields are skipped; with default open, unmapped columns preserved."""
        import polars as pl

        df = pl.DataFrame({"keep": [1, 2], "extra": [10, 20]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="keep", type=UniversalType.INTEGER),
                FieldSpec(name="gone", type=UniversalType.STRING),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "keep" in result.columns
        assert "extra" in result.columns
        assert result["keep"].to_list() == [1, 2]

    def test_missing_rename_from_skipped(self):
        """Missing rename source is skipped; other columns preserved with default open."""
        import polars as pl

        df = pl.DataFrame({"raw_id": ["1", "2"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw_id"),
                FieldSpec(name="duration", type=UniversalType.NUMBER, rename_from="stress_duration"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "id" in result.columns
        assert result["id"].to_list() == [1, 2]

    def test_missing_dotted_source_skipped(self):
        import polars as pl

        df = pl.DataFrame({"id": [1, 2]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="strain", type=UniversalType.NUMBER, rename_from="score.strain"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "id" in result.columns

    def test_all_spec_fields_missing_keeps_originals(self):
        """When all spec fields are missing, default open keeps original columns."""
        import polars as pl

        df = pl.DataFrame({"a": [1, 2]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="x", type=UniversalType.INTEGER),
                FieldSpec(name="y", type=UniversalType.STRING),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_all_spec_fields_missing_partial_raises(self):
        """With partial, all-missing spec fields raises NoMatchingFieldsError."""
        import polars as pl
        from mountainash.conform.errors import NoMatchingFieldsError

        df = pl.DataFrame({"a": [1, 2]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="x", type=UniversalType.INTEGER),
                FieldSpec(name="y", type=UniversalType.STRING),
            ],
            fields_match="partial",
        )
        with pytest.raises(NoMatchingFieldsError):
            ma.relation(df).conform(spec).to_polars()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRelationConformFieldsMatchOpen:
    """Tests for fields_match='open' — preserving columns not in the TypeSpec."""

    def test_unmapped_columns_preserved(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"raw_id": ["1", "2"], "extra": [10, 20]}, backend_name,
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw_id")],
            fields_match="open",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "id" in result.columns
        assert "extra" in result.columns
        assert "raw_id" not in result.columns
        assert result["id"].to_list() == [1, 2]
        assert result["extra"].to_list() == [10, 20]

    def test_default_fields_match_keeps_extra(self, backend_name, backend_factory):
        """Unset fields_match defaults to 'open' — unmapped columns are preserved."""
        df = backend_factory.create(
            {"raw_id": ["1", "2"], "extra": [10, 20]}, backend_name,
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw_id")],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "id" in result.columns
        assert "extra" in result.columns
        assert "raw_id" not in result.columns
        assert result["id"].to_list() == [1, 2]
        assert result["extra"].to_list() == [10, 20]

    def test_explicit_partial_drops_extra(self, backend_name, backend_factory):
        """Explicit fields_match='partial' drops unmapped columns."""
        df = backend_factory.create(
            {"raw_id": ["1", "2"], "extra": [10, 20]}, backend_name,
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw_id")],
            fields_match="partial",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["id"]

    def test_same_name_field_overwrites_in_place(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"val": ["1", "2"], "other": ["a", "b"]}, backend_name,
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER)],
            fields_match="open",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1, 2]
        assert result["other"].to_list() == ["a", "b"]

    def test_null_fill_with_open(self, backend_name, backend_factory):
        if backend_name.startswith("ibis"):
            pytest.xfail("Ibis coalesce cannot mix column type with different literal type")
        df = backend_factory.create(
            {"val": [1, None, 3], "tag": ["a", "b", "c"]}, backend_name,
        )
        spec = TypeSpec(
            fields=[FieldSpec(name="val", type=UniversalType.INTEGER, null_fill=-1)],
            fields_match="open",
        )
        result = ma.relation(df).conform(spec).to_polars()
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
            fields_match="open",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "a" in result.columns
        assert "b" in result.columns
        assert "keep" in result.columns
        assert "src_a" not in result.columns
        assert "src_b" not in result.columns


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestFieldsMatchModes:
    """Comprehensive tests for all six fields_match modes."""

    def test_open_keeps_unmapped(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.INTEGER)],
            fields_match="open",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert sorted(result.columns) == ["a", "b", "c"]

    def test_none_defaults_to_open(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.INTEGER)],
        )
        assert spec.fields_match is None
        result = ma.relation(df).conform(spec).to_polars()
        assert sorted(result.columns) == ["a", "b", "c"]

    def test_partial_drops_unmapped(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.INTEGER)],
            fields_match="partial",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_partial_skips_missing_fields(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1], "b": [2]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="gone", type=UniversalType.STRING),
            ],
            fields_match="partial",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_partial_raises_when_zero_match(self, backend_name, backend_factory):
        from mountainash.conform.errors import NoMatchingFieldsError

        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="x", type=UniversalType.INTEGER)],
            fields_match="partial",
        )
        with pytest.raises(NoMatchingFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_exact_passes_when_count_matches(self, backend_name, backend_factory):
        df = backend_factory.create({"a": ["1"], "b": ["2"]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.INTEGER),
            ],
            fields_match="exact",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert sorted(result.columns) == ["a", "b"]

    def test_exact_raises_on_count_mismatch(self, backend_name, backend_factory):
        from mountainash.conform.errors import ExactFieldCountError

        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.INTEGER)],
            fields_match="exact",
        )
        with pytest.raises(ExactFieldCountError):
            ma.relation(df).conform(spec).to_polars()

    def test_equal_passes_when_columns_match(self, backend_name, backend_factory):
        df = backend_factory.create({"a": ["1"], "b": ["2"]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.INTEGER),
            ],
            fields_match="equal",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert sorted(result.columns) == ["a", "b"]

    def test_equal_raises_on_missing(self, backend_name, backend_factory):
        from mountainash.conform.errors import MissingFieldsError

        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.INTEGER),
            ],
            fields_match="equal",
        )
        with pytest.raises(MissingFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_equal_raises_on_extra(self, backend_name, backend_factory):
        from mountainash.conform.errors import ExtraFieldsError

        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.INTEGER),
            ],
            fields_match="equal",
        )
        with pytest.raises(ExtraFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_subset_passes_when_all_spec_fields_present(self, backend_name, backend_factory):
        df = backend_factory.create({"a": ["1"], "b": [2], "c": [3]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.INTEGER)],
            fields_match="subset",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_subset_raises_on_missing(self, backend_name, backend_factory):
        from mountainash.conform.errors import MissingFieldsError

        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="gone", type=UniversalType.STRING),
            ],
            fields_match="subset",
        )
        with pytest.raises(MissingFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_superset_passes_when_no_extra_columns(self, backend_name, backend_factory):
        df = backend_factory.create({"a": ["1"]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.STRING),
            ],
            fields_match="superset",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_superset_raises_on_extra(self, backend_name, backend_factory):
        from mountainash.conform.errors import ExtraFieldsError

        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=UniversalType.INTEGER),
                FieldSpec(name="b", type=UniversalType.INTEGER),
            ],
            fields_match="superset",
        )
        with pytest.raises(ExtraFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_invalid_fields_match_raises(self, backend_name, backend_factory):
        from mountainash.conform.errors import ConformError

        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=UniversalType.INTEGER)],
            fields_match="bogus",
        )
        with pytest.raises(ConformError, match="Invalid fields_match"):
            ma.relation(df).conform(spec).to_polars()


class TestRelationConformOpenStructAccess:
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
            fields_match="open",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "id" in result.columns
        assert "strain" in result.columns
        assert "score" in result.columns
