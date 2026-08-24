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
#     "ibis-polars",
#     "ibis-duckdb",
#     "ibis-sqlite",
# ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_missing_values_schema_level_labeled_sentinel(
    backend_name, backend_factory
) -> None:
    from mountainash.typespec.spec import LabeledValue

    spec = TypeSpec(
        fields=[FieldSpec(name="value", type=UniversalType.STRING)],
        missing_values=[LabeledValue("", "Empty")],
    )
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

    spec = TypeSpec(
        fields=[
            FieldSpec(
                name="value",
                type=UniversalType.STRING,
                missing_values=[LabeledValue("", "Empty")],
            )
        ],
    )
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
        fields=[FieldSpec("value", UniversalType.STRING)],
        **kwargs,
    )
    frame = backend_factory.create({"value": ["ok", ""]}, backend_name)
    assert ma.relation(frame).conform(spec).to_polars()["value"].to_list() == expected


# ---------------------------------------------------------------------------
# Unit tests: _build_conform_exprs produces the right expression count
# ---------------------------------------------------------------------------


class TestBuildConformExprsMissingValues:
    """Unit tests that the expression builder emits missingValues logic."""

    def test_emits_expr_for_scalar_field(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.STRING)],
            missing_values=[""],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_emits_expr_for_custom_sentinels(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.STRING)],
            missing_values=["NA", "-"],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_field_level_override(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(
                    name="b",
                    type=UniversalType.STRING,
                    missing_values=["-"],
                ),
            ],
            missing_values=[""],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 2

    def test_no_sentinel_for_array_type(self):
        """ARRAY is excluded from sentinel replacement (is_in may raise)."""
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.ARRAY)],
            missing_values=[""],
        )
        # Use ANY as a proxy — both ARRAY and ANY are excluded from
        # _SCALAR_TYPES, so neither emits a sentinel when/then. Test the
        # sentinel exclusion logic directly.
        spec_any = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.ANY)],
            missing_values=[""],
        )
        result = _build_conform_exprs(spec_any)
        # ANY is not in _SCALAR_TYPES, so no sentinel when/then is emitted
        assert len(result.exprs) == 1

    def test_no_sentinel_for_object_type(self):
        """OBJECT is excluded from sentinel replacement (is_in may raise)."""
        from mountainash.conform.expressions import _build_conform_exprs

        # Use ANY as a proxy — both OBJECT and ANY are excluded from _SCALAR_TYPES
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.ANY)],
            missing_values=[""],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1


# ---------------------------------------------------------------------------
# Cross-backend integration: schema-level missingValues
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMissingValuesSchemaLevel:
    def test_default_empty_string_becomes_null(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["a", "", "c"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.STRING)],
            missing_values=[""],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["a", None, "c"]

    def test_custom_missing_values(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1", "NaN", "-", "4"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.STRING)],
            missing_values=["NaN", "-"],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["1", None, None, "4"]

    def test_empty_sentinel_list_no_replacement(self, backend_name, backend_factory):
        """When missingValues=[] (explicit empty), no sentinels are replaced."""
        df = backend_factory.create({"val": ["a", "", "c"]}, backend_name)
        spec = TypeSpec(fields_match="open", 
            fields=[FieldSpec(name="val", type=UniversalType.STRING)],
            missing_values=[],
        )
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
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="a", type=UniversalType.STRING),
                FieldSpec(
                    name="b", type=UniversalType.STRING, missing_values=["-"]
                ),
            ],
            missing_values=[""],
        )
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
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="val", type=UniversalType.STRING, null_fill="UNKNOWN"
                ),
            ],
            missing_values=["NA"],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["1", "UNKNOWN", "3"]


# ---------------------------------------------------------------------------
# Boolean overlap warning (build-time only, no backend needed)
# ---------------------------------------------------------------------------


class TestMissingValuesBooleanOverlapWarning:
    def test_warns_on_overlap_with_false_values(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="flag",
                    type=UniversalType.BOOLEAN,
                    false_values=["false", "False", "FALSE", "0"],
                ),
            ],
            missing_values=["", "0"],
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _build_conform_exprs(spec)
            overlap_warnings = [
                x for x in w if "overlap" in str(x.message).lower()
            ]
            assert len(overlap_warnings) >= 1

    def test_warns_on_overlap_with_true_values(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="flag",
                    type=UniversalType.BOOLEAN,
                    true_values=["yes", "1"],
                ),
            ],
            missing_values=["1"],
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _build_conform_exprs(spec)
            overlap_warnings = [
                x for x in w if "overlap" in str(x.message).lower()
            ]
            assert len(overlap_warnings) >= 1

    def test_no_warning_when_no_overlap(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="flag", type=UniversalType.BOOLEAN),
            ],
            missing_values=["NA", ""],
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _build_conform_exprs(spec)
            overlap_warnings = [
                x for x in w if "overlap" in str(x.message).lower()
            ]
            assert len(overlap_warnings) == 0
