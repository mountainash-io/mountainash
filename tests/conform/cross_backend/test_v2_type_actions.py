"""Task 7 evaluator and action-policy contracts."""
from __future__ import annotations

import pytest

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.call_expectations import expect_call_failure

from mountainash.conform.errors import (
    ExactFieldsMismatchError,
    IncompatibleSourceTypeError,
    SchemaDriftError,
    UnresolvedSourceTypeError,
)
from mountainash.conform.expressions import resolve_conform_output
from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec.source_shape import SourceShape
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType


def _spec(*fields: FieldDefinition, fields_match: str = "exact") -> TableSchema:
    return TableSchema(fields=dict(fields), fields_match=fields_match)


@pytest.mark.parametrize(
    "actual,reason",
    [(('a',), "count"), (('a', 'c'), "name"), (('b', 'a'), "order")],
)
def test_exact_reports_stable_reason(actual: tuple[str, ...], reason: str) -> None:
    spec = _spec(("a", FieldDefinition()), ("b", FieldDefinition()))
    with pytest.raises(ExactFieldsMismatchError) as exc_info:
        resolve_conform_output(spec, available_columns=actual)
    assert exc_info.value.reason == reason


def test_exact_rejects_dotted_sources_before_count() -> None:
    spec = _spec(("a", FieldDefinition(rename_from="payload.a")))
    with pytest.raises(ExactFieldsMismatchError) as exc_info:
        resolve_conform_output(spec, available_columns=("payload",))
    assert exc_info.value.reason == "nested_source"


def test_structural_only_assesses_drift_without_actions() -> None:
    spec = _spec(("a", FieldDefinition(type=UniversalType.INTEGER)), fields_match="open")
    result = resolve_conform_output(
        spec,
        available_columns=("a",),
        actual_dtypes={"a": MountainashDtype.STRING},
        apply_value_transforms=False,
    )
    assert result.drift is not None
    assert result.drift.type_mismatches[0].applied is False
    assert result.drift.type_mismatches[0].action == "coerce"


def test_unknown_actual_shape_is_unknown_drift_evidence() -> None:
    spec = _spec(("a", FieldDefinition(type=UniversalType.INTEGER)), fields_match="open")
    result = resolve_conform_output(
        spec,
        available_columns=("a",),
        actual_shapes={"a": SourceShape(None)},
    )
    assert result.drift is not None
    mismatch = result.drift.type_mismatches[0]
    assert mismatch.reason == "unknown"
    assert mismatch.source_detail is None


def test_native_list_representation_drift_precedes_item_shape() -> None:
    spec = _spec(("a", FieldDefinition(type=UniversalType.LIST, item_type="string")), fields_match="open")
    result = resolve_conform_output(
        spec,
        available_columns=("a",),
        actual_shapes={"a": SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))},
    )
    assert result.drift is not None
    mismatch = result.drift.type_mismatches[0]
    assert mismatch.reason == "representation"


@pytest.mark.parametrize("action", ("evolve", "discard_value", "discard_row"))
def test_native_list_representation_carries_data_type_action(action: str) -> None:
    import dataclasses

    from mountainash.conform.contract import resolve_contract

    spec = _spec(("items", FieldDefinition(type=UniversalType.LIST, item_type="integer")), fields_match="open")
    contract = dataclasses.replace(resolve_contract("open"), data_type=action, from_preset=False)
    result = resolve_conform_output(
        spec,
        available_columns=("items",),
        actual_shapes={
            "items": SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))
        },
        contract=contract,
    )

    assert result.drift is not None
    mismatch = result.drift.type_mismatches[0]
    assert mismatch.reason == "representation"
    assert mismatch.action == action
    assert result.emitted[0].type_action == action


def test_native_list_representation_freeze_raises_schema_drift() -> None:
    import dataclasses

    from mountainash.conform.contract import resolve_contract

    spec = _spec(("items", FieldDefinition(type=UniversalType.LIST, item_type="integer")), fields_match="open")
    contract = dataclasses.replace(resolve_contract("open"), data_type="freeze", from_preset=False)
    with pytest.raises(SchemaDriftError):
        resolve_conform_output(
            spec,
            available_columns=("items",),
            actual_shapes={
                "items": SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))
            },
            contract=contract,
        )


def test_nested_struct_shape_detail_reports_child_types() -> None:
    spec = _spec(
        ("record", FieldDefinition(type=UniversalType.OBJECT,
        fields={"child": FieldDefinition(type=UniversalType.STRING)},)),
        fields_match="open",
    )
    result = resolve_conform_output(
        spec,
        available_columns=("record",),
        actual_shapes={
            "record": SourceShape(
                MountainashDtype.STRUCT,
                struct_fields=(("child", SourceShape(MountainashDtype.I64)),),
            )
        },
    )
    mismatch = result.drift.type_mismatches[0]
    assert mismatch.reason == "shape"


def test_object_lon_lat_children_remain_ordered() -> None:
    spec = _spec(
        ("record", FieldDefinition(type=UniversalType.OBJECT,
        fields={"lon": FieldDefinition(type=UniversalType.NUMBER),
            "lat": FieldDefinition(type=UniversalType.NUMBER),},)),
        fields_match="open",
    )
    result = resolve_conform_output(
        spec,
        available_columns=("record",),
        actual_shapes={
            "record": SourceShape(
                MountainashDtype.STRUCT,
                struct_fields=(
                    ("lat", SourceShape(MountainashDtype.FP64)),
                    ("lon", SourceShape(MountainashDtype.FP64)),
                ),
            )
        },
    )

    assert result.drift is not None
    assert result.drift.type_mismatches[0].reason == "shape"

def test_shape_drift_uses_configured_action() -> None:
    import dataclasses
    from mountainash.conform.contract import resolve_contract

    spec = _spec(("a", FieldDefinition(type=UniversalType.LIST, item_type="string")), fields_match="open")
    contract = dataclasses.replace(
        resolve_contract("open"), data_type="discard_value", from_preset=False,
    )
    result = resolve_conform_output(
        spec,
        available_columns=("a",),
        actual_shapes={"a": SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))},
        contract=contract,
    )
    assert result.drift is not None
    assert result.drift.type_mismatches[0].action == "discard_value"


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_unknown_lexical_and_incompatible_shapes_dispatch_by_contract(backend_name, backend_factory) -> None:
    from mountainash.conform.expressions import _build_conform_exprs
    unknown = _spec(("items", FieldDefinition(type=UniversalType.LIST)), fields_match="open")
    result = _build_conform_exprs(
        unknown,
        available_columns=("items",),
        actual_shapes={"items": SourceShape(None)},
    )
    from mountainash import relation
    from mountainash.core.types import BackendCapabilityError

    frame = backend_factory.create({"items": ["one,two", "three"]}, backend_name)
    with expect_call_failure(
        when=backend_name in {"ibis-sqlite", "pandas", "narwhals-pandas"},
        errors=(BackendCapabilityError,),
        reason="Lexical-list capabilities: SQLite has no parser; pandas needs Arrow-backed strings",
    ):
        assert relation(frame).select(result.exprs[0]).to_dict()["items"] == [
            ["one", "two"], ["three"],
        ]
    incompatible = _spec(("items", FieldDefinition(type=UniversalType.LIST)), fields_match="open")
    with pytest.raises(IncompatibleSourceTypeError):
        _build_conform_exprs(
            incompatible,
            available_columns=("items",),
            actual_shapes={"items": SourceShape(MountainashDtype.STRUCT)},
        )


def test_structural_only_relation_skips_cast() -> None:
    import polars as pl
    from mountainash import relation

    spec = _spec(("value", FieldDefinition(type=UniversalType.INTEGER)), fields_match="open")
    result = relation(pl.DataFrame({"value": ["7"]})).conform(
        spec, apply_value_transforms=False
    ).to_polars()
    assert result["value"].to_list() == ["7"]


def test_discard_row_keeps_null_and_invalid_fill_rows() -> None:
    import polars as pl
    from mountainash import relation

    spec = _spec(
        ("value", FieldDefinition(type=UniversalType.INTEGER, null_fill="bad")),
        fields_match="open",
    )
    result = relation(pl.DataFrame({"value": [None, "bad", "3", "4"]})).conform(
        spec, contract={"data_type": "discard_row"}
    ).to_polars()
    assert result["value"].to_list() == [None, 3, 4]


def test_native_list_requires_array_declaration() -> None:
    import polars as pl
    from mountainash import relation

    spec = _spec(
        ("items", FieldDefinition(type=UniversalType.LIST, item_type="integer")),
        fields_match="open",
    )
    with pytest.raises(IncompatibleSourceTypeError):
        relation(pl.DataFrame({"items": [["1", "bad"], ["2", "3"]]})).conform(spec).to_polars()


def test_native_list_discard_value_emits_typed_null() -> None:
    import polars as pl
    from mountainash import relation

    spec = _spec(
        ("items", FieldDefinition(type=UniversalType.LIST, item_type="integer")),
        fields_match="open",
    )
    result = relation(pl.DataFrame({"items": [["1", "bad"], ["2", "3"]]})).conform(
        spec, contract={"data_type": "discard_value"}
    ).to_polars()
    assert result["items"].to_list() == [None, None]


def test_invalid_temporal_child_discards_whole_list_value() -> None:
    from datetime import date
    import polars as pl
    from mountainash import relation

    spec = _spec(
        ("items", FieldDefinition(type=UniversalType.ARRAY, element=FieldDefinition(fields = {"day": FieldDefinition(type=UniversalType.DATE),}))),
        fields_match="open",
    )
    result = relation(
        pl.DataFrame(
            {"items": [[{"day": "2026-10-12"}, {"day": "invalid"}], [{"day": "2026-10-13"}, None], None]},
            schema={"items": pl.List(pl.Struct({"day": pl.String}))},
        )
    ).conform(spec, contract={"data_type": "discard_value"}).to_polars()
    assert result.schema["items"] == pl.List(pl.Struct({"day": pl.Date}))
    assert result["items"].to_list() == [None, [{"day": date(2026, 10, 13)}, None], None]


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("evolve", [[1, 2], [3, 4]]),
        ("discard_value", [None, None]),
        ("discard_row", []),
    ],
)
def test_native_list_representation_action_materializes(
    action: str, expected: list[object]
) -> None:
    import polars as pl
    from mountainash import relation

    spec = _spec(
        ("items", FieldDefinition(type=UniversalType.LIST, item_type="integer")),
        fields_match="open",
    )
    result = relation(pl.DataFrame({"items": [[1, 2], [3, 4]]})).conform(
        spec, contract={"data_type": action}
    ).to_polars()

    assert result["items"].to_list() == expected




@pytest.mark.parametrize("action", ("coerce", "evolve", "freeze", "discard_value", "discard_row"))
def test_every_data_type_action_has_one_evaluator_branch(action: str) -> None:
    import dataclasses
    from mountainash.conform.contract import resolve_contract

    spec = _spec(("value", FieldDefinition(type=UniversalType.INTEGER)), fields_match="open")
    contract = dataclasses.replace(
        resolve_contract("open"), data_type=action, from_preset=False
    )
    result = resolve_conform_output(
        spec,
        available_columns=("value",),
        actual_shapes={"value": SourceShape(MountainashDtype.STRING)},
        contract=contract,
        raise_on_freeze=False,
    )
    assert result.drift is not None
    mismatch = result.drift.type_mismatches[0]
    assert mismatch.action == action



# ---------------------------------------------------------------------------
# Item 113 Unit D Task 7 step 1/2: the complete structured failure-policy
# matrix for resolve_structured_cell() (spec sections 12.1-12.6).
# ---------------------------------------------------------------------------


def _structured_plan(
    *,
    action: str,
    apply_value_transforms: bool,
    null_fill=None,
    root=None,
):
    from mountainash.conform.structured_transport import (
        StructuredCarrier,
        StructuredFieldPlan,
        StructuredRoot,
    )

    return StructuredFieldPlan(
        field_name="payload",
        root=root or StructuredRoot.OBJECT,
        carrier=StructuredCarrier.OPAQUE,
        configured_action=action,
        apply_value_transforms=apply_value_transforms,
        missing_values=("MISSING",),
        null_fill=null_fill,
        declaration_fingerprint="test",
        origin_node_id="test",
    )


#: The exact discriminating rows from the plan: physical null, a missing
#: sentinel, valid JSON text, malformed JSON text, and a valid native value.
#: Root is OBJECT, so every value except "{broken" decodes successfully;
#: null/"MISSING" decode to logical null, "{broken" is the one genuinely
#: invalid non-null row.
_DISCRIMINATING_VALUES = (None, "MISSING", '{"ok": 1}', "{broken", {"native": True})

#: Each value's (decoded_logical_value_or_INVALID, post_missing_is_null)
#: after missing-value normalization + decode, independent of action.
#: Filled in per-test since INVALID_STRUCTURED_VALUE is a runtime import.


class TestResolveStructuredCellMatrix:
    """Task 7 step 1: parametrize every action with value transforms
    enabled and disabled, across schema-level/field-level missing values,
    JSON-text and native cells, and a malformed non-null row."""

    def _decoded_table(self):
        from mountainash.conform.structured_transport import INVALID_STRUCTURED_VALUE

        return {
            None: (None, True),
            "MISSING": (None, True),
            '{"ok": 1}': ({"ok": 1}, False),
            "{broken": (INVALID_STRUCTURED_VALUE, False),
            "__native__": ({"native": True}, False),
        }

    def _key(self, value):
        return "__native__" if value == {"native": True} else value

    @pytest.mark.parametrize("consumer_name", ("VALIDATION", "LOGICAL_EGRESS"))
    @pytest.mark.parametrize("action", ("coerce", "evolve", "freeze", "discard_value", "discard_row"))
    def test_transforms_disabled_never_discards_and_always_decodes_for_validation(
        self, action, consumer_name
    ):
        """Structural-only conform (apply_value_transforms=False) never
        removes a row for any action; a logical egress passes the raw
        physical value through untouched, validation still decodes to
        report the true logical state (spec 12.1)."""
        from mountainash.conform.structured_transport import (
            StructuredActionConsumer,
            resolve_structured_cell,
        )

        consumer = getattr(StructuredActionConsumer, consumer_name)
        plan = _structured_plan(action=action, apply_value_transforms=False)
        decoded_table = self._decoded_table()
        for value in _DISCRIMINATING_VALUES:
            resolution = resolve_structured_cell(value, plan=plan, consumer=consumer)
            assert resolution.keep is True, (action, consumer_name, value)
            if consumer is StructuredActionConsumer.LOGICAL_EGRESS:
                assert resolution.logical_value is value, (action, consumer_name, value)
            else:
                expected, expected_null = decoded_table[self._key(value)]
                assert resolution.logical_value is expected or resolution.logical_value == expected, (
                    action, consumer_name, value,
                )
                assert resolution.post_missing_is_null is expected_null, (action, consumer_name, value)

    @pytest.mark.parametrize("consumer_name", ("VALIDATION", "LOGICAL_EGRESS"))
    def test_coerce_always_reports_the_decoded_value_and_never_discards(self, consumer_name):
        """`coerce` (spec 12.3): every row is kept at the cell-resolution
        layer for both consumers -- whether an invalid decode instead
        *raises* is a `resolve_logical_snapshot()`-level, consumer-gated
        decision (spec 12.2/12.3), not this function's."""
        from mountainash.conform.structured_transport import (
            StructuredActionConsumer,
            resolve_structured_cell,
        )

        consumer = getattr(StructuredActionConsumer, consumer_name)
        plan = _structured_plan(action="coerce", apply_value_transforms=True)
        decoded_table = self._decoded_table()
        for value in _DISCRIMINATING_VALUES:
            resolution = resolve_structured_cell(value, plan=plan, consumer=consumer)
            expected, _ = decoded_table[self._key(value)]
            assert resolution.logical_value is expected or resolution.logical_value == expected, (
                consumer_name, value,
            )
            assert resolution.keep is True, (consumer_name, value)

    @pytest.mark.parametrize("consumer_name", ("VALIDATION", "LOGICAL_EGRESS"))
    def test_discard_value_nulls_only_the_invalid_cell(self, consumer_name):
        """`discard_value` (spec 12.4): an invalid decoded value becomes
        logical null; a valid decoded value remains unchanged; every row
        is kept. Identical for both consumers."""
        from mountainash.conform.structured_transport import (
            StructuredActionConsumer,
            resolve_structured_cell,
        )

        consumer = getattr(StructuredActionConsumer, consumer_name)
        plan = _structured_plan(action="discard_value", apply_value_transforms=True)
        decoded_table = self._decoded_table()
        for value in _DISCRIMINATING_VALUES:
            resolution = resolve_structured_cell(value, plan=plan, consumer=consumer)
            assert resolution.keep is True, (consumer_name, value)
            if value == "{broken":
                assert resolution.logical_value is None, (consumer_name, value)
            else:
                expected, _ = decoded_table[self._key(value)]
                assert resolution.logical_value is expected or resolution.logical_value == expected, (
                    consumer_name, value,
                )

    @pytest.mark.parametrize("consumer_name", ("VALIDATION", "LOGICAL_EGRESS"))
    def test_discard_row_removes_only_the_genuinely_invalid_non_null_row(self, consumer_name):
        """`discard_row` (spec 12.5): a physical null or missing sentinel is
        retained and becomes logical null; a genuinely non-null malformed
        value is removed; a valid value is retained unchanged. Identical
        keep mask for every logical terminal and validation."""
        from mountainash.conform.structured_transport import (
            INVALID_STRUCTURED_VALUE,
            StructuredActionConsumer,
            resolve_structured_cell,
        )

        consumer = getattr(StructuredActionConsumer, consumer_name)
        plan = _structured_plan(action="discard_row", apply_value_transforms=True)
        decoded_table = self._decoded_table()
        for value in _DISCRIMINATING_VALUES:
            resolution = resolve_structured_cell(value, plan=plan, consumer=consumer)
            if value == "{broken":
                assert resolution.logical_value is INVALID_STRUCTURED_VALUE, (consumer_name, value)
                assert resolution.keep is False, (consumer_name, value)
            else:
                expected, _ = decoded_table[self._key(value)]
                assert resolution.logical_value is expected or resolution.logical_value == expected, (
                    consumer_name, value,
                )
                assert resolution.keep is True, (consumer_name, value)

    @pytest.mark.parametrize("action", ("evolve", "freeze"))
    def test_evolve_and_freeze_preserve_source_for_egress_and_decode_for_validation(self, action):
        """`evolve`/`freeze` (spec 12.6): a logical egress preserves the
        actual UNTOUCHED source value in relation results (not even
        missing-value normalized); validation still parses its private
        logical cache from the declared field plan. Every row is kept --
        `freeze` never raises at the cell-resolution layer; a schema-drift
        raise (if configured) happens at a higher layer, not here."""
        from mountainash.conform.structured_transport import (
            StructuredActionConsumer,
            resolve_structured_cell,
        )

        plan = _structured_plan(action=action, apply_value_transforms=True)
        decoded_table = self._decoded_table()
        for value in _DISCRIMINATING_VALUES:
            egress = resolve_structured_cell(
                value, plan=plan, consumer=StructuredActionConsumer.LOGICAL_EGRESS
            )
            assert egress.keep is True, (action, value)
            assert egress.logical_value is value, (action, value)

            validation = resolve_structured_cell(
                value, plan=plan, consumer=StructuredActionConsumer.VALIDATION
            )
            assert validation.keep is True, (action, value)
            expected, _ = decoded_table[self._key(value)]
            assert validation.logical_value is expected or validation.logical_value == expected, (
                action, value,
            )


class TestPreFillDiscardRowException:
    """Task 7 step 2: a null_fill that is itself invalid never makes a
    physically-null/missing row look like a genuine decode failure."""

    def test_invalid_null_fill_keeps_null_and_missing_rows_as_logical_null(self):
        from mountainash.conform.structured_transport import (
            StructuredActionConsumer,
            resolve_structured_cell,
        )

        plan = _structured_plan(
            action="discard_row", apply_value_transforms=True, null_fill="{broken"
        )
        for value in (None, "MISSING"):
            for consumer in (
                StructuredActionConsumer.VALIDATION,
                StructuredActionConsumer.LOGICAL_EGRESS,
            ):
                res = resolve_structured_cell(value, plan=plan, consumer=consumer)
                assert res.logical_value is None, (value, consumer)
                assert res.keep is True, (value, consumer)

    def test_malformed_non_null_row_is_still_removed_under_the_same_plan(self):
        from mountainash.conform.structured_transport import (
            INVALID_STRUCTURED_VALUE,
            StructuredActionConsumer,
            resolve_structured_cell,
        )

        plan = _structured_plan(
            action="discard_row", apply_value_transforms=True, null_fill="{broken"
        )
        res = resolve_structured_cell(
            "{broken", plan=plan, consumer=StructuredActionConsumer.VALIDATION
        )
        assert res.logical_value is INVALID_STRUCTURED_VALUE
        assert res.keep is False

def _placeholder_cases():
    import polars as pl

    return [
        pytest.param(
            FieldDefinition(type=UniversalType.LIST, item_type="integer"),
            pl.Series("x", [{"id": 1}, None]), pl.List(pl.Int64), id="lexical-list",
        ),
        pytest.param(
            FieldDefinition(type=UniversalType.ARRAY, element=FieldDefinition(
                fields={"id": FieldDefinition(dtype=MountainashDtype.I16)},
            )),
            pl.Series("x", ["a", None]), pl.List(pl.Struct({"id": pl.Int16})), id="array-of-struct",
        ),
    ]


@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize("action", ["discard_value", "discard_row"])
@pytest.mark.parametrize("field,source,dtype", _placeholder_cases())
def test_incompatible_source_placeholder_executes_with_selected_dtype(lazy, action, field, source, dtype) -> None:
    from mountainash import relation

    frame = source.to_frame()
    result = relation(frame.lazy() if lazy else frame).conform(
        TableSchema(fields={"x": field}, fields_match="open", missing_values=[]),
        contract={"data_type": action},
    ).to_polars()
    assert result.schema["x"] == dtype
    # discard_value nulls every incompatible value; discard_row additionally
    # drops the non-null source row but keeps the null one.
    assert result["x"].to_list() == ([None, None] if action == "discard_value" else [None])


@pytest.mark.parametrize("action", ["coerce", "discard_value"])
def test_lexical_list_item_type_parses_then_converts(action) -> None:
    import polars as pl
    from mountainash import relation

    values = ["1,2", "3", None] if action == "coerce" else ["1,2", "3,x", None]
    spec = _spec(
        ("items", FieldDefinition(type=UniversalType.LIST, item_type="integer")),
        fields_match="open",
    )
    result = relation(pl.DataFrame({"items": values})).conform(
        spec, contract={"data_type": action}
    ).to_polars()
    assert result.schema["items"] == pl.List(pl.Int64)
    assert result["items"].to_list() == (
        [[1, 2], [3], None] if action == "coerce" else [[1, 2], None, None]
    )
