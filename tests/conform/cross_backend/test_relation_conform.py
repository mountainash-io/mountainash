"""Cross-backend tests for Relation.conform()."""

from __future__ import annotations

import pytest
import mountainash as ma
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.dtypes import SchemaTypeStatus

from ibis.common.exceptions import UnsupportedBackendType

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.call_expectations import expect_call_failure



@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("dtype,values", [
    (ma.MountainashDtype.I8, [-128, 127, None]),
    (ma.MountainashDtype.U8, [0, 255, None]),
    (ma.MountainashDtype.FP32, [1.5, -2.25, None]),
])
def test_canonical_conform_retains_declared_identity(backend_name, backend_factory, dtype, values, request):
    if dtype in {ma.MountainashDtype.I8, ma.MountainashDtype.U8} and backend_name in {"pandas", "narwhals-pandas"}:
        from pandas.errors import IntCastingNaNError
        request.applymarker(pytest.mark.xfail(
            strict=True, raises=IntCastingNaNError,
            reason="252: native Narwhals NumPy-backed float/NaN -> integer cast loses nullable representation",
        ))
    source = backend_factory.create({"value": values}, backend_name)
    rel = ma.relation(source).conform(TableSchema(
        fields={"value": FieldDefinition(dtype=dtype)}, missing_values=[],
    ))
    out = rel.to_polars()
    assert out["value"].to_list() == values
    # Native-first schema reports SQLite's physical affinities. The typed
    # Polars/Arrow egress below must still retain the precise declaration.
    native_dtype = (
        ma.MountainashDtype.FP64 if dtype is ma.MountainashDtype.FP32 else ma.MountainashDtype.I64
    ) if backend_name == "ibis-sqlite" else dtype
    assert rel.schema["value"] is native_dtype
    import polars as pl
    assert out.schema["value"] == {
        ma.MountainashDtype.I8: pl.Int8,
        ma.MountainashDtype.U8: pl.UInt8,
        ma.MountainashDtype.FP32: pl.Float32,
    }[dtype]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_native_override_controls_conform_and_inference(backend_name, backend_factory, request):
    if backend_name in {"pandas", "narwhals-pandas"}:
        from pandas.errors import IntCastingNaNError
        request.applymarker(pytest.mark.xfail(
            strict=True, raises=IntCastingNaNError,
            reason="252: native Narwhals NumPy-backed float/NaN -> integer cast loses nullable representation",
        ))
    source = backend_factory.create({"value": [127, None]}, backend_name)
    override = "int64" if backend_name.startswith("ibis") else "Int64"
    rel = ma.relation(source).conform(TableSchema(
        fields={"value": FieldDefinition(dtype=ma.MountainashDtype.I8, backend_type=override)},
        missing_values=[],
    ))
    with pytest.warns(UserWarning, match="value"):
        out = rel.to_polars()
    assert out["value"].to_list() == [127, None]
    assert rel.schema["value"] is ma.MountainashDtype.I64
    import polars as pl
    assert out.schema["value"] == pl.Int64


def test_explicit_native_timestamp_freeze_compares_parameters():
    # Polars-owned parameters: other targets cannot consume this native object.
    import polars as pl
    from mountainash.conform.errors import SchemaDriftError
    source = pl.DataFrame({"at": [1, 1001, None]}).with_columns(pl.col("at").cast(pl.Datetime("ns", "UTC")))
    for unit in ("ns", "us"):
        spec = TableSchema(fields={"at": FieldDefinition(
            backend_type=pl.Datetime(unit, "UTC"),
        )}, missing_values=[])
        rel = ma.relation(source).conform(spec, contract={"data_type": "freeze"})
        if unit == "ns":
            assert rel.to_polars()["at"].dt.epoch("ns").to_list() == [1, 1001, None]
        else:
            with pytest.raises(SchemaDriftError):
                rel.to_polars()


# ALL_BACKENDS = [
#     "polars",
#     "pandas",
#     "narwhals",
#     "ibis-duckdb",
#     "ibis-sqlite",
# ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRelationConformBasic:
    def test_rename_and_cast(self, backend_name, backend_factory):
        df = backend_factory.create({"raw_id": ["1", "2", "3"]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"user_id": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw_id")},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["user_id"].to_list() == [1, 2, 3]
        assert list(result.columns) == ["user_id"]

    def test_null_fill_and_cast(self, backend_name, backend_factory):
        df = backend_factory.create({"val": [1, None, 3]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"val": FieldDefinition(type=UniversalType.INTEGER, null_fill=-1)},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1, -1, 3]

    def test_default_keeps_unmapped(self, backend_name, backend_factory):
        """fields_match="open" keeps unmapped columns."""
        df = backend_factory.create({"keep": ["a", "b"], "extra": [1, 2]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"keep": FieldDefinition(type=UniversalType.STRING)},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "keep" in result.columns
        assert "extra" in result.columns


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRelationConformComposition:
    def test_conform_then_filter(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1", "2", "3"]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"val": FieldDefinition(type=UniversalType.INTEGER)},
        )
        result = ma.relation(df).conform(spec).filter(ma.col("val").gt(1)).to_polars()
        assert result["val"].to_list() == [2, 3]

    def test_conform_then_sort(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["3", "1", "2"]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"val": FieldDefinition(type=UniversalType.INTEGER)},
        )
        result = ma.relation(df).conform(spec).sort("val").to_polars()
        assert result["val"].to_list() == [1, 2, 3]


class TestRelationConformStructAccess:
    def test_dotted_source_name(self):
        import polars as pl

        df = pl.DataFrame(
            [
                {"id": 1, "score": {"strain": 10.5, "kilojoule": 500.0}},
                {"id": 2, "score": {"strain": 8.2, "kilojoule": 350.0}},
            ]
        )
        spec = TableSchema(
            fields_match="open",
            fields={"id": FieldDefinition(type=UniversalType.INTEGER),
                "strain": FieldDefinition(type=UniversalType.NUMBER, rename_from="score.strain"),},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["strain"].to_list() == [10.5, 8.2]
        assert "id" in result.columns
        assert "strain" in result.columns
        assert "score" in result.columns


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRelationConformStructStrictModes:
    """Item 46 (b): dotted sources under strict fields_match modes validate on
    the struct ROOT and actually extract the nested field at runtime."""

    def test_equal_dotted_source_extracts(self, backend_name, backend_factory):
        with expect_call_failure(
            when=backend_name == "ibis-sqlite",
            errors=(UnsupportedBackendType,),
            reason="SQLite does not support native Struct-column construction; this is native input construction, not conform() execution",
        ):
            df = backend_factory.create({"payload": [{"id": 1}, {"id": 2}]}, backend_name)
        spec = TableSchema(
            fields={"pid": FieldDefinition(type=UniversalType.INTEGER, rename_from="payload.id")},
            fields_match="equal",
        )
        with expect_call_failure(
            when=backend_name in ("narwhals-pandas", "pandas"),
            errors=(TypeError,),
            reason="conform() with a dotted struct source path raises TypeError on pandas/narwhals-pandas; polars and ibis native structured backends extract it",
        ):
            result = ma.relation(df).conform(spec).to_polars()
            assert result["pid"].to_list() == [1, 2]

    def test_subset_dotted_source_extracts_with_extra_column(self, backend_name, backend_factory):
        with expect_call_failure(
            when=backend_name == "ibis-sqlite",
            errors=(UnsupportedBackendType,),
            reason="SQLite does not support native Struct-column construction; this is native input construction, not conform() execution",
        ):
            df = backend_factory.create({"payload": [{"id": 1}, {"id": 2}], "other": ["x", "y"]}, backend_name)
        spec = TableSchema(
            fields={"pid": FieldDefinition(type=UniversalType.INTEGER, rename_from="payload.id")},
            fields_match="subset",
        )
        with expect_call_failure(
            when=backend_name in ("narwhals-pandas", "pandas"),
            errors=(TypeError,),
            reason="conform() with a dotted struct source path raises TypeError on pandas/narwhals-pandas; polars and ibis native structured backends extract it",
        ):
            result = ma.relation(df).conform(spec).to_polars()
            assert result["pid"].to_list() == [1, 2]
            # Subset is a select mode: only spec fields are emitted — the extra
            # unmapped column is allowed in the INPUT (that's subset's point)
            # but discarded from the OUTPUT.
            assert list(result.columns) == ["pid"]
            assert "other" not in result.columns


_STRUCT_CAST = [
    pytest.param("narwhals-polars"),
    pytest.param("ibis-duckdb"),
    "ibis-sqlite",
    # narwhals-pandas deliberately excluded: MA-CONF-01 already establishes
    # pandas-backed struct data is broken at a more fundamental level.
]


@pytest.mark.parametrize("backend_name", _STRUCT_CAST)
class TestRelationConformStructCastOffPolars:
    """Struct conform lowers through the backend-neutral struct operation."""

    def test_struct_cast_uses_neutral_operation(self, backend_name, backend_factory):
        with expect_call_failure(
            when=backend_name == "ibis-sqlite",
            errors=(UnsupportedBackendType,),
            reason="SQLite does not support native Struct-column construction; this is native input construction, not conform() execution",
        ):
            df = backend_factory.create({"addr": [{"street": "Main St", "zip": "12345"}]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"addr": FieldDefinition(
                    type=UniversalType.OBJECT,
                    fields={"street": FieldDefinition(type=UniversalType.STRING),
                        "zip": FieldDefinition(type=UniversalType.STRING),},
                )},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "addr" in result.columns



@pytest.mark.parametrize(
    "backend_name",
    ("polars", "polars-lazy", "ibis-duckdb"),
)
def test_native_struct_keeps_child_conversion_metadata(backend_name, backend_factory):
    from datetime import datetime
    from decimal import Decimal

    from mountainash.core.dtypes import DecimalDtype, TimestampDtype, MountainashDtype as D

    with expect_call_failure(
        when=backend_name == "ibis-sqlite",
        errors=(UnsupportedBackendType,),
        reason="SQLite does not support native Struct-column construction; this is native input construction, not conform() execution",
    ):
        source = backend_factory.create(
            {"x": [
                {"v": "20260101", "count": "1,234", "flag": "yes", "backup": 11, "price": "1.245"},
                {"v": "20260102", "count": "2,345", "flag": "no", "backup": None, "price": "1.255"},
            ]},
            backend_name,
        )
    field = FieldDefinition(fields={
        "v": FieldDefinition(
            type=UniversalType.DATETIME, dtype=TimestampDtype(6, False), format="%Y%m%d",
        ),
        "count": FieldDefinition(type=UniversalType.INTEGER, dtype=D.I64, group_char=","),
        "flag": FieldDefinition(
            type=UniversalType.BOOLEAN, dtype=D.BOOL, true_values=["yes"], false_values=["no"],
        ),
        "backup": FieldDefinition(type=UniversalType.INTEGER, dtype=D.I64, null_fill=12),
        "price": FieldDefinition(
            type=UniversalType.NUMBER, dtype=DecimalDtype(5, 2), rounding="half_to_even",
        ),
    })
    result = ma.relation(source).conform(
        TableSchema(fields={"x": field}, missing_values=[]),
    ).to_polars()
    assert result["x"].to_list() == [
        {
            "v": datetime(2026, 1, 1), "count": 1234, "flag": True,
            "backup": 11, "price": Decimal("1.24"),
        },
        {
            "v": datetime(2026, 1, 2), "count": 2345, "flag": False,
            "backup": 12, "price": Decimal("1.26"),
        },
    ]


@pytest.mark.parametrize("backend_name", ("polars", "polars-lazy", "ibis-duckdb"))
def test_native_array_of_struct_keeps_child_conversion_metadata(
    backend_name, backend_factory,
):
    from datetime import datetime

    from mountainash.core.dtypes import TimestampDtype

    source = backend_factory.create(
        {"items": [[{"v": "20260101"}]]},
        backend_name,
    )
    field = FieldDefinition(
        type=UniversalType.ARRAY,
        element=FieldDefinition(fields={
            "v": FieldDefinition(
                type=UniversalType.DATETIME, dtype=TimestampDtype(6, False), format="%Y%m%d",
            ),
        }),
    )
    result = ma.relation(source).conform(
        TableSchema(fields={"items": field}, missing_values=[]),
    ).to_polars()
    assert result["items"].to_list() == [[{"v": datetime(2026, 1, 1)}]]


@pytest.mark.parametrize(
    "backend_name",
    ("narwhals-polars",),
)
def test_native_array_child_conversion_retains_provider_capability_boundary(
    backend_name, backend_factory,
):
    from mountainash.core.types import BackendCapabilityError
    from mountainash.core.dtypes import TimestampDtype
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_LIST,
    )

    source = backend_factory.create(
        {"items": [[{"v": "20260101"}]]},
        backend_name,
    )
    field = FieldDefinition(
        type=UniversalType.ARRAY,
        element=FieldDefinition(fields={
            "v": FieldDefinition(
                type=UniversalType.DATETIME, dtype=TimestampDtype(6, False), format="%Y%m%d",
            ),
        }),
    )
    with pytest.raises(BackendCapabilityError) as error:
        ma.relation(source).conform(
            TableSchema(fields={"items": field}, missing_values=[]),
        ).to_polars()
    assert error.value.function_key is FKEY_MOUNTAINASH_SCALAR_LIST.ELEMENT


@pytest.mark.parametrize("backend_name", ("narwhals-polars", "narwhals-pandas"))
def test_narwhals_struct_child_conversion_preserves_metadata(
    backend_name, backend_factory,
):
    from datetime import datetime
    from mountainash.core.dtypes import TimestampDtype

    source = backend_factory.create(
        {"x": [{"v": "20260101"}]},
        backend_name,
    )
    field = FieldDefinition(fields={
        "v": FieldDefinition(
            type=UniversalType.DATETIME, dtype=TimestampDtype(6, False), format="%Y%m%d",
        ),
    })
    result = ma.relation(source).conform(
        TableSchema(fields={"x": field}, missing_values=[]),
    ).to_polars()
    assert result["x"].to_list() == [{"v": datetime(2026, 1, 1)}]


class TestRelationConformFullPipeline:
    def test_full_pipeline(self):
        import polars as pl

        df = pl.DataFrame(
            {
                "raw_score": ["1.5", None, "3.5"],
                "raw_label": ["foo", "bar", None],
                "extra": [10, 20, 30],
            }
        )
        spec = TableSchema(
            fields_match="open",
            fields={"score": FieldDefinition(type=UniversalType.NUMBER, rename_from="raw_score", null_fill=0.0),
                "label": FieldDefinition(type=UniversalType.STRING, rename_from="raw_label", null_fill="n/a"),},
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
        spec = TableSchema(fields_match="open", fields={})
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a", "b"]

    def test_empty_spec_partial_raises(self):
        """Empty spec with partial raises NoMatchingFieldsError — zero fields match."""
        import polars as pl
        from mountainash.conform.errors import NoMatchingFieldsError

        df = pl.DataFrame({"a": [1], "b": [2]})
        spec = TableSchema(fields={}, fields_match="partial")
        with pytest.raises(NoMatchingFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_type_any_skips_cast(self):
        import polars as pl

        df = pl.DataFrame({"val": ["hello", "world"]})
        spec = TableSchema(
            fields_match="open",
            fields={"val": FieldDefinition(type=UniversalType.ANY)},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["hello", "world"]


class TestRelationConformMissingColumns:
    """Missing spec fields are silently skipped — the visitor auto-detects columns."""

    def test_missing_spec_field_skipped(self):
        """Missing spec fields are skipped; with default open, unmapped columns preserved."""
        import polars as pl

        df = pl.DataFrame({"keep": [1, 2], "extra": [10, 20]})
        spec = TableSchema(
            fields_match="open",
            fields={"keep": FieldDefinition(type=UniversalType.INTEGER),
                "gone": FieldDefinition(type=UniversalType.STRING),},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "keep" in result.columns
        assert "extra" in result.columns
        assert result["keep"].to_list() == [1, 2]

    def test_missing_rename_from_skipped(self):
        """Missing rename source is skipped; other columns preserved with default open."""
        import polars as pl

        df = pl.DataFrame({"raw_id": ["1", "2"]})
        spec = TableSchema(
            fields_match="open",
            fields={"id": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw_id"),
                "duration": FieldDefinition(type=UniversalType.NUMBER, rename_from="stress_duration"),},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "id" in result.columns
        assert result["id"].to_list() == [1, 2]

    def test_missing_dotted_source_skipped(self):
        import polars as pl

        df = pl.DataFrame({"id": [1, 2]})
        spec = TableSchema(
            fields_match="open",
            fields={"id": FieldDefinition(type=UniversalType.INTEGER),
                "strain": FieldDefinition(type=UniversalType.NUMBER, rename_from="score.strain"),},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "id" in result.columns

    def test_all_spec_fields_missing_keeps_originals(self):
        """When all spec fields are missing, default open keeps original columns."""
        import polars as pl

        df = pl.DataFrame({"a": [1, 2]})
        spec = TableSchema(
            fields_match="open",
            fields={"x": FieldDefinition(type=UniversalType.INTEGER),
                "y": FieldDefinition(type=UniversalType.STRING),},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_all_spec_fields_missing_partial_raises(self):
        """With partial, all-missing spec fields raises NoMatchingFieldsError."""
        import polars as pl
        from mountainash.conform.errors import NoMatchingFieldsError

        df = pl.DataFrame({"a": [1, 2]})
        spec = TableSchema(
            fields={"x": FieldDefinition(type=UniversalType.INTEGER),
                "y": FieldDefinition(type=UniversalType.STRING),},
            fields_match="partial",
        )
        with pytest.raises(NoMatchingFieldsError):
            ma.relation(df).conform(spec).to_polars()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRelationConformFieldsMatchOpen:
    """Tests for fields_match='open' — preserving columns not in the TypeSpec."""

    def test_unmapped_columns_preserved(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"raw_id": ["1", "2"], "extra": [10, 20]},
            backend_name,
        )
        spec = TableSchema(
            fields={"id": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw_id")},
            fields_match="open",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "id" in result.columns
        assert "extra" in result.columns
        assert "raw_id" not in result.columns
        assert result["id"].to_list() == [1, 2]
        assert result["extra"].to_list() == [10, 20]

    def test_default_fields_match_keeps_extra(self, backend_name, backend_factory):
        """fields_match="open" preserves unmapped columns."""
        df = backend_factory.create(
            {"raw_id": ["1", "2"], "extra": [10, 20]},
            backend_name,
        )
        spec = TableSchema(
            fields_match="open",
            fields={"id": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw_id")},
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
            {"raw_id": ["1", "2"], "extra": [10, 20]},
            backend_name,
        )
        spec = TableSchema(
            fields={"id": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw_id")},
            fields_match="partial",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["id"]

    def test_same_name_field_overwrites_in_place(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"val": ["1", "2"], "other": ["a", "b"]},
            backend_name,
        )
        spec = TableSchema(
            fields={"val": FieldDefinition(type=UniversalType.INTEGER)},
            fields_match="open",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1, 2]
        assert result["other"].to_list() == ["a", "b"]

    def test_null_fill_with_open(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"val": [1, None, 3], "tag": ["a", "b", "c"]},
            backend_name,
        )
        spec = TableSchema(
            fields={"val": FieldDefinition(type=UniversalType.INTEGER, null_fill=-1)},
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
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER, rename_from="src_a"),
                "b": FieldDefinition(type=UniversalType.STRING, rename_from="src_b"),},
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
        # fields_match must be set to "open" explicitly (the model default is
        # now the strict "exact"); open keeps the unmapped b/c columns.
        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER)},
            fields_match="open",
        )
        assert spec.fields_match == "open"
        result = ma.relation(df).conform(spec).to_polars()
        assert sorted(result.columns) == ["a", "b", "c"]

    def test_partial_drops_unmapped(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER)},
            fields_match="partial",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_partial_skips_missing_fields(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1], "b": [2]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER),
                "gone": FieldDefinition(type=UniversalType.STRING),},
            fields_match="partial",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_partial_raises_when_zero_match(self, backend_name, backend_factory):
        from mountainash.conform.errors import NoMatchingFieldsError

        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TableSchema(
            fields={"x": FieldDefinition(type=UniversalType.INTEGER)},
            fields_match="partial",
        )
        with pytest.raises(NoMatchingFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_exact_passes_when_count_matches(self, backend_name, backend_factory):
        df = backend_factory.create({"a": ["1"], "b": ["2"]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER),
                "b": FieldDefinition(type=UniversalType.INTEGER),},
            fields_match="exact",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert sorted(result.columns) == ["a", "b"]

    def test_exact_raises_on_count_mismatch(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(), "b": FieldDefinition()},
            fields_match="exact",
        )
        from mountainash.conform.errors import ExactFieldsMismatchError

        with pytest.raises(ExactFieldsMismatchError) as error:
            ma.relation(df).conform(spec).to_polars()
        assert error.value.reason == "count"

    def test_equal_passes_when_columns_match(self, backend_name, backend_factory):
        df = backend_factory.create({"a": ["1"], "b": ["2"]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER),
                "b": FieldDefinition(type=UniversalType.INTEGER),},
            fields_match="equal",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert sorted(result.columns) == ["a", "b"]

    def test_equal_raises_on_missing(self, backend_name, backend_factory):
        from mountainash.conform.errors import MissingFieldsError

        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER),
                "b": FieldDefinition(type=UniversalType.INTEGER),},
            fields_match="equal",
        )
        with pytest.raises(MissingFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_equal_raises_on_extra(self, backend_name, backend_factory):
        from mountainash.conform.errors import ExtraFieldsError

        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER),
                "b": FieldDefinition(type=UniversalType.INTEGER),},
            fields_match="equal",
        )
        with pytest.raises(ExtraFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_subset_passes_when_all_spec_fields_present(self, backend_name, backend_factory):
        df = backend_factory.create({"a": ["1"], "b": [2], "c": [3]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER)},
            fields_match="subset",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_subset_raises_on_missing(self, backend_name, backend_factory):
        from mountainash.conform.errors import MissingFieldsError

        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER),
                "gone": FieldDefinition(type=UniversalType.STRING),},
            fields_match="subset",
        )
        with pytest.raises(MissingFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_superset_passes_when_no_extra_columns(self, backend_name, backend_factory):
        df = backend_factory.create({"a": ["1"]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER),
                "b": FieldDefinition(type=UniversalType.STRING),},
            fields_match="superset",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert list(result.columns) == ["a"]

    def test_superset_raises_on_extra(self, backend_name, backend_factory):
        from mountainash.conform.errors import ExtraFieldsError

        df = backend_factory.create({"a": [1], "b": [2], "c": [3]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER),
                "b": FieldDefinition(type=UniversalType.INTEGER),},
            fields_match="superset",
        )
        with pytest.raises(ExtraFieldsError):
            ma.relation(df).conform(spec).to_polars()

    def test_invalid_fields_match_raises(self, backend_name, backend_factory):
        from mountainash.conform.errors import ConformError

        df = backend_factory.create({"a": [1]}, backend_name)
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER)},
            fields_match="bogus",
        )
        with pytest.raises(ConformError, match="Invalid fields_match"):
            ma.relation(df).conform(spec).to_polars()


class TestRelationConformOpenStructAccess:
    def test_dotted_source_preserves_parent_struct(self):
        import polars as pl

        df = pl.DataFrame(
            [
                {"id": 1, "score": {"strain": 10.5, "recovery": 80}},
                {"id": 2, "score": {"strain": 8.2, "recovery": 90}},
            ]
        )
        spec = TableSchema(
            fields={"id": FieldDefinition(type=UniversalType.INTEGER),
                "strain": FieldDefinition(type=UniversalType.NUMBER, rename_from="score.strain"),},
            fields_match="open",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "id" in result.columns
        assert "strain" in result.columns
        assert "score" in result.columns


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformOwnsDeclarations:
    """A conform relation keeps the declaration it was built with."""

    def _check(
        self, rel, expected_cols=None, expected=None, column="value", schema_parity=True
    ):
        for _ in range(2):
            out = rel.to_polars()
            if expected is not None:
                assert out[column].to_list() == expected
            if expected_cols is not None:
                assert list(out.columns) == expected_cols
            if schema_parity:
                assert list(rel.schema) == list(out.columns)

    def test_owns_declared_type(self, backend_name, backend_factory):
        data = backend_factory.create({"value": ["7"]}, backend_name)
        spec = TableSchema(fields={"value": FieldDefinition(type=UniversalType.INTEGER)})
        old = ma.relation(data).conform(spec)
        spec.fields["value"] = spec.fields["value"].variant(type=UniversalType.STRING)
        new = ma.relation(data).conform(spec)
        self._check(old, expected=[7])
        self._check(new, expected=["7"])

    def test_owns_raw_mapping_schema(self, backend_name, backend_factory):
        data = backend_factory.create({"value": ["7"]}, backend_name)
        spec = {"fields": [{"name": "value", "type": "integer"}]}
        old = ma.relation(data).conform(spec)
        spec["fields"][0]["type"] = "string"
        new = ma.relation(data).conform(spec)
        self._check(old, expected=[7])
        self._check(new, expected=["7"])

    def test_owns_missing_values(self, backend_name, backend_factory):
        data = backend_factory.create({"value": ["NA"]}, backend_name)
        spec = TableSchema(
            fields={"value": FieldDefinition(type=UniversalType.STRING, missing_values=[""])}
        )
        old = ma.relation(data).conform(spec)
        spec.fields["value"] = spec.fields["value"].variant(missing_values=["", "NA"])
        new = ma.relation(data).conform(spec)
        self._check(old, expected=["NA"])
        self._check(new, expected=[None])

    @pytest.mark.parametrize("as_proxy", [False, True])
    def test_owns_contract_override(self, backend_name, backend_factory, as_proxy):
        from types import MappingProxyType

        data = backend_factory.create(
            {"value": [1], "support": [2]}, backend_name
        )
        spec = TableSchema(
            fields_match="open",
            fields={"value": FieldDefinition(type=UniversalType.INTEGER)},
        )
        override = {"extra_columns": "discard"}
        arg = MappingProxyType(override) if as_proxy else override
        old = ma.relation(data).conform(spec, contract=arg)
        override["extra_columns"] = "evolve"
        new = ma.relation(data).conform(spec, contract=arg)
        # schema inference keeps unmapped columns under an extra_columns=discard
        # override while execution drops them (separate defect, not ownership).
        self._check(old, expected_cols=["value"], schema_parity=False)
        self._check(new, expected_cols=["value", "support"])


def test_nested_override_freeze_uses_effective_child_type():
    import polars as pl
    spec = TableSchema(fields={"record": FieldDefinition(
        fields={"id": FieldDefinition(dtype=ma.MountainashDtype.I8, backend_type=pl.Int64)},
    )}, missing_values=[])
    source = pl.DataFrame({"record": [{"id": 300}, None]})
    with pytest.warns(UserWarning):
        out = ma.relation(source).conform(spec, contract={"data_type": "freeze"}).to_polars()
    assert out.schema["record"] == pl.Struct({"id": pl.Int64})
    assert out["record"].to_list() == [{"id": 300}, None]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("action", ["coerce", "evolve", "freeze", "discard_value", "discard_row"])
def test_native_override_reconciliation_policy(backend_name, backend_factory, action):
    from mountainash.conform.errors import SchemaDriftError
    from mountainash.core.types import BackendCapabilityError
    from ibis.common.exceptions import OperationNotDefinedError
    from fixtures.call_expectations import expect_call_failure
    discarding = action in {"discard_value", "discard_row"}
    values = ["1", "300", "bad"] if discarding else ["1", "300"]
    source = backend_factory.create({"value": values}, backend_name)
    override = "int64" if backend_name.startswith("ibis") else "Int64"
    spec = TableSchema(fields={"value": FieldDefinition(
        dtype=ma.MountainashDtype.I8, backend_type=override,
    )}, missing_values=[])
    rel = ma.relation(source).conform(spec, contract={"data_type": action})
    with pytest.warns(UserWarning, match="value"):
        if action == "freeze":
            with pytest.raises(SchemaDriftError):
                rel.to_polars()
            return
        with expect_call_failure(
            when=discarding and backend_name in {
                "pandas", "narwhals-polars", "narwhals-pandas", "narwhals-lazy", "ibis-sqlite",
            },
            errors=(OperationNotDefinedError,) if backend_name == "ibis-sqlite" else (BackendCapabilityError,),
            reason="Existing null-on-failure cast capability gap (known-divergences #19/#20)",
        ):
            out = rel.to_polars()
    if action == "evolve":
        assert out["value"].to_list() == ["1", "300"]
        assert rel.schema == ma.relation(source).schema
    else:
        assert out["value"].to_list() == ([1, 300, None] if action == "discard_value" else [1, 300])
        assert rel.schema["value"] is ma.MountainashDtype.I64


def test_native_container_override_replaces_nested_casts():
    # This native dtype is Polars-owned; other targets reject it.
    import polars as pl
    spec = TableSchema(fields={"record": FieldDefinition(
        fields={"id": FieldDefinition(dtype=ma.MountainashDtype.I8)},
        backend_type=pl.Struct({"id": pl.Int64}),
    )}, missing_values=[])
    source = pl.DataFrame({"record": [{"id": 128}, None]})
    with pytest.warns(UserWarning):
        out = ma.relation(source).conform(spec).to_polars()
    assert out.schema["record"] == pl.Struct({"id": pl.Int64})
    assert out["record"].to_list() == [{"id": 128}, None]


@pytest.mark.parametrize("values", [[], [None, None]])
@pytest.mark.parametrize("in_array", [False, True])
def test_null_typed_native_container_uses_declared_children(values, in_array):
    # Polars Null is schema evidence; pandas object is deliberately not equivalent.
    import polars as pl
    record = FieldDefinition(fields={"id": FieldDefinition(dtype=ma.MountainashDtype.I8)})
    field = FieldDefinition(element=record) if in_array else record
    out = ma.relation(pl.DataFrame({"record": values})).conform(
        TableSchema(fields={"record": field}, missing_values=[]),
    ).to_polars()
    expected = pl.List(pl.Struct({"id": pl.Int8})) if in_array else pl.Struct({"id": pl.Int8})
    assert out.schema["record"] == expected
    assert out["record"].to_list() == values


@pytest.mark.parametrize("action", ["discard_value", "discard_row"])
def test_null_container_fill_obeys_failure_policy(action):
    import polars as pl
    field = FieldDefinition(
        fields={"id": FieldDefinition(dtype=ma.MountainashDtype.I8)},
        null_fill={"id": 128})
    out = ma.relation(pl.DataFrame({"record": [None]})).conform(
        TableSchema(fields={"record": field}, missing_values=[]), contract={"data_type": action},
    ).to_polars()
    assert out.schema["record"] == pl.Struct({"id": pl.Int8})
    assert out["record"].to_list() == [{"id": None}]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("all_null", [False, True])
def test_parameterized_timestamp_conform_retains_known_type(backend_name, backend_factory, all_null, request):
    from datetime import datetime, timezone
    import polars as pl
    from mountainash.core.dtypes import TimestampDtype

    value = None if all_null else datetime(2026, 1, 1, microsecond=123456, tzinfo=timezone.utc)
    if backend_name == "ibis-sqlite" and not all_null:
        request.applymarker(pytest.mark.xfail(strict=True, raises=AssertionError,
            reason="298: Ibis-SQLite timestamp CAST truncates fractions to milliseconds"))
    if backend_name == "ibis-duckdb" and all_null:
        import ibis
        conn = ibis.duckdb.connect()
        source = conn.create_table(
            "parameterized_timestamp_nulls",
            {"at": [datetime(2026, 1, 1, tzinfo=timezone.utc), None]},
            overwrite=True,
        ).select(at=ibis.null().cast(ibis.expr.datatypes.Timestamp(timezone="UTC", scale=6)))
    else:
        source = backend_factory.create({"at": [value, None]}, backend_name)
    spec = TableSchema(
        fields={"at": FieldDefinition(dtype=TimestampDtype(6, True, "UTC"))},
        missing_values=[],
    )
    try:
        out = ma.relation(source).conform(spec).to_polars()
        assert out.schema["at"] == pl.Datetime("us", "UTC")
        assert out["at"].to_list() == [value, None]
    finally:
        if backend_name == "ibis-duckdb" and all_null:
            conn.disconnect()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("action", ["coerce", "evolve", "freeze", "discard_value", "discard_row"])
@pytest.mark.parametrize("format", ["default", "any"])
def test_parameterized_timestamp_actions_preserve_policy(backend_name, backend_factory, action, format, request):
    from datetime import datetime
    import polars as pl
    from mountainash.conform.errors import SchemaDriftError
    from mountainash.core.dtypes import TimestampDtype

    from fixtures.call_expectations import expect_call_failure
    from mountainash.core.types import BackendCapabilityError
    from ibis.common.exceptions import OperationNotDefinedError

    value = "2026-01-01T00:00:00.123456"
    values = [value] if action == "coerce" else [value, "not-a-timestamp", None]
    source = backend_factory.create({"at": values}, backend_name)
    spec = TableSchema(
        fields={"at": FieldDefinition(
            type=UniversalType.DATETIME,
            dtype=TimestampDtype(6, False, None),
            format=format,
        )},
        missing_values=[],
    )
    relation = ma.relation(source).conform(spec, contract={"data_type": action})
    if action == "freeze":
        with pytest.raises(SchemaDriftError):
            relation.to_polars()
        return
    with expect_call_failure(
        when=backend_name not in {"polars", "polars-lazy"} and action != "evolve",
        errors=(BackendCapabilityError, OperationNotDefinedError),
        reason="Existing default/arbitrary datetime parser capability",
    ):
        out = relation.to_polars()
    if action == "evolve":
        assert out.schema["at"] == pl.String
        assert out["at"].to_list() == values
        return
    assert out.schema["at"] == pl.Datetime("us")
    parsed = datetime(2026, 1, 1, microsecond=123456)
    if action == "coerce":
        assert out["at"].to_list() == [parsed]
    elif action == "discard_value":
        assert out["at"].to_list() == [parsed, None, None]
    else:
        assert out["at"].to_list() == [parsed, None]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_missing_parameterized_timestamp_is_typed_null(backend_name, backend_factory):
    import polars as pl
    from mountainash.core.dtypes import TimestampDtype

    source = backend_factory.create({"id": [1, 2]}, backend_name)
    spec = TableSchema(
        fields_match="open",
        fields={"at": FieldDefinition(dtype=TimestampDtype(6, True, "UTC"))},
        missing_values=[],
    )
    out = ma.relation(source).conform(
        spec, contract={"missing_columns": "null_fill"},
    ).to_polars()
    assert out.schema["at"] == pl.Datetime("us", "UTC")
    assert out["at"].to_list() == [None, None]
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_parameterized_nested_conform_preserves_null_shapes(backend_name, backend_factory):
    from datetime import datetime, timezone
    import polars as pl
    from mountainash.core.dtypes import TimestampDtype

    import json

    instant = datetime(2026, 1, 1, microsecond=123456, tzinfo=timezone.utc)
    records = [
        None,
        {"at": instant, "events": [{"id": 1}, None]},
        {"at": None, "events": None},
        {"at": None, "events": []},
        {"at": None, "events": [None]},
    ]
    physical = (
        [json.dumps(value, default=lambda value: value.isoformat()) if value is not None else None for value in records]
        if backend_name == "ibis-sqlite" else records
    )
    source = backend_factory.create({"record": physical}, backend_name)
    # The retired fixture declared a parent dtype (id: I16) beside child
    # metadata (id: I64); the parent dtype governed. Its effective single
    # declaration is the I16 child, in the parent's at/events order.
    children = {
        "at": FieldDefinition(
            type=UniversalType.DATETIME,
            dtype=TimestampDtype(6, True, "UTC"),
            format="any",
            description="event time",
        ),
        "events": FieldDefinition(
            type=UniversalType.ARRAY,
            element=FieldDefinition(fields={
                "id": FieldDefinition(type=UniversalType.INTEGER, dtype=ma.MountainashDtype.I16),
            }),
        ),
    }
    out = ma.relation(source).conform(TableSchema(
        fields={"record": FieldDefinition(type=UniversalType.OBJECT, fields=children)},
        missing_values=[],
    )).to_polars()
    assert out.schema["record"] == pl.Struct({
        "at": pl.Datetime("us", "UTC"),
        "events": pl.List(pl.Struct({"id": pl.Int16})),
    })
    assert out["record"].to_list() == [
        None,
        {"at": instant, "events": [{"id": 1}, None]},
        {"at": None, "events": None},
        {"at": None, "events": []},
        {"at": None, "events": [None]},
    ]
@pytest.mark.parametrize("target_precision", [6, 9, SchemaTypeStatus.UNKNOWN])
@pytest.mark.parametrize("action", ["coerce", "evolve", "freeze"])
def test_parameterized_timestamp_action_preserves_exact_ns(action, target_precision):
    """Polars ns storage is needed because Python datetime erases sub-us digits."""
    import polars as pl
    from mountainash.conform.errors import SchemaDriftError
    from mountainash.core.dtypes import TimestampDtype

    source = pl.DataFrame({"at": [1, 1001, 123456789, None]}).with_columns(
        pl.col("at").cast(pl.Datetime("ns", "UTC"))
    )
    spec = TableSchema(
        fields={"at": FieldDefinition(dtype=TimestampDtype(target_precision, True, "UTC"))},
        missing_values=[],
    )
    relation = ma.relation(source).conform(spec, contract={"data_type": action})
    if action == "freeze" and target_precision == 6:
        with pytest.raises(SchemaDriftError):
            relation.to_polars()
        return
    out = relation.to_polars()
    if action == "evolve" or target_precision in {9, SchemaTypeStatus.UNKNOWN}:
        assert out.schema["at"] == pl.Datetime("ns", "UTC")
        assert out["at"].dt.epoch("ns").to_list() == [1, 1001, 123456789, None]
    else:
        assert out.schema["at"] == pl.Datetime("us", "UTC")
        assert out["at"].dt.epoch("us").to_list() == [0, 1, 123456, None]

@pytest.mark.parametrize("nested", [False, True], ids=["struct", "list-struct"])
def test_partial_nested_timestamp_preserves_resolved_ns_precision(nested):
    import polars as pl
    from mountainash.core.dtypes import TimestampDtype

    source = pl.DataFrame({"value": [1, 1001, 123456789, None]}).with_columns(
        pl.col("value").cast(pl.Datetime("ns", "UTC"))
    )
    child = FieldDefinition(
        type=UniversalType.DATETIME,
        dtype=TimestampDtype(SchemaTypeStatus.UNKNOWN, True, "UTC"),
    )
    column = "items" if nested else "record"
    members = {"value": child}
    field = FieldDefinition(
        type=UniversalType.ARRAY, element=FieldDefinition(fields=members),
    ) if nested else FieldDefinition(type=UniversalType.OBJECT, fields=members)
    value = pl.struct("value")
    source = source.select((pl.concat_list(value) if nested else value).alias(column))
    out = ma.relation(source).conform(TableSchema(fields={column: field}, missing_values=[])).to_polars()
    actual = out[column].explode() if nested else out[column]
    actual = actual.struct.field("value")
    assert actual.dtype == pl.Datetime("ns", "UTC")
    assert actual.dt.epoch("ns").to_list() == [1, 1001, 123456789, None]

@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("action", ["coerce", "freeze"])
def test_aware_none_target_matches_utc_source(backend_name, backend_factory, action, request):
    from datetime import datetime, timezone
    import polars as pl
    from mountainash.core.dtypes import TimestampDtype

    if backend_name == "ibis-sqlite":
        request.applymarker(pytest.mark.xfail(strict=True, raises=AssertionError,
            reason="298: Ibis-SQLite timestamp CAST truncates fractions to milliseconds"))
    instant = datetime(2026, 1, 1, microsecond=123456, tzinfo=timezone.utc)
    source = backend_factory.create({"at": [instant, None]}, backend_name)
    target = TimestampDtype(6, True, None)
    spec = TableSchema(fields={"at": FieldDefinition(dtype=target)}, missing_values=[])
    out = ma.relation(source).conform(spec, contract={"data_type": action}).to_polars()
    assert out.schema["at"] == pl.Datetime("us", "UTC")
    assert out["at"].to_list() == [instant, None]
    assert target.timezone is None


@pytest.mark.parametrize("backend_name", ["polars", "polars-lazy"])
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("action", ["discard_value", "discard_row"])
def test_native_child_conversion_discards_invalid_parent_not_missing_child(
    backend_name, backend_factory, nested, action,
):
    # Native atomic nested discard is a Polars capability; the other native
    # providers' explicit capability outcomes are covered separately above.
    from datetime import datetime
    from mountainash.core.dtypes import TimestampDtype

    child = FieldDefinition(
        type=UniversalType.DATETIME, dtype=TimestampDtype(6, False), format="%Y%m%d",
        missing_values=["MISSING"],
    )
    field = (
        FieldDefinition(type=UniversalType.ARRAY, element=FieldDefinition(fields={"v": child}))
        if nested else FieldDefinition(type=UniversalType.OBJECT, fields={"v": child})
    )
    values = [{"v": "20260101"}, {"v": "bad"}, {"v": "MISSING"}, None]
    expected = [{"v": datetime(2026, 1, 1)}, None, {"v": None}, None]
    if nested:
        values = [[value, None] if value is not None else None for value in values]
        expected = [[value, None] if value is not None else None for value in expected]
    if action == "discard_row":
        del expected[1]
    source = backend_factory.create({"x": values}, backend_name)
    result = ma.relation(source).conform(
        TableSchema(fields={"x": field}, missing_values=[]), contract={"data_type": action},
    ).to_polars()
    assert result["x"].to_list() == expected
