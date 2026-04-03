"""Merged test suite for dataclass_mapping functions.

Merges tests from:
- test_dataclass_utils.py
- test_dataclass_structure_mapping.py
- test_new_dataclass_utils.py
- test_error_conditions.py (dataclass portions)
"""

from dataclasses import dataclass, field
from collections import namedtuple
from typing import List, Any
import pytest

from mountainash.pydata.mappers.dataclass_mapping import (
    create_all_none_dataclass,
    create_dataclass_with_defaults,
    get_dataclass_field_list,
    get_dataclass_field_types,
    get_field_defaults,
    get_required_fields,
    get_optional_fields,
    is_dataclass,
    is_dataclass_object_all_none,
    map_dict_to_dataclass,
    map_tuple_to_dataclass,
    map_namedtuple_to_dataclass,
    map_list_of_dicts_to_dataclasses,
    map_list_of_tuples_to_dataclasses,
    map_list_of_namedtuples_to_dataclasses,
)


# ---------------------------------------------------------------------------
# Fixtures from test_dataclass_utils.py
# ---------------------------------------------------------------------------

@dataclass
class SimpleDataclass:
    name: str
    age: int


@dataclass
class SimpleDataclassArr:
    name: str
    age: List[int]


@dataclass
class NestedDataclass:
    simple: SimpleDataclass
    score: float


@dataclass
class NestedDataclassArr:
    simple: SimpleDataclassArr
    score: float


class TestDataclassMapping:
    """Test suite for dataclass mapping operations"""

    def test_map_dict_to_dataclass_basecase(self):
        row = {'name': 'Alice', 'age': 30}
        mapping = {'name': 'name', 'age': 'age'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name == 'Alice'
        assert instance.age == 30

    def test_map_dict_to_dataclass_datanonevals(self):
        row = {'name': None, 'age': None}
        mapping = {'name': 'name', 'age': 'age'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name is None
        assert instance.age is None

    def test_map_dict_to_dataclass_mappingnonevals(self):
        row = {'name': 'Alice', 'age': 30}
        mapping = {'name': None, 'age': None}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name == 'Alice'
        assert instance.age == 30

    def test_map_dict_to_dataclass_datanone(self):
        row = None
        mapping = {'name': 'name', 'age': 'age'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name is None
        assert instance.age is None

    def test_map_dict_to_dataclass_mappingnone(self):
        row = {'name': 'Alice', 'age': 30}
        mapping = None
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name == 'Alice'
        assert instance.age == 30

    def test_map_dict_to_dataclass_mappingnone_mismatchfieldnames(self):
        row = {'ALTAGE': 'Alice', 'ALTNAME': 30}
        mapping = None
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name is None
        assert instance.age is None
        assert not hasattr(instance, 'ALTNAME')
        assert not hasattr(instance, 'ALTAGE')

    def test_map_dict_to_dataclass_misnamedmapping(self):
        row = {'name': 'Alice', 'age': 30}
        mapping = {'name': 'ALTNAME', 'age': 'ALTAGE'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name is None
        assert instance.age is None
        assert not hasattr(instance, 'ALTNAME')
        assert not hasattr(instance, 'ALTAGE')

    def test_map_dict_to_dataclass_extramappings(self):
        row = {'name': 'Alice', 'age': 30}
        mapping = {'ALTNAME': 'ALTNAME', 'ALTAGE': 'ALTAGE'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name == 'Alice'
        assert instance.age == 30
        assert not hasattr(instance, 'ALTNAME')
        assert not hasattr(instance, 'ALTAGE')

    def test_map_dict_to_dataclass_altnames(self):
        row = {'ALTNAME': 'Alice', 'ALTAGE': 30}
        mapping = {'name': 'ALTNAME', 'age': 'ALTAGE'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name == 'Alice'
        assert instance.age == 30
        assert not hasattr(instance, 'ALTNAME')
        assert not hasattr(instance, 'ALTAGE')

    def test_map_dict_to_dataclass_extradata(self):
        row = {'name': 'Alice', 'age': 30, 'extra': 'extra'}
        mapping = {'name': 'name', 'age': 'age'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name == 'Alice'
        assert instance.age == 30
        assert not hasattr(instance, 'extra')

    def test_map_dict_to_dataclass_extramapping(self):
        row = {'name': 'Alice', 'age': 30}
        mapping = {'name': 'name', 'age': 'age', 'extra': 'extra'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name == 'Alice'
        assert instance.age == 30
        assert not hasattr(instance, 'extra')

    def test_map_dict_to_dataclass_missingdata(self):
        row = {'name': 'Alice'}
        mapping = {'name': 'name', 'age': 'age'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name == 'Alice'
        assert instance.age is None

    def test_map_dict_to_dataclass_missingmapping(self):
        row = {'name': 'Alice', 'age': 30}
        mapping = {'name': 'name'}
        instance = map_dict_to_dataclass(row, SimpleDataclass, mapping)

        assert instance.name == 'Alice'
        assert instance.age == 30


class TestDataclassOperations:
    """Test suite for dataclass utility operations"""

    @pytest.mark.parametrize("input_obj, expected", [
        (SimpleDataclass(None, None), True),
        (SimpleDataclass('Alice', 30), True),
        (SimpleDataclass, True),
    ])
    def test_is_dataclass(self, input_obj, expected):
        assert is_dataclass(input_obj) == expected

    @pytest.mark.parametrize("input_obj, expected", [
        (SimpleDataclass(None, None), True),
        (NestedDataclass(None, None), True),
        (NestedDataclass(SimpleDataclass(None, None), None), True),
        (SimpleDataclass(None, 30), False),
        (SimpleDataclass('Alice', None), False),
        (SimpleDataclass('Alice', 30), False),
        (NestedDataclass(SimpleDataclass("Alice", 30), 745), False),
        (NestedDataclass(SimpleDataclass(None, None), 745), False),
        (NestedDataclass(SimpleDataclass(None, 30), None), False),
        (NestedDataclass(SimpleDataclass("Alice", None), None), False),
        (SimpleDataclass(" ", 0), False),
        (SimpleDataclass(" ", None), False),
        (SimpleDataclass(0, " "), False),
        (NestedDataclass(SimpleDataclass(None, 0), 0), False),
        (NestedDataclass(SimpleDataclass(None, None), 0), False),
        (NestedDataclass(SimpleDataclass(0, 0), None), False),
    ])
    def test_is_dataclass_object_all_none(self, input_obj, expected):
        assert is_dataclass_object_all_none(input_obj) == expected

    @pytest.mark.parametrize("input_obj, expected", [
        (SimpleDataclassArr(name=None, age=[]), True),
        (NestedDataclassArr(simple=SimpleDataclassArr(name=None, age=[]), score=None), True)
    ])
    def test_is_dataclass_object_all_none_emptyarrays_are_none(self, input_obj, expected):
        assert is_dataclass_object_all_none(input_obj, consider_empty_as_none=True) == expected

    @pytest.mark.parametrize("input_obj, expected", [
        (SimpleDataclassArr(name=None, age=[]), False),
        (NestedDataclassArr(simple=SimpleDataclassArr(name=None, age=[]), score=None), False)
    ])
    def test_is_dataclass_object_all_none_emptyarrays_are_data(self, input_obj, expected):
        assert is_dataclass_object_all_none(input_obj, consider_empty_as_none=False) == expected

    @pytest.mark.parametrize("input_obj, expected", [
        (SimpleDataclass(name=None, age=0), False),
        (SimpleDataclass(name=0, age=None), False)
    ])
    def test_is_dataclass_object_all_none_unexpected_fails(self, input_obj, expected):
        assert is_dataclass_object_all_none(input_obj) == expected

    def test_get_dataclass_field_list(self):
        field_list_nested = get_dataclass_field_list(NestedDataclass(SimpleDataclass("Alice", 30), 745))
        field_list_simple = get_dataclass_field_list(SimpleDataclass("Alice", 30))

        assert 'simple' in field_list_nested
        assert 'score' in field_list_nested
        assert 'name' in field_list_simple
        assert 'age' in field_list_simple
        assert 'score' not in field_list_simple


class TestEdgeCasesFromUtils:
    """Test edge cases for dataclass operations (from test_dataclass_utils)"""

    def test_map_dict_to_dataclass_empty_dataclass(self):
        @dataclass
        class EmptyDataclass:
            pass

        row = {}
        mapping = {}
        instance = map_dict_to_dataclass(row, EmptyDataclass, mapping)
        assert isinstance(instance, EmptyDataclass)


# ---------------------------------------------------------------------------
# Fixtures from test_dataclass_structure_mapping.py
# ---------------------------------------------------------------------------

@dataclass
class User:
    """Simple dataclass for testing."""
    name: str
    age: int
    active: bool


@dataclass
class UserWithDefaults:
    """Dataclass with default values."""
    name: str
    age: int
    active: bool = True
    role: str = "user"


@dataclass
class Product:
    """Product dataclass for testing field mapping."""
    product_id: int
    product_name: str
    price: float


# Named tuple fixtures
Person = namedtuple('Person', ['name', 'age', 'active'])
PersonAlt = namedtuple('PersonAlt', ['full_name', 'years', 'status'])
Item = namedtuple('Item', ['id', 'name', 'cost'])


class TestTupleToDataclass:
    """Test mapping regular tuples to dataclass instances."""

    def test_tuple_basic_mapping(self):
        """Test basic tuple to dataclass conversion."""
        record = ('Alice', 30, True)
        user = map_tuple_to_dataclass(record, User)

        assert user.name == 'Alice'
        assert user.age == 30
        assert user.active is True

    def test_tuple_with_explicit_field_order(self):
        """Test tuple mapping with explicit field order."""
        record = (30, 'Bob', False)
        user = map_tuple_to_dataclass(
            record,
            User,
            field_order=['age', 'name', 'active']
        )

        assert user.name == 'Bob'
        assert user.age == 30
        assert user.active is False

    def test_tuple_with_defaults(self):
        """Test tuple mapping with partial data and defaults."""
        record = ('Charlie', 35)
        user = map_tuple_to_dataclass(
            record,
            UserWithDefaults,
            field_order=['name', 'age'],
            apply_defaults=True
        )

        assert user.name == 'Charlie'
        assert user.age == 35
        assert user.active is True  # Default value
        assert user.role == 'user'  # Default value

    def test_tuple_none_record(self):
        """Test handling None tuple."""
        user = map_tuple_to_dataclass(None, User)

        assert user.name is None
        assert user.age is None
        assert user.active is None

    def test_tuple_none_with_defaults(self):
        """Test handling None tuple with defaults."""
        user = map_tuple_to_dataclass(
            None,
            UserWithDefaults,
            apply_defaults=True
        )

        assert user.name is None
        assert user.age is None
        assert user.active is True
        assert user.role == 'user'

    def test_tuple_length_mismatch_raises_error(self):
        """Test that mismatched tuple length raises ValueError."""
        record = ('Alice', 30)  # Missing 'active' field

        with pytest.raises(ValueError, match="Tuple length.*does not match"):
            map_tuple_to_dataclass(record, User)

    def test_tuple_custom_field_order_length_mismatch(self):
        """Test that custom field_order length mismatch raises error."""
        record = ('Alice', 30, True)

        with pytest.raises(ValueError, match="Tuple length.*does not match"):
            map_tuple_to_dataclass(
                record,
                User,
                field_order=['name', 'age']  # Only 2 fields, tuple has 3
            )


class TestNamedTupleToDataclass:
    """Test mapping named tuples to dataclass instances."""

    def test_namedtuple_basic_mapping(self):
        """Test basic named tuple to dataclass conversion."""
        person = Person('Alice', 30, True)
        user = map_namedtuple_to_dataclass(person, User)

        assert user.name == 'Alice'
        assert user.age == 30
        assert user.active is True

    def test_namedtuple_with_field_mapping(self):
        """Test named tuple mapping with field name translation."""
        person = PersonAlt('Bob Smith', 25, False)
        user = map_namedtuple_to_dataclass(
            person,
            User,
            mapping={
                'name': 'full_name',
                'age': 'years',
                'active': 'status'
            }
        )

        assert user.name == 'Bob Smith'
        assert user.age == 25
        assert user.active is False

    def test_namedtuple_partial_mapping(self):
        """Test named tuple with partial field mapping."""
        person = PersonAlt('Charlie', 35, True)
        user = map_namedtuple_to_dataclass(
            person,
            User,
            mapping={'name': 'full_name'}  # Only map name
        )

        assert user.name == 'Charlie'
        # Other fields don't match, so they should be None
        assert user.age is None
        assert user.active is None

    def test_namedtuple_with_defaults(self):
        """Test named tuple mapping with defaults for missing fields."""
        PersonPartial = namedtuple('PersonPartial', ['name', 'age'])
        person = PersonPartial('Dave', 40)

        user = map_namedtuple_to_dataclass(
            person,
            UserWithDefaults,
            apply_defaults=True
        )

        assert user.name == 'Dave'
        assert user.age == 40
        assert user.active is True  # Default value
        assert user.role == 'user'  # Default value

    def test_namedtuple_none_record(self):
        """Test handling None named tuple."""
        user = map_namedtuple_to_dataclass(None, User)

        assert user.name is None
        assert user.age is None
        assert user.active is None

    def test_namedtuple_invalid_input_raises_error(self):
        """Test that non-named-tuple input raises ValueError."""
        regular_tuple = ('Alice', 30, True)

        with pytest.raises(ValueError, match="must be a named tuple"):
            map_namedtuple_to_dataclass(regular_tuple, User)

    def test_namedtuple_typed_annotations(self):
        """Test handling typed named tuples (with __annotations__)."""
        TypedPerson = namedtuple('TypedPerson', ['name', 'age', 'active'])
        TypedPerson.__annotations__ = {'name': str, 'age': int, 'active': bool}

        person = TypedPerson('Eve', 28, True)
        user = map_namedtuple_to_dataclass(person, User)

        assert user.name == 'Eve'
        assert user.age == 28
        assert user.active is True


class TestBatchConversions:
    """Test batch conversion methods for lists of structures."""

    def test_list_of_dicts_to_dataclasses(self):
        """Test converting list of dictionaries to dataclasses."""
        records = [
            {'name': 'Alice', 'age': 30, 'active': True},
            {'name': 'Bob', 'age': 25, 'active': False},
            {'name': 'Charlie', 'age': 35, 'active': True}
        ]

        users = map_list_of_dicts_to_dataclasses(records, User)

        assert len(users) == 3
        assert users[0].name == 'Alice'
        assert users[1].age == 25
        assert users[2].active is True

    def test_list_of_dicts_empty(self):
        """Test handling empty list of dicts."""
        users = map_list_of_dicts_to_dataclasses([], User)
        assert users == []

    def test_list_of_dicts_none(self):
        """Test handling None list of dicts."""
        users = map_list_of_dicts_to_dataclasses(None, User)
        assert users == []

    def test_list_of_tuples_to_dataclasses(self):
        """Test converting list of tuples to dataclasses."""
        records = [
            ('Alice', 30, True),
            ('Bob', 25, False),
            ('Charlie', 35, True)
        ]

        users = map_list_of_tuples_to_dataclasses(
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
        users = map_list_of_tuples_to_dataclasses([], User)
        assert users == []

    def test_list_of_tuples_none(self):
        """Test handling None list of tuples."""
        users = map_list_of_tuples_to_dataclasses(None, User)
        assert users == []

    def test_list_of_namedtuples_to_dataclasses(self):
        """Test converting list of named tuples to dataclasses."""
        records = [
            Person('Alice', 30, True),
            Person('Bob', 25, False),
            Person('Charlie', 35, True)
        ]

        users = map_list_of_namedtuples_to_dataclasses(records, User)

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

        users = map_list_of_namedtuples_to_dataclasses(
            records,
            User,
            mapping={
                'name': 'full_name',
                'age': 'years',
                'active': 'status'
            }
        )

        assert len(users) == 2
        assert users[0].name == 'Alice Smith'
        assert users[1].age == 25

    def test_list_of_namedtuples_empty(self):
        """Test handling empty list of named tuples."""
        users = map_list_of_namedtuples_to_dataclasses([], User)
        assert users == []

    def test_list_of_namedtuples_none(self):
        """Test handling None list of named tuples."""
        users = map_list_of_namedtuples_to_dataclasses(None, User)
        assert users == []


class TestRoundtripConversion:
    """
    Test roundtrip conversions simulating mountainash-dataframes cast outputs.
    """

    def test_roundtrip_list_of_tuples(self):
        """Simulate: DataFrame -> to_list_of_tuples() -> dataclass_mapping -> dataclasses"""
        df_as_tuples = [
            ('Alice', 30, True),
            ('Bob', 25, False),
            ('Charlie', 35, True)
        ]

        users = map_list_of_tuples_to_dataclasses(
            df_as_tuples,
            User,
            field_order=['name', 'age', 'active']
        )

        assert len(users) == 3
        assert all(isinstance(u, User) for u in users)
        assert users[0].name == 'Alice' and users[0].age == 30
        assert users[1].name == 'Bob' and users[1].age == 25
        assert users[2].name == 'Charlie' and users[2].age == 35

    def test_roundtrip_list_of_named_tuples(self):
        """Simulate: DataFrame -> to_list_of_named_tuples() -> dataclass_mapping -> dataclasses"""
        Row = namedtuple('Row', ['name', 'age', 'active'])
        df_as_named_tuples = [
            Row('Alice', 30, True),
            Row('Bob', 25, False),
            Row('Charlie', 35, True)
        ]

        users = map_list_of_namedtuples_to_dataclasses(df_as_named_tuples, User)

        assert len(users) == 3
        assert all(isinstance(u, User) for u in users)
        assert users[0].name == 'Alice'
        assert users[1].age == 25
        assert users[2].active is True

    def test_roundtrip_list_of_typed_named_tuples(self):
        """Simulate: DataFrame -> to_list_of_typed_named_tuples() -> dataclass_mapping -> dataclasses"""
        Row = namedtuple('Row', ['name', 'age', 'active'])
        Row.__annotations__ = {'name': str, 'age': int, 'active': bool}

        df_as_typed_named_tuples = [
            Row('Alice', 30, True),
            Row('Bob', 25, False),
            Row('Charlie', 35, True)
        ]

        users = map_list_of_namedtuples_to_dataclasses(df_as_typed_named_tuples, User)

        assert len(users) == 3
        assert all(isinstance(u, User) for u in users)
        assert users[0].name == 'Alice'
        assert users[1].age == 25
        assert users[2].active is True

    def test_roundtrip_list_of_dictionaries(self):
        """Simulate: DataFrame -> to_list_of_dictionaries() -> dataclass_mapping -> dataclasses"""
        df_as_dicts = [
            {'name': 'Alice', 'age': 30, 'active': True},
            {'name': 'Bob', 'age': 25, 'active': False},
            {'name': 'Charlie', 'age': 35, 'active': True}
        ]

        users = map_list_of_dicts_to_dataclasses(df_as_dicts, User)

        assert len(users) == 3
        assert all(isinstance(u, User) for u in users)
        assert users[0].name == 'Alice'
        assert users[1].age == 25
        assert users[2].active is True

    def test_roundtrip_with_field_mapping(self):
        """Test roundtrip with field name mapping (DataFrame columns != dataclass fields)."""
        Row = namedtuple('Row', ['product_id', 'product_name', 'price'])
        df_as_named_tuples = [
            Row(1, 'Widget', 9.99),
            Row(2, 'Gadget', 19.99),
            Row(3, 'Doohickey', 14.99)
        ]

        products = map_list_of_namedtuples_to_dataclasses(df_as_named_tuples, Product)

        assert len(products) == 3
        assert products[0].product_id == 1
        assert products[1].product_name == 'Gadget'
        assert products[2].price == 14.99


class TestEdgeCasesFromStructureMapping:
    """Test edge cases and error conditions (from test_dataclass_structure_mapping)."""

    def test_empty_dataclass_tuple_mapping(self):
        """Test mapping to empty dataclass."""
        @dataclass
        class EmptyDataclass:
            pass

        record = ()
        instance = map_tuple_to_dataclass(record, EmptyDataclass)
        assert isinstance(instance, EmptyDataclass)

    def test_empty_dataclass_namedtuple_mapping(self):
        """Test mapping empty named tuple to empty dataclass."""
        @dataclass
        class EmptyDataclass:
            pass

        EmptyTuple = namedtuple('EmptyTuple', [])
        record = EmptyTuple()
        instance = map_namedtuple_to_dataclass(record, EmptyDataclass)
        assert isinstance(instance, EmptyDataclass)

    def test_mixed_types_in_tuple(self):
        """Test tuple with mixed types."""
        record = ('Alice', '30', 'True')  # All strings
        user = map_tuple_to_dataclass(record, User)

        # Values are assigned as-is (no type conversion)
        assert user.name == 'Alice'
        assert user.age == '30'  # String, not int
        assert user.active == 'True'  # String, not bool

    def test_none_values_in_tuple(self):
        """Test tuple with None values."""
        record = (None, None, None)
        user = map_tuple_to_dataclass(record, User)

        assert user.name is None
        assert user.age is None
        assert user.active is None

    def test_partial_defaults_application(self):
        """Test that defaults only apply to missing fields."""
        record = ('Alice', 30)
        user = map_tuple_to_dataclass(
            record,
            UserWithDefaults,
            field_order=['name', 'age'],
            apply_defaults=True
        )

        assert user.name == 'Alice'
        assert user.age == 30
        assert user.active is True  # Default applied
        assert user.role == 'user'  # Default applied


# ---------------------------------------------------------------------------
# Fixtures from test_new_dataclass_utils.py
# ---------------------------------------------------------------------------

@dataclass
class DataclassWithDefaults:
    name: str
    count: int = 0
    active: bool = True
    role: str = "user"


@dataclass
class DataclassWithFactory:
    name: str
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class MixedDefaultsDataclass:
    required_field: str
    optional_with_default: int = 42
    optional_with_factory: List[int] = field(default_factory=list)
    optional_none: str = None


class TestFieldIntrospection:
    """Test field introspection utility methods."""

    def test_get_field_defaults_simple(self):
        """Test getting defaults from dataclass with simple defaults."""
        defaults = get_field_defaults(DataclassWithDefaults)

        assert defaults == {
            'count': 0,
            'active': True,
            'role': 'user'
        }
        assert 'name' not in defaults  # No default for required field

    def test_get_field_defaults_with_factory(self):
        """Test getting defaults from dataclass with default_factory."""
        defaults = get_field_defaults(DataclassWithFactory)

        assert 'tags' in defaults
        assert defaults['tags'] == []
        assert 'metadata' in defaults
        assert defaults['metadata'] == {}
        assert 'name' not in defaults

    def test_get_field_defaults_mixed(self):
        """Test getting defaults from dataclass with mixed defaults."""
        defaults = get_field_defaults(MixedDefaultsDataclass)

        assert defaults == {
            'optional_with_default': 42,
            'optional_with_factory': [],
            'optional_none': None
        }

    def test_get_dataclass_field_types(self):
        """Test getting field types from dataclass."""
        types = get_dataclass_field_types(SimpleDataclass)

        assert types == {
            'name': str,
            'age': int
        }

    def test_get_required_fields(self):
        """Test getting required fields (no defaults)."""
        required = get_required_fields(MixedDefaultsDataclass)

        assert required == ['required_field']

    def test_get_optional_fields(self):
        """Test getting optional fields (with defaults)."""
        optional = get_optional_fields(MixedDefaultsDataclass)

        assert set(optional) == {
            'optional_with_default',
            'optional_with_factory',
            'optional_none'
        }


class TestCreateDataclassWithDefaults:
    """Test creating dataclass instances with defaults."""

    def test_create_dataclass_with_defaults(self):
        """Test creating instance with all defaults applied."""
        instance = create_dataclass_with_defaults(DataclassWithDefaults)

        assert instance.name is None  # No default
        assert instance.count == 0
        assert instance.active is True
        assert instance.role == "user"

    def test_create_dataclass_with_factory_defaults(self):
        """Test creating instance with factory defaults."""
        instance = create_dataclass_with_defaults(DataclassWithFactory)

        assert instance.name is None
        assert instance.tags == []
        assert instance.metadata == {}

    def test_create_dataclass_with_defaults_none_type(self):
        """Test with None dataclass type returns None."""
        result = create_dataclass_with_defaults(None)
        assert result is None

    def test_create_dataclass_no_defaults(self):
        """Test creating instance when no defaults exist."""
        instance = create_dataclass_with_defaults(SimpleDataclass)

        assert instance.name is None
        assert instance.age is None


class TestMapDictToDataclassWithDefaults:
    """Test map_dict_to_dataclass with apply_defaults parameter."""

    def test_map_dict_without_defaults(self):
        """Test mapping without applying defaults (original behavior)."""
        record = {'name': 'Alice'}
        instance = map_dict_to_dataclass(
            record,
            DataclassWithDefaults,
            apply_defaults=False
        )

        assert instance.name == 'Alice'
        assert instance.count is None  # Missing field becomes None
        assert instance.active is None
        assert instance.role is None

    def test_map_dict_with_defaults(self):
        """Test mapping with defaults applied."""
        record = {'name': 'Bob'}
        instance = map_dict_to_dataclass(
            record,
            DataclassWithDefaults,
            apply_defaults=True
        )

        assert instance.name == 'Bob'
        assert instance.count == 0  # Default applied
        assert instance.active is True  # Default applied
        assert instance.role == "user"  # Default applied

    def test_map_dict_with_defaults_partial_data(self):
        """Test mapping with some fields present, defaults for missing."""
        record = {'name': 'Charlie', 'count': 5}
        instance = map_dict_to_dataclass(
            record,
            DataclassWithDefaults,
            apply_defaults=True
        )

        assert instance.name == 'Charlie'
        assert instance.count == 5  # From record
        assert instance.active is True  # Default applied
        assert instance.role == "user"  # Default applied

    def test_map_dict_with_defaults_override_defaults(self):
        """Test that explicit values override defaults."""
        record = {
            'name': 'David',
            'count': 10,
            'active': False,
            'role': 'admin'
        }
        instance = map_dict_to_dataclass(
            record,
            DataclassWithDefaults,
            apply_defaults=True
        )

        assert instance.name == 'David'
        assert instance.count == 10
        assert instance.active is False
        assert instance.role == 'admin'

    def test_map_dict_with_defaults_none_record(self):
        """Test with None record and apply_defaults=True."""
        instance = map_dict_to_dataclass(
            None,
            DataclassWithDefaults,
            apply_defaults=True
        )

        assert instance.name is None
        assert instance.count == 0  # Default applied
        assert instance.active is True
        assert instance.role == "user"

    def test_map_dict_without_defaults_none_record(self):
        """Test with None record and apply_defaults=False."""
        instance = map_dict_to_dataclass(
            None,
            DataclassWithDefaults,
            apply_defaults=False
        )

        assert instance.name is None
        assert instance.count is None  # All None
        assert instance.active is None
        assert instance.role is None

    def test_map_dict_with_factory_defaults(self):
        """Test mapping with factory defaults."""
        record = {'name': 'Eve'}
        instance = map_dict_to_dataclass(
            record,
            DataclassWithFactory,
            apply_defaults=True
        )

        assert instance.name == 'Eve'
        assert instance.tags == []  # Factory default
        assert instance.metadata == {}  # Factory default

    def test_map_dict_with_field_mapping_and_defaults(self):
        """Test field mapping works with defaults."""
        record = {'full_name': 'Frank'}
        mapping = {'name': 'full_name'}

        instance = map_dict_to_dataclass(
            record,
            DataclassWithDefaults,
            mapping=mapping,
            apply_defaults=True
        )

        assert instance.name == 'Frank'
        assert instance.count == 0
        assert instance.active is True


class TestApplyFieldDefaults:
    """Test internal _apply_field_defaults helper (via public API)."""

    def test_apply_field_defaults_to_empty_dict(self):
        """Test applying defaults fills optional fields — required fields without defaults become None."""
        # name has no default so it becomes None; count/active/role get their defaults
        instance = map_dict_to_dataclass({'name': None}, DataclassWithDefaults, apply_defaults=True)

        assert instance.name is None
        assert instance.count == 0
        assert instance.active is True
        assert instance.role == 'user'

    def test_apply_field_defaults_preserves_existing(self):
        """Test that existing values are preserved."""
        record = {'name': 'Alice', 'count': 5}
        instance = map_dict_to_dataclass(record, DataclassWithDefaults, apply_defaults=True)

        assert instance.name == 'Alice'
        assert instance.count == 5  # Preserved
        assert instance.active is True  # Default added
        assert instance.role == "user"  # Default added

    def test_apply_field_defaults_replaces_none(self):
        """Test that None values are replaced with defaults."""
        record = {'name': 'Bob', 'count': None}
        instance = map_dict_to_dataclass(record, DataclassWithDefaults, apply_defaults=True)

        assert instance.name == 'Bob'
        assert instance.count == 0  # None replaced with default


# ---------------------------------------------------------------------------
# Error conditions (from test_error_conditions.py, dataclass portions)
# ---------------------------------------------------------------------------

class TestErrorConditions:
    """Test error conditions and edge cases."""

    def test_map_dict_to_dataclass_with_none_dataclass_type(self):
        """Test dict mapping with None dataclass type returns None."""
        record = {'name': 'Alice', 'age': 30}

        result = map_dict_to_dataclass(
            record=record,
            dataclass_type=None
        )

        assert result is None

    def test_create_all_none_dataclass_with_none_type(self):
        """Test create_all_none_dataclass with None type returns None."""
        result = create_all_none_dataclass(dataclass_type=None)
        assert result is None

    def test_create_all_none_dataclass_with_valid_type(self):
        """Test create_all_none_dataclass creates instance with all None fields."""
        result = create_all_none_dataclass(dataclass_type=SimpleDataclass)

        assert result.name is None
        assert result.age is None
        assert isinstance(result, SimpleDataclass)

    def test_is_dataclass_object_all_none_with_non_dataclass_no_empty_consideration(self):
        """Test is_dataclass_object_all_none with non-dataclass object."""
        result = is_dataclass_object_all_none(
            obj_dataclass="not a dataclass",
            consider_empty_as_none=False
        )

        assert result is False

    def test_is_dataclass_object_all_none_with_non_dataclass_string(self):
        """Test is_dataclass_object_all_none with non-dataclass string input."""
        result = is_dataclass_object_all_none("not a dataclass")
        assert result is False

    def test_is_dataclass_object_all_none_with_none(self):
        """Test is_dataclass_object_all_none with None input."""
        result = is_dataclass_object_all_none(None)
        assert result is True

    def test_is_dataclass_object_all_none_with_valid_dataclass(self):
        """Test is_dataclass_object_all_none with valid dataclass."""
        obj = SimpleDataclass(name="Alice", age=30)
        result = is_dataclass_object_all_none(obj)
        assert result is False

    def test_is_dataclass_object_all_none_with_all_none_dataclass(self):
        """Test is_dataclass_object_all_none with all-None dataclass."""
        obj = SimpleDataclass(name=None, age=None)
        result = is_dataclass_object_all_none(obj)
        assert result is True


class TestEmptyDataclassHandling:
    """Test handling of empty dataclasses."""

    def test_empty_dataclass_creation(self):
        """Test creating an empty dataclass works properly."""
        @dataclass
        class EmptyDataclass:
            pass

        result = create_all_none_dataclass(EmptyDataclass)
        assert isinstance(result, EmptyDataclass)

    def test_empty_dataclass_field_list(self):
        """Test getting field list from empty dataclass."""
        @dataclass
        class EmptyDataclass:
            pass

        result = get_dataclass_field_list(EmptyDataclass)
        assert result == []

    def test_empty_dataclass_all_none_check(self):
        """Test checking if empty dataclass is all None."""
        @dataclass
        class EmptyDataclass:
            pass

        obj = EmptyDataclass()
        result = is_dataclass_object_all_none(obj)
        assert result is True
