"""
Shared fixtures for mountainash.schema tests.

Provides:
- Sample DataFrames for all backends (Polars, Pandas, PyArrow, Narwhals, Ibis)
- Sample TableSchema fixtures (simple and full)
- Sample dataclass types (SampleEmployee, SampleOptionalFields)
- clean_custom_registry: fixture that saves/restores CustomTypeRegistry state
"""
from __future__ import annotations

import copy
import datetime
from dataclasses import dataclass
from typing import Optional

import pytest

from mountainash.schema.config.types import UniversalType
from mountainash.schema.config.universal_schema import FieldConstraints, SchemaField, TableSchema
from mountainash.schema.config.custom_types import CustomTypeRegistry, _register_standard_converters


# ============================================================================
# Sample Dataclass Types
# ============================================================================

@dataclass
class SampleEmployee:
    """Sample dataclass with basic types for schema extraction tests."""
    employee_id: int
    name: str
    salary: float
    is_active: bool


@dataclass
class SampleOptionalFields:
    """Sample dataclass with Optional fields."""
    record_id: int
    description: Optional[str]
    score: Optional[float]
    tags: Optional[str]


# ============================================================================
# Fixtures — Dataclass types
# ============================================================================

@pytest.fixture
def sample_employee_cls():
    return SampleEmployee


@pytest.fixture
def sample_optional_fields_cls():
    return SampleOptionalFields


# ============================================================================
# Fixtures — TableSchema
# ============================================================================

@pytest.fixture
def simple_table_schema():
    """Minimal TableSchema with two fields."""
    return TableSchema.from_simple_dict({"id": "integer", "name": "string"})


@pytest.fixture
def full_table_schema():
    """TableSchema with all common types, constraints, and metadata."""
    fields = [
        SchemaField(
            name="employee_id",
            type=UniversalType.INTEGER,
            description="Primary key",
            constraints=FieldConstraints(required=True, unique=True),
        ),
        SchemaField(
            name="full_name",
            type=UniversalType.STRING,
            description="Employee full name",
            constraints=FieldConstraints(required=True, max_length=200),
        ),
        SchemaField(
            name="salary",
            type=UniversalType.NUMBER,
            description="Annual salary",
            constraints=FieldConstraints(minimum=0),
        ),
        SchemaField(
            name="is_active",
            type=UniversalType.BOOLEAN,
        ),
        SchemaField(
            name="hire_date",
            type=UniversalType.DATE,
        ),
        SchemaField(
            name="notes",
            type=UniversalType.STRING,
            constraints=FieldConstraints(required=False),
        ),
    ]
    return TableSchema(
        fields=fields,
        title="Employee",
        description="Employee records",
        primary_key="employee_id",
    )


@pytest.fixture
def source_schema():
    """Source schema with user_ prefix field names."""
    return TableSchema.from_simple_dict({
        "user_id": "integer",
        "user_name": "string",
        "user_email": "string",
    })


@pytest.fixture
def target_schema():
    """Target schema with short field names."""
    return TableSchema.from_simple_dict({
        "id": "integer",
        "name": "string",
        "email": "string",
    })


# ============================================================================
# Fixtures — DataFrames
# ============================================================================

@pytest.fixture
def polars_df():
    """Sample Polars DataFrame with mixed types including nulls and dates."""
    import polars as pl
    return pl.DataFrame({
        "id": [1, 2, 3, None],
        "name": ["Alice", "Bob", "Carol", None],
        "score": [9.5, 7.0, None, 4.2],
        "active": [True, False, True, None],
        "birth_date": [
            datetime.date(1990, 1, 15),
            datetime.date(1985, 6, 30),
            datetime.date(2000, 12, 1),
            None,
        ],
    })


@pytest.fixture
def pandas_df():
    """Sample Pandas DataFrame with mixed types."""
    pd = pytest.importorskip("pandas")
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Carol"],
        "score": [9.5, 7.0, None],
        "active": [True, False, True],
    })


@pytest.fixture
def pyarrow_table():
    """Sample PyArrow Table with mixed types."""
    pa = pytest.importorskip("pyarrow")
    return pa.table({
        "id": pa.array([1, 2, 3], type=pa.int64()),
        "name": pa.array(["Alice", "Bob", "Carol"], type=pa.string()),
        "score": pa.array([9.5, 7.0, None], type=pa.float64()),
        "active": pa.array([True, False, True], type=pa.bool_()),
    })


@pytest.fixture
def narwhals_df(polars_df):
    """Sample Narwhals DataFrame wrapping the Polars fixture."""
    nw = pytest.importorskip("narwhals")
    return nw.from_native(polars_df)


@pytest.fixture
def ibis_table():
    """Sample Ibis in-memory table with mixed types."""
    ibis = pytest.importorskip("ibis")
    return ibis.memtable({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Carol"],
        "score": [9.5, 7.0, 4.2],
        "active": [True, False, True],
    })


# ============================================================================
# Fixtures — CustomTypeRegistry isolation
# ============================================================================

@pytest.fixture
def clean_custom_registry():
    """
    Save and restore the CustomTypeRegistry state around a test.

    Allows tests to register / unregister custom converters without
    polluting the global registry state for other tests.
    """
    saved = copy.copy(CustomTypeRegistry._converters)
    yield CustomTypeRegistry
    # Restore original state
    CustomTypeRegistry._converters = saved
