"""Cross-backend parametrized tests for conform compilation."""
from __future__ import annotations

import pytest
import mountainash as ma

from mountainash.conform.builder import ConformBuilder
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
        result = ConformBuilder({"val": {"cast": "integer"}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == [1, 2, 3]

    def test_cast_string_to_number(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1.5", "2.5", "3.5"]}, backend_name)
        result = ConformBuilder({"val": {"cast": "number"}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == [1.5, 2.5, 3.5]

    def test_cast_string_to_string(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["hello", "world"]}, backend_name)
        result = ConformBuilder({"val": {"cast": "string"}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == ["hello", "world"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformRename:
    def test_rename_column(self, backend_name, backend_factory):
        df = backend_factory.create({"old_name": ["a", "b", "c"]}, backend_name)
        result = ConformBuilder({"new_name": {"rename_from": "old_name", "cast": "string"}}).apply(df)
        actual = ma.relation(result).select("new_name").to_dict()["new_name"]
        assert actual == ["a", "b", "c"]

    def test_rename_preserves_other_columns(self, backend_name, backend_factory):
        df = backend_factory.create({"old": ["a", "b"], "keep": [1, 2]}, backend_name)
        result = ConformBuilder({"new": {"rename_from": "old", "cast": "string"}}).apply(df)
        result_dict = ma.relation(result).to_dict()
        assert "new" in result_dict
        assert "keep" in result_dict
        assert "old" not in result_dict


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformNullFill:
    def test_null_fill_integer(self, backend_name, backend_factory):
        df = backend_factory.create({"val": [1, None, 3]}, backend_name)
        result = ConformBuilder({"val": {"cast": "integer", "null_fill": -1}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == [1, -1, 3]

    def test_null_fill_string(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["x", None, "z"]}, backend_name)
        result = ConformBuilder({"val": {"cast": "string", "null_fill": "unknown"}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == ["x", "unknown", "z"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformKeepOnlyMapped:
    def test_keep_only_mapped_drops_extra(self, backend_name, backend_factory):
        df = backend_factory.create({"keep": ["a", "b"], "drop": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="keep", type=UniversalType.STRING)],
            keep_only_mapped=True,
        )
        result = ConformBuilder(spec).apply(df)
        result_dict = ma.relation(result).to_dict()
        assert "keep" in result_dict
        assert "drop" not in result_dict

    def test_keep_only_mapped_false_preserves_extra(self, backend_name, backend_factory):
        df = backend_factory.create({"mapped": ["a", "b"], "extra": [1, 2]}, backend_name)
        spec = TypeSpec(
            fields=[FieldSpec(name="mapped", type=UniversalType.STRING)],
            keep_only_mapped=False,
        )
        result = ConformBuilder(spec).apply(df)
        result_dict = ma.relation(result).to_dict()
        assert "mapped" in result_dict
        assert "extra" in result_dict


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformMultiTransform:
    def test_cast_and_rename(self, backend_name, backend_factory):
        df = backend_factory.create({"raw_id": ["1", "2", "3"]}, backend_name)
        result = ConformBuilder({
            "user_id": {"rename_from": "raw_id", "cast": "integer"},
        }).apply(df)
        actual = ma.relation(result).select("user_id").to_dict()["user_id"]
        assert actual == [1, 2, 3]

    def test_full_pipeline(self, backend_name, backend_factory):
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
        result = ConformBuilder(spec).apply(df)
        result_dict = ma.relation(result).to_dict()
        assert result_dict["score"] == [1.5, 0.0, 3.5]
        assert result_dict["label"] == ["foo", "bar", "n/a"]
        assert "extra" in result_dict


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
        result = ConformBuilder.from_frictionless(frictionless_data).apply(df)
        actual = ma.relation(result).select("user_id").to_dict()["user_id"]
        assert actual == [1, 2]
