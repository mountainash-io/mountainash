"""Unit tests for resolve_conform_output and ConformOutputContract.

These tests exercise the structural contract extraction — which fields are
emitted, their source names, declared types, and rename tracking — without
running any backend expression compilation.

Declared-type table (from spec 2026-06-25-conform-output-contract-design.md):

  | Shape                               | declared_type       |
  |-------------------------------------|---------------------|
  | type concrete (int/str/date/…)      | to_canonical(type)  |
  | type ANY/None, non-dotted, no fill  | PASSTHROUGH         |
  | type ANY/None + null_fill           | UNDETERMINED        |
  | type ANY/None, dotted source        | UNDETERMINED        |
  | categories                          | STRING              |
  | type ARRAY                          | to_canonical(ARRAY) |
"""
from __future__ import annotations

import pytest

from mountainash.conform.errors import (
    ExactFieldsMismatchError,
    ExtraFieldsError,
    MissingFieldsError,
    NoMatchingFieldsError,
)
from mountainash.conform.expressions import (
    PASSTHROUGH,
    UNDETERMINED,
    ConformOutputContract,
    EmittedField,
    resolve_conform_output,
)
from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType, to_canonical


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_UNSET = object()


def _spec(*fields, fields_match=_UNSET, missing_values=None):
    """Build a TypeSpec with minimal boilerplate.

    When ``fields_match`` is not supplied, the TypeSpec default ("exact")
    applies — the model default is non-optional post-cutover.
    """
    kwargs = {}
    if fields_match is not _UNSET:
        kwargs["fields_match"] = fields_match
    return TypeSpec(
        fields=list(fields),
        missing_values=missing_values or [],
        **kwargs,
    )


def _fld(name, type_=UniversalType.STRING, **kwargs):
    return FieldSpec(name=name, type=type_, **kwargs)


# ---------------------------------------------------------------------------
# fields_match resolution
# ---------------------------------------------------------------------------

class TestFieldsMatchResolution:
    """fields_match defaults to 'exact' when omitted; 'open' must be explicit."""

    def test_default_resolves_to_exact(self):
        spec = _spec(_fld("a"))
        contract = resolve_conform_output(spec, available_columns=["a"])
        assert contract.fields_match == "exact"

    def test_explicit_open(self):
        spec = _spec(_fld("a"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=None)
        assert contract.fields_match == "open"

    def test_explicit_equal(self):
        spec = _spec(_fld("a"), fields_match="equal")
        contract = resolve_conform_output(spec, available_columns=["a"])
        assert contract.fields_match == "equal"

    def test_keeps_unmapped_true_for_open(self):
        spec = _spec(_fld("a"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=None)
        assert contract.keeps_unmapped is True

    def test_keeps_unmapped_false_for_select(self):
        spec = _spec(_fld("a"), fields_match="equal")
        contract = resolve_conform_output(spec, available_columns=["a"])
        assert contract.keeps_unmapped is False


# ---------------------------------------------------------------------------
# open mode — skip-on-absent
# ---------------------------------------------------------------------------

class TestOpenModeSkipOnAbsent:
    """open mode: fields whose source root is absent are skipped."""

    def test_absent_field_skipped(self):
        spec = _spec(_fld("a"), _fld("b"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["a"])
        assert len(contract.emitted) == 1
        assert contract.emitted[0].field.name == "a"

    def test_all_absent_yields_empty(self):
        spec = _spec(_fld("a"), _fld("b"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["x", "y"])
        assert contract.emitted == []

    def test_all_present_yields_all(self):
        spec = _spec(_fld("a"), _fld("b"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["a", "b", "extra"])
        assert len(contract.emitted) == 2
        assert {em.field.name for em in contract.emitted} == {"a", "b"}

    def test_open_without_available_columns_includes_all(self):
        """open mode with available_columns=None: no skip guard, all fields emitted."""
        spec = _spec(_fld("a"), _fld("b"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=None)
        assert len(contract.emitted) == 2


# ---------------------------------------------------------------------------
# partial mode
# ---------------------------------------------------------------------------

class TestPartialMode:
    def test_partial_skips_absent(self):
        spec = _spec(_fld("a"), _fld("b"), fields_match="partial")
        contract = resolve_conform_output(spec, available_columns=["a"])
        assert len(contract.emitted) == 1
        assert contract.emitted[0].field.name == "a"

    def test_partial_raises_when_none_match(self):
        spec = _spec(_fld("a"), _fld("b"), fields_match="partial")
        with pytest.raises(NoMatchingFieldsError):
            resolve_conform_output(spec, available_columns=["x", "y"])


# ---------------------------------------------------------------------------
# superset mode
# ---------------------------------------------------------------------------

class TestSupersetMode:
    def test_superset_raises_on_extra(self):
        spec = _spec(_fld("a"), fields_match="superset")
        with pytest.raises(ExtraFieldsError):
            resolve_conform_output(spec, available_columns=["a", "b"])

    def test_superset_passes_when_exact(self):
        spec = _spec(_fld("a"), fields_match="superset")
        contract = resolve_conform_output(spec, available_columns=["a"])
        assert len(contract.emitted) == 1


# ---------------------------------------------------------------------------
# subset mode
# ---------------------------------------------------------------------------

class TestSubsetMode:
    def test_subset_raises_on_missing(self):
        spec = _spec(_fld("a"), _fld("b"), fields_match="subset")
        with pytest.raises(MissingFieldsError):
            resolve_conform_output(spec, available_columns=["a"])

    def test_subset_passes_when_all_present(self):
        spec = _spec(_fld("a"), _fld("b"), fields_match="subset")
        contract = resolve_conform_output(spec, available_columns=["a", "b"])
        assert len(contract.emitted) == 2


# ---------------------------------------------------------------------------
# equal mode
# ---------------------------------------------------------------------------

class TestEqualMode:
    def test_equal_raises_on_missing(self):
        spec = _spec(_fld("a"), _fld("b"), fields_match="equal")
        with pytest.raises(MissingFieldsError):
            resolve_conform_output(spec, available_columns=["a"])

    def test_equal_raises_on_extra(self):
        spec = _spec(_fld("a"), fields_match="equal")
        with pytest.raises(ExtraFieldsError):
            resolve_conform_output(spec, available_columns=["a", "b"])

    def test_equal_passes_exact_match(self):
        spec = _spec(_fld("a"), _fld("b"), fields_match="equal")
        contract = resolve_conform_output(spec, available_columns=["a", "b"])
        assert len(contract.emitted) == 2


# ---------------------------------------------------------------------------
# exact mode — positional mapping
# ---------------------------------------------------------------------------

class TestExactMode:
    def test_exact_maps_by_name_after_order_guard(self):
        spec = _spec(_fld("x"), _fld("y"), fields_match="exact")
        contract = resolve_conform_output(spec, available_columns=["x", "y"])
        assert [field.source_name for field in contract.emitted] == ["x", "y"]

    def test_exact_raises_on_count_mismatch(self):
        spec = _spec(_fld("x"), _fld("y"), fields_match="exact")
        with pytest.raises(ExactFieldsMismatchError) as exc_info:
            resolve_conform_output(spec, available_columns=["x"])
        assert exc_info.value.reason == "count"


# ---------------------------------------------------------------------------
# Rename tracking
# ---------------------------------------------------------------------------

class TestRenameTracking:
    def test_rename_from_tracked(self):
        spec = _spec(
            _fld("target", rename_from="source"),
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["source"])
        assert "source" in contract.renamed_sources
        assert contract.emitted[0].renamed is True
        assert contract.emitted[0].source_name == "source"

    def test_no_rename_when_names_equal(self):
        spec = _spec(_fld("a"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["a"])
        assert contract.renamed_sources == set()
        assert contract.emitted[0].renamed is False

    def test_dotted_source_not_tracked_as_rename(self):
        """Dotted sources are struct access paths, not column renames."""
        spec = _spec(
            FieldSpec(name="strain", type=UniversalType.NUMBER, rename_from="score.strain"),
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["score"])
        # root col "score" is present → emitted
        assert len(contract.emitted) == 1
        assert contract.emitted[0].source_name == "score.strain"
        # dotted → no rename tracking
        assert "score" not in contract.renamed_sources
        assert contract.emitted[0].renamed is False


# ---------------------------------------------------------------------------
# Dotted source — struct field access
# ---------------------------------------------------------------------------

class TestDottedSource:
    def test_dotted_root_checked_for_availability(self):
        """The root col (before '.') must be in available_columns."""
        spec = _spec(
            FieldSpec(name="city", type=UniversalType.STRING, rename_from="address.city"),
            fields_match="open",
        )
        # root "address" not available → skipped
        contract = resolve_conform_output(spec, available_columns=["other"])
        assert contract.emitted == []

    def test_dotted_root_present_includes_field(self):
        spec = _spec(
            FieldSpec(name="city", type=UniversalType.STRING, rename_from="address.city"),
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["address"])
        assert len(contract.emitted) == 1
        assert contract.emitted[0].source_name == "address.city"


# ---------------------------------------------------------------------------
# declared_type — the Declared-type table
# ---------------------------------------------------------------------------

class TestDeclaredType:
    """declared_type values must match the spec table exactly."""

    def test_concrete_type_yields_canonical_dtype(self):
        """Non-ANY concrete types → to_canonical(type)."""
        cases = [
            (UniversalType.INTEGER, to_canonical(UniversalType.INTEGER)),
            (UniversalType.NUMBER,  to_canonical(UniversalType.NUMBER)),
            (UniversalType.STRING,  to_canonical(UniversalType.STRING)),
            (UniversalType.BOOLEAN, to_canonical(UniversalType.BOOLEAN)),
            (UniversalType.DATE,    to_canonical(UniversalType.DATE)),
        ]
        for utype, expected in cases:
            spec = _spec(FieldSpec(name="f", type=utype), fields_match="open")
            contract = resolve_conform_output(spec, available_columns=["f"])
            assert contract.emitted[0].declared_type == expected, (
                f"Expected {expected} for {utype}, got {contract.emitted[0].declared_type}"
            )

    def test_any_no_fill_non_dotted_yields_passthrough(self):
        """ANY type, non-dotted source, no null_fill → PASSTHROUGH."""
        spec = _spec(FieldSpec(name="f", type=UniversalType.ANY), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["f"])
        assert contract.emitted[0].declared_type is PASSTHROUGH

    def test_none_type_no_fill_non_dotted_yields_passthrough(self):
        """type=None (falls to ANY branch), non-dotted, no null_fill → PASSTHROUGH."""
        spec = _spec(FieldSpec(name="f", type=None), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["f"])
        assert contract.emitted[0].declared_type is PASSTHROUGH

    def test_any_with_null_fill_yields_undetermined(self):
        """ANY type + null_fill → UNDETERMINED (coalesce may coerce dtype)."""
        spec = _spec(
            FieldSpec(name="f", type=UniversalType.ANY, null_fill=""),
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["f"])
        assert contract.emitted[0].declared_type is UNDETERMINED

    def test_any_dotted_source_yields_undetermined(self):
        """ANY type + dotted source → UNDETERMINED (nested ≠ struct root type)."""
        spec = _spec(
            FieldSpec(name="f", type=UniversalType.ANY, rename_from="payload.id"),
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["payload"])
        assert contract.emitted[0].declared_type is UNDETERMINED

    def test_categories_yields_string(self):
        """categories → STRING (dtype registry maps Categorical/Enum → STRING)."""
        spec = _spec(
            FieldSpec(name="f", type=UniversalType.STRING, categories=["a", "b"]),
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["f"])
        assert contract.emitted[0].declared_type == MountainashDtype.STRING

    def test_categories_on_integer_field_yields_string(self):
        """categories on an integer-base field still → STRING (registry rule)."""
        spec = _spec(
            FieldSpec(name="f", type=UniversalType.INTEGER, categories=[1, 2, 3]),
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["f"])
        assert contract.emitted[0].declared_type == MountainashDtype.STRING

    def test_array_type_yields_canonical_array(self):
        """ARRAY → to_canonical(ARRAY)."""
        spec = _spec(
            FieldSpec(name="f", type=UniversalType.ARRAY),
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["f"])
        expected = to_canonical(UniversalType.ARRAY)
        assert contract.emitted[0].declared_type == expected

    def test_list_type_yields_canonical_list(self):
        """LIST lexical parsing still emits the physical canonical list."""
        field = FieldSpec(name="f", type=UniversalType.LIST, item_type="integer")
        spec = _spec(field, fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["f"])
        assert contract.emitted[0].declared_type == to_canonical(UniversalType.LIST)

    def test_temporal_with_custom_format_yields_canonical(self):
        """DATE/DATETIME/TIME with custom format → to_canonical(type)."""
        spec = _spec(
            FieldSpec(name="f", type=UniversalType.DATE, format="%Y/%m/%d"),
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["f"])
        assert contract.emitted[0].declared_type == to_canonical(UniversalType.DATE)

    def test_temporal_with_default_format_yields_canonical(self):
        """DATE with default format falls to stage-5d → to_canonical(DATE)."""
        spec = _spec(
            FieldSpec(name="f", type=UniversalType.DATE),  # format defaults to "default"
            fields_match="open",
        )
        contract = resolve_conform_output(spec, available_columns=["f"])
        assert contract.emitted[0].declared_type == to_canonical(UniversalType.DATE)


    @pytest.mark.parametrize(
        "format_name",
        ["default", "array", "object"],
    )
    def test_geopoint_formats_use_field_aware_canonical(
        self, format_name
    ):
        from mountainash.typespec.converters import resolve_field_canonical

        field = FieldSpec(
            name="location",
            type=UniversalType.GEOPOINT,
            format=format_name,
        )
        spec = _spec(field, fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["location"])
        assert contract.emitted[0].declared_type == resolve_field_canonical(field)

    @pytest.mark.parametrize("format_name", ["default", "topojson"])
    def test_geojson_formats_use_field_aware_canonical(self, format_name):
        from mountainash.typespec.converters import resolve_field_canonical

        field = FieldSpec(
            name="geometry",
            type=UniversalType.GEOJSON,
            format=format_name,
        )
        spec = _spec(field, fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["geometry"])
        assert contract.emitted[0].declared_type == resolve_field_canonical(field)

# ---------------------------------------------------------------------------
# ConformOutputContract structural properties
# ---------------------------------------------------------------------------

class TestConformOutputContractStructure:
    def test_emitted_order_matches_spec_field_order(self):
        spec = _spec(_fld("c"), _fld("a"), _fld("b"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["a", "b", "c"])
        assert [em.field.name for em in contract.emitted] == ["c", "a", "b"]

    def test_renamed_sources_accumulates_multiple_renames(self):
        spec = _spec(
            FieldSpec(name="x", type=UniversalType.STRING, rename_from="src_x"),
            FieldSpec(name="y", type=UniversalType.STRING, rename_from="src_y"),
            fields_match="open",
        )
        contract = resolve_conform_output(
            spec, available_columns=["src_x", "src_y"]
        )
        assert contract.renamed_sources == {"src_x", "src_y"}

    def test_empty_spec_yields_empty_contract(self):
        spec = _spec(fields_match="open")
        contract = resolve_conform_output(spec, available_columns=[])
        assert contract.emitted == []
        assert contract.renamed_sources == set()

    def test_emitted_field_is_frozen_dataclass(self):
        spec = _spec(_fld("a"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["a"])
        em = contract.emitted[0]
        assert isinstance(em, EmittedField)
        # frozen → immutable
        with pytest.raises((AttributeError, TypeError)):
            em.field = None  # type: ignore[misc]

    def test_contract_is_frozen_dataclass(self):
        spec = _spec(_fld("a"), fields_match="open")
        contract = resolve_conform_output(spec, available_columns=["a"])
        assert isinstance(contract, ConformOutputContract)
        with pytest.raises((AttributeError, TypeError)):
            contract.fields_match = "equal"  # type: ignore[misc]
