"""Schema inference unit tests for ConformRelNode.

Covers the unit matrix described in the conform-output-contract design spec
(Consumer 2 — schema introspection): open mode pass-through extras, the five
select modes (exact / equal / subset / superset / partial), renamed sources,
non-dotted ANY w/o transform → source type, ANY + null_fill → UNKNOWN,
typed cast → concrete dtype, and a spec given as a raw Frictionless dict.

Also includes parity-guard tests asserting that inferred schema column names
match ``rel.to_polars().columns`` and that concretely-typed inferred dtypes
agree with the registry-mapped Polars output dtypes — including the critical
non-string categorical case (Polars Enum/Categorical → canonical STRING).
"""
from __future__ import annotations

import polars as pl

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.dtypes import TypeTarget, registry
from mountainash.relations.schema_inference import (
    SchemaTypeStatus,
    infer_schema,
)
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType as U


def _infer(rel):
    return infer_schema(rel._node)


# ---------------------------------------------------------------------------
# Unit matrix
# ---------------------------------------------------------------------------

class TestOpenMode:
    """fields_match='open' (or None default) — with_columns semantics."""

    def test_open_keeps_unmapped_extras(self):
        df = pl.DataFrame({"a": [1], "b": [2], "c": ["x"]})
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=U.INTEGER)],
            fields_match="open",
        )
        schema = _infer(ma.relation(df).conform(spec))
        # Spec field 'a' is in output, plus unmapped 'b' and 'c'.
        assert set(schema.keys()) == {"a", "b", "c"}
        assert schema["a"] == D.I64
        assert schema["b"] == D.I64
        assert schema["c"] == D.STRING

    def test_open_renamed_source_drops_original(self):
        df = pl.DataFrame({"src_a": [1], "b": [2]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="a", type=U.INTEGER, rename_from="src_a",
                ),
            ],
            fields_match="open",
        )
        schema = _infer(ma.relation(df).conform(spec))
        # 'src_a' was renamed → dropped; 'a' present; 'b' pass-through.
        assert set(schema.keys()) == {"a", "b"}
        assert schema["a"] == D.I64
        assert schema["b"] == D.I64

    def test_open_typed_cast(self):
        df = pl.DataFrame({"a": ["1", "2"]})  # string source, cast to INTEGER
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=U.INTEGER)],
            fields_match="open",
        )
        schema = _infer(ma.relation(df).conform(spec))
        assert schema["a"] == D.I64

    def test_open_any_no_transform_passthrough_source_type(self):
        # Non-dotted ANY type with no null_fill → passthrough → source dtype.
        df = pl.DataFrame({"a": [1.5, 2.5]})
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=U.ANY)],
            fields_match="open",
        )
        schema = _infer(ma.relation(df).conform(spec))
        # 'a' source dtype is F64, passthrough yields F64.
        assert schema["a"] == D.FP64

    def test_open_any_with_null_fill_undetermined(self):
        df = pl.DataFrame({"a": [1, None]})
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=U.ANY, null_fill=0)],
            fields_match="open",
        )
        schema = _infer(ma.relation(df).conform(spec))
        # ANY + null_fill → UNDETERMINED → UNKNOWN.
        assert schema["a"] == SchemaTypeStatus.UNKNOWN


class TestSelectExact:
    def test_select_exact_positional_mapping(self):
        df = pl.DataFrame({"x_src": [1], "y_src": ["a"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="x", type=U.INTEGER),
                FieldSpec(name="y", type=U.STRING),
            ],
            fields_match="exact",
        )
        schema = _infer(ma.relation(df).conform(spec))
        # Projection only — no extras.
        assert list(schema.keys()) == ["x", "y"]
        assert schema["x"] == D.I64
        assert schema["y"] == D.STRING


class TestSelectEqual:
    def test_select_equal_one_to_one(self):
        df = pl.DataFrame({"a": [1], "b": ["x"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=U.INTEGER),
                FieldSpec(name="b", type=U.STRING),
            ],
            fields_match="equal",
        )
        schema = _infer(ma.relation(df).conform(spec))
        assert set(schema.keys()) == {"a", "b"}


class TestSelectSubset:
    def test_select_subset_drops_extras(self):
        # Subset: spec is subset of available — extras are dropped from output.
        df = pl.DataFrame({"a": [1], "b": ["x"], "extra": [3.14]})
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=U.INTEGER)],
            fields_match="subset",
        )
        schema = _infer(ma.relation(df).conform(spec))
        assert list(schema.keys()) == ["a"]
        assert schema["a"] == D.I64


class TestSelectSuperset:
    def test_select_superset_skips_absent_sources(self):
        # Superset: spec may declare more than available; absent skipped in infer.
        df = pl.DataFrame({"a": [1]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=U.INTEGER),
                FieldSpec(name="missing", type=U.STRING),
            ],
            fields_match="superset",
        )
        schema = _infer(ma.relation(df).conform(spec))
        assert list(schema.keys()) == ["a"]


class TestSelectPartial:
    def test_select_partial_some_present_some_absent(self):
        df = pl.DataFrame({"a": [1], "c": [2.0]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=U.INTEGER),
                FieldSpec(name="b", type=U.STRING),
                FieldSpec(name="c", type=U.NUMBER),
            ],
            fields_match="partial",
        )
        schema = _infer(ma.relation(df).conform(spec))
        # Only 'a' and 'c' have sources available; 'b' skipped.
        assert set(schema.keys()) == {"a", "c"}
        assert schema["a"] == D.I64
        assert schema["c"] == D.FP64


class TestFrictionlessDictSpec:
    """Spec provided as a raw Frictionless dict — exercises typespec_from_frictionless."""

    def test_frictionless_dict_spec(self):
        df = pl.DataFrame({"a": [1], "b": ["x"]})
        # Raw Frictionless schema dict (not a TypeSpec)
        spec_dict = {
            "fields": [
                {"name": "a", "type": "integer"},
                {"name": "b", "type": "string"},
            ],
            "fieldsMatch": "equal",
        }
        rel = ma.relation(df).conform(spec_dict)
        schema = _infer(rel)
        assert set(schema.keys()) == {"a", "b"}
        assert schema["a"] == D.I64
        assert schema["b"] == D.STRING


# ---------------------------------------------------------------------------
# Parity guards: inferred vs to_polars() (the anti-drift oracle)
# ---------------------------------------------------------------------------

def _polars_schema_canonical(plschema):
    """Map a Polars Schema to canonical MountainashDtype dict."""
    out = {}
    for name, dtype in zip(plschema.names(), plschema.dtypes()):
        canon = registry.from_native(dtype, target=TypeTarget.POLARS)
        out[name] = canon
    return out


class TestParityGuards:
    def test_parity_open_typed_cast(self):
        df = pl.DataFrame({"a": ["1", "2"], "b": ["keep", "me"]})
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=U.INTEGER)],
            fields_match="open",
        )
        rel = ma.relation(df).conform(spec)
        inferred = _infer(rel)
        actual = rel.to_polars().schema
        assert set(inferred.keys()) == set(actual.names())
        for name, dt in inferred.items():
            if isinstance(dt, SchemaTypeStatus):
                continue
            actual_canon = _polars_schema_canonical(actual)[name]
            assert dt == actual_canon, f"{name}: inferred={dt} actual={actual_canon}"

    def test_parity_select_exact_order(self):
        # Exact-mode order parity: inferred == to_polars() for fields_match='exact'.
        df = pl.DataFrame({"x_src": [1], "y_src": ["a"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="x", type=U.INTEGER),
                FieldSpec(name="y", type=U.STRING),
            ],
            fields_match="exact",
        )
        rel = ma.relation(df).conform(spec)
        inferred = _infer(rel)
        actual = rel.to_polars().schema
        assert list(inferred.keys()) == list(actual.names())

    def test_parity_categorical_string_field(self):
        # Categorical on a STRING field → registry maps pl.Categorical → STRING.
        df = pl.DataFrame({"grade": ["A", "B", "A"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="grade", type=U.STRING, categories=["A", "B"],
                ),
            ],
            fields_match="open",
        )
        rel = ma.relation(df).conform(spec)
        inferred = _infer(rel)
        actual = rel.to_polars().schema
        assert set(inferred.keys()) == set(actual.names())
        # Categorical → canonical STRING per registry.
        assert inferred["grade"] == D.STRING
        assert _polars_schema_canonical(actual)["grade"] == D.STRING

    def test_categorical_on_non_string_field_infers_string(self):
        # Critical oracle: INTEGER-typed field + categories constraint must
        # report STRING (Polars Enum/Categorical → canonical STRING).
        # We don't call to_polars() here because Polars cannot cast Int64→Cat
        # without an intermediate string step — the inference contract is what
        # we're verifying.
        df = pl.DataFrame({"grade": ["1", "2", "3"]})  # string source
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="grade", type=U.INTEGER, categories=[1, 2, 3],
                ),
            ],
            fields_match="open",
        )
        rel = ma.relation(df).conform(spec)
        inferred = _infer(rel)
        assert inferred["grade"] == D.STRING
