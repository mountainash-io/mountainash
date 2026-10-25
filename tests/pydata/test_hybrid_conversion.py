"""Tests for the three-tier hybrid conversion strategy (TableSchema/FieldDefinition API)."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.ingress.custom_type_helpers import (
    _apply_narwhals_custom_converters,
    apply_custom_converters_to_dict,
    apply_custom_converters_to_dicts,
    apply_hybrid_conversion,
    apply_native_conversions_to_dataframe,
    separate_conversions,
    source_column_name,
)
from mountainash.typespec.custom_types import CustomTypeRegistry, _register_standard_converters
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType



def test_ingress_native_override_is_authoritative():
    from mountainash import MountainashDtype
    schema = TableSchema(fields={"id": FieldDefinition(dtype=MountainashDtype.I8, backend_type=pl.Int64)})
    with pytest.warns(UserWarning):
        out = apply_hybrid_conversion([{"id": 300}], schema)
    assert out["id"].to_list() == [300]
    assert out.schema["id"] == pl.Int64

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def ensure_standard_converters():
    """Ensure standard converters are registered before each test."""
    _register_standard_converters()


@pytest.fixture
def tagging_converter():
    """A Python-only converter whose real invocations are observable."""
    name = "_test_python_only_tag_"
    calls: list = []

    def _tag(value, *, field_name=None, **kwargs):
        calls.append(value)
        return f"<{value}>"

    CustomTypeRegistry.register(
        name=name,
        target_universal_type="string",
        python_converter=_tag,
        description="Test Python-only converter recording each invocation",
    )
    try:
        yield name, calls
    finally:
        CustomTypeRegistry.unregister(name)


# ---------------------------------------------------------------------------
# TestSeparateConversions
# ---------------------------------------------------------------------------


class TestSeparateConversions:
    """Tests for the standalone separate_conversions() function."""

    def test_native_integer(self):
        """A field with type=INTEGER and no custom_cast goes to native tier."""
        schema = TableSchema(fields={"id": FieldDefinition(type=UniversalType.INTEGER)})
        python_only, narwhals, native = separate_conversions(schema)
        assert "id" in native
        assert "id" not in python_only
        assert "id" not in narwhals

    def test_custom_safe_float_is_narwhals(self):
        """safe_float has a Narwhals converter → goes to narwhals tier."""
        schema = TableSchema(fields={
            "amount": FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float"),
        })
        python_only, narwhals, native = separate_conversions(schema)
        assert "amount" in narwhals
        assert "amount" not in python_only
        assert "amount" not in native

    def test_no_cast_is_native(self):
        """Field with no cast type goes to native (nothing to do but pass through)."""
        schema = TableSchema(fields={"label": FieldDefinition(type=UniversalType.ANY)})
        python_only, narwhals, native = separate_conversions(schema)
        assert "label" in native
        assert "label" not in python_only
        assert "label" not in narwhals

    def test_mixed_routing(self):
        """Mixed schema routes each field to the correct tier, keyed by target name."""
        schema = TableSchema(
            fields={
                "amount": FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float"),   # → narwhals
                "id": FieldDefinition(type=UniversalType.INTEGER),      # → native
                "tag": FieldDefinition(type=UniversalType.ANY, rename_from="label"),            # → native
            }
        )
        python_only, narwhals, native = separate_conversions(schema)

        assert "amount" in narwhals
        # tag is declared under its target name; its source column is "label"
        assert "tag" in native
        assert source_column_name("tag", native["tag"]) == "label"
        assert "id" in native
        assert len(python_only) == 0

    def test_fan_out_targets_keep_distinct_entries(self):
        """Two targets reading one source are both routed (neither replaces the other)."""
        schema = TableSchema(fields={
            "x": FieldDefinition(type=UniversalType.INTEGER, rename_from="raw"),
            "y": FieldDefinition(type=UniversalType.STRING, rename_from="raw"),
        })
        _, _, native = separate_conversions(schema)
        assert list(native) == ["x", "y"]

    def test_python_only_converter_goes_to_python_only(self):
        """A custom_cast with no Narwhals implementation goes to python_only."""
        # Register a Python-only converter for this test
        def _dummy(value, *, field_name=None):
            return value

        name = "_test_python_only_dummy_"
        if not CustomTypeRegistry.has_converter(name):
            CustomTypeRegistry.register(
                name=name,
                target_universal_type="string",
                python_converter=_dummy,
                description="Test Python-only converter",
            )

        try:
            schema = TableSchema(fields={"col": FieldDefinition(type=UniversalType.ANY, custom_cast=name)})
            python_only, narwhals, native = separate_conversions(schema)
            assert "col" in python_only
            assert "col" not in narwhals
            assert "col" not in native
        finally:
            CustomTypeRegistry.unregister(name)


# ---------------------------------------------------------------------------
# TestTier3PythonEdge
# ---------------------------------------------------------------------------


class TestTier3PythonEdge:
    """Tests for apply_custom_converters_to_dict and apply_custom_converters_to_dicts."""

    def test_single_dict_safe_float(self):
        """safe_float converter on 'amount' field converts string to float."""
        definition = FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float")
        custom_conversions = {"amount": definition}
        data = {"amount": "42.5", "id": "123", "name": "Alice"}
        result = apply_custom_converters_to_dict(data, custom_conversions)
        assert result["amount"] == 42.5
        assert isinstance(result["amount"], float)
        # Other fields untouched
        assert result["id"] == "123"
        assert result["name"] == "Alice"
        # The caller's dict is not mutated
        assert data["amount"] == "42.5"

    def test_list_of_dicts(self):
        """safe_float converter applied to multiple rows."""
        definition = FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float")
        custom_conversions = {"amount": definition}
        data = [
            {"amount": "10.0", "label": "a"},
            {"amount": "99.9", "label": "b"},
            {"amount": "0.5", "label": "c"},
        ]
        result = apply_custom_converters_to_dicts(data, custom_conversions)
        assert len(result) == 3
        assert result[0]["amount"] == 10.0
        assert result[1]["amount"] == 99.9
        assert result[2]["amount"] == 0.5
        assert result[0]["label"] == "a"

    def test_empty_conversions_passthrough(self):
        """Empty conversions dict returns data unchanged (no definition applied)."""
        data = {"amount": "42.5", "id": "123"}
        result = apply_custom_converters_to_dict(data, {})
        assert result == data

    def test_empty_conversions_list_passthrough(self):
        """Empty conversions on list of dicts returns same list (short-circuit)."""
        data = [{"amount": "42.5"}, {"amount": "10.0"}]
        result = apply_custom_converters_to_dicts(data, {})
        assert result is data  # Short-circuit returns same object

    def test_none_value_safe_float(self):
        """safe_float handles None value without error."""
        definition = FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float")
        custom_conversions = {"amount": definition}
        data = {"amount": None, "id": "1"}
        result = apply_custom_converters_to_dict(data, custom_conversions)
        assert result["amount"] is None
        assert result["id"] == "1"

    def test_target_reads_its_source_column(self, tagging_converter):
        name, calls = tagging_converter
        schema = TableSchema(fields={
            "tag": FieldDefinition(rename_from="label", custom_cast=name),
        })
        python_only, _, _ = separate_conversions(schema)
        result = apply_custom_converters_to_dict({"label": "a", "id": 1}, python_only)
        assert result == {"label": "a", "id": 1, "tag": "<a>"}
        assert calls == ["a"]

    def test_swapped_targets_read_unchanged_source_values(self, tagging_converter):
        name, calls = tagging_converter
        schema = TableSchema(fields={
            "left": FieldDefinition(rename_from="right", custom_cast=name),
            "right": FieldDefinition(rename_from="left", custom_cast=name),
        })
        python_only, _, _ = separate_conversions(schema)
        result = apply_custom_converters_to_dict({"left": "L", "right": "R"}, python_only)
        assert result == {"left": "<R>", "right": "<L>"}
        # exactly one invocation per declared target, each on an original value
        assert calls == ["R", "L"]

    def test_fan_out_runs_each_target_once_on_the_original_source(self, tagging_converter):
        name, calls = tagging_converter
        schema = TableSchema(fields={
            "x": FieldDefinition(rename_from="raw", custom_cast=name),
            "y": FieldDefinition(rename_from="raw", custom_cast=name),
        })
        python_only, _, _ = separate_conversions(schema)
        result = apply_custom_converters_to_dict({"raw": "v"}, python_only)
        assert result == {"raw": "v", "x": "<v>", "y": "<v>"}
        assert calls == ["v", "v"]


# ---------------------------------------------------------------------------
# TestTier1NativeDataFrame
# ---------------------------------------------------------------------------


class TestTier1NativeDataFrame:
    """Tests for apply_native_conversions_to_dataframe."""

    def test_integer_cast(self):
        """String column cast to integer via native conversions."""
        df = pl.DataFrame({"id": ["1", "2", "3"], "name": ["a", "b", "c"]})
        definition = FieldDefinition(type=UniversalType.INTEGER)
        native_conversions = {"id": definition}
        result = apply_native_conversions_to_dataframe(df, native_conversions)
        assert result["id"].dtype == pl.Int64

    def test_empty_conversions_passthrough(self):
        """Empty native conversions returns DataFrame unchanged."""
        df = pl.DataFrame({"id": ["1", "2"], "name": ["a", "b"]})
        result = apply_native_conversions_to_dataframe(df, {})
        assert result.schema == df.schema

    def test_geopoint_native_conversion_uses_field_format(self):
        df = pl.DataFrame({"point": [[1.0, 2.0]]})
        definition = FieldDefinition(type=UniversalType.GEOPOINT, format="array")
        result = apply_native_conversions_to_dataframe(df, {"point": definition})
        assert result["point"].to_list() == [[1.0, 2.0]]
        assert result.shape == df.shape


# ---------------------------------------------------------------------------
# TestTier2NarwhalsVectorized
# ---------------------------------------------------------------------------


class TestTier2NarwhalsVectorized:
    """Tests for _apply_narwhals_custom_converters."""

    def test_safe_float_vectorized(self):
        """safe_float via Narwhals converts string column to Float64."""
        df = pl.DataFrame({"amount": ["1.5", "2.7", "10.0"]})
        definition = FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float")
        narwhals_custom = {"amount": definition}
        result = _apply_narwhals_custom_converters(df, narwhals_custom)
        assert result["amount"].dtype == pl.Float64
        assert result["amount"].to_list() == [1.5, 2.7, 10.0]

    def test_safe_float_vectorized_with_none(self):
        """safe_float via Narwhals converts NaN values to None."""
        df = pl.DataFrame({"amount": ["1.5", None, "3.0"]})
        definition = FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float")
        narwhals_custom = {"amount": definition}
        result = _apply_narwhals_custom_converters(df, narwhals_custom)
        assert result["amount"].dtype == pl.Float64
        vals = result["amount"].to_list()
        assert vals[0] == 1.5
        assert vals[1] is None
        assert vals[2] == 3.0

    def test_swapped_targets_read_unchanged_source_columns(self):
        df = pl.DataFrame({"a": ["1.5"], "b": ["2.5"]})
        narwhals_custom = {
            "a": FieldDefinition(rename_from="b", custom_cast="safe_float"),
            "b": FieldDefinition(rename_from="a", custom_cast="safe_float"),
        }
        result = _apply_narwhals_custom_converters(df, narwhals_custom)
        assert result["a"].to_list() == [2.5]
        assert result["b"].to_list() == [1.5]

    def test_fan_out_reads_the_original_source_for_each_target(self):
        df = pl.DataFrame({"raw": ["1.5"]})
        narwhals_custom = {
            "x": FieldDefinition(rename_from="raw", custom_cast="safe_float"),
            "y": FieldDefinition(rename_from="raw", custom_cast="safe_float"),
        }
        result = _apply_narwhals_custom_converters(df, narwhals_custom)
        assert result["x"].to_list() == [1.5]
        assert result["y"].to_list() == [1.5]
        assert result["raw"].to_list() == ["1.5"]


# ---------------------------------------------------------------------------
# TestHybridEndToEnd
# ---------------------------------------------------------------------------


class TestHybridEndToEnd:
    """Tests for apply_hybrid_conversion (full pipeline)."""

    def test_native_only(self):
        """TableSchema with integer cast produces correct dtype."""
        schema = TableSchema(
            fields={
                "id": FieldDefinition(type=UniversalType.INTEGER),
                "name": FieldDefinition(type=UniversalType.STRING),
            },
        )
        data = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
        df = apply_hybrid_conversion(data, schema)
        assert isinstance(df, pl.DataFrame)
        assert df["id"].dtype == pl.Int64
        assert df["name"].to_list() == ["Alice", "Bob"]

    def test_no_schema_creates_dataframe(self):
        """None schema just creates DataFrame from dicts."""
        data = [{"x": 1, "y": "hello"}, {"x": 2, "y": "world"}]
        df = apply_hybrid_conversion(data, None)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 2)
        assert set(df.columns) == {"x", "y"}

    def test_safe_float_end_to_end(self):
        """apply_hybrid_conversion with safe_float produces Float64 column."""
        schema = TableSchema(
            fields={
                "price": FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float"),
                "name": FieldDefinition(type=UniversalType.STRING),
            },
        )
        data = [{"price": "9.99", "name": "Widget"}, {"price": "4.50", "name": "Gizmo"}]
        df = apply_hybrid_conversion(data, schema)
        assert df["price"].dtype == pl.Float64
        assert df["price"].to_list() == [9.99, 4.50]

    def test_tier_assignment(self):
        """separate_conversions routes safe_float to narwhals, integer to native."""
        schema = TableSchema(
            fields={
                "amount": FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float"),
                "id": FieldDefinition(type=UniversalType.INTEGER),
                "tag": FieldDefinition(type=UniversalType.ANY, rename_from="label"),
            },
        )
        python_only, narwhals_custom, native = separate_conversions(schema)

        # safe_float is vectorized → narwhals tier
        assert "amount" in narwhals_custom

        # integer → native tier
        assert "id" in native

        # rename (source column is "label") → native tier, keyed by target
        assert "tag" in native

        # safe_float must NOT be in python_only
        assert "amount" not in python_only

    def test_python_only_fan_out_converts_once_per_target(self, tagging_converter):
        name, calls = tagging_converter
        schema = TableSchema(fields={
            "x": FieldDefinition(rename_from="raw", custom_cast=name),
            "y": FieldDefinition(rename_from="raw", custom_cast=name),
        })
        df = apply_hybrid_conversion([{"raw": "v"}, {"raw": "w"}], schema)
        assert df["x"].to_list() == ["<v>", "<w>"]
        assert df["y"].to_list() == ["<v>", "<w>"]
        assert df["raw"].to_list() == ["v", "w"]
        assert calls == ["v", "v", "w", "w"]

    def test_python_only_swap_converts_original_sources(self, tagging_converter):
        name, calls = tagging_converter
        schema = TableSchema(fields={
            "left": FieldDefinition(rename_from="right", custom_cast=name),
            "right": FieldDefinition(rename_from="left", custom_cast=name),
        })
        df = apply_hybrid_conversion([{"left": "L", "right": "R"}], schema)
        assert df.to_dicts() == [{"left": "<R>", "right": "<L>"}]
        assert calls == ["R", "L"]

    @pytest.mark.parametrize("shape", [
        "rows", "record", "columns", "tuple", "tuples", "namedtuple",
        "namedtuples", "dataclass", "dataclasses", "pydantic", "pydantics",
        "indexed", "polars_series", "pandas_series", "frame",
    ])
    def test_mixed_tier_rotation_reads_original_sources(self, tagging_converter, shape):
        from collections import namedtuple
        from dataclasses import make_dataclass

        import pandas as pd
        from pydantic import create_model
        from mountainash.pydata.ingress.pydata_ingress import PydataIngress

        name, calls = tagging_converter
        schema = TableSchema(fields={
            "copy": FieldDefinition(type=UniversalType.INTEGER, rename_from="col_2"),
            "col_1": FieldDefinition(rename_from="col_2", custom_cast=name),
            "col_2": FieldDefinition(rename_from="col_3", custom_cast="safe_float"),
            "col_3": FieldDefinition(type=UniversalType.INTEGER, rename_from="col_1"),
        }, fields_match="open")
        row = {"col_0": "untouched", "col_1": "1", "col_2": "2", "col_3": "3"}
        RecordTuple = namedtuple("RecordTuple", row)
        RecordClass = make_dataclass("RecordClass", [(key, str) for key in row])
        RecordModel = create_model("RecordModel", **{key: (str, ...) for key in row})
        inputs = {
            "rows": lambda: [row], "record": lambda: row,
            "columns": lambda: {key: [value] for key, value in row.items()},
            "tuple": lambda: tuple(row.values()), "tuples": lambda: [tuple(row.values())],
            "namedtuple": lambda: RecordTuple(**row),
            "namedtuples": lambda: [RecordTuple(**row)],
            "dataclass": lambda: RecordClass(**row),
            "dataclasses": lambda: [RecordClass(**row)],
            "pydantic": lambda: RecordModel(**row),
            "pydantics": lambda: [RecordModel(**row)],
            "indexed": lambda: {"group": [row]},
            "polars_series": lambda: {key: pl.Series([value]) for key, value in row.items()},
            "pandas_series": lambda: {key: pd.Series([value]) for key, value in row.items()},
            "frame": lambda: pl.DataFrame([row]),
        }
        result = PydataIngress.convert(inputs[shape](), table_schema=schema)
        expected = {"col_0": "untouched", "col_1": "<2>", "col_2": 3.0, "col_3": 1}
        if shape == "indexed":
            expected["index"] = "group"
        expected["copy"] = 2
        assert result.to_dicts() == [expected]
        # Row-based hybrid ingress preserves source positions; constructed-frame
        # ingress retains its existing shared-conform projection order.
        if shape in {"rows", "columns", "dataclass", "dataclasses", "pydantic", "pydantics"}:
            assert result.columns == list(expected)
        else:
            columns = ["col_0", "col_3", "copy", "col_1", "col_2"]
            if shape == "indexed":
                columns.append("index")
            assert result.columns == columns
        assert calls == ["2"]
        assert row == {"col_0": "untouched", "col_1": "1", "col_2": "2", "col_3": "3"}

    @pytest.mark.parametrize("container", [list, set, frozenset])
    def test_scalar_collection_fanout_uses_original_value(self, tagging_converter, container):
        from mountainash.pydata.ingress.pydata_ingress import PydataIngress

        name, calls = tagging_converter
        schema = TableSchema(fields={
            "value": FieldDefinition(custom_cast=name),
            "number": FieldDefinition(rename_from="value", custom_cast="safe_float"),
            "integer": FieldDefinition(type=UniversalType.INTEGER, rename_from="value"),
        }, fields_match="open")
        result = PydataIngress.convert(container(["2"]), table_schema=schema)
        assert result.to_dicts() == [{"value": "<2>", "number": 2.0, "integer": 2}]
        assert calls == ["2"]

    @pytest.mark.parametrize("mode", ["open", "exact"])
    @pytest.mark.parametrize("values,indices", [
        (["1", "bad", "3"], [0, 2]),
        (["bad", "bad", "bad"], []),
    ])
    def test_frame_custom_results_follow_native_row_discard(self, tagging_converter, values, indices, mode):
        from mountainash.pydata import PydataIngress

        name, calls = tagging_converter
        source = pl.DataFrame({
            "n": values,
            "label": ["A", "B", "C"],
            "raw": ["10", "20", "30"],
            "__ma_pydata_row_index": ["user-A", "user-B", "user-C"],
        })
        fields = {
            "n": FieldDefinition(type=UniversalType.INTEGER),
            "label": FieldDefinition(custom_cast=name),
            "number": FieldDefinition(rename_from="raw", custom_cast="safe_float"),
        }
        if mode == "exact":
            fields["__ma_pydata_row_index"] = FieldDefinition()
        schema = TableSchema(fields=fields, fields_match=mode, contract={"data_type": "discard_row"})
        result = PydataIngress.convert(source, table_schema=schema)
        expected = [
            {"n": 1, "label": "<A>", "__ma_pydata_row_index": "user-A", "number": 10.0},
            {"n": 2, "label": "<B>", "__ma_pydata_row_index": "user-B", "number": 20.0},
            {"n": 3, "label": "<C>", "__ma_pydata_row_index": "user-C", "number": 30.0},
        ]
        assert result.to_dicts() == [expected[index] for index in indices]
        assert set(result.columns) == {"n", "label", "__ma_pydata_row_index", "number"}
        assert calls == ["A", "B", "C"]
        assert source["label"].to_list() == ["A", "B", "C"]

    @pytest.mark.parametrize("empty", [False, True])
    def test_frame_custom_conversion_preserves_untouched_native_precision(self, tagging_converter, empty):
        from decimal import Decimal
        from mountainash.pydata import PydataIngress

        name, calls = tagging_converter
        source = pl.DataFrame({
            "label": ["001", "002"],
            "at": pl.Series([1, 1001]).cast(pl.Datetime("ns", "UTC")),
            "amount": pl.Series(
                [Decimal("1.2345"), Decimal("9.8765")], dtype=pl.Decimal(8, 4),
            ),
        }).with_columns(pl.struct("at").alias("payload"))
        if empty:
            source = source.clear()
        schema = TableSchema(fields={"label": FieldDefinition(custom_cast=name)}, fields_match="open")
        result = PydataIngress.convert(source, table_schema=schema)
        untouched = ["at", "amount", "payload"]
        assert result.select(untouched).equals(source.select(untouched))
        assert result.select(untouched).schema == source.select(untouched).schema
        assert result["label"].to_list() == ([] if empty else ["<001>", "<002>"])
        assert calls == ([] if empty else ["001", "002"])


def test_decimal_rename_survives_evidence_free_lowering():
    """This ingress boundary constructs Polars frames; it has no backend parameter."""
    from decimal import Decimal
    from mountainash.core.dtypes import DecimalDtype

    schema = TableSchema(fields={"amount": FieldDefinition(
        rename_from="raw", type=UniversalType.NUMBER,
        dtype=DecimalDtype(precision=38, scale=2),
    )}, fields_match="open")
    result = apply_hybrid_conversion([{"raw": Decimal("1.25")}], schema)
    assert result["amount"].to_list() == [Decimal("1.25")]


@pytest.mark.parametrize("inline", [False, True])
@pytest.mark.parametrize("vectorized", [False, True])
def test_source_typing_does_not_undo_custom_conversion(inline, vectorized):
    from mountainash.pydata.ingress.pydata_ingress import PydataIngress

    name = "safe_float" if vectorized else "_item302_digits_to_integer"
    if not vectorized:
        CustomTypeRegistry.register(
            name=name, target_universal_type="integer",
            python_converter=lambda value, **kwargs: None if value is None else int(value),
        )
    source = TableSchema(fields={"x": FieldDefinition(type=UniversalType.STRING)})
    target = TableSchema(fields={"x": FieldDefinition(custom_cast=name)})
    try:
        result = PydataIngress.convert(
            [{"x": "00123"}, {"x": None}, {"x": "00456"}],
            table_schema=target, source_table_schema=source, inline_conform=inline,
        )
        if inline:
            assert result["x"].dtype == (pl.Float64 if vectorized else pl.Int64)
            assert result["x"].to_list() == [123, None, 456]
        else:
            assert result["x"].dtype == pl.String
            assert result["x"].to_list() == ["00123", None, "00456"]
    finally:
        if not vectorized:
            CustomTypeRegistry.unregister(name)


def test_ingress_source_schema_overrides_preserve_nested_timestamp_parameters():
    from datetime import datetime, timezone
    from mountainash.core.dtypes import ListDtype, StructDtype, TimestampDtype
    from mountainash.pydata.ingress.pydata_ingress import PydataIngress

    dtype = ListDtype(StructDtype((
        ("at", TimestampDtype(9, True, "UTC")),
    )))
    source = TableSchema(fields={"events": FieldDefinition(dtype=dtype)})
    value = datetime(2026, 1, 1, tzinfo=timezone.utc)
    frame = PydataIngress.convert(
        [{"events": [{"at": value}]}], source_table_schema=source, inline_conform=False,
    )
    assert frame.schema["events"] == pl.List(
        pl.Struct([pl.Field("at", pl.Datetime("ns", "UTC"))])
    )
