"""Tests for Relation schema/dtypes/width introspection."""
import polars as pl
import mountainash as ma


class TestRelationSchema:
    def test_schema_bare_relation(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [1.0, 2.0], "c": ["x", "y"]})
        r = ma.relation(df)
        schema = r.schema
        assert "a" in schema
        assert "b" in schema
        assert "c" in schema
        assert len(schema) == 3

    def test_schema_after_select(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [1.0, 2.0], "c": ["x", "y"]})
        r = ma.relation(df).select("a", "b")
        schema = r.schema
        assert list(schema.keys()) == ["a", "b"]

    def test_schema_after_with_columns(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [3, 4]})
        r = ma.relation(df).with_columns(ma.col("a").add(ma.col("b")).alias("c"))
        schema = r.schema
        assert "c" in schema
        assert len(schema) == 3

    def test_schema_after_rename(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [3, 4]})
        r = ma.relation(df).rename({"a": "x"})
        schema = r.schema
        assert "x" in schema
        assert "a" not in schema


class TestRelationDtypes:
    def test_dtypes(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [1.0, 2.0]})
        r = ma.relation(df)
        dtypes = r.dtypes
        assert len(dtypes) == 2


class TestRelationWidth:
    def test_width(self):
        df = pl.LazyFrame({"a": [1], "b": [2], "c": [3]})
        r = ma.relation(df)
        assert r.width == 3

    def test_width_after_select(self):
        df = pl.LazyFrame({"a": [1], "b": [2], "c": [3]})
        r = ma.relation(df).select("a")
        assert r.width == 1


class TestRelationExplain:
    def test_explain_polars_returns_string(self):
        df = pl.LazyFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        r = ma.relation(df).filter(ma.col("a").gt(1)).select("a", "b")
        plan = r.explain()
        assert isinstance(plan, str)
        assert len(plan) > 0

    def test_explain_contains_filter_info(self):
        df = pl.LazyFrame({"a": [1, 2, 3]})
        r = ma.relation(df).filter(ma.col("a").gt(1))
        plan = r.explain()
        assert "FILTER" in plan or "filter" in plan.lower()


class TestRelationOutputSchema:
    """Tests for Relation.output_schema — Frictionless schema dict from inferred types."""

    def test_output_schema_fully_typed_polars(self):
        """Fully-typed Polars relation produces correct Frictionless type strings."""
        df = pl.LazyFrame({"a": [1, 2], "b": ["x", "y"], "c": [1.0, 2.0]})
        r = ma.relation(df)
        result = r.output_schema
        assert result is not None
        assert "fields" in result
        fields_by_name = {f["name"]: f["type"] for f in result["fields"]}
        assert fields_by_name["a"] == "integer"
        assert fields_by_name["b"] == "string"
        assert fields_by_name["c"] == "number"

    def test_output_schema_boolean_and_date(self):
        """Boolean and date dtypes map to correct Frictionless types."""
        import datetime
        df = pl.LazyFrame({
            "flag": [True, False],
            "dt": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)],
        })
        r = ma.relation(df)
        result = r.output_schema
        assert result is not None
        fields_by_name = {f["name"]: f["type"] for f in result["fields"]}
        assert fields_by_name["flag"] == "boolean"
        assert fields_by_name["dt"] == "date"

    def test_output_schema_empty_dataframe_returns_none(self):
        """Relation from empty DataFrame (no columns) returns None."""
        df = pl.LazyFrame({})
        r = ma.relation(df)
        assert r.output_schema is None

    def test_output_schema_structure(self):
        """output_schema returns dict with 'fields' list of {name, type} dicts."""
        df = pl.LazyFrame({"x": [1], "y": ["a"]})
        r = ma.relation(df)
        result = r.output_schema
        assert isinstance(result, dict)
        assert isinstance(result["fields"], list)
        assert all("name" in f and "type" in f for f in result["fields"])
        assert [f["name"] for f in result["fields"]] == ["x", "y"]


class TestFrictionlessFromInferred:
    """Unit tests for _frictionless_from_inferred converter."""

    def test_empty_schema_returns_none(self):
        from mountainash.relations.dag.packaging import _frictionless_from_inferred
        assert _frictionless_from_inferred({}) is None

    def test_unknown_status_maps_to_any(self):
        from mountainash.relations.dag.packaging import _frictionless_from_inferred
        from mountainash.relations.schema_inference import SchemaTypeStatus
        result = _frictionless_from_inferred({"col": SchemaTypeStatus.UNKNOWN})
        assert result == {"fields": [{"name": "col", "type": "any"}]}

    def test_unconstrained_status_maps_to_any(self):
        from mountainash.relations.dag.packaging import _frictionless_from_inferred
        from mountainash.relations.schema_inference import SchemaTypeStatus
        result = _frictionless_from_inferred({"col": SchemaTypeStatus.UNCONSTRAINED})
        assert result == {"fields": [{"name": "col", "type": "any"}]}

    def test_concrete_dtype_maps_to_frictionless_string(self):
        from mountainash.relations.dag.packaging import _frictionless_from_inferred
        from mountainash.core.dtypes import MountainashDtype
        result = _frictionless_from_inferred({"n": MountainashDtype.I64, "s": MountainashDtype.STRING})
        assert result == {"fields": [{"name": "n", "type": "integer"}, {"name": "s", "type": "string"}]}

    def test_mixed_status_and_concrete(self):
        from mountainash.relations.dag.packaging import _frictionless_from_inferred
        from mountainash.relations.schema_inference import SchemaTypeStatus
        from mountainash.core.dtypes import MountainashDtype
        result = _frictionless_from_inferred({
            "known": MountainashDtype.FP64,
            "unknown_col": SchemaTypeStatus.UNKNOWN,
            "unconstrained_col": SchemaTypeStatus.UNCONSTRAINED,
        })
        assert result is not None
        fields_by_name = {f["name"]: f["type"] for f in result["fields"]}
        assert fields_by_name["known"] == "number"
        assert fields_by_name["unknown_col"] == "any"
        assert fields_by_name["unconstrained_col"] == "any"
