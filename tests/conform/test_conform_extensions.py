from __future__ import annotations

import polars as pl
import pytest

from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestDotPathRename:
    def test_nested_struct_access(self):
        from mountainash.conform.compiler import compile_conform

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

        result = compile_conform(spec, df)
        assert result["strain"].to_list() == [10.5, 8.2]
        assert list(result.columns) == ["id", "strain"]

    def test_flat_rename_still_works(self):
        from mountainash.conform.compiler import compile_conform

        df = pl.DataFrame({"old_name": [1, 2]})
        spec = TypeSpec(
            fields=[FieldSpec(name="new_name", type=UniversalType.INTEGER, rename_from="old_name")],
            keep_only_mapped=True,
        )

        result = compile_conform(spec, df)
        assert result["new_name"].to_list() == [1, 2]


class TestMultiplyBy:
    def test_basic_multiplication(self):
        from mountainash.conform.compiler import compile_conform

        df = pl.DataFrame({"kilojoule": [500.0, 350.0, None]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="calories", type=UniversalType.NUMBER,
                          rename_from="kilojoule", multiply_by=0.239),
            ],
            keep_only_mapped=True,
        )
        result = compile_conform(spec, df)
        assert result["calories"][0] == pytest.approx(119.5)
        assert result["calories"][1] == pytest.approx(83.65)
        assert result["calories"][2] is None

    def test_multiply_with_struct_path(self):
        from mountainash.conform.compiler import compile_conform

        df = pl.DataFrame([{"score": {"kilojoule": 100.0}}])
        spec = TypeSpec(
            fields=[
                FieldSpec(name="calories", type=UniversalType.NUMBER,
                          rename_from="score.kilojoule", multiply_by=0.239),
            ],
            keep_only_mapped=True,
        )
        result = compile_conform(spec, df)
        assert result["calories"][0] == pytest.approx(23.9)


class TestCoalesceFrom:
    def test_first_non_null(self):
        from mountainash.conform.compiler import compile_conform

        df = pl.DataFrame([
            {"score": {"state": None}, "state": "completed"},
            {"score": {"state": "recovering"}, "state": "completed"},
        ])
        spec = TypeSpec(
            fields=[
                FieldSpec(name="score_state", type=UniversalType.STRING,
                          coalesce_from=["score.state", "state"]),
            ],
            keep_only_mapped=True,
        )
        result = compile_conform(spec, df)
        assert result["score_state"].to_list() == ["completed", "recovering"]


class TestDurationFrom:
    def test_iso_datetime_diff(self):
        from mountainash.conform.compiler import compile_conform

        df = pl.DataFrame({
            "start": ["2024-01-15T10:00:00Z", "2024-01-15T08:00:00Z"],
            "end": ["2024-01-15T10:30:00Z", "2024-01-15T09:15:00Z"],
        })
        spec = TypeSpec(
            fields=[
                FieldSpec(name="duration_seconds", type=UniversalType.INTEGER,
                          duration_from=("start", "end")),
            ],
            keep_only_mapped=True,
        )
        result = compile_conform(spec, df)
        assert result["duration_seconds"].to_list() == [1800, 4500]

    def test_null_timestamps(self):
        from mountainash.conform.compiler import compile_conform

        df = pl.DataFrame({"start": [None], "end": ["2024-01-15T10:30:00Z"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="duration_seconds", type=UniversalType.INTEGER,
                          duration_from=("start", "end")),
            ],
            keep_only_mapped=True,
        )
        result = compile_conform(spec, df)
        assert result["duration_seconds"][0] is None


class TestRequiredFieldsFiltering:
    def test_skipped_records_separated(self):
        from mountainash.conform.compiler import compile_conform_with_skipped

        df = pl.DataFrame({
            "id": [1, None, 3],
            "name": ["alice", "bob", "carol"],
        })
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="name", type=UniversalType.STRING),
            ],
            required_fields=["id"],
            keep_only_mapped=True,
        )

        conformed, skipped = compile_conform_with_skipped(spec, df)
        assert len(conformed) == 2
        assert conformed["id"].to_list() == [1, 3]
        assert len(skipped) == 1
        assert skipped["name"][0] == "bob"


class TestApplyWithSkipped:
    def test_builder_apply_with_skipped(self):
        from mountainash import conform

        df = pl.DataFrame({
            "id": [1, None],
            "value": [10, 20],
        })
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="value", type=UniversalType.INTEGER),
            ],
            required_fields=["id"],
            keep_only_mapped=True,
        )

        builder = conform(spec)
        conformed, skipped = builder.apply_with_skipped(df)
        assert len(conformed) == 1
        assert len(skipped) == 1

    def test_builder_apply_still_works_without_required(self):
        from mountainash import conform

        df = pl.DataFrame({"id": [1, None], "value": [10, 20]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="value", type=UniversalType.INTEGER),
            ],
            keep_only_mapped=True,
        )

        result = conform(spec).apply(df)
        assert len(result) == 2
