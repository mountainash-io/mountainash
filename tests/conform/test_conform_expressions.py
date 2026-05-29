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
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_dotted_source_name_struct_access(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="strain", type=UniversalType.NUMBER, rename_from="score.strain"),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_null_fill(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="val", type=UniversalType.INTEGER, null_fill=-1),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_type_any_skips_cast(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="val", type=UniversalType.ANY),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_empty_spec_produces_no_exprs(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields=[])
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 0
