"""Tests for Relation terminal methods delegating to the egress module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import polars as pl
import pytest

import mountainash as ma


@dataclass
class PersonDC:
    name: str
    age: int
    score: Optional[float] = None


try:
    from pydantic import BaseModel

    class PersonPydantic(BaseModel):
        name: str
        age: int
        score: Optional[float] = None

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    PersonPydantic = None  # type: ignore


@pytest.fixture
def sample_rel():
    df = pl.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
        "score": [1.5, None, 3.0],
    })
    return ma.relation(df)


class TestToDictDelegation:
    def test_returns_dict_of_lists(self, sample_rel):
        result = sample_rel.to_dict()
        assert isinstance(result, dict)
        assert result["name"] == ["Alice", "Bob", "Charlie"]
        assert result["age"] == [30, 25, 35]

    def test_values_not_series(self, sample_rel):
        result = sample_rel.to_dict()
        assert isinstance(result["name"], list)


class TestToDictsDelegation:
    def test_returns_list_of_dicts(self, sample_rel):
        result = sample_rel.to_dicts()
        assert isinstance(result, list)
        assert result[0] == {"name": "Alice", "age": 30, "score": 1.5}

    def test_null_preserved(self, sample_rel):
        result = sample_rel.to_dicts()
        assert result[1]["score"] is None


class TestToTuplesDelegation:
    def test_returns_list_of_tuples(self, sample_rel):
        result = sample_rel.to_tuples()
        assert isinstance(result, list)
        assert result[0] == ("Alice", 30, 1.5)


class TestToPandasDelegation:
    def test_returns_pandas_dataframe(self, sample_rel):
        pytest.importorskip("pandas")
        import pandas as pd
        result = sample_rel.to_pandas()
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name", "age", "score"]


class TestToDataclassesDelegation:
    def test_returns_dataclass_instances(self, sample_rel):
        result = sample_rel.to_dataclasses(PersonDC)
        assert len(result) == 3
        assert isinstance(result[0], PersonDC)
        assert result[0].name == "Alice"
        assert result[0].age == 30

    def test_auto_derive_schema_false_skips_hybrid(self, sample_rel):
        result = sample_rel.to_dataclasses(PersonDC, auto_derive_schema=False)
        assert len(result) == 3
        assert isinstance(result[0], PersonDC)


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic not installed")
class TestToPydanticDelegation:
    def test_returns_pydantic_instances(self, sample_rel):
        result = sample_rel.to_pydantic(PersonPydantic)
        assert len(result) == 3
        assert result[0].name == "Alice"

    def test_non_pydantic_class_raises(self, sample_rel):
        """Non-Pydantic fallback is removed -- must raise, not silently work."""
        with pytest.raises((ValueError, TypeError, ImportError, AttributeError)):
            sample_rel.to_pydantic(PersonDC)


# ---------------------------------------------------------------------------
# New terminals (Task 4)
# ---------------------------------------------------------------------------


class TestToNamedTuples:
    def test_returns_named_tuples(self, sample_rel):
        result = sample_rel.to_named_tuples()
        assert len(result) == 3
        assert hasattr(result[0], "name")
        assert result[0].name == "Alice"


class TestToTypedNamedTuples:
    def test_returns_typed_named_tuples(self, sample_rel):
        result = sample_rel.to_typed_named_tuples()
        assert len(result) == 3
        assert hasattr(result[0], "__annotations__")

    def test_preserve_dates_parameter(self):
        import datetime
        df = pl.DataFrame({"dt": [datetime.date(2024, 1, 1)]})
        rel = ma.relation(df)
        result = rel.to_typed_named_tuples(preserve_dates=True)
        assert result[0].__class__.__annotations__["dt"] is datetime.date


class TestToPyArrow:
    def test_returns_pyarrow_table(self, sample_rel):
        pa = pytest.importorskip("pyarrow")
        result = sample_rel.to_pyarrow()
        assert isinstance(result, pa.Table)
        assert result.num_rows == 3


class TestToNarwhals:
    def test_returns_narwhals_frame(self, sample_rel):
        nw = pytest.importorskip("narwhals")
        result = sample_rel.to_narwhals()
        assert hasattr(result, "to_native")

    def test_as_lazy(self, sample_rel):
        nw = pytest.importorskip("narwhals")
        result = sample_rel.to_narwhals(as_lazy=True)
        assert hasattr(result, "collect")


class TestToIbis:
    def test_returns_ibis_table(self, sample_rel):
        ibis = pytest.importorskip("ibis")
        result = sample_rel.to_ibis()
        assert hasattr(result, "execute")


class TestToDictOfSeriesPolars:
    def test_returns_dict_of_series(self, sample_rel):
        result = sample_rel.to_dict_of_series_polars()
        assert isinstance(result, dict)
        assert isinstance(result["name"], pl.Series)


class TestToDictOfSeriesPandas:
    def test_returns_dict_of_pandas_series(self, sample_rel):
        pd = pytest.importorskip("pandas")
        result = sample_rel.to_dict_of_series_pandas()
        assert isinstance(result, dict)
        assert isinstance(result["name"], pd.Series)


class TestToIndexOfDicts:
    def test_single_key(self, sample_rel):
        result = sample_rel.to_index_of_dicts(index_fields="name")
        assert "Alice" in result
        assert isinstance(result["Alice"], list)
        assert result["Alice"][0]["age"] == 30

    def test_multi_key(self):
        df = pl.DataFrame({"region": ["AU", "AU", "US"], "year": [2024, 2025, 2024], "val": [1, 2, 3]})
        result = ma.relation(df).to_index_of_dicts(index_fields=["region", "year"])
        assert ("AU", 2024) in result


class TestToIndexOfTuples:
    def test_single_key(self, sample_rel):
        result = sample_rel.to_index_of_tuples(index_fields="name")
        assert "Alice" in result
        assert isinstance(result["Alice"][0], tuple)


class TestToIndexOfNamedTuples:
    def test_single_key(self, sample_rel):
        result = sample_rel.to_index_of_named_tuples(index_fields="name")
        assert "Alice" in result
        assert hasattr(result["Alice"][0], "age")


class TestToIndexOfTypedNamedTuples:
    def test_single_key(self, sample_rel):
        result = sample_rel.to_index_of_typed_named_tuples(index_fields="name")
        assert "Alice" in result
        assert hasattr(result["Alice"][0], "__annotations__")


# ---------------------------------------------------------------------------
# Edge cases (Task 6 — to_dicts behavioral equivalence)
# ---------------------------------------------------------------------------


class TestToDictsEdgeCases:
    def test_nested_struct(self):
        df = pl.DataFrame([
            {"id": 1, "meta": {"score": 10.5, "label": "high"}},
            {"id": 2, "meta": {"score": 3.2, "label": "low"}},
        ])
        rel = ma.relation(df)
        old_result = df.to_dicts()
        new_result = rel.to_dicts()
        assert new_result == old_result

    def test_list_column(self):
        df = pl.DataFrame({"tags": [["a", "b"], ["c"]], "id": [1, 2]})
        rel = ma.relation(df)
        old_result = df.to_dicts()
        new_result = rel.to_dicts()
        assert new_result == old_result

    def test_null_values(self):
        df = pl.DataFrame({"a": [1, None, 3], "b": [None, "x", None]})
        rel = ma.relation(df)
        old_result = df.to_dicts()
        new_result = rel.to_dicts()
        assert new_result == old_result


# ---------------------------------------------------------------------------
# Structured logical egress delegation (spec Task 5)
# ---------------------------------------------------------------------------


@pytest.fixture
def structured_rel():
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    df = pl.DataFrame({"tags": ["[1,2]", "[3]"], "name": ["a", "b"]})
    spec = TypeSpec(
        fields_match="open", fields=[FieldSpec(name="tags", type=UniversalType.ARRAY)]
    )
    return ma.relation(df).conform(spec, contract={"data_type": "coerce"})


class TestStructuredLogicalEgressDelegation:
    """Every Python-egress terminal delegates through to_polars(); a
    structured field resolves once through the shared logical snapshot,
    not per terminal (spec Task 5 step 6)."""

    def test_to_dict_decodes_structured_field(self, structured_rel):
        result = structured_rel.to_dict()
        assert result["tags"] == [[1, 2], [3]]

    def test_to_dicts_decodes_structured_field(self, structured_rel):
        result = structured_rel.to_dicts()
        assert result == [{"tags": [1, 2], "name": "a"}, {"tags": [3], "name": "b"}]

    def test_to_tuples_decodes_structured_field(self, structured_rel):
        result = structured_rel.to_tuples()
        assert result[0][0] == [1, 2]

    def test_item_decodes_structured_field(self, structured_rel):
        assert structured_rel.item("tags", 0) == [1, 2]

    def test_to_pandas_tags_object_column(self, structured_rel):
        result = structured_rel.to_pandas()
        assert result["tags"].dtype == object
        assert result["tags"].tolist() == [[1, 2], [3]]
