"""Tests for _build_conform_exprs — the shared conform expression builder."""
from __future__ import annotations

from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestBuildConformExprs:
    def test_basic_rename_and_cast(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="user_id", type=UniversalType.INTEGER, rename_from="raw_id"),
            ],
            keep_only_mapped=True,
        )
        exprs = _build_conform_exprs(spec, source_columns=["raw_id", "extra"])
        assert len(exprs) == 1

    def test_pass_through_unmapped(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
            ],
            keep_only_mapped=False,
        )
        exprs = _build_conform_exprs(spec, source_columns=["id", "extra_a", "extra_b"])
        assert len(exprs) == 3

    def test_dotted_source_name_struct_access(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="strain", type=UniversalType.NUMBER, rename_from="score.strain"),
            ],
            keep_only_mapped=True,
        )
        exprs = _build_conform_exprs(spec, source_columns=["score"])
        assert len(exprs) == 1

    def test_null_fill(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="val", type=UniversalType.INTEGER, null_fill=-1),
            ],
            keep_only_mapped=True,
        )
        exprs = _build_conform_exprs(spec, source_columns=["val"])
        assert len(exprs) == 1

    def test_type_any_skips_cast(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="val", type=UniversalType.ANY),
            ],
            keep_only_mapped=True,
        )
        exprs = _build_conform_exprs(spec, source_columns=["val"])
        assert len(exprs) == 1

    def test_empty_spec_keep_only_mapped_true(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields=[], keep_only_mapped=True)
        exprs = _build_conform_exprs(spec, source_columns=["a", "b"])
        assert len(exprs) == 0

    def test_empty_spec_keep_only_mapped_false(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields=[], keep_only_mapped=False)
        exprs = _build_conform_exprs(spec, source_columns=["a", "b"])
        assert len(exprs) == 2

    def test_dotted_name_maps_root_column_for_passthrough(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="strain", type=UniversalType.NUMBER, rename_from="score.strain"),
            ],
            keep_only_mapped=False,
        )
        exprs = _build_conform_exprs(spec, source_columns=["score", "extra"])
        assert len(exprs) == 2
