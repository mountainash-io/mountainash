"""Shared fixtures for convert module tests."""

from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal


# Simple test dataclasses
@dataclass
class SimpleUser:
    """Basic user dataclass for simple conversion tests."""
    user_id: int
    name: str
    email: str


@dataclass
class UserWithDefaults:
    """User dataclass with default values."""
    user_id: int
    name: str
    email: str
    is_active: bool = True
    score: float = 0.0


@dataclass
class ComplexUser:
    """Complex user with various field types."""
    user_id: int
    name: str
    email: str
    balance: Decimal
    created_at: datetime
    birth_date: Optional[date] = None
    tags: List[str] = field(default_factory=list)
    is_verified: bool = False


@dataclass
class Employee:
    """Employee dataclass for realistic workflow tests."""
    employee_id: int
    first_name: str
    last_name: str
    department: str
    salary: float
    hire_date: date
    is_active: bool = True


# Pydantic models (conditional on pydantic availability)
try:
    from pydantic import BaseModel

    class SimplePydanticUser(BaseModel):
        """Basic Pydantic user model."""
        user_id: int
        name: str
        email: str

    class ComplexPydanticUser(BaseModel):
        """Complex Pydantic user model."""
        user_id: int
        name: str
        email: str
        balance: Decimal
        created_at: datetime
        birth_date: Optional[date] = None
        is_verified: bool = False

    PYDANTIC_AVAILABLE = True

except ImportError:
    SimplePydanticUser = None
    ComplexPydanticUser = None
    PYDANTIC_AVAILABLE = False


# Test data fixtures
@pytest.fixture
def simple_dataclass_single() -> SimpleUser:
    """Single simple dataclass instance."""
    return SimpleUser(user_id=1, name="Alice", email="alice@example.com")


@pytest.fixture
def simple_dataclass_list() -> List[SimpleUser]:
    """List of simple dataclass instances."""
    return [
        SimpleUser(user_id=1, name="Alice", email="alice@example.com"),
        SimpleUser(user_id=2, name="Bob", email="bob@example.com"),
        SimpleUser(user_id=3, name="Charlie", email="charlie@example.com")
    ]


@pytest.fixture
def complex_dataclass_list() -> List[ComplexUser]:
    """List of complex dataclass instances with various field types."""
    return [
        ComplexUser(
            user_id=1,
            name="Alice Smith",
            email="alice@example.com",
            balance=Decimal("1250.75"),
            created_at=datetime(2024, 1, 1, 10, 30),
            birth_date=date(1990, 5, 15),
            tags=["premium", "verified"],
            is_verified=True
        ),
        ComplexUser(
            user_id=2,
            name="Bob Jones",
            email="bob@example.com",
            balance=Decimal("0.00"),
            created_at=datetime(2024, 2, 1, 14, 0),
            birth_date=None,
            tags=[],
            is_verified=False
        )
    ]


@pytest.fixture
def employee_dataclass_list() -> List[Employee]:
    """List of employee dataclass instances."""
    return [
        Employee(
            employee_id=1001,
            first_name="Alice",
            last_name="Johnson",
            department="Engineering",
            salary=95000.0,
            hire_date=date(2022, 3, 15),
            is_active=True
        ),
        Employee(
            employee_id=1002,
            first_name="Bob",
            last_name="Smith",
            department="Sales",
            salary=75000.0,
            hire_date=date(2023, 1, 10),
            is_active=False
        )
    ]


@pytest.fixture
def simple_pydantic_single():
    """Single simple Pydantic model instance."""
    if not PYDANTIC_AVAILABLE:
        pytest.skip("Pydantic not available")
    return SimplePydanticUser(user_id=1, name="Alice", email="alice@example.com")


@pytest.fixture
def simple_pydantic_list():
    """List of simple Pydantic model instances."""
    if not PYDANTIC_AVAILABLE:
        pytest.skip("Pydantic not available")
    return [
        SimplePydanticUser(user_id=1, name="Alice", email="alice@example.com"),
        SimplePydanticUser(user_id=2, name="Bob", email="bob@example.com"),
        SimplePydanticUser(user_id=3, name="Charlie", email="charlie@example.com")
    ]


@pytest.fixture
def dict_of_lists_simple() -> dict:
    """Simple dictionary of lists (columnar format)."""
    return {
        "user_id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "email": ["alice@example.com", "bob@example.com", "charlie@example.com"]
    }


@pytest.fixture
def dict_of_lists_complex() -> dict:
    """Complex dictionary of lists with various types."""
    return {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "active": [True, False, True, True, False]
    }


@pytest.fixture
def dict_of_lists_with_nulls() -> dict:
    """Dictionary of lists with null values."""
    return {
        "id": [1, 2, None, 4],
        "name": ["Alice", None, "Charlie", "Diana"],
        "value": [100.5, None, 300.9, None]
    }


@pytest.fixture
def list_of_dicts_simple() -> List[dict]:
    """Simple list of dictionaries (row format)."""
    return [
        {"user_id": 1, "name": "Alice", "email": "alice@example.com"},
        {"user_id": 2, "name": "Bob", "email": "bob@example.com"},
        {"user_id": 3, "name": "Charlie", "email": "charlie@example.com"}
    ]


@pytest.fixture
def list_of_dicts_complex() -> List[dict]:
    """Complex list of dictionaries with various types."""
    return [
        {"id": 1, "name": "Alice", "category": "A", "value": 100.5, "active": True},
        {"id": 2, "name": "Bob", "category": "B", "value": 200.7, "active": False},
        {"id": 3, "name": "Charlie", "category": "A", "value": 300.9, "active": True},
        {"id": 4, "name": "Diana", "category": "C", "value": 400.2, "active": True},
        {"id": 5, "name": "Eve", "category": "B", "value": 500.8, "active": False}
    ]


@pytest.fixture
def list_of_dicts_with_nulls() -> List[dict]:
    """List of dictionaries with null values."""
    return [
        {"id": 1, "name": "Alice", "value": 100.5},
        {"id": 2, "name": None, "value": None},
        {"id": None, "name": "Charlie", "value": 300.9}
    ]


# Edge case fixtures
@pytest.fixture
def empty_dict_of_lists() -> dict:
    """Empty dictionary of lists."""
    return {}


@pytest.fixture
def empty_list_of_dicts() -> List[dict]:
    """Empty list of dictionaries."""
    return []


@pytest.fixture
def single_row_dict_of_lists() -> dict:
    """Dictionary of lists with single row."""
    return {
        "user_id": [1],
        "name": ["Alice"],
        "email": ["alice@example.com"]
    }


@pytest.fixture
def single_item_list_of_dicts() -> List[dict]:
    """List with single dictionary."""
    return [{"user_id": 1, "name": "Alice", "email": "alice@example.com"}]


# Column mapping configuration fixtures
@pytest.fixture
def simple_column_mapping() -> dict:
    """Simple column rename mapping."""
    return {
        "user_id": {"rename": "id"},
        "name": {"rename": "full_name"},
        "email": {"rename": "email_address"}
    }


@pytest.fixture
def complex_column_config() -> dict:
    """Complex column configuration with type conversions."""
    return {
        "user_id": {"rename": "id", "dtype": "int64"},
        "name": {"rename": "full_name", "dtype": "str"},
        "value": {"dtype": "float64"}
    }


# Expected results fixtures for validation
@pytest.fixture
def expected_simple_columns() -> List[str]:
    """Expected columns for simple user data."""
    return ["user_id", "name", "email"]


@pytest.fixture
def expected_complex_columns() -> List[str]:
    """Expected columns for complex data."""
    return ["id", "name", "category", "value", "active"]


@pytest.fixture
def expected_row_count_simple() -> int:
    """Expected row count for simple data."""
    return 3


@pytest.fixture
def expected_row_count_complex() -> int:
    """Expected row count for complex data."""
    return 5
