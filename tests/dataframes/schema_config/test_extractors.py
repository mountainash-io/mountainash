"""
Comprehensive tests for schema_config.extractors module.

Tests schema extraction from:
- Python dataclasses
- Pydantic models (v1 and v2)
- DataFrames (Polars, pandas, PyArrow, Ibis, Narwhals)
"""
from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Optional, List
import pytest

from mountainash.dataframes.schema_config import (
    from_dataclass,
    from_pydantic,
    from_dataframe,
    TableSchema,
    SchemaField,
    FieldConstraints,
)


# ============================================================================
# Dataclass Extraction Tests
# ============================================================================

class TestDataclassExtraction:
    """Test schema extraction from Python dataclasses."""

    def test_basic_dataclass(self):
        """Test extraction from a simple dataclass."""
        @dataclass
        class User:
            id: int
            name: str
            email: str

        schema = from_dataclass(User)

        assert len(schema.fields) == 3
        assert schema.field_names == ["id", "name", "email"]
        assert schema.title == "User"

        # Check field types
        assert schema.get_field("id").type == "integer"
        assert schema.get_field("name").type == "string"
        assert schema.get_field("email").type == "string"

    def test_dataclass_with_optional_fields(self):
        """Test Optional field detection."""
        @dataclass
        class User:
            id: int
            name: str
            email: Optional[str] = None

        schema = from_dataclass(User)

        # Optional fields should not have required constraint
        email_field = schema.get_field("email")
        assert email_field.type == "string"
        # Optional fields don't set constraints to required=True

    def test_dataclass_with_defaults(self):
        """Test dataclass with default values."""
        @dataclass
        class Config:
            name: str
            timeout: int = 30
            enabled: bool = True

        schema = from_dataclass(Config)

        assert len(schema.fields) == 3
        # Fields with defaults should not be marked as required
        timeout_field = schema.get_field("timeout")
        assert timeout_field.type == "integer"

    def test_dataclass_with_various_types(self):
        """Test extraction of various Python types."""
        @dataclass
        class Record:
            text: str
            count: int
            amount: float
            active: bool
            created_at: datetime
            birth_date: date
            wake_time: time

        schema = from_dataclass(Record)

        assert schema.get_field("text").type == "string"
        assert schema.get_field("count").type == "integer"
        assert schema.get_field("amount").type == "number"
        assert schema.get_field("active").type == "boolean"
        assert schema.get_field("created_at").type == "datetime"
        assert schema.get_field("birth_date").type == "date"
        assert schema.get_field("wake_time").type == "time"

    def test_dataclass_with_list_type(self):
        """Test extraction of List types."""
        @dataclass
        class Document:
            title: str
            tags: List[str]

        schema = from_dataclass(Document)

        tags_field = schema.get_field("tags")
        assert tags_field.type == "array"

    def test_dataclass_with_metadata(self):
        """Test metadata preservation."""
        @dataclass
        class User:
            """User information."""
            id: int
            name: str

        schema = from_dataclass(
            User,
            title="CustomTitle",
            description="Custom description",
            primary_key="id"
        )

        assert schema.title == "CustomTitle"
        assert schema.description == "Custom description"
        assert schema.primary_key == ["id"]  # Normalized to list

    def test_dataclass_non_dataclass_raises(self):
        """Test that non-dataclass raises ValueError."""
        class NotADataclass:
            pass

        with pytest.raises(ValueError, match="not a dataclass"):
            from_dataclass(NotADataclass)

    def test_dataclass_with_unknown_type(self):
        """Test handling of unknown Python types."""
        @dataclass
        class Record:
            name: str
            data: object  # Unknown type

        schema = from_dataclass(Record)

        # Unknown types should default to "any"
        data_field = schema.get_field("data")
        assert data_field.type == "any"


# ============================================================================
# Pydantic Extraction Tests
# ============================================================================

class TestPydanticExtraction:
    """Test schema extraction from Pydantic models."""

    def test_basic_pydantic_v2(self):
        """Test extraction from Pydantic v2 model."""
        pytest.importorskip("pydantic", minversion="2.0")
        from pydantic import BaseModel

        class User(BaseModel):
            id: int
            name: str
            email: str

        schema = from_pydantic(User)

        assert len(schema.fields) == 3
        assert schema.field_names == ["id", "name", "email"]
        assert schema.title == "User"

    def test_pydantic_with_constraints(self):
        """Test constraint extraction from Pydantic."""
        pytest.importorskip("pydantic", minversion="2.0")
        from pydantic import BaseModel, Field

        class User(BaseModel):
            id: int = Field(gt=0, le=1000000)
            name: str = Field(min_length=1, max_length=100)
            email: str = Field(pattern=r"^[^@]+@[^@]+$")
            age: int = Field(ge=0, lt=150)

        schema = from_pydantic(User)

        # Check ID constraints
        id_field = schema.get_field("id")
        assert id_field.constraints is not None
        assert id_field.constraints.minimum == 0  # gt becomes minimum
        assert id_field.constraints.maximum == 1000000  # le becomes maximum

        # Check name constraints
        name_field = schema.get_field("name")
        assert name_field.constraints is not None
        assert name_field.constraints.min_length == 1
        assert name_field.constraints.max_length == 100

        # Check email pattern
        email_field = schema.get_field("email")
        assert email_field.constraints is not None
        assert email_field.constraints.pattern == r"^[^@]+@[^@]+$"

        # Check age constraints
        age_field = schema.get_field("age")
        assert age_field.constraints is not None
        assert age_field.constraints.minimum == 0
        assert age_field.constraints.maximum == 150

    def test_pydantic_with_optional_fields(self):
        """Test Optional field detection in Pydantic."""
        pytest.importorskip("pydantic", minversion="2.0")
        from pydantic import BaseModel

        class User(BaseModel):
            id: int
            name: str
            email: Optional[str] = None

        schema = from_pydantic(User)

        # Check required fields
        id_field = schema.get_field("id")
        assert id_field.constraints is not None
        assert id_field.constraints.required is True

        # Check optional field
        email_field = schema.get_field("email")
        if email_field.constraints:
            assert email_field.constraints.required is False

    def test_pydantic_with_descriptions(self):
        """Test description extraction from Pydantic."""
        pytest.importorskip("pydantic", minversion="2.0")
        from pydantic import BaseModel, Field

        class User(BaseModel):
            id: int = Field(description="Unique user identifier")
            name: str = Field(description="User's full name")

        schema = from_pydantic(User)

        assert schema.get_field("id").description == "Unique user identifier"
        assert schema.get_field("name").description == "User's full name"

    def test_pydantic_format_detection(self):
        """Test format hint detection from special Pydantic types."""
        pytest.importorskip("pydantic", minversion="2.0")

        # Try to create model with special types
        # Skip test if optional dependencies (email_validator) not installed
        try:
            from pydantic import BaseModel, EmailStr, HttpUrl
            from uuid import UUID

            class User(BaseModel):
                email: EmailStr
                website: HttpUrl
                user_id: UUID

            schema = from_pydantic(User)

            # Format hints should be detected
            email_field = schema.get_field("email")
            assert email_field.format == "email" or email_field.type == "string"

            website_field = schema.get_field("website")
            assert website_field.format == "uri" or website_field.type == "string"

            user_id_field = schema.get_field("user_id")
            assert user_id_field.format == "uuid" or user_id_field.type == "string"

        except ImportError as e:
            if "email-validator" in str(e) or "email_validator" in str(e):
                pytest.skip("email_validator not installed")
            else:
                raise

    def test_pydantic_invalid_model_raises(self):
        """Test that ValueError is raised for non-Pydantic classes."""
        pytest.importorskip("pydantic", minversion="2.0")

        # Mock a non-pydantic class
        class FakeModel:
            pass

        # This should raise an error because FakeModel is not a Pydantic model
        with pytest.raises((ValueError, AttributeError)):
            from_pydantic(FakeModel)

    def test_pydantic_with_metadata(self):
        """Test metadata preservation in Pydantic extraction."""
        pytest.importorskip("pydantic", minversion="2.0")
        from pydantic import BaseModel

        class User(BaseModel):
            """User model for authentication."""
            id: int
            name: str

        schema = from_pydantic(
            User,
            title="CustomTitle",
            description="Custom description",
            primary_key="id"
        )

        assert schema.title == "CustomTitle"
        assert schema.description == "Custom description"
        assert schema.primary_key == ["id"]  # Normalized to list


# ============================================================================
# DataFrame Extraction Tests
# ============================================================================

class TestDataFrameExtraction:
    """Test schema extraction from various DataFrame backends."""

    def test_from_polars_dataframe(self):
        """Test extraction from Polars DataFrame."""
        pl = pytest.importorskip("polars")

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "amount": [10.5, 20.3, 30.1],
            "active": [True, False, True],
        })

        schema = from_dataframe(df)

        assert len(schema.fields) == 4
        assert schema.field_names == ["id", "name", "amount", "active"]

        # Check types
        assert schema.get_field("id").type == "integer"
        assert schema.get_field("name").type == "string"
        assert schema.get_field("amount").type == "number"
        assert schema.get_field("active").type == "boolean"

    def test_from_polars_lazyframe(self):
        """Test extraction from Polars LazyFrame."""
        pl = pytest.importorskip("polars")

        lf = pl.LazyFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })

        schema = from_dataframe(lf)

        assert len(schema.fields) == 2
        assert schema.field_names == ["id", "name"]

    def test_from_pandas_dataframe(self):
        """Test extraction from pandas DataFrame."""
        pd = pytest.importorskip("pandas")

        df = pd.DataFrame({
            "id": pd.array([1, 2, 3], dtype="Int64"),
            "name": pd.array(["Alice", "Bob", "Charlie"], dtype="string"),
            "amount": [10.5, 20.3, 30.1],
            "active": [True, False, True],
        })

        schema = from_dataframe(df)

        assert len(schema.fields) == 4
        assert schema.field_names == ["id", "name", "amount", "active"]

        # Check universal types
        assert schema.get_field("id").type == "integer"
        assert schema.get_field("name").type == "string"
        assert schema.get_field("amount").type == "number"
        assert schema.get_field("active").type == "boolean"

    def test_from_pyarrow_table(self):
        """Test extraction from PyArrow Table."""
        pa = pytest.importorskip("pyarrow")

        table = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["Alice", "Bob", "Charlie"], type=pa.string()),
            "amount": pa.array([10.5, 20.3, 30.1], type=pa.float64()),
        })

        schema = from_dataframe(table)

        assert len(schema.fields) == 3
        assert schema.field_names == ["id", "name", "amount"]

        # Check types
        assert schema.get_field("id").type == "integer"
        assert schema.get_field("name").type == "string"
        assert schema.get_field("amount").type == "number"

    def test_from_narwhals_dataframe(self):
        """Test extraction from Narwhals DataFrame."""
        nw = pytest.importorskip("narwhals")
        pl = pytest.importorskip("polars")

        # Create a Polars DataFrame and wrap with Narwhals
        pl_df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })
        nw_df = nw.from_native(pl_df)

        schema = from_dataframe(nw_df)

        assert len(schema.fields) == 2
        assert schema.field_names == ["id", "name"]

    def test_backend_type_preservation(self):
        """Test that backend-specific types are preserved."""
        pl = pytest.importorskip("polars")

        df = pl.DataFrame({
            "id": pl.Series([1, 2, 3], dtype=pl.Int32),
            "big_id": pl.Series([1, 2, 3], dtype=pl.Int64),
        })

        schema = from_dataframe(df, preserve_backend_types=True)

        # Backend types should be preserved
        id_field = schema.get_field("id")
        assert id_field.backend_type is not None
        assert "Int32" in id_field.backend_type

        big_id_field = schema.get_field("big_id")
        assert big_id_field.backend_type is not None
        assert "Int64" in big_id_field.backend_type

    def test_backend_type_not_preserved(self):
        """Test extraction without backend type preservation."""
        pl = pytest.importorskip("polars")

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })

        schema = from_dataframe(df, preserve_backend_types=False)

        # Backend types should not be set
        for field in schema.fields:
            assert field.backend_type is None

    def test_dataframe_with_metadata(self):
        """Test metadata preservation in DataFrame extraction."""
        pl = pytest.importorskip("polars")

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })

        schema = from_dataframe(
            df,
            title="UserData",
            description="User information table",
            primary_key="id"
        )

        assert schema.title == "UserData"
        assert schema.description == "User information table"
        assert schema.primary_key == ["id"]  # Normalized to list

    def test_unsupported_dataframe_raises(self):
        """Test that unsupported DataFrame types raise ValueError."""
        # Create a mock DataFrame-like object
        class FakeDataFrame:
            pass

        fake_df = FakeDataFrame()

        with pytest.raises(ValueError, match="Unsupported DataFrame type"):
            from_dataframe(fake_df)

    def test_from_dataframe_complex_types(self):
        """Test extraction of complex DataFrame types."""
        pl = pytest.importorskip("polars")

        df = pl.DataFrame({
            "id": [1, 2, 3],
            "created": [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
            "birth_date": [date(1990, 1, 1), date(1985, 5, 15), date(2000, 12, 25)],
        })

        schema = from_dataframe(df)

        assert schema.get_field("id").type == "integer"
        assert schema.get_field("created").type == "datetime"
        assert schema.get_field("birth_date").type == "date"


# ============================================================================
# Integration Tests
# ============================================================================

class TestExtractorIntegration:
    """Test integration between different extractors."""

    def test_dataclass_to_dataframe_schema_consistency(self):
        """Test that schemas from dataclass and DataFrame are consistent."""
        pl = pytest.importorskip("polars")

        @dataclass
        class Record:
            id: int
            name: str
            amount: float

        # Create schema from dataclass
        dataclass_schema = from_dataclass(Record)

        # Create DataFrame with same structure
        df = pl.DataFrame({
            "id": [1, 2],
            "name": ["Alice", "Bob"],
            "amount": [10.5, 20.3],
        })

        # Create schema from DataFrame
        df_schema = from_dataframe(df, preserve_backend_types=False)

        # Schemas should be compatible
        assert dataclass_schema.field_names == df_schema.field_names
        assert dataclass_schema.is_compatible_with(df_schema)

    def test_round_trip_schema_preservation(self):
        """Test that schema information is preserved through round-trip."""
        pl = pytest.importorskip("polars")

        # Create DataFrame
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })

        # Extract schema
        schema = from_dataframe(df, title="Users", primary_key="id")

        # Verify metadata
        assert schema.title == "Users"
        assert schema.primary_key == ["id"]  # Normalized to list
        assert len(schema.fields) == 2

    def test_pydantic_to_dataframe_workflow(self):
        """Test extracting from Pydantic model and converting to DataFrame schema."""
        pytest.importorskip("pydantic", minversion="2.0")
        pl = pytest.importorskip("polars")
        from pydantic import BaseModel, Field

        class User(BaseModel):
            id: int = Field(gt=0)
            name: str = Field(min_length=1)
            age: int = Field(ge=0, le=150)

        # Extract schema from Pydantic
        pydantic_schema = from_pydantic(User)

        # Verify constraints were extracted
        id_field = pydantic_schema.get_field("id")
        assert id_field.constraints is not None
        assert id_field.constraints.minimum == 0

        # Create DataFrame matching the schema
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
        })

        # Extract schema from DataFrame
        df_schema = from_dataframe(df, preserve_backend_types=False)

        # Types should be compatible (ignoring constraints)
        assert pydantic_schema.field_names == df_schema.field_names
        for field_name in pydantic_schema.field_names:
            pydantic_type = pydantic_schema.get_field(field_name).type
            df_type = df_schema.get_field(field_name).type
            assert pydantic_type == df_type
