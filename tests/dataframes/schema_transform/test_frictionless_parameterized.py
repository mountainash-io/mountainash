"""
Parameterized functional tests for Frictionless Table Schema features.

Tests missing_values and true_values/false_values across all DataFrame backends.
Uses fixtures for data and parameterization for backends.
"""
import pytest

from mountainash.dataframes.schema_config import TableSchema, SchemaField, SchemaConfig
from mountainash.dataframes.schema_transform import SchemaTransformFactory
from mountainash.dataframes.schema_transform.base_schema_transform_strategy import SchemaTransformError


# Mark all tests to run on implemented backends
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
        df = create_dataframe(missing_values_simple_data, backend)

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

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Verify empty strings became null
        assert get_column_value(result, "name", 1) is None
        assert get_column_value(result, "score", 1) is None
        assert get_column_value(result, "score", 0) == 95
        assert get_column_value(result, "score", 2) == 87

    def test_missing_values_custom_markers(
        self,
        backend,
        create_dataframe,
        get_column_value,
        missing_values_custom_markers_data
    ):
        """Test custom missing value markers (NA, N/A, null, -)."""
        df = create_dataframe(missing_values_custom_markers_data, backend)

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

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Verify all custom markers became null
        assert get_column_value(result, "value1", 1) is None  # "NA"
        assert get_column_value(result, "value2", 1) is None  # "N/A"
        assert get_column_value(result, "value3", 1) is None  # "null"
        assert get_column_value(result, "value4", 1) is None  # "-"

        # Verify valid values preserved
        assert get_column_value(result, "value1", 0) == 10
        assert get_column_value(result, "value2", 0) == 30
        assert get_column_value(result, "value3", 0) == 50
        assert get_column_value(result, "value4", 0) == 70


class TestBooleanValuesTransformation:
    """Test that true_values/false_values are actually converted during transformation."""

    def test_boolean_values_basic(
        self,
        backend,
        create_dataframe,
        get_column_value,
        boolean_values_basic_data
    ):
        """Test basic boolean value conversion (yes/no)."""
        df = create_dataframe(boolean_values_basic_data, backend)

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
        assert get_column_value(result, "approved", 0) is True
        assert get_column_value(result, "approved", 1) is False
        assert get_column_value(result, "approved", 2) is True
        assert get_column_value(result, "approved", 3) is False

    def test_boolean_values_multiple_representations(
        self,
        backend,
        create_dataframe,
        get_column_value,
        boolean_values_multiple_representations_data
    ):
        """Test multiple representations for true/false."""
        df = create_dataframe(boolean_values_multiple_representations_data, backend)

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
        assert get_column_value(result, "flag", 0) is True  # "yes"
        assert get_column_value(result, "flag", 1) is True  # "Y"
        assert get_column_value(result, "flag", 2) is True  # "true"
        assert get_column_value(result, "flag", 3) is True  # "1"

        # All false representations
        assert get_column_value(result, "flag", 4) is False  # "no"
        assert get_column_value(result, "flag", 5) is False  # "N"
        assert get_column_value(result, "flag", 6) is False  # "false"
        assert get_column_value(result, "flag", 7) is False  # "0"

    def test_boolean_values_unmapped_becomes_null(
        self,
        backend,
        create_dataframe,
        get_column_value,
        boolean_values_unmapped_data
    ):
        """Test that unmapped values become null when casting to boolean."""
        df = create_dataframe(boolean_values_unmapped_data, backend)

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
        assert get_column_value(result, "status", 0) is True   # "yes"
        assert get_column_value(result, "status", 1) is False  # "no"

        # Unmapped values become null
        assert get_column_value(result, "status", 2) is None  # "maybe"
        assert get_column_value(result, "status", 3) is None  # "unknown"


class TestCombinedFrictionlessFeatures:
    """Test missing_values and boolean_values working together."""

    def test_missing_values_before_boolean_conversion(
        self,
        backend,
        create_dataframe,
        get_column_value,
        combined_features_data
    ):
        """Test that missing_values are replaced BEFORE boolean conversion."""
        df = create_dataframe(combined_features_data, backend)

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

        assert get_column_value(result, "approved", 0) is True   # "yes"
        assert get_column_value(result, "approved", 1) is None   # "NA" → null (missing_values)
        assert get_column_value(result, "approved", 2) is False  # "no"
        assert get_column_value(result, "approved", 3) is None   # "N/A" → null (missing_values)
        assert get_column_value(result, "approved", 4) is True   # "yes"

    def test_comprehensive_transformation_pipeline(
        self,
        backend,
        create_dataframe,
        get_column_value,
        comprehensive_pipeline_data
    ):
        """Test complete transformation pipeline with all features."""
        df = create_dataframe(comprehensive_pipeline_data, backend)

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
        assert get_column_value(result, "id", 0) == 1
        assert get_column_value(result, "id", 1) == 2
        assert get_column_value(result, "id", 2) == -1       # "NA" → null → -1
        assert get_column_value(result, "id", 3) == 4

        assert get_column_value(result, "approved", 0) is True   # "yes"
        assert get_column_value(result, "approved", 1) is False  # "no"
        assert get_column_value(result, "approved", 2) is False  # "null" → null → False
        assert get_column_value(result, "approved", 3) is True   # "Y"

        assert get_column_value(result, "score", 0) == 95.0
        assert get_column_value(result, "score", 1) == 0.0  # "-" → null → 0.0
        assert get_column_value(result, "score", 2) == 87.0
        assert get_column_value(result, "score", 3) == 0.0  # "N/A" → null → 0.0

        assert get_column_value(result, "name", 0) == "Alice"
        assert get_column_value(result, "name", 1) == "Bob"
        assert get_column_value(result, "name", 2) == "Charlie"
        assert get_column_value(result, "name", 3) == "Unknown"  # "" → null → "Unknown"


class TestRenameTransformation:
    """Test column renaming functionality."""

    def test_rename_simple(
        self,
        backend,
        create_dataframe,
        get_column_value,
        get_columns,
        rename_simple_data
    ):
        """Test basic column renaming."""
        df = create_dataframe(rename_simple_data, backend)

        config = SchemaConfig(
            columns={
                "user_id": {"rename": "id"},
                "user_name": {"rename": "name"},
                "user_age": {"rename": "age", "cast": "integer"}
            }
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        columns = get_columns(result)

        # Check renamed columns exist
        assert "id" in columns
        assert "name" in columns
        assert "age" in columns

        # Check old names don't exist
        assert "user_id" not in columns
        assert "user_name" not in columns
        assert "user_age" not in columns

        # Verify data preserved
        assert get_column_value(result, "id", 0) == "1"
        assert get_column_value(result, "name", 1) == "Bob"
        assert get_column_value(result, "age", 2) == 35

    def test_rename_with_cast_and_null_fill(
        self,
        backend,
        create_dataframe,
        get_column_value,
        rename_simple_data
    ):
        """Test renaming combined with casting and null filling."""
        df = create_dataframe(rename_simple_data, backend)

        schema = TableSchema(
            fields=[
                SchemaField(name="user_id", type="integer"),
                SchemaField(name="user_name", type="string"),
                SchemaField(name="user_age", type="integer")
            ]
        )

        config = SchemaConfig(
            columns={
                "user_id": {"rename": "id", "cast": "integer"},
                "user_name": {"rename": "full_name"},
                "user_age": {"rename": "age", "cast": "integer", "null_fill": 0}
            },
            source_schema=schema
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        assert get_column_value(result, "id", 0) == 1
        assert get_column_value(result, "full_name", 1) == "Bob"
        assert get_column_value(result, "age", 2) == 35


class TestDefaultValues:
    """Test default value functionality for missing columns."""

    def test_add_column_with_default(
        self,
        backend,
        create_dataframe,
        get_column_value,
        default_values_data
    ):
        """Test adding missing column with default value."""
        df = create_dataframe(default_values_data, backend)

        config = SchemaConfig(
            columns={
                "id": {"cast": "integer"},
                "name": {},
                "status": {"default": "active"},  # Missing column
                "created_at": {"default": "2025-01-01"}  # Missing column
            }
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Verify new columns exist with defaults
        assert get_column_value(result, "status", 0) == "active"
        assert get_column_value(result, "status", 1) == "active"
        assert get_column_value(result, "created_at", 2) == "2025-01-01"

        # Verify original data preserved
        assert get_column_value(result, "id", 0) == 1
        assert get_column_value(result, "name", 1) == "Bob"

    def test_default_with_rename_and_cast(
        self,
        backend,
        create_dataframe,
        get_column_value,
        default_values_data
    ):
        """Test default values combined with renaming and casting."""
        df = create_dataframe(default_values_data, backend)

        config = SchemaConfig(
            columns={
                "id": {"rename": "user_id", "cast": "integer"},
                "name": {},
                "score": {"default": 0, "cast": "integer"},  # Missing, add with default
                "is_active": {"default": True}  # Missing, add with default
            }
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        # Check defaults applied
        assert get_column_value(result, "score", 0) == 0
        assert get_column_value(result, "score", 2) == 0
        assert get_column_value(result, "is_active", 1) is True


class TestKeepOnlyMapped:
    """Test keep_only_mapped column filtering."""

    def test_keep_all_columns_default(
        self,
        backend,
        create_dataframe,
        get_column_value,
        get_columns,
        keep_only_mapped_data
    ):
        """Test default behavior: keep unmapped columns."""
        df = create_dataframe(keep_only_mapped_data, backend)

        config = SchemaConfig(
            columns={
                "id": {"cast": "integer"},
                "name": {}
            },
            keep_only_mapped=False  # Default
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        columns = get_columns(result)

        # Mapped columns should exist
        assert "id" in columns
        assert "name" in columns

        # Unmapped columns should also exist (keep_only_mapped=False)
        assert "extra1" in columns
        assert "extra2" in columns

        # Verify data
        assert get_column_value(result, "extra1", 0) == "x"

    def test_keep_only_mapped_columns(
        self,
        backend,
        create_dataframe,
        get_column_value,
        get_columns,
        keep_only_mapped_data
    ):
        """Test keep_only_mapped=True: drop unmapped columns."""
        df = create_dataframe(keep_only_mapped_data, backend)

        config = SchemaConfig(
            columns={
                "id": {"cast": "integer"},
                "name": {}
            },
            keep_only_mapped=True
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        result = strategy.apply(df, config)

        columns = get_columns(result)

        # Mapped columns should exist
        assert "id" in columns
        assert "name" in columns

        # Unmapped columns should NOT exist (keep_only_mapped=True)
        assert "extra1" not in columns
        assert "extra2" not in columns

        # Verify data preserved for kept columns
        assert get_column_value(result, "id", 1) == 2
        assert get_column_value(result, "name", 2) == "Charlie"


class TestStrictMode:
    """Test strict mode error handling."""

    def test_lenient_mode_skips_missing_columns(
        self,
        backend,
        create_dataframe,
        get_column_value,
        strict_mode_data
    ):
        """Test lenient mode (default): missing columns are skipped."""
        df = create_dataframe(strict_mode_data, backend)

        config = SchemaConfig(
            columns={
                "id": {"cast": "integer"},
                "name": {},
                "missing_field": {}  # This column doesn't exist
            },
            strict=False  # Default
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        # Should NOT raise error in lenient mode
        result = strategy.apply(df, config)

        # Existing columns should be processed
        assert get_column_value(result, "id", 0) == 1
        assert get_column_value(result, "name", 1) == "Bob"

    def test_strict_mode_raises_on_missing_column(
        self,
        backend,
        create_dataframe,
        strict_mode_data
    ):
        """Test strict mode: missing columns without defaults raise error."""
        df = create_dataframe(strict_mode_data, backend)

        config = SchemaConfig(
            columns={
                "id": {"cast": "integer"},
                "name": {},
                "required_field": {}  # Missing column, no default
            },
            strict=True
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)

        # Should raise SchemaTransformError (wraps ValueError) in strict mode
        with pytest.raises(SchemaTransformError, match="Column 'required_field' not found"):
            strategy.apply(df, config)

    def test_strict_mode_allows_missing_with_default(
        self,
        backend,
        create_dataframe,
        get_column_value,
        strict_mode_data
    ):
        """Test strict mode: missing columns WITH defaults are allowed."""
        df = create_dataframe(strict_mode_data, backend)

        config = SchemaConfig(
            columns={
                "id": {"cast": "integer"},
                "name": {},
                "status": {"default": "pending"}  # Missing but has default
            },
            strict=True
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        # Should NOT raise error - default provided
        result = strategy.apply(df, config)

        assert get_column_value(result, "id", 0) == 1
        assert get_column_value(result, "status", 0) == "pending"
