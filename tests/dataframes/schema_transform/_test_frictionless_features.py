"""
Functional tests for Frictionless Table Schema features.

Tests the actual application of:
- missing_values (schema-level)
- true_values/false_values (field-level)

These tests verify that the schema fields don't just serialize correctly,
but actually transform data as expected.

Tests are parameterized across all DataFrame backends to ensure
consistent behavior.
"""
import pytest

from mountainash.dataframes.schema_config import TableSchema, SchemaField, SchemaConfig
from mountainash.dataframes.schema_transform import SchemaTransformFactory


# Mark for backend parameterization
pytestmark = pytest.mark.implemented_backends


class TestMissingValuesTransformation:
    """Test that missing_values are actually replaced with null during transformation."""

    def test_missing_values_simple(
        self,
        backend,
        create_dataframe,
        get_column_value,
        missing_values_simple_data
    ):
        """Test basic missing value replacement with default ['']."""
        # Create DataFrame from fixture data
        df = create_dataframe(missing_values_simple_data, backend)

        # Create schema with default missing_values (empty string)
        schema = TableSchema(
            fields=[
                SchemaField(name="name", type="string"),
                SchemaField(name="score", type="integer")
            ]
            # missing_values defaults to [""]
        )

        config = SchemaConfig(
            columns={
                "name": {},
                "score": {"cast": "integer"}
            },
            source_schema=schema
        )

        # Apply transformation
        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Verify empty strings became null
        assert get_column_value(result, "name", 1) is None
        assert get_column_value(result, "score", 1) is None
        assert get_column_value(result, "score", 0) == 95
        assert get_column_value(result, "score", 2) == 87

    def test_missing_values_custom_markers(self):
        """Test custom missing value markers (NA, N/A, null, -)."""
        # Create DataFrame with various missing value markers
        df = pl.DataFrame({
            "value1": ["10", "NA", "20"],
            "value2": ["30", "N/A", "40"],
            "value3": ["50", "null", "60"],
            "value4": ["70", "-", "80"]
        })

        # Create schema with custom missing values
        schema = TableSchema(
            fields=[
                SchemaField(name="value1", type="integer"),
                SchemaField(name="value2", type="integer"),
                SchemaField(name="value3", type="integer"),
                SchemaField(name="value4", type="integer")
            ],
            missing_values=["", "NA", "N/A", "null", "-"]
        )

        config = SchemaConfig(
            columns={
                "value1": {"cast": "integer"},
                "value2": {"cast": "integer"},
                "value3": {"cast": "integer"},
                "value4": {"cast": "integer"}
            },
            source_schema=schema
        )

        # Apply transformation
        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Verify all custom markers became null
        assert result["value1"][1] is None  # "NA"
        assert result["value2"][1] is None  # "N/A"
        assert result["value3"][1] is None  # "null"
        assert result["value4"][1] is None  # "-"

        # Verify valid values preserved
        assert result["value1"][0] == 10
        assert result["value2"][0] == 30
        assert result["value3"][0] == 50
        assert result["value4"][0] == 70

    def test_missing_values_with_null_fill(self):
        """Test missing_values combined with null_fill."""
        df = pl.DataFrame({
            "score": ["95", "NA", "87", "N/A", "92"]
        })

        schema = TableSchema(
            fields=[SchemaField(name="score", type="integer")],
            missing_values=["", "NA", "N/A"]
        )

        config = SchemaConfig(
            columns={
                "score": {"cast": "integer", "null_fill": 0}
            },
            source_schema=schema
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # "NA" and "N/A" should become null, then filled with 0
        assert result["score"][1] == 0  # Was "NA"
        assert result["score"][3] == 0  # Was "N/A"
        assert result["score"][0] == 95
        assert result["score"][2] == 87

    def test_missing_values_all_columns(self):
        """Test that missing_values applies to ALL columns."""
        df = pl.DataFrame({
            "col_a": ["value", "NA", "data"],
            "col_b": ["100", "-", "200"],
            "col_c": ["X", "null", "Y"]
        })

        schema = TableSchema(
            fields=[
                SchemaField(name="col_a", type="string"),
                SchemaField(name="col_b", type="integer"),
                SchemaField(name="col_c", type="string")
            ],
            missing_values=["NA", "-", "null"]
        )

        config = SchemaConfig(
            columns={
                "col_a": {},
                "col_b": {"cast": "integer"},
                "col_c": {}
            },
            source_schema=schema
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Verify missing values replaced across all columns
        assert result["col_a"][1] is None  # "NA"
        assert result["col_b"][1] is None  # "-"
        assert result["col_c"][1] is None  # "null"


class TestBooleanValuesTransformation:
    """Test that true_values/false_values are actually converted during transformation."""

    def test_boolean_values_basic(self):
        """Test basic boolean value conversion (yes/no)."""
        df = pl.DataFrame({
            "approved": ["yes", "no", "yes", "no"]
        })

        schema = TableSchema(
            fields=[
                SchemaField(
                    name="approved",
                    type="boolean",
                    true_values=["yes", "Y"],
                    false_values=["no", "N"]
                )
            ]
        )

        config = SchemaConfig(
            columns={
                "approved": {"cast": "boolean"}
            },
            source_schema=schema
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Verify conversion
        assert result["approved"][0] is True
        assert result["approved"][1] is False
        assert result["approved"][2] is True
        assert result["approved"][3] is False

    def test_boolean_values_multiple_representations(self):
        """Test multiple representations for true/false."""
        df = pl.DataFrame({
            "flag": ["yes", "Y", "true", "1", "no", "N", "false", "0"]
        })

        schema = TableSchema(
            fields=[
                SchemaField(
                    name="flag",
                    type="boolean",
                    true_values=["yes", "Y", "true", "1"],
                    false_values=["no", "N", "false", "0"]
                )
            ]
        )

        config = SchemaConfig(
            columns={
                "flag": {"cast": "boolean"}
            },
            source_schema=schema
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # All true representations
        assert result["flag"][0] is True  # "yes"
        assert result["flag"][1] is True  # "Y"
        assert result["flag"][2] is True  # "true"
        assert result["flag"][3] is True  # "1"

        # All false representations
        assert result["flag"][4] is False  # "no"
        assert result["flag"][5] is False  # "N"
        assert result["flag"][6] is False  # "false"
        assert result["flag"][7] is False  # "0"

    def test_boolean_values_unmapped_becomes_null(self):
        """Test that unmapped values become null when casting to boolean."""
        df = pl.DataFrame({
            "status": ["yes", "no", "maybe", "unknown"]
        })

        schema = TableSchema(
            fields=[
                SchemaField(
                    name="status",
                    type="boolean",
                    true_values=["yes"],
                    false_values=["no"]
                )
            ]
        )

        config = SchemaConfig(
            columns={
                "status": {"cast": "boolean"}
            },
            source_schema=schema
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Mapped values
        assert result["status"][0] is True   # "yes"
        assert result["status"][1] is False  # "no"

        # Unmapped values - these will be null after boolean cast
        # (Polars will try to cast "maybe" to boolean and fail → null)
        assert result["status"][2] is None  # "maybe"
        assert result["status"][3] is None  # "unknown"

    def test_boolean_values_with_null_fill(self):
        """Test boolean conversion combined with null_fill."""
        df = pl.DataFrame({
            "enabled": ["yes", "no", "unknown", "yes"]
        })

        schema = TableSchema(
            fields=[
                SchemaField(
                    name="enabled",
                    type="boolean",
                    true_values=["yes"],
                    false_values=["no"]
                )
            ]
        )

        config = SchemaConfig(
            columns={
                "enabled": {"cast": "boolean", "null_fill": False}
            },
            source_schema=schema
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        assert result["enabled"][0] is True
        assert result["enabled"][1] is False
        assert result["enabled"][2] is False  # "unknown" → null → filled with False
        assert result["enabled"][3] is True


class TestCombinedFrictionlessFeatures:
    """Test missing_values and boolean_values working together."""

    def test_missing_values_before_boolean_conversion(self):
        """Test that missing_values are replaced BEFORE boolean conversion."""
        df = pl.DataFrame({
            "approved": ["yes", "NA", "no", "N/A", "yes"]
        })

        schema = TableSchema(
            fields=[
                SchemaField(
                    name="approved",
                    type="boolean",
                    true_values=["yes"],
                    false_values=["no"]
                )
            ],
            missing_values=["NA", "N/A"]  # Schema-level
        )

        config = SchemaConfig(
            columns={
                "approved": {"cast": "boolean"}
            },
            source_schema=schema
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        assert result["approved"][0] is True   # "yes"
        assert result["approved"][1] is None   # "NA" → null (missing_values)
        assert result["approved"][2] is False  # "no"
        assert result["approved"][3] is None   # "N/A" → null (missing_values)
        assert result["approved"][4] is True   # "yes"

    def test_comprehensive_transformation_pipeline(self):
        """Test complete transformation pipeline with all features."""
        df = pl.DataFrame({
            "id": ["1", "2", "NA", "4"],
            "approved": ["yes", "no", "null", "Y"],
            "score": ["95", "-", "87", "N/A"],
            "name": ["Alice", "Bob", "Charlie", ""]
        })

        schema = TableSchema(
            fields=[
                SchemaField(name="id", type="integer"),
                SchemaField(
                    name="approved",
                    type="boolean",
                    true_values=["yes", "Y", "true"],
                    false_values=["no", "N", "false"]
                ),
                SchemaField(name="score", type="number"),
                SchemaField(name="name", type="string")
            ],
            missing_values=["", "NA", "N/A", "null", "-"]
        )

        config = SchemaConfig(
            columns={
                "id": {"cast": "integer", "null_fill": -1},
                "approved": {"cast": "boolean", "null_fill": False},
                "score": {"cast": "number", "null_fill": 0.0},
                "name": {"null_fill": "Unknown"}
            },
            source_schema=schema
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Verify comprehensive transformation
        assert result["id"][0] == 1
        assert result["id"][1] == 2
        assert result["id"][2] == -1       # "NA" → null → -1
        assert result["id"][3] == 4

        assert result["approved"][0] is True   # "yes"
        assert result["approved"][1] is False  # "no"
        assert result["approved"][2] is False  # "null" → null → False
        assert result["approved"][3] is True   # "Y"

        assert result["score"][0] == 95.0
        assert result["score"][1] == 0.0  # "-" → null → 0.0
        assert result["score"][2] == 87.0
        assert result["score"][3] == 0.0  # "N/A" → null → 0.0

        assert result["name"][0] == "Alice"
        assert result["name"][1] == "Bob"
        assert result["name"][2] == "Charlie"
        assert result["name"][3] == "Unknown"  # "" → null → "Unknown"
