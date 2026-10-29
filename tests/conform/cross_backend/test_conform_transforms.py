"""Cross-backend parametrized tests for Relation.conform()."""

from __future__ import annotations

import pytest
import mountainash as ma

from mountainash.typespec.spec import TableSchema, FieldDefinition
from mountainash.typespec.universal_types import UniversalType

from ibis.common.exceptions import OperationNotDefinedError, UnsupportedBackendType

from fixtures.backend_registry import ALL_BACKENDS, REGISTRY
from fixtures.call_expectations import expect_call_failure
from mountainash.core.types import BackendCapabilityError



@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformCast:
    def test_cast_string_to_integer(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1", "2", "3"]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"val": FieldDefinition(type=UniversalType.INTEGER)},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1, 2, 3]

    def test_cast_string_to_number(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1.5", "2.5", "3.5"]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"val": FieldDefinition(type=UniversalType.NUMBER)},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1.5, 2.5, 3.5]

    def test_cast_string_to_string(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["hello", "world"]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"val": FieldDefinition(type=UniversalType.STRING)},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["hello", "world"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformRename:
    def test_rename_column(self, backend_name, backend_factory):
        df = backend_factory.create({"old_name": ["a", "b", "c"]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"new_name": FieldDefinition(type=UniversalType.STRING, rename_from="old_name")},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["new_name"].to_list() == ["a", "b", "c"]

    def test_rename_default_keeps_unmapped(self, backend_name, backend_factory):
        """fields_match="open" keeps unmapped columns; the renamed source is dropped."""
        df = backend_factory.create({"old": ["a", "b"], "keep": [1, 2]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"new": FieldDefinition(type=UniversalType.STRING, rename_from="old")},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "new" in result.columns
        assert "keep" in result.columns
        assert "old" not in result.columns

    def test_rename_partial_drops_unmapped(self, backend_name, backend_factory):
        """Explicit fields_match='partial' drops unmapped columns."""
        df = backend_factory.create({"old": ["a", "b"], "keep": [1, 2]}, backend_name)
        spec = TableSchema(
            fields={"new": FieldDefinition(type=UniversalType.STRING, rename_from="old")},
            fields_match="partial",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "new" in result.columns
        assert "keep" not in result.columns
        assert "old" not in result.columns


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformNullFill:
    @pytest.mark.parametrize(
        "values,fill,action,expected",
        [
            (["4", None], 0, "coerce", [4, 0]),
            (["4", None, "bad"], 0, "discard_value", [4, 0, None]),
            (["4", None, "bad"], 0, "discard_row", [4, 0]),
            ([None, "bad", "3", "4"], "bad", "discard_row", [None, 3, 4]),
            (["3", "4"], "bad", "coerce", [3, 4]),
        ],
    )
    def test_string_integer_fill_preserves_failure_policy(
        self, backend_name, backend_factory, values, fill, action, expected, request,
    ):
        from mountainash.core.dtypes import MountainashDtype as D

        if action == "coerce" and backend_name in {"pandas", "narwhals-pandas"}:
            request.applymarker(pytest.mark.xfail(
                strict=True, raises=ValueError,
                reason="373: owned conform fill regression introduces a nullable integer intermediate",
            ))

        frame = backend_factory.create({"qty": values}, backend_name)
        schema = TableSchema(fields={
            "qty": FieldDefinition(dtype=D.I64, null_fill=fill),
        })
        # Existing cast capability boundaries also apply when a fill is present.
        # Coerce remains required on every cell; 373 tracks temporary owned debt.
        with expect_call_failure(
            when=action != "coerce" and (
                REGISTRY[backend_name].family in {"pandas", "narwhals"}
                or backend_name == "ibis-sqlite"
            ),
            errors=(OperationNotDefinedError,) if backend_name == "ibis-sqlite"
            else (BackendCapabilityError,),
            reason="Narwhals has no null-on-failure cast; SQLite has no TryCast compiler",
        ):
            result = ma.relation(frame).conform(
                schema, contract={"data_type": action},
            ).to_polars()
            assert result["qty"].to_list() == expected

    def test_null_fill_integer(self, backend_name, backend_factory, request):
        if backend_name in {"pandas", "narwhals-pandas"}:
            request.applymarker(pytest.mark.xfail(
                strict=True, raises=ValueError,
                reason="373: owned conform fill regression introduces a nullable integer intermediate",
            ))
        df = backend_factory.create({"val": [1, None, 3]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"val": FieldDefinition(type=UniversalType.INTEGER, null_fill=-1)},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == [1, -1, 3]

    def test_null_fill_string(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["x", None, "z"]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"val": FieldDefinition(type=UniversalType.STRING, null_fill="unknown")},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["val"].to_list() == ["x", "unknown", "z"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformOnlyMappedFields:
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

    def test_partial_drops_unmapped(self, backend_name, backend_factory):
        """Explicit fields_match='partial' produces only spec fields."""
        df = backend_factory.create({"keep": ["a", "b"], "drop": [1, 2]}, backend_name)
        spec = TableSchema(
            fields={"keep": FieldDefinition(type=UniversalType.STRING)},
            fields_match="partial",
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert "keep" in result.columns
        assert "drop" not in result.columns


class TestConformMultiTransform:
    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_cast_and_rename(self, backend_name, backend_factory):
        df = backend_factory.create({"raw_id": ["1", "2", "3"]}, backend_name)
        spec = TableSchema(
            fields_match="open",
            fields={"user_id": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw_id")},
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["user_id"].to_list() == [1, 2, 3]

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_full_pipeline(self, backend_name, backend_factory):
        df = backend_factory.create(
            {
                "raw_score": ["1.5", None, "3.5"],
                "raw_label": ["foo", "bar", None],
                "extra": [10, 20, 30],
            },
            backend_name,
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


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformFromFrictionless:
    def test_from_frictionless_dict(self, backend_name, backend_factory):
        df = backend_factory.create({"raw_id": ["1", "2"]}, backend_name)
        frictionless_data = {
            "fields": [
                {"name": "user_id", "type": "integer", "x-mountainash": {"rename_from": "raw_id"}},
            ],
        }
        spec = TableSchema.from_frictionless(frictionless_data)
        # Frictionless default is "exact" which requires available_columns.
        # Override to the permissive "open" mode for Relation.conform(), which
        # doesn't have column info at build time.
        spec.fields_match = "open"
        result = ma.relation(df).conform(spec).to_polars()
        assert result["user_id"].to_list() == [1, 2]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_value_domains_follow_conform_cast_and_rename(backend_name, backend_factory):
    frame = backend_factory.create({"raw": ["0", "1", "2"]}, backend_name)
    spec = TableSchema(
        fields_match="open",
        fields={"number": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw"),},
    )
    result = (
        ma.relation(frame)
        .conform(spec)
        .select(
            ma.col("number").value_kind().name.alias("kind"),
            ma.col("number").boolean_value(source="binary_number").name.alias("candidate"),
        )
        .to_dict()
    )
    assert result == {"kind": ["integer"] * 3, "candidate": [False, True, None]}


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "preset,extra_columns,expected_columns",
    [("open", "discard", ["qty"]), ("subset", "evolve", ["qty", "spare"])],
)
def test_explicit_extra_column_policy_overrides_preset(
    backend_name, backend_factory, preset, extra_columns, expected_columns,
):
    frame = backend_factory.create({"qty": ["1", "2"], "spare": [8, 9]}, backend_name)
    schema = TableSchema(
        fields={"qty": FieldDefinition(type=UniversalType.INTEGER)},
        fields_match=preset,
    )
    result = ma.relation(frame).conform(
        schema, contract={"extra_columns": extra_columns},
    ).to_polars()
    assert result.columns == expected_columns
    assert result["qty"].to_list() == [1, 2]
    if extra_columns == "evolve":
        assert result["spare"].to_list() == [8, 9]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "element,values,expected",
    [
        (
            FieldDefinition(
                element=FieldDefinition(type=UniversalType.INTEGER),
                null_fill=["2"],
            ),
            [["1"], None],
            [[1], [2]],
        ),
        (
            FieldDefinition(
                fields={"id": FieldDefinition(type=UniversalType.INTEGER)},
                null_fill={"id": "2"},
            ),
            [{"id": "1"}, None],
            [{"id": 1}, {"id": 2}],
        ),
    ],
)
def test_complete_element_definition_applies_container_fill(
    backend_name, backend_factory, element, values, expected,
):
    with expect_call_failure(
        when=backend_name in {"narwhals-polars", "narwhals-lazy", "ibis-sqlite"},
        errors=(UnsupportedBackendType,) if backend_name == "ibis-sqlite"
        else (BackendCapabilityError,),
        reason="SQLite cannot store arrays; Narwhals lacks native element expressions",
    ):
        frame = backend_factory.create({"groups": [values]}, backend_name)
        schema = TableSchema(fields={"groups": FieldDefinition(element=element)})
        result = ma.relation(frame).conform(schema).to_polars()
        assert result["groups"].to_list() == [expected]


@pytest.mark.parametrize("dimensions,values,expected", [
    ((2,), [["1", None], ["2", "3"]], [[1, 0], [2, 3]]),
    ((2, 2), [[["1", None], ["2", "3"]]], [[[1, 0], [2, 3]]]),
])
@pytest.mark.parametrize("lazy", [False, True])
def test_native_fixed_array_element_fill_preserves_dimensions(lazy, dimensions, values, expected):
    """Polars-specific physical representation; other routes use the list matrix above."""
    import polars as pl
    from mountainash.core.dtypes import MountainashDtype as D

    frame = pl.DataFrame(
        {"groups": values},
        schema={"groups": pl.Array(pl.String, dimensions)},
    )
    schema = TableSchema(fields={
        "groups": FieldDefinition(
            element=FieldDefinition(dtype=D.I64, null_fill=0), dimensions=dimensions,
        ),
    })
    result = ma.relation(frame.lazy() if lazy else frame).conform(schema).to_polars()
    assert result["groups"].to_list() == expected
    assert result.schema["groups"] == pl.Array(pl.Int64, dimensions)


# ---------------------------------------------------------------------------
# Fills under the effective container target. The authored child is narrower
# (Int8) than the complete target (Int64); 128/129 only exist under the latter.
# ---------------------------------------------------------------------------

def _native_target(dtype, backend_name):
    """The complete container target in the backend's own native vocabulary.

    FieldDefinition rejects a portable ``dtype`` beside authored ``fields`` /
    ``element`` (single structural authority), so an effective container
    target is declared through the owning carrier's native dtype.
    """
    from mountainash.core.dtypes import TypeTarget, registry

    # pandas executes through the Narwhals expression system (core/constants.py).
    target = (
        TypeTarget.POLARS if backend_name.startswith("polars")
        else TypeTarget.NARWHALS if backend_name in {"pandas"} or backend_name.startswith("narwhals")
        else TypeTarget.IBIS
    )
    return registry.to_native_cast(dtype, target)


def _struct_source(backend_name, backend_factory, records):
    import json

    physical = (
        [None if value is None else json.dumps(value) for value in records]
        if backend_name == "ibis-sqlite" else records
    )
    return backend_factory.create({"record": physical}, backend_name)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_child_fill_converts_under_effective_container_target(backend_name, backend_factory):
    import polars as pl
    from mountainash.core.dtypes import MountainashDtype as D, StructDtype

    source = _struct_source(backend_name, backend_factory, [
        {"id": None, "keep": "a"}, {"id": 5, "keep": None}, None,
    ])
    field = FieldDefinition(
        type=UniversalType.OBJECT,
        backend_type=_native_target(StructDtype((("keep", D.STRING), ("id", D.I64))), backend_name),
        fields={"id": FieldDefinition(dtype=D.I8, null_fill=129)},
    )
    out = ma.relation(source).conform(
        TableSchema(fields={"record": field}, missing_values=[]),
    ).to_polars()
    assert out.schema["record"] == pl.Struct({"keep": pl.String, "id": pl.Int64})
    assert out["record"].to_list() == [
        {"keep": "a", "id": 129},   # child null: filled under Int64, not Int8
        {"keep": None, "id": 5},    # untouched member preserved
        None,                       # parent null is not a child null
    ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_list_element_fill_converts_under_effective_list_target(backend_name, backend_factory):
    from mountainash.core.dtypes import ListDtype, MountainashDtype as D

    with expect_call_failure(
        when=backend_name in {"narwhals-polars", "narwhals-lazy", "ibis-sqlite"},
        errors=(UnsupportedBackendType,) if backend_name == "ibis-sqlite"
        else (BackendCapabilityError,),
        reason="SQLite cannot store arrays; Narwhals lacks native element expressions",
    ):
        frame = backend_factory.create({"groups": [["128", None], None, []]}, backend_name)
        schema = TableSchema(fields={"groups": FieldDefinition(
            backend_type=_native_target(ListDtype(D.I64), backend_name),
            element=FieldDefinition(dtype=D.I8, null_fill=129),
        )}, missing_values=[])
        result = ma.relation(frame).conform(schema).to_polars()
        assert result["groups"].to_list() == [[128, 129], None, []]


@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize("action", ["discard_value", "discard_row"])
def test_invalid_nonmissing_child_is_never_filled(lazy, action):
    # Native atomic nested discard is a Polars capability (see
    # test_native_child_conversion_discards_invalid_parent_not_missing_child).
    import polars as pl
    from mountainash.core.dtypes import MountainashDtype as D, StructDtype

    field = FieldDefinition(
        type=UniversalType.OBJECT,
        backend_type=_native_target(StructDtype((("id", D.I64),)), "polars"),
        fields={"id": FieldDefinition(dtype=D.I8, null_fill=7, missing_values=["NA"])},
    )
    frame = pl.DataFrame({"record": [
        {"id": "bad"}, {"id": "NA"}, {"id": None}, {"id": "3"}, {"id": "129"}, None,
    ]})
    out = ma.relation(frame.lazy() if lazy else frame).conform(
        TableSchema(fields={"record": field}, missing_values=[]), contract={"data_type": action},
    ).to_polars()
    expected = [None, {"id": 7}, {"id": 7}, {"id": 3}, {"id": 129}, None]
    if action == "discard_row":
        del expected[0]
    assert out.schema["record"] == pl.Struct({"id": pl.Int64})
    assert out["record"].to_list() == expected


def test_invalid_nonmissing_child_with_fill_still_fails_under_coerce():
    import polars as pl
    from mountainash.conform.errors import ConformTransformError
    from mountainash.core.dtypes import MountainashDtype as D, StructDtype

    field = FieldDefinition(
        type=UniversalType.OBJECT,
        backend_type=_native_target(StructDtype((("id", D.I64),)), "polars"),
        fields={"id": FieldDefinition(dtype=D.I8, null_fill=7)},
    )
    with pytest.raises((pl.exceptions.PolarsError, ConformTransformError)):
        ma.relation(pl.DataFrame({"record": [{"id": "bad"}]})).conform(
            TableSchema(fields={"record": field}, missing_values=[]),
        ).to_polars()


@pytest.mark.parametrize("action", ["discard_value", "discard_row"])
def test_invalid_child_fill_keeps_existing_failure_scope(action):
    # Original missingness remains authoritative: an invalid fill leaves the
    # originally-null child null, rather than turning it into a source failure.
    import polars as pl
    from mountainash.core.dtypes import MountainashDtype as D, StructDtype

    field = FieldDefinition(
        type=UniversalType.OBJECT,
        backend_type=_native_target(StructDtype((("id", D.I64),)), "polars"),
        fields={"id": FieldDefinition(dtype=D.I8, null_fill="oops")},
    )
    out = ma.relation(pl.DataFrame({"record": [{"id": None}, {"id": "3"}, None]})).conform(
        TableSchema(fields={"record": field}, missing_values=[]), contract={"data_type": action},
    ).to_polars()
    assert out.schema["record"] == pl.Struct({"id": pl.Int64})
    assert out["record"].to_list() == [{"id": None}, {"id": 3}, None]


@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize("dimensions,values,expected", [
    ((2,), [["128", None], None], [[128, 129], None]),
    ((2, 2), [[["1", None], ["128", "3"]], None], [[[1, 129], [128, 3]], None]),
])
def test_fixed_array_effective_element_fills_under_wide_target(lazy, dimensions, values, expected):
    """Polars-specific physical representation; other routes use the list matrix above."""
    import polars as pl
    from mountainash.core.dtypes import ArrayDtype, MountainashDtype as D

    frame = pl.DataFrame({"groups": values}, schema={"groups": pl.Array(pl.String, dimensions)})
    schema = TableSchema(fields={"groups": FieldDefinition(
        backend_type=_native_target(ArrayDtype(D.I64, dimensions), "polars"),
        element=FieldDefinition(dtype=D.I8, null_fill=129), dimensions=dimensions,
    )}, missing_values=[])
    result = ma.relation(frame.lazy() if lazy else frame).conform(schema).to_polars()
    assert result.schema["groups"] == pl.Array(pl.Int64, dimensions)
    assert result["groups"].to_list() == expected


def test_fixed_array_invalid_element_is_not_filled_and_discards_array():
    import polars as pl
    from mountainash.core.dtypes import ArrayDtype, MountainashDtype as D

    frame = pl.DataFrame(
        {"groups": [[["1", None], ["bad", "3"]], [["1", None], ["128", "3"]]]},
        schema={"groups": pl.Array(pl.String, (2, 2))},
    )
    schema = TableSchema(fields={"groups": FieldDefinition(
        backend_type=_native_target(ArrayDtype(D.I64, (2, 2)), "polars"),
        element=FieldDefinition(dtype=D.I8, null_fill=129), dimensions=(2, 2),
    )}, missing_values=[])
    result = ma.relation(frame).conform(schema, contract={"data_type": "discard_value"}).to_polars()
    assert result.schema["groups"] == pl.Array(pl.Int64, (2, 2))
    assert result["groups"].to_list() == [None, [[1, 129], [128, 3]]]
