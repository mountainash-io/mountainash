"""End-to-end pipeline integration tests.

Tests the full pipeline: Python data → ingress → conform → relation → expression filter → output.
Validates that typespec, conform, pydata, relations, and expressions modules work together.
"""

import pytest
import polars as pl
import mountainash as ma
from mountainash.conform.builder import ConformBuilder
from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory


@pytest.fixture
def ingress_factory():
    return PydataIngressFactory()


@pytest.fixture
def sample_records():
    return [
        {"age": "25", "name": "alice", "score": "88.5"},
        {"age": "35", "name": "bob", "score": "92.1"},
        {"age": "20", "name": "charlie", "score": "76.3"},
        {"age": "42", "name": "diana", "score": "95.0"},
    ]


class TestPydataIngress:
    """Test Python data → DataFrame conversion."""

    def test_dict_to_dataframe(self, ingress_factory):
        data = {"col1": [1, 2, 3], "col2": ["a", "b", "c"]}
        result = ingress_factory.convert(data)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 2)

    def test_list_of_dicts_to_dataframe(self, ingress_factory, sample_records):
        result = ingress_factory.convert(sample_records)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (4, 3)
        assert set(result.columns) == {"age", "name", "score"}

    def test_ingress_preserves_string_types(self, ingress_factory, sample_records):
        result = ingress_factory.convert(sample_records)
        assert result.dtypes == [pl.String, pl.String, pl.String]


class TestConformTransform:
    """Test DataFrame → conform-transformed DataFrame."""

    def test_cast_string_to_integer(self):
        df = pl.DataFrame({"age": ["25", "35"], "name": ["alice", "bob"]})
        result = ConformBuilder({"age": {"cast": "integer"}}).apply(df)
        assert result["age"].dtype == pl.Int64

    def test_cast_string_to_float(self):
        df = pl.DataFrame({"score": ["88.5", "92.1"]})
        result = ConformBuilder({"score": {"cast": "number"}}).apply(df)
        assert result["score"].dtype == pl.Float64

    def test_cast_multiple_columns(self):
        df = pl.DataFrame({"age": ["25", "35"], "score": ["88.5", "92.1"], "name": ["a", "b"]})
        result = ConformBuilder({
            "age": {"cast": "integer"},
            "score": {"cast": "number"},
        }).apply(df)
        assert result["age"].dtype == pl.Int64
        assert result["score"].dtype == pl.Float64
        assert result["name"].dtype == pl.String


class TestRelationExpressionFilter:
    """Test DataFrame → relation → expression filter → output."""

    def test_filter_with_expression(self):
        df = pl.DataFrame({"age": [25, 35, 20, 42], "name": ["alice", "bob", "charlie", "diana"]})
        result = ma.relation(df).filter(ma.col("age").gt(ma.lit(30))).to_polars()
        assert result.shape[0] == 2
        assert set(result["name"].to_list()) == {"bob", "diana"}

    def test_sort_and_head(self):
        df = pl.DataFrame({"age": [25, 35, 20, 42], "name": ["alice", "bob", "charlie", "diana"]})
        result = ma.relation(df).sort("age").head(2).to_polars()
        assert result.shape[0] == 2
        assert result["name"].to_list() == ["charlie", "alice"]

    def test_select_columns(self):
        df = pl.DataFrame({"age": [25, 35], "name": ["alice", "bob"], "score": [88, 92]})
        result = ma.relation(df).select("name", "score").to_polars()
        assert result.columns == ["name", "score"]


class TestFullPipeline:
    """End-to-end: Python data → ingress → conform → relation filter → output."""

    def test_full_pipeline(self, ingress_factory, sample_records):
        # Step 1: Ingress
        df = ingress_factory.convert(sample_records)
        assert df.dtypes == [pl.String, pl.String, pl.String]

        # Step 2: Conform (replaces old schema transform)
        df = ConformBuilder({
            "age": {"cast": "integer"},
            "score": {"cast": "number"},
        }).apply(df)
        assert df["age"].dtype == pl.Int64
        assert df["score"].dtype == pl.Float64

        # Step 3: Relation + expression filter
        result = (
            ma.relation(df)
            .filter(ma.col("age").gt(ma.lit(25)))
            .sort("score")
            .to_polars()
        )

        assert result.shape[0] == 2
        assert result["name"].to_list() == ["bob", "diana"]
        assert result["score"].to_list() == [92.1, 95.0]

    def test_pipeline_with_aggregation(self, ingress_factory):
        records = [
            {"dept": "eng", "salary": "100000"},
            {"dept": "eng", "salary": "120000"},
            {"dept": "sales", "salary": "90000"},
            {"dept": "sales", "salary": "95000"},
        ]

        # Ingress + conform
        df = ingress_factory.convert(records)
        df = ConformBuilder({"salary": {"cast": "integer"}}).apply(df)

        # Relation: group by + aggregate (agg takes native Polars expressions)
        result = (
            ma.relation(df)
            .group_by("dept")
            .agg(pl.col("salary").mean().alias("avg_salary"))
            .sort("dept")
            .to_polars()
        )

        assert result.shape[0] == 2
        assert result["dept"].to_list() == ["eng", "sales"]

    def test_pipeline_with_select_and_rename(self, ingress_factory, sample_records):
        # Ingress + conform
        df = ingress_factory.convert(sample_records)
        df = ConformBuilder({"age": {"cast": "integer"}}).apply(df)

        # Relation: select + rename + filter
        result = (
            ma.relation(df)
            .select("age", "name")
            .rename({"name": "person"})
            .filter(ma.col("age").lt(ma.lit(30)))
            .to_polars()
        )

        assert result.columns == ["age", "person"]
        assert result.shape[0] == 2
