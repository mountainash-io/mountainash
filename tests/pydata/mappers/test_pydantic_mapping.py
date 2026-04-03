"""
Test suite for pydantic_mapping — mapping various data structures to Pydantic models.

Tests the Pydantic model conversion capabilities with support for both
Pydantic v1 and v2.
"""

from collections import namedtuple
from typing import List
import pytest

# Check if pydantic is available
pytest.importorskip("pydantic")

from pydantic import BaseModel, ValidationError
from mountainash.pydata.mappers.pydantic_mapping import (
    _is_pydantic_model,
    _get_pydantic_field_names,
    map_dict_to_pydantic,
    map_tuple_to_pydantic,
    map_namedtuple_to_pydantic,
    map_list_of_dicts_to_pydantic,
    map_list_of_tuples_to_pydantic,
    map_list_of_namedtuples_to_pydantic,
)


# Test Pydantic model fixtures
class User(BaseModel):
    """Simple Pydantic model for testing."""
    name: str
    age: int
    active: bool


class UserWithDefaults(BaseModel):
    """Pydantic model with default values."""
    name: str
    age: int
    active: bool = True
    role: str = "user"


class Product(BaseModel):
    """Product Pydantic model for testing field mapping."""
    product_id: int
    product_name: str
    price: float


# Named tuple fixtures
Person = namedtuple('Person', ['name', 'age', 'active'])
PersonAlt = namedtuple('PersonAlt', ['full_name', 'years', 'status'])
Item = namedtuple('Item', ['id', 'name', 'cost'])


class TestPydanticDetection:
    """Test Pydantic model detection."""

    def test_is_pydantic_model_true(self):
        """Test that Pydantic models are correctly identified."""
        assert _is_pydantic_model(User)
        assert _is_pydantic_model(UserWithDefaults)
        assert _is_pydantic_model(Product)

    def test_is_pydantic_model_false(self):
        """Test that non-Pydantic classes are not identified as models."""
        class RegularClass:
            pass

        assert not _is_pydantic_model(RegularClass)
        assert not _is_pydantic_model(str)
        assert not _is_pydantic_model(dict)

    def test_get_pydantic_field_names(self):
        """Test extracting field names from Pydantic models."""
        field_names = _get_pydantic_field_names(User)
        assert 'name' in field_names
        assert 'age' in field_names
        assert 'active' in field_names
        assert len(field_names) == 3


class TestDictToPydantic:
    """Test mapping dictionaries to Pydantic models."""

    def test_dict_basic_mapping(self):
        """Test basic dictionary to Pydantic model conversion."""
        record = {'name': 'Alice', 'age': 30, 'active': True}
        user = map_dict_to_pydantic(record, User)

        assert user.name == 'Alice'
        assert user.age == 30
        assert user.active is True

    def test_dict_with_field_mapping(self):
        """Test dictionary mapping with field name translation."""
        record = {'full_name': 'Bob', 'years': 25, 'status': False}
        user = map_dict_to_pydantic(
            record,
            User,
            mapping={'name': 'full_name', 'age': 'years', 'active': 'status'}
        )

        assert user.name == 'Bob'
        assert user.age == 25
        assert user.active is False

    def test_dict_with_defaults(self):
        """Test that Pydantic defaults are applied correctly."""
        record = {'name': 'Charlie', 'age': 35}
        user = map_dict_to_pydantic(record, UserWithDefaults)

        assert user.name == 'Charlie'
        assert user.age == 35
        assert user.active is True  # Default value
        assert user.role == 'user'  # Default value

    def test_dict_none_record(self):
        """Test handling None record."""
        user = map_dict_to_pydantic(None, User)
        assert user is None

    def test_dict_validation_error(self):
        """Test that Pydantic validation errors are raised."""
        record = {'name': 'Dave', 'age': 'not_a_number', 'active': True}

        with pytest.raises(ValidationError):
            map_dict_to_pydantic(record, User)


class TestTupleToPydantic:
    """Test mapping tuples to Pydantic models."""

    def test_tuple_basic_mapping(self):
        """Test basic tuple to Pydantic model conversion."""
        record = ('Alice', 30, True)
        user = map_tuple_to_pydantic(record, User)

        assert user.name == 'Alice'
        assert user.age == 30
        assert user.active is True

    def test_tuple_with_explicit_field_order(self):
        """Test tuple mapping with explicit field order."""
        record = (30, 'Bob', False)
        user = map_tuple_to_pydantic(
            record,
            User,
            field_order=['age', 'name', 'active']
        )

        assert user.name == 'Bob'
        assert user.age == 30
        assert user.active is False

    def test_tuple_with_defaults(self):
        """Test tuple mapping with Pydantic defaults."""
        record = ('Charlie', 35)
        user = map_tuple_to_pydantic(
            record,
            UserWithDefaults,
            field_order=['name', 'age']
        )

        assert user.name == 'Charlie'
        assert user.age == 35
        assert user.active is True  # Default value
        assert user.role == 'user'  # Default value

    def test_tuple_none_record(self):
        """Test handling None tuple."""
        user = map_tuple_to_pydantic(None, User)
        assert user is None

    def test_tuple_length_mismatch_raises_error(self):
        """Test that mismatched tuple length raises ValueError."""
        record = ('Alice', 30)  # Missing 'active' field

        with pytest.raises(ValueError, match="Tuple length.*does not match"):
            map_tuple_to_pydantic(record, User)

    def test_tuple_validation_error(self):
        """Test that Pydantic validation errors are raised."""
        record = ('Dave', 'not_a_number', True)

        with pytest.raises(ValidationError):
            map_tuple_to_pydantic(record, User)


class TestNamedTupleToPydantic:
    """Test mapping named tuples to Pydantic models."""

    def test_namedtuple_basic_mapping(self):
        """Test basic named tuple to Pydantic model conversion."""
        person = Person('Alice', 30, True)
        user = map_namedtuple_to_pydantic(person, User)

        assert user.name == 'Alice'
        assert user.age == 30
        assert user.active is True

    def test_namedtuple_with_field_mapping(self):
        """Test named tuple mapping with field name translation."""
        person = PersonAlt('Bob Smith', 25, False)
        user = map_namedtuple_to_pydantic(
            person,
            User,
            mapping={'name': 'full_name', 'age': 'years', 'active': 'status'}
        )

        assert user.name == 'Bob Smith'
        assert user.age == 25
        assert user.active is False

    def test_namedtuple_with_defaults(self):
        """Test named tuple mapping with Pydantic defaults."""
        PersonPartial = namedtuple('PersonPartial', ['name', 'age'])
        person = PersonPartial('Charlie', 35)

        user = map_namedtuple_to_pydantic(person, UserWithDefaults)

        assert user.name == 'Charlie'
        assert user.age == 35
        assert user.active is True  # Default value
        assert user.role == 'user'  # Default value

    def test_namedtuple_none_record(self):
        """Test handling None named tuple."""
        user = map_namedtuple_to_pydantic(None, User)
        assert user is None

    def test_namedtuple_invalid_input_raises_error(self):
        """Test that non-named-tuple input raises ValueError."""
        regular_tuple = ('Alice', 30, True)

        with pytest.raises(ValueError, match="must be a named tuple"):
            map_namedtuple_to_pydantic(regular_tuple, User)

    def test_namedtuple_validation_error(self):
        """Test that Pydantic validation errors are raised."""
        InvalidPerson = namedtuple('InvalidPerson', ['name', 'age', 'active'])
        person = InvalidPerson('Dave', 'not_a_number', True)

        with pytest.raises(ValidationError):
            map_namedtuple_to_pydantic(person, User)


class TestBatchConversions:
    """Test batch conversion methods for lists of structures."""

    def test_list_of_dicts_to_pydantic(self):
        """Test converting list of dictionaries to Pydantic models."""
        records = [
            {'name': 'Alice', 'age': 30, 'active': True},
            {'name': 'Bob', 'age': 25, 'active': False},
            {'name': 'Charlie', 'age': 35, 'active': True}
        ]

        users = map_list_of_dicts_to_pydantic(records, User)

        assert len(users) == 3
        assert users[0].name == 'Alice'
        assert users[1].age == 25
        assert users[2].active is True

    def test_list_of_dicts_empty(self):
        """Test handling empty list of dicts."""
        users = map_list_of_dicts_to_pydantic([], User)
        assert users == []

    def test_list_of_dicts_none(self):
        """Test handling None list of dicts."""
        users = map_list_of_dicts_to_pydantic(None, User)
        assert users == []

    def test_list_of_tuples_to_pydantic(self):
        """Test converting list of tuples to Pydantic models."""
        records = [
            ('Alice', 30, True),
            ('Bob', 25, False),
            ('Charlie', 35, True)
        ]

        users = map_list_of_tuples_to_pydantic(
            records,
            User,
            field_order=['name', 'age', 'active']
        )

        assert len(users) == 3
        assert users[0].name == 'Alice'
        assert users[1].age == 25
        assert users[2].active is True

    def test_list_of_tuples_empty(self):
        """Test handling empty list of tuples."""
        users = map_list_of_tuples_to_pydantic([], User)
        assert users == []

    def test_list_of_tuples_none(self):
        """Test handling None list of tuples."""
        users = map_list_of_tuples_to_pydantic(None, User)
        assert users == []

    def test_list_of_namedtuples_to_pydantic(self):
        """Test converting list of named tuples to Pydantic models."""
        records = [
            Person('Alice', 30, True),
            Person('Bob', 25, False),
            Person('Charlie', 35, True)
        ]

        users = map_list_of_namedtuples_to_pydantic(records, User)

        assert len(users) == 3
        assert users[0].name == 'Alice'
        assert users[1].age == 25
        assert users[2].active is True

    def test_list_of_namedtuples_with_mapping(self):
        """Test converting list of named tuples with field mapping."""
        records = [
            PersonAlt('Alice Smith', 30, True),
            PersonAlt('Bob Jones', 25, False)
        ]

        users = map_list_of_namedtuples_to_pydantic(
            records,
            User,
            mapping={'name': 'full_name', 'age': 'years', 'active': 'status'}
        )

        assert len(users) == 2
        assert users[0].name == 'Alice Smith'
        assert users[1].age == 25

    def test_list_of_namedtuples_empty(self):
        """Test handling empty list of named tuples."""
        users = map_list_of_namedtuples_to_pydantic([], User)
        assert users == []

    def test_list_of_namedtuples_none(self):
        """Test handling None list of named tuples."""
        users = map_list_of_namedtuples_to_pydantic(None, User)
        assert users == []


class TestPydanticValidation:
    """Test that Pydantic validation features work correctly."""

    def test_type_coercion(self):
        """Test that Pydantic performs type coercion."""
        record = {'name': 'Alice', 'age': '30', 'active': 1}  # String age, int active
        user = map_dict_to_pydantic(record, User)

        # Pydantic should coerce '30' to int and 1 to bool
        assert user.age == 30
        assert isinstance(user.age, int)
        assert user.active is True
        assert isinstance(user.active, bool)

    def test_missing_required_field(self):
        """Test that missing required fields raise validation error."""
        record = {'name': 'Alice'}  # Missing 'age' and 'active'

        with pytest.raises(ValidationError) as exc_info:
            map_dict_to_pydantic(record, User)

        # Check that error mentions missing fields
        error_str = str(exc_info.value)
        assert 'age' in error_str or 'field required' in error_str.lower()

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored by default."""
        record = {
            'name': 'Alice',
            'age': 30,
            'active': True,
            'extra_field': 'should be ignored'
        }

        user = map_dict_to_pydantic(record, User)

        assert user.name == 'Alice'
        assert user.age == 30
        assert user.active is True
        assert not hasattr(user, 'extra_field')
