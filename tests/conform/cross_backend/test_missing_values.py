"""Tests for missingValues transform stage in the conform pipeline."""
from __future__ import annotations

import warnings

import pytest
import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS

# ALL_BACKENDS = [
#     "polars",
#     "pandas",
#     "narwhals",
#     "ibis-duckdb",
#     "ibis-sqlite",
# ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_missing_values_schema_level_labeled_sentinel(
    backend_name, backend_factory
) -> None:
    from mountainash.typespec.spec import LabeledValue

    spec = TypeSpec(fields={"value": FieldSpec(type=UniversalType.STRING)}, missing_values=[LabeledValue("", "Empty")],)
    frame = backend_factory.create({"value": ["ok", ""]}, backend_name)
    assert ma.relation(frame).conform(spec).to_polars()["value"].to_list() == [
        "ok",
        None,
    ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_missing_values_field_level_labeled_sentinel(
    backend_name, backend_factory
) -> None:
    from mountainash.typespec.spec import LabeledValue

    spec = TypeSpec(fields={"value": FieldSpec(type=UniversalType.STRING,
    missing_values=[LabeledValue("", "Empty")],)})
    frame = backend_factory.create({"value": ["ok", ""]}, backend_name)
    assert ma.relation(frame).conform(spec).to_polars()["value"].to_list() == [
        "ok",
        None,
    ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "missing_values,expected",
    [
        (None, ["ok", None]),
        ([], ["ok", ""]),
    ],
)
def test_missing_values_default_and_explicit_empty(
    backend_name, backend_factory, missing_values, expected
) -> None:
    kwargs = {} if missing_values is None else {"missing_values": missing_values}
    spec = TypeSpec(
        fields={"value": FieldSpec(type=UniversalType.STRING)},
        **kwargs,
    )
    frame = backend_factory.create({"value": ["ok", ""]}, backend_name)
    assert ma.relation(frame).conform(spec).to_polars()["value"].to_list() == expected


# ---------------------------------------------------------------------------
# Cross-backend integration: schema-level missingValues
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMissingValuesSchemaLevel:
    def test_default_empty_string_becomes_null(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["a", "", "c"]}, backend_name)
        spec = TypeSpec(fields_match="open", fields={"val": FieldSpec(type=UniversalType.STRING)}, missing_values=[""],)
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["a", None, "c"]

    def test_custom_missing_values(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1", "NaN", "-", "4"]}, backend_name)
        spec = TypeSpec(fields_match="open", fields={"val": FieldSpec(type=UniversalType.STRING)}, missing_values=["NaN", "-"],)
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["1", None, None, "4"]

    def test_empty_sentinel_list_no_replacement(self, backend_name, backend_factory):
        """When missingValues=[] (explicit empty), no sentinels are replaced."""
        df = backend_factory.create({"val": ["a", "", "c"]}, backend_name)
        spec = TypeSpec(fields_match="open", fields={"val": FieldSpec(type=UniversalType.STRING)}, missing_values=[],)
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["a", "", "c"]


# ---------------------------------------------------------------------------
# Cross-backend integration: field-level missingValues override
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMissingValuesFieldLevel:
    def test_field_level_overrides_schema_level(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": ["x", "", "-"], "b": ["y", "", "-"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", fields={"a": FieldSpec(type=UniversalType.STRING), "b": FieldSpec(type=UniversalType.STRING, missing_values=["-"])}, missing_values=[""],)
        result = ma.relation(df).conform(spec).to_polars()
        # "a" uses schema-level [""] → empty string becomes null
        assert result["a"].to_list() == ["x", None, "-"]
        # "b" uses field-level ["-"] → dash becomes null, empty string kept
        assert result["b"].to_list() == ["y", "", None]


# ---------------------------------------------------------------------------
# Cross-backend integration: interaction with null_fill
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMissingValuesInteraction:
    def test_missing_values_before_null_fill(self, backend_name, backend_factory):
        """missingValues converts sentinel → null, then null_fill replaces null."""
        df = backend_factory.create({"val": ["1", "NA", "3"]}, backend_name)
        spec = TypeSpec(fields_match="open", fields={"val": FieldSpec(type=UniversalType.STRING, null_fill="UNKNOWN")}, missing_values=["NA"],)
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["1", "UNKNOWN", "3"]


# ---------------------------------------------------------------------------
# Boolean overlap warning (build-time only, no backend needed)
# ---------------------------------------------------------------------------


class TestMissingValuesBooleanOverlapWarning:
    def test_warns_on_overlap_with_false_values(self):
        import polars as pl

        spec = TypeSpec(
            fields={
                "flag": FieldSpec(
                    type=UniversalType.BOOLEAN,
                    false_values=["false", "False", "FALSE", "0"],
                ),
            },
            missing_values=["", "0"],
            fields_match="open",
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ma.relation(pl.DataFrame({"flag": ["0"]})).conform(spec).to_polars()
            overlap_warnings = [
                x for x in w if "overlap" in str(x.message).lower()
            ]
            assert len(overlap_warnings) >= 1

    def test_warns_on_overlap_with_true_values(self):
        import polars as pl

        spec = TypeSpec(
            fields={
                "flag": FieldSpec(
                    type=UniversalType.BOOLEAN, true_values=["yes", "1"]
                ),
            },
            missing_values=["1"],
            fields_match="open",
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ma.relation(pl.DataFrame({"flag": ["1"]})).conform(spec).to_polars()
            overlap_warnings = [
                x for x in w if "overlap" in str(x.message).lower()
            ]
            assert len(overlap_warnings) >= 1

    def test_no_warning_when_no_overlap(self):
        import polars as pl

        spec = TypeSpec(
            fields={"flag": FieldSpec(type=UniversalType.BOOLEAN)},
            missing_values=["NA", ""],
            fields_match="open",
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ma.relation(pl.DataFrame({"flag": ["true"]})).conform(spec).to_polars()
            overlap_warnings = [
                x for x in w if "overlap" in str(x.message).lower()
            ]
            assert len(overlap_warnings) == 0
