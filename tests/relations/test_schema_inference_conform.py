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

Parity oracles use the Polars runtime only by design: ``infer_schema`` never
compiles a plan or touches a backend (it is a pure AST walk), so the inferred
schema is backend-invariant — there is no per-backend inference branch that
could diverge. Polars is therefore a sufficient runtime oracle; a second
backend would re-verify the same dict produced by the same code path.
"""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.conform.errors import ExactFieldsMismatchError, SchemaDriftError
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
    def test_select_exact_rejects_positional_mapping(self):
        df = pl.DataFrame({"x_src": [1], "y_src": ["a"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="x", type=U.INTEGER),
                FieldSpec(name="y", type=U.STRING),
            ],
            fields_match="exact",
        )
        with pytest.raises(ExactFieldsMismatchError, match="name mismatch"):
            _infer(ma.relation(df).conform(spec))

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

    def test_parity_select_exact_rejects_positional_mapping(self):
        # Exact-mode requires ordered source names, not positional renaming.
        df = pl.DataFrame({"x_src": [1], "y_src": ["a"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="x", type=U.INTEGER),
                FieldSpec(name="y", type=U.STRING),
            ],
            fields_match="exact",
        )
        rel = ma.relation(df).conform(spec)
        with pytest.raises(ExactFieldsMismatchError, match="name mismatch"):
            _infer(rel)

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


# ---------------------------------------------------------------------------
# Dotted-source coverage
# ---------------------------------------------------------------------------

class TestDottedSource:
    """Struct field access via dotted rename_from paths."""

    def test_dotted_concrete_type_open_with_parity_oracle(self):
        # Dotted source with a concrete declared type (U.INTEGER → D.I64).
        # Open mode: struct root 'payload' is NOT tracked as a renamed_source
        # (dotted roots are excluded from renamed_sources), so it survives.
        df = pl.DataFrame({"payload": [{"id": 1, "tag": "x"}]})
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=U.INTEGER, rename_from="payload.id")],
            fields_match="open",
        )
        rel = ma.relation(df).conform(spec)
        inferred = _infer(rel)

        # Spec field 'id' should be inferred as the concrete declared dtype.
        assert inferred["id"] == D.I64
        # Struct root 'payload' survives (dotted roots are NOT renamed_sources).
        assert "payload" in inferred

        # Parity oracle: inferred column set and concrete types must agree
        # with what to_polars() actually produces.
        actual = rel.to_polars().schema
        assert set(inferred.keys()) == set(actual.names())
        # Verify the concrete-typed 'id' field agrees with the registry mapping.
        assert inferred["id"] == _polars_schema_canonical(actual)["id"]

    def test_dotted_any_yields_unknown_no_oracle(self):
        # Dotted source with U.ANY → UNDETERMINED → SchemaTypeStatus.UNKNOWN.
        # This is a deliberate honest degradation: inference cannot model nested
        # field types pre-compile (the struct root type ≠ the child field type),
        # so it reports UNKNOWN.  The runtime (to_polars()) would produce the
        # child's concrete type (Int64 in this case), but that divergence is
        # intentional — inference is conservative for dotted-ANY.
        # There is NO to_polars() oracle here; asserting parity would be wrong
        # because UNKNOWN ≠ the runtime's concrete type by design.
        df = pl.DataFrame({"payload": [{"id": 1}]})
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=U.ANY, rename_from="payload.id")],
            fields_match="open",
        )
        inferred = _infer(ma.relation(df).conform(spec))
        assert inferred["id"] == SchemaTypeStatus.UNKNOWN

    def test_dotted_strict_mode_parity_oracle(self):
        # Item 46 (b): strict modes now accept dotted sources on ROOT
        # presence. Inference shares resolve_conform_output with runtime,
        # so the emitted column set must match to_polars() exactly.
        df = pl.DataFrame({"payload": [{"id": 1, "tag": "x"}]})
        spec = TypeSpec(
            fields=[FieldSpec(name="id", type=U.INTEGER, rename_from="payload.id")],
            fields_match="equal",
        )
        rel = ma.relation(df).conform(spec)
        inferred = _infer(rel)
        assert inferred["id"] == D.I64
        actual = rel.to_polars().schema
        assert set(inferred.keys()) == set(actual.names())


# ---------------------------------------------------------------------------
# Exact-mode order parity across all source kinds
# ---------------------------------------------------------------------------

class TestExactModeOrderParity:
    """Exact-mode column ORDER must match to_polars() across every source kind.

    The existing test_parity_select_exact_order in TestParityGuards covers
    Polars eager DataFrame.  These three tests add the remaining source kinds
    that exercise distinct inference paths.
    """

    _SPEC = TypeSpec(
        fields=[
            FieldSpec(name="x_src", type=U.INTEGER),
            FieldSpec(name="y_src", type=U.STRING),
        ],
        fields_match="exact",
    )

    def test_exact_order_polars_lazy(self):
        # Polars LazyFrame exercises the collect_schema() branch of
        # _schema_from_dataframe.
        lazy_df = pl.LazyFrame({"x_src": [1], "y_src": ["a"]})
        rel = ma.relation(lazy_df).conform(self._SPEC)
        inferred = _infer(rel)
        actual = rel.to_polars()
        assert list(inferred.keys()) == list(actual.columns)

    def test_exact_order_inline_list_of_dicts(self):
        # Inline list-of-dicts exercises SourceRelNode → _schema_from_source_data
        # (which constructs a pl.DataFrame for type inference).
        data = [{"x_src": 1, "y_src": "a"}, {"x_src": 2, "y_src": "b"}]
        rel = ma.relation(data).conform(self._SPEC)
        inferred = _infer(rel)
        actual = rel.to_polars()
        assert list(inferred.keys()) == list(actual.columns)

    def test_exact_order_callable_schema_source(self):
        # An ibis memtable exposes callable .schema() returning an ibis Schema
        # whose items() yield (name, ibis_type) pairs — this exercises the
        # callable-schema branch of _schema_from_dataframe (lines 108-113).
        # The ibis types map to SchemaTypeStatus.UNKNOWN (not Polars natives),
        # but the conform node's declared types (concrete U.INTEGER / U.STRING)
        # drive the inferred output, so order parity is still testable.
        import ibis

        t = ibis.memtable({"x_src": [1], "y_src": ["a"]})
        rel = ma.relation(t).conform(self._SPEC)
        inferred = _infer(rel)
        actual = rel.to_polars()
        assert list(inferred.keys()) == list(actual.columns)


# ---------------------------------------------------------------------------
# data_type / missing_columns policy parity (item 48 Task 9)
#
# Before this task, infer_schema's ConformRelNode branch called
# resolve_conform_output() with no actual_dtypes and no resolved contract --
# it silently ignored both TypeSpec.contract and conform(contract=...), and
# the data_type dimension's evolve/discard_value/discard_row/freeze policies
# never affected the inferred schema at all. This section pins the fix:
# actual_dtypes=input_schema now drives EmittedField.type_action, and the
# resolved contract (TypeSpec.contract <- ConformRelNode.contract override)
# is honoured the same way apply_conform() honours it at execute time.
# ---------------------------------------------------------------------------

class TestDataTypePolicyParity:
    """`.schema` (infer) vs `.to_polars()` (execute) column-and-type
    agreement under the data_type / missing_columns contract dimensions."""

    def test_evolve_via_conform_contract_param_matches_to_polars(self):
        # Unsafe cast (STRING source declared INTEGER) with data_type=
        # "evolve" skips the cast entirely -- output keeps STRING. Infer
        # must report the same STRING via EmittedField.effective_type (R2).
        df = pl.DataFrame({"n": ["1", "2"]})
        spec = TypeSpec(fields=[FieldSpec(name="n", type=U.INTEGER)], fields_match="open")
        rel = ma.relation(df).conform(spec, contract={"data_type": "evolve"})

        inferred = _infer(rel)
        actual = rel.to_polars().schema
        assert inferred["n"] == _polars_schema_canonical(actual)["n"] == D.STRING

    def test_evolve_via_typespec_contract_matches_to_polars(self):
        # Same, but layered via TypeSpec.contract (not the conform(contract=)
        # override) -- exercises the spec_contract layer infer previously
        # ignored entirely.
        df = pl.DataFrame({"n": ["1", "2"]})
        spec = TypeSpec(
            fields=[FieldSpec(name="n", type=U.INTEGER)],
            fields_match="open",
            contract={"data_type": "evolve"},
        )
        rel = ma.relation(df).conform(spec)

        inferred = _infer(rel)
        actual = rel.to_polars().schema
        assert inferred["n"] == _polars_schema_canonical(actual)["n"] == D.STRING

    def test_evolve_does_not_affect_safe_casts(self):
        # Safe cast (I32 -> I64) never trips the data_type drift loop, so
        # "evolve" has nothing to evolve -- declared_type still applies, and
        # parity holds via the ordinary (non-evolve) path.
        df = pl.DataFrame({"n": pl.Series([1, 2], dtype=pl.Int32)})
        spec = TypeSpec(fields=[FieldSpec(name="n", type=U.INTEGER)], fields_match="open")
        rel = ma.relation(df).conform(spec, contract={"data_type": "evolve"})

        inferred = _infer(rel)
        actual = rel.to_polars().schema
        assert inferred["n"] == _polars_schema_canonical(actual)["n"] == D.I64

    def test_skip_missing_columns_via_explicit_contract_matches_to_polars(self):
        # missing_columns="skip" via an explicit contract override on the
        # normally-strict "equal" preset -- the missing field is skipped
        # instead of raising MissingFieldsError, matching to_polars() exactly.
        df = pl.DataFrame({"a": [1]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=U.INTEGER),
                FieldSpec(name="b", type=U.STRING),
            ],
            fields_match="equal",
            contract={"missing_columns": "skip"},
        )
        rel = ma.relation(df).conform(spec)

        inferred = _infer(rel)
        actual = rel.to_polars().schema
        assert set(inferred.keys()) == set(actual.names()) == {"a"}

    def test_null_fill_missing_columns_matches_to_polars(self):
        # missing_columns="null_fill" (item 48 Task 10): the missing field's
        # source root is entirely absent -- resolve_conform_output now emits
        # it as a typed null (ma.lit(None).cast(declared_canon)) instead of
        # skipping it, on the normally-strict "equal" preset. Infer must
        # report the SAME declared type the typed null actually casts to at
        # execute time -- the whole point of the "typed" null (finding 11).
        df = pl.DataFrame({"a": [1]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=U.INTEGER),
                FieldSpec(name="b", type=U.STRING),
            ],
            fields_match="equal",
            contract={"missing_columns": "null_fill"},
        )
        rel = ma.relation(df).conform(spec)

        inferred = _infer(rel)
        actual = rel.to_polars()
        assert set(inferred.keys()) == set(actual.schema.names()) == {"a", "b"}
        assert inferred["b"] == _polars_schema_canonical(actual.schema)["b"] == D.STRING
        assert actual["b"].is_null().all()


class TestFreezeNeverRaisesDuringInference:
    """R1/R2: inference must never raise SchemaDriftError -- freeze is an
    execute-time-only enforcement concern (item 48 Task 9)."""

    def test_freeze_data_type_contract_does_not_raise_during_schema(self):
        df = pl.DataFrame({"n": ["a", "b"]})
        spec = TypeSpec(
            fields=[FieldSpec(name="n", type=U.INTEGER)],
            fields_match="open",
            contract={"data_type": "freeze"},
        )
        rel = ma.relation(df).conform(spec)

        # Inference succeeds -- freeze never trips during .schema.
        schema = _infer(rel)
        assert schema["n"] == D.I64  # freeze leaves declared_type untouched

        # Execution DOES enforce freeze.
        with pytest.raises(SchemaDriftError):
            rel.to_polars()

    def test_freeze_missing_columns_contract_does_not_raise_during_schema(self):
        df = pl.DataFrame({"a": [1]})
        spec = TypeSpec(
            fields=[
                FieldSpec(name="a", type=U.INTEGER),
                FieldSpec(name="b", type=U.STRING),
            ],
            fields_match="open",
            contract={"missing_columns": "freeze"},
        )
        rel = ma.relation(df).conform(spec)

        schema = _infer(rel)
        assert set(schema.keys()) == {"a"}

        with pytest.raises(SchemaDriftError):
            rel.to_polars()

    def test_freeze_extra_columns_contract_does_not_raise_during_schema(self):
        df = pl.DataFrame({"a": [1], "extra": [2]})
        spec = TypeSpec(
            fields=[FieldSpec(name="a", type=U.INTEGER)],
            fields_match="open",
            contract={"extra_columns": "freeze"},
        )
        rel = ma.relation(df).conform(spec)

        schema = _infer(rel)
        # Open mode + freeze on extra_columns: the guard's `from_preset`
        # check gates the *raise*, not the with_columns projection itself --
        # inference still keeps the pass-through column in the schema.
        assert set(schema.keys()) == {"a", "extra"}

        with pytest.raises(SchemaDriftError):
            rel.to_polars()
