"""
Comprehensive tests for schema_config.converters module.

Tests schema conversion to backend-specific formats:
- Polars schema dict
- pandas dtypes dict
- PyArrow Schema
- Ibis schema dict
- Generic backend converter
"""
import pytest

from mountainash.dataframes.schema_config import (
    TableSchema,
    SchemaField,
    to_polars_schema,
    to_pandas_dtypes,
    to_arrow_schema,
    to_ibis_schema,
    convert_to_backend,
)


# ============================================================================
# Polars Converter Tests
# ============================================================================

class TestPolarsConverter:
    """Test conversion to Polars schema format."""

    def test_basic_polars_conversion(self):
        """Test basic schema conversion to Polars."""
        pl = pytest.importorskip("polars")

        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
            "amount": "number",
            "active": "boolean",
        })

        polars_schema = to_polars_schema(schema)

        assert len(polars_schema) == 4
        assert "id" in polars_schema
        assert "name" in polars_schema
        assert "amount" in polars_schema
        assert "active" in polars_schema

        # Check Polars types
        assert polars_schema["id"] == pl.Int64
        assert polars_schema["name"] == pl.Utf8
        assert polars_schema["amount"] == pl.Float64
        assert polars_schema["active"] == pl.Boolean

    def test_polars_all_universal_types(self):
        """Test conversion of all universal types to Polars."""
        pl = pytest.importorskip("polars")

        schema = TableSchema.from_simple_dict({
            "text": "string",
            "count": "integer",
            "price": "number",
            "enabled": "boolean",
            "birth_date": "date",
            "created_at": "datetime",
            "wake_time": "time",
            "duration": "duration",
            "tags": "array",
            "metadata": "object",
        })

        polars_schema = to_polars_schema(schema)

        # Verify all types are mapped
        assert len(polars_schema) == 10
        assert polars_schema["text"] == pl.Utf8
        assert polars_schema["count"] == pl.Int64
        assert polars_schema["price"] == pl.Float64
        assert polars_schema["enabled"] == pl.Boolean
        assert polars_schema["birth_date"] == pl.Date
        assert polars_schema["created_at"] == pl.Datetime
        assert polars_schema["wake_time"] == pl.Time
        assert polars_schema["duration"] == pl.Duration
        assert polars_schema["tags"] == pl.List(pl.Utf8)
        assert polars_schema["metadata"] == pl.Struct

    def test_polars_backend_type_preservation(self):
        """Test that backend_type is preferred over universal type."""
        pl = pytest.importorskip("polars")

        schema = TableSchema(fields=[
            SchemaField(
                name="small_id",
                type="integer",
                backend_type="Int32"  # Preserve Int32 instead of default Int64
            ),
            SchemaField(
                name="big_id",
                type="integer",
                backend_type="Int64"
            ),
        ])

        polars_schema = to_polars_schema(schema)

        # Backend types should be used
        assert polars_schema["small_id"] == pl.Int32
        assert polars_schema["big_id"] == pl.Int64

    def test_polars_unknown_type_fallback(self):
        """Test fallback behavior for unknown types."""
        pl = pytest.importorskip("polars")

        # Use "any" type instead of invalid type (TableSchema validates types)
        schema = TableSchema(fields=[
            SchemaField(name="normal", type="string"),
            SchemaField(name="any_type", type="any"),
        ])

        polars_schema = to_polars_schema(schema)

        # Known type should work
        assert polars_schema["normal"] == pl.String or polars_schema["normal"] == pl.Utf8

        # "any" type maps to Utf8/String in Polars
        assert polars_schema["any_type"] == pl.String or polars_schema["any_type"] == pl.Utf8

    def test_polars_not_installed_raises(self):
        """Test that ImportError is raised when polars not available."""
        # Mock scenario where polars is not available
        # This test may not run if polars is installed, which is fine
        schema = TableSchema.from_simple_dict({"id": "integer"})

        try:
            # This should work if polars is installed
            result = to_polars_schema(schema)
            assert result is not None
        except ImportError as e:
            # Expected if polars not installed
            assert "polars" in str(e).lower()


# ============================================================================
# Pandas Converter Tests
# ============================================================================

class TestPandasConverter:
    """Test conversion to pandas dtypes format."""

    def test_basic_pandas_conversion(self):
        """Test basic schema conversion to pandas."""
        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
            "amount": "number",
            "active": "boolean",
        })

        pandas_dtypes = to_pandas_dtypes(schema)

        assert len(pandas_dtypes) == 4
        assert pandas_dtypes["id"] == "Int64"
        assert pandas_dtypes["name"] == "string"
        assert pandas_dtypes["amount"] == "float64"  # pandas uses lowercase
        assert pandas_dtypes["active"] == "boolean"

    def test_pandas_all_universal_types(self):
        """Test conversion of all universal types to pandas."""
        schema = TableSchema.from_simple_dict({
            "text": "string",
            "count": "integer",
            "price": "number",
            "enabled": "boolean",
            "birth_date": "date",
            "created_at": "datetime",
            "wake_time": "time",
            "tags": "array",
            "metadata": "object",
        })

        pandas_dtypes = to_pandas_dtypes(schema)

        # Verify all types are mapped
        assert pandas_dtypes["text"] == "string"
        assert pandas_dtypes["count"] == "Int64"
        assert pandas_dtypes["price"] == "float64"  # pandas uses lowercase
        assert pandas_dtypes["enabled"] == "boolean"
        assert pandas_dtypes["birth_date"] == "datetime64[ns]"
        assert pandas_dtypes["created_at"] == "datetime64[ns]"
        # Note: pandas doesn't have native time/array types, uses object
        assert pandas_dtypes["metadata"] == "object"

    def test_pandas_backend_type_preservation(self):
        """Test that backend_type is used when available."""
        schema = TableSchema(fields=[
            SchemaField(
                name="small_int",
                type="integer",
                backend_type="Int32"
            ),
            SchemaField(
                name="category",
                type="string",
                backend_type="category"
            ),
        ])

        pandas_dtypes = to_pandas_dtypes(schema)

        # Backend types should be preserved
        assert pandas_dtypes["small_int"] == "Int32"
        assert pandas_dtypes["category"] == "category"

    def test_pandas_unknown_type_fallback(self):
        """Test fallback behavior for 'any' type."""
        schema = TableSchema(fields=[
            SchemaField(name="normal", type="string"),
            SchemaField(name="any_type", type="any"),
        ])

        pandas_dtypes = to_pandas_dtypes(schema)

        # Known type should work
        assert pandas_dtypes["normal"] == "string"

        # "any" type maps to "object" in pandas
        assert pandas_dtypes["any_type"] == "object"


# ============================================================================
# PyArrow Converter Tests
# ============================================================================

class TestPyArrowConverter:
    """Test conversion to PyArrow Schema format."""

    def test_basic_arrow_conversion(self):
        """Test basic schema conversion to PyArrow."""
        pa = pytest.importorskip("pyarrow")

        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
            "amount": "number",
            "active": "boolean",
        })

        arrow_schema = to_arrow_schema(schema)

        assert len(arrow_schema) == 4
        assert arrow_schema.field("id").type == pa.int64()
        assert arrow_schema.field("name").type == pa.string()
        assert arrow_schema.field("amount").type == pa.float64()
        assert arrow_schema.field("active").type == pa.bool_()

    def test_arrow_all_universal_types(self):
        """Test conversion of all universal types to PyArrow."""
        pa = pytest.importorskip("pyarrow")

        schema = TableSchema.from_simple_dict({
            "text": "string",
            "count": "integer",
            "price": "number",
            "enabled": "boolean",
            "birth_date": "date",
            "created_at": "datetime",
            "wake_time": "time",
            "duration": "duration",
        })

        arrow_schema = to_arrow_schema(schema)

        # Verify all types are mapped
        assert arrow_schema.field("text").type == pa.string()
        assert arrow_schema.field("count").type == pa.int64()
        assert arrow_schema.field("price").type == pa.float64()
        assert arrow_schema.field("enabled").type == pa.bool_()
        assert arrow_schema.field("birth_date").type == pa.date32()
        assert arrow_schema.field("created_at").type == pa.timestamp("ns")  # Uses nanoseconds
        assert arrow_schema.field("wake_time").type == pa.time64("ns")  # Uses nanoseconds
        assert arrow_schema.field("duration").type == pa.duration("ns")  # Uses nanoseconds

    def test_arrow_backend_type_preservation(self):
        """Test that backend_type is used when available."""
        pa = pytest.importorskip("pyarrow")

        schema = TableSchema(fields=[
            SchemaField(
                name="id",
                type="integer",
                backend_type="int32"  # Smaller int
            ),
        ])

        arrow_schema = to_arrow_schema(schema)

        # Backend type should be used
        assert arrow_schema.field("id").type == pa.int32()

    def test_arrow_unknown_type_fallback(self):
        """Test fallback behavior for 'any' type."""
        pa = pytest.importorskip("pyarrow")

        schema = TableSchema(fields=[
            SchemaField(name="normal", type="string"),
            SchemaField(name="any_type", type="any"),
        ])

        arrow_schema = to_arrow_schema(schema)

        # Known type should work
        assert arrow_schema.field("normal").type == pa.string()

        # "any" type maps to string in PyArrow
        assert arrow_schema.field("any_type").type == pa.string()

    def test_arrow_not_installed_raises(self):
        """Test that ImportError is raised when pyarrow not available."""
        schema = TableSchema.from_simple_dict({"id": "integer"})

        try:
            # This should work if pyarrow is installed
            result = to_arrow_schema(schema)
            assert result is not None
        except ImportError as e:
            # Expected if pyarrow not installed
            assert "pyarrow" in str(e).lower()


# ============================================================================
# Ibis Converter Tests
# ============================================================================

class TestIbisConverter:
    """Test conversion to Ibis schema format."""

    def test_basic_ibis_conversion(self):
        """Test basic schema conversion to Ibis."""
        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
            "amount": "number",
            "active": "boolean",
        })

        ibis_schema = to_ibis_schema(schema)

        assert len(ibis_schema) == 4
        assert ibis_schema["id"] == "int64"
        assert ibis_schema["name"] == "string"
        assert ibis_schema["amount"] == "float64"
        assert ibis_schema["active"] == "bool"  # Ibis uses "bool" not "boolean"

    def test_ibis_all_universal_types(self):
        """Test conversion of all universal types to Ibis."""
        schema = TableSchema.from_simple_dict({
            "text": "string",
            "count": "integer",
            "price": "number",
            "enabled": "boolean",
            "birth_date": "date",
            "created_at": "datetime",
            "wake_time": "time",
        })

        ibis_schema = to_ibis_schema(schema)

        # Verify all types are mapped
        assert ibis_schema["text"] == "string"
        assert ibis_schema["count"] == "int64"
        assert ibis_schema["price"] == "float64"
        assert ibis_schema["enabled"] == "bool"  # Ibis uses "bool" not "boolean"
        assert ibis_schema["birth_date"] == "date"
        assert ibis_schema["created_at"] == "timestamp"
        assert ibis_schema["wake_time"] == "time"

    def test_ibis_backend_type_preservation(self):
        """Test that backend_type is used when available."""
        schema = TableSchema(fields=[
            SchemaField(
                name="id",
                type="integer",
                backend_type="int32"
            ),
        ])

        ibis_schema = to_ibis_schema(schema)

        # Backend type should be preserved
        assert ibis_schema["id"] == "int32"

    def test_ibis_unknown_type_fallback(self):
        """Test fallback behavior for 'any' type."""
        schema = TableSchema(fields=[
            SchemaField(name="normal", type="string"),
            SchemaField(name="any_type", type="any"),
        ])

        ibis_schema = to_ibis_schema(schema)

        # Known type should work
        assert ibis_schema["normal"] == "string"

        # "any" type maps to "string" in Ibis
        assert ibis_schema["any_type"] == "string"


# ============================================================================
# Generic Backend Converter Tests
# ============================================================================

class TestGenericBackendConverter:
    """Test generic convert_to_backend function."""

    def test_convert_to_polars(self):
        """Test generic conversion to Polars."""
        pl = pytest.importorskip("polars")

        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
        })

        result = convert_to_backend(schema, "polars")

        assert isinstance(result, dict)
        assert result["id"] == pl.Int64
        assert result["name"] == pl.Utf8

    def test_convert_to_pandas(self):
        """Test generic conversion to pandas."""
        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
        })

        result = convert_to_backend(schema, "pandas")

        assert isinstance(result, dict)
        assert result["id"] == "Int64"
        assert result["name"] == "string"

    def test_convert_to_arrow(self):
        """Test generic conversion to PyArrow."""
        pa = pytest.importorskip("pyarrow")

        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
        })

        result = convert_to_backend(schema, "arrow")

        assert isinstance(result, pa.Schema)
        assert result.field("id").type == pa.int64()
        assert result.field("name").type == pa.string()

    def test_convert_to_pyarrow(self):
        """Test generic conversion to pyarrow (alias)."""
        pa = pytest.importorskip("pyarrow")

        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
        })

        result = convert_to_backend(schema, "pyarrow")

        assert isinstance(result, pa.Schema)

    def test_convert_to_ibis(self):
        """Test generic conversion to Ibis."""
        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
        })

        result = convert_to_backend(schema, "ibis")

        assert isinstance(result, dict)
        assert result["id"] == "int64"
        assert result["name"] == "string"

    def test_convert_unknown_backend_raises(self):
        """Test that unknown backend raises ValueError."""
        schema = TableSchema.from_simple_dict({"id": "integer"})

        with pytest.raises(ValueError, match="Unknown backend"):
            convert_to_backend(schema, "unknown_backend")


# ============================================================================
# Round-Trip Tests
# ============================================================================

class TestRoundTripConversion:
    """Test round-trip conversions between DataFrames and schemas."""

    def test_polars_round_trip(self):
        """Test Polars DataFrame → Schema → Polars schema conversion."""
        pl = pytest.importorskip("polars")
        from mountainash.dataframes.schema_config import from_dataframe

        # Create DataFrame
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "amount": [10.5, 20.3, 30.1],
        })

        # Extract schema
        schema = from_dataframe(df, preserve_backend_types=False)

        # Convert back to Polars schema
        polars_schema = to_polars_schema(schema)

        # Verify we can create a DataFrame with this schema
        new_df = pl.DataFrame(schema=polars_schema)
        assert new_df.schema == polars_schema

    def test_pandas_round_trip(self):
        """Test pandas DataFrame → Schema → pandas dtypes conversion."""
        pd = pytest.importorskip("pandas")
        from mountainash.dataframes.schema_config import from_dataframe

        # Create DataFrame
        df = pd.DataFrame({
            "id": pd.array([1, 2, 3], dtype="Int64"),
            "name": pd.array(["Alice", "Bob", "Charlie"], dtype="string"),
        })

        # Extract schema
        schema = from_dataframe(df)

        # Convert back to pandas dtypes
        pandas_dtypes = to_pandas_dtypes(schema)

        # Verify dtypes are preserved
        assert pandas_dtypes["id"] == "Int64"
        assert pandas_dtypes["name"] == "string"

    def test_pyarrow_round_trip(self):
        """Test PyArrow Table → Schema → PyArrow schema conversion."""
        pa = pytest.importorskip("pyarrow")
        from mountainash.dataframes.schema_config import from_dataframe

        # Create Table
        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["Alice", "Bob", "Charlie"], type=pa.string()),
        })

        # Extract schema
        schema = from_dataframe(table, preserve_backend_types=False)

        # Convert back to PyArrow schema
        arrow_schema = to_arrow_schema(schema)

        # Verify schema matches
        assert arrow_schema.field("id").type == pa.int64()
        assert arrow_schema.field("name").type == pa.string()

    def test_cross_backend_conversion(self):
        """Test converting schema extracted from one backend to another."""
        pl = pytest.importorskip("polars")
        pa = pytest.importorskip("pyarrow")
        from mountainash.dataframes.schema_config import from_dataframe

        # Create Polars DataFrame
        pl_df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })

        # Extract schema from Polars
        schema = from_dataframe(pl_df, preserve_backend_types=False)

        # Convert to PyArrow
        arrow_schema = to_arrow_schema(schema)

        # Verify conversion worked
        assert arrow_schema.field("id").type == pa.int64()
        assert arrow_schema.field("name").type == pa.string()

        # Convert to pandas
        pandas_dtypes = to_pandas_dtypes(schema)

        assert pandas_dtypes["id"] == "Int64"
        assert pandas_dtypes["name"] == "string"

    def test_backend_type_precision_preservation(self):
        """Test that backend-specific type precision is preserved."""
        pl = pytest.importorskip("polars")
        from mountainash.dataframes.schema_config import from_dataframe

        # Create DataFrame with specific precision
        df = pl.DataFrame({
            "small_id": pl.Series([1, 2, 3], dtype=pl.Int32),
            "big_id": pl.Series([1, 2, 3], dtype=pl.Int64),
        })

        # Extract schema WITH backend types
        schema = from_dataframe(df, preserve_backend_types=True)

        # Convert back to Polars - should preserve precision
        polars_schema = to_polars_schema(schema)

        # Verify precision is preserved
        assert polars_schema["small_id"] == pl.Int32
        assert polars_schema["big_id"] == pl.Int64


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestConverterEdgeCases:
    """Test edge cases and error handling in converters."""

    def test_single_field_schema_conversion(self):
        """Test converting a schema with a single field."""
        pl = pytest.importorskip("polars")

        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer")
        ])

        polars_schema = to_polars_schema(schema)
        pandas_dtypes = to_pandas_dtypes(schema)
        ibis_schema = to_ibis_schema(schema)

        # All converters should handle single-field schemas
        assert len(polars_schema) == 1
        assert len(pandas_dtypes) == 1
        assert len(ibis_schema) == 1

    def test_schema_with_all_types(self):
        """Test schema with every universal type."""
        pl = pytest.importorskip("polars")

        schema = TableSchema.from_simple_dict({
            "string_col": "string",
            "integer_col": "integer",
            "number_col": "number",
            "boolean_col": "boolean",
            "date_col": "date",
            "time_col": "time",
            "datetime_col": "datetime",
            "duration_col": "duration",
            "year_col": "year",
            "yearmonth_col": "yearmonth",
            "array_col": "array",
            "object_col": "object",
            "any_col": "any",
        })

        # Should not raise any errors
        polars_schema = to_polars_schema(schema)
        pandas_dtypes = to_pandas_dtypes(schema)
        ibis_schema = to_ibis_schema(schema)

        # All schemas should have all columns
        assert len(polars_schema) == 13
        assert len(pandas_dtypes) == 13
        assert len(ibis_schema) == 13

    def test_special_characters_in_column_names(self):
        """Test conversion with special characters in column names."""
        pl = pytest.importorskip("polars")

        schema = TableSchema.from_simple_dict({
            "normal_name": "string",
            "name with spaces": "integer",
            "name-with-dashes": "number",
            "name.with.dots": "boolean",
        })

        # Should handle special characters
        polars_schema = to_polars_schema(schema)
        pandas_dtypes = to_pandas_dtypes(schema)

        assert len(polars_schema) == 4
        assert len(pandas_dtypes) == 4
        assert "name with spaces" in polars_schema
        assert "name-with-dashes" in pandas_dtypes
