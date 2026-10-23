"""Tests for all 10 pydata ingress handlers via PydataIngress.convert()."""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd
import polars as pl
import pytest
from pydantic import BaseModel

from mountainash.pydata.ingress.pydata_ingress import PydataIngress
from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType

# ---------------------------------------------------------------------------
# Inline test types (conftest types available as fixtures but not importable)
# ---------------------------------------------------------------------------


@dataclass
class Person:
    name: str
    age: int
    score: float


class PersonModel(BaseModel):
    name: str
    age: int
    score: float


Row = namedtuple("Row", ["name", "age", "score"])

SAMPLE_DICTS = [
    {"name": "Alice", "age": 30, "score": 1.5},
    {"name": "Bob", "age": 25, "score": 2.0},
    {"name": "Charlie", "age": 35, "score": 3.0},
]

SAMPLE_DICT_OF_LISTS = {
    "name": ["Alice", "Bob", "Charlie"],
    "age": [30, 25, 35],
    "score": [1.5, 2.0, 3.0],
}


# ---------------------------------------------------------------------------
# TestIngressFromPylist
# ---------------------------------------------------------------------------


class TestIngressFromPylist:
    def test_basic_list_of_dicts(self):
        df = PydataIngress.convert(SAMPLE_DICTS)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 3)
        assert set(df.columns) == {"name", "age", "score"}

    def test_correct_values(self):
        df = PydataIngress.convert(SAMPLE_DICTS)
        assert df["name"].to_list() == ["Alice", "Bob", "Charlie"]
        assert df["age"].to_list() == [30, 25, 35]

    def test_none_values_become_null(self):
        data = [{"a": 1, "b": None}, {"a": 2, "b": "x"}]
        df = PydataIngress.convert(data)
        assert df.shape == (2, 2)
        assert df["b"][0] is None

    def test_single_dict_in_list(self):
        df = PydataIngress.convert([{"x": 42}])
        assert df.shape == (1, 1)
        assert df["x"][0] == 42


# ---------------------------------------------------------------------------
# TestIngressFromPydict
# ---------------------------------------------------------------------------


class TestIngressFromPydict:
    def test_basic_dict_of_lists(self):
        df = PydataIngress.convert(SAMPLE_DICT_OF_LISTS)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 3)

    def test_column_order_preserved(self):
        data = {"c": [1, 2], "a": [3, 4], "b": [5, 6]}
        df = PydataIngress.convert(data)
        assert df.columns == ["c", "a", "b"]


# ---------------------------------------------------------------------------
# TestIngressFromDataclass
# ---------------------------------------------------------------------------


class TestIngressFromDataclass:
    def test_single_instance(self):
        df = PydataIngress.convert(Person("Alice", 30, 1.5))
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] >= 1
        assert "name" in df.columns

    def test_list_of_instances(self):
        persons = [Person("Alice", 30, 1.5), Person("Bob", 25, 2.0)]
        df = PydataIngress.convert(persons)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 3)
        assert df["name"].to_list() == ["Alice", "Bob"]
        assert df["age"].to_list() == [30, 25]


# ---------------------------------------------------------------------------
# TestIngressFromPydantic
# ---------------------------------------------------------------------------


class TestIngressFromPydantic:
    def test_single_instance(self):
        df = PydataIngress.convert(PersonModel(name="Alice", age=30, score=1.5))
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] >= 1

    def test_list_of_instances(self):
        persons = [
            PersonModel(name="Alice", age=30, score=1.5),
            PersonModel(name="Bob", age=25, score=2.0),
        ]
        df = PydataIngress.convert(persons)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 3)
        assert df["name"].to_list() == ["Alice", "Bob"]


# ---------------------------------------------------------------------------
# TestIngressFromNamedTuple
# ---------------------------------------------------------------------------


class TestIngressFromNamedTuple:
    def test_single_instance(self):
        df = PydataIngress.convert(Row("Alice", 30, 1.5))
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] >= 1

    def test_list_of_instances(self):
        rows = [Row("Alice", 30, 1.5), Row("Bob", 25, 2.0)]
        df = PydataIngress.convert(rows)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 3)

    def test_field_names_become_columns(self):
        rows = [Row("Alice", 30, 1.5), Row("Bob", 25, 2.0)]
        df = PydataIngress.convert(rows)
        assert set(df.columns) == {"name", "age", "score"}


# ---------------------------------------------------------------------------
# TestIngressFromTuple
# ---------------------------------------------------------------------------


class TestIngressFromTuple:
    def test_list_of_plain_tuples(self):
        data = [(1, "a"), (2, "b"), (3, "c")]
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 2)


# ---------------------------------------------------------------------------
# TestIngressFromSeriesDict
# ---------------------------------------------------------------------------


class TestIngressFromSeriesDict:
    def test_polars_series_dict(self):
        data = {
            "a": pl.Series([1, 2, 3]),
            "b": pl.Series(["x", "y", "z"]),
        }
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 2)
        assert set(df.columns) == {"a", "b"}

    def test_pandas_series_dict(self):
        data = {
            "a": pd.Series([1, 2, 3]),
            "b": pd.Series(["x", "y", "z"]),
        }
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 2)
        assert set(df.columns) == {"a", "b"}


# ---------------------------------------------------------------------------
# TestIngressFromIndexedData
# ---------------------------------------------------------------------------


class TestIngressFromIndexedData:
    def test_basic_indexed_data(self):
        data = {
            "group_a": [{"x": 1}, {"x": 2}],
            "group_b": [{"x": 3}],
        }
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 3


# ---------------------------------------------------------------------------
# TestIngressFromCollection
# ---------------------------------------------------------------------------


class TestIngressFromCollection:
    def test_list_of_scalars(self):
        data = [1, 2, 3]
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 3

    def test_set_of_strings(self):
        data = {"a", "b", "c"}
        df = PydataIngress.convert(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 3


# ---------------------------------------------------------------------------
# TestIngressFromDefault
# ---------------------------------------------------------------------------


class TestIngressFromDefault:
    def test_polars_dataframe_falls_back_to_default(self):
        # A pl.DataFrame is not explicitly handled by any specific ingress type,
        # so it routes to the UNKNOWN/default strategy
        df_input = pl.DataFrame(SAMPLE_DICT_OF_LISTS)
        strategy = PydataIngressFactory.get_strategy(df_input)
        assert strategy is not None


@dataclass
class SourceCell:
    amount: float | None
    source_text: str | None


class SourceCellModel(BaseModel):
    amount: float | None
    source_text: str | None


@dataclass
class AnnotatedSource:
    code: int | None
    label: str | None
    inferred: Any


@dataclass
class MixedSource:
    value: int | str | None


class TestDeclaredIngress:
    @pytest.mark.parametrize("model", [SourceCell, SourceCellModel])
    @pytest.mark.parametrize("late_text", ["N/A", None])
    def test_model_evidence_retains_late_and_all_null_columns(self, model, late_text):
        rows = [model(amount=1.5, source_text=None) for _ in range(108)]
        rows.append(model(amount=None, source_text=late_text))
        result = PydataIngress.convert(rows)
        assert result.schema == {"amount": pl.Float64, "source_text": pl.String}
        assert result.to_dicts() == [
            {"amount": 1.5, "source_text": None}
        ] * 108 + [{"amount": None, "source_text": late_text}]

    def test_explicit_source_precedence_is_per_column(self):
        rows = [AnnotatedSource(None, None, 7)] * 100
        rows.append(AnnotatedSource("00123", "N/A", 8))
        source = TableSchema(fields={"code": FieldDefinition(type=UniversalType.STRING)})
        result = PydataIngress.convert(rows, source_table_schema=source)
        assert result.schema == {"code": pl.String, "label": pl.String, "inferred": pl.Int64}
        assert result.to_dicts() == [
            {"code": None, "label": None, "inferred": 7}
        ] * 100 + [{"code": "00123", "label": "N/A", "inferred": 8}]

    def test_any_source_falls_through_to_model_and_value_evidence(self):
        source = TableSchema(fields={
            "code": FieldDefinition(type=UniversalType.ANY),
            "inferred": FieldDefinition(type=UniversalType.ANY),
        })
        result = PydataIngress.convert([AnnotatedSource(42, None, 7)], source_table_schema=source)
        assert result.schema == {"code": pl.Int64, "label": pl.String, "inferred": pl.Int64}
        assert result.to_dicts() == [{"code": 42, "label": None, "inferred": 7}]

    def test_multi_type_model_union_leaves_native_inference(self):
        result = PydataIngress.convert([MixedSource("00123"), MixedSource(None)])
        assert result.schema == {"value": pl.String}
        assert result.to_dicts() == [{"value": "00123"}, {"value": None}]

    @pytest.mark.parametrize("columnar", [False, True])
    @pytest.mark.parametrize("inline", [False, True])
    def test_source_text_and_target_date_are_separate(self, columnar, inline):
        values = [None] * 100 + ["2026-10-12"]
        data = {"raw": values} if columnar else [{"raw": value} for value in values]
        source = TableSchema(fields={"raw": FieldDefinition(type=UniversalType.STRING)})
        target = TableSchema(fields={
            "day": FieldDefinition(rename_from="raw", type=UniversalType.DATE)
        })
        result = PydataIngress.convert(
            data, table_schema=target, source_table_schema=source, inline_conform=inline,
        )
        if inline:
            assert result["day"].dtype == pl.Date
            assert result["day"].to_list() == [None] * 100 + [date(2026, 10, 12)]
        else:
            assert result.schema == {"raw": pl.String}
            assert result.to_dicts() == [{"raw": value} for value in values]

    def test_target_does_not_supply_source_evidence(self):
        target = TableSchema(fields={"x": FieldDefinition(type=UniversalType.DATE)})
        rows = [{"x": None}] * 101
        result = PydataIngress.convert(rows, table_schema=target, inline_conform=False)
        assert result.schema == {"x": pl.Null}
        assert result.to_dicts() == rows

    def test_source_names_do_not_apply_target_transforms_or_drop_columns(self):
        source = TableSchema(fields={
            "renamed": FieldDefinition(rename_from="raw", type=UniversalType.STRING, null_fill="filled")
        })
        result = PydataIngress.convert([{"other": 7, "raw": None}], source_table_schema=source)
        assert result.schema == {"other": pl.Int64, "raw": pl.String}
        assert result.to_dicts() == [{"other": 7, "raw": None}]

    def test_source_alias_cannot_replace_another_model_column_dtype(self):
        source = TableSchema(fields={
            "code": FieldDefinition(rename_from="label", type=UniversalType.STRING)
        })
        result = PydataIngress.convert([AnnotatedSource(42, "00123", 7)], source_table_schema=source)
        assert result.schema == {"code": pl.Int64, "label": pl.String, "inferred": pl.Int64}
        assert result.to_dicts() == [{"code": 42, "label": "00123", "inferred": 7}]

    @pytest.mark.parametrize("series_type", [pl.Series, pd.Series])
    def test_explicit_native_refinement_overrides_series_type(self, series_type):
        source = TableSchema(fields={
            "x": FieldDefinition(type=UniversalType.ANY, backend_type="Int8")
        })
        result = PydataIngress.convert({"x": series_type([1, 2])}, source_table_schema=source)
        assert result.schema == {"x": pl.Int8}
        assert result.to_dicts() == [{"x": 1}, {"x": 2}]
