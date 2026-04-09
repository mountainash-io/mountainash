"""Dataclass mapping utilities.

Functions for creating, inspecting, and mapping Python data structures
(dicts, tuples, named tuples) to dataclass instances. Works with pure
Python data structures with zero external dependencies.
"""
from __future__ import annotations

from dataclasses import fields
from typing import Dict, Any, Type, Optional, List
import dataclasses

from mountainash.pydata.utils.collection_helpers import is_empty


__all__ = [
    "create_all_none_dataclass",
    "create_dataclass_with_defaults",
    "get_dataclass_field_list",
    "get_dataclass_field_types",
    "get_field_defaults",
    "get_required_fields",
    "get_optional_fields",
    "is_dataclass",
    "is_dataclass_object_all_none",
    "map_dict_to_dataclass",
    "map_tuple_to_dataclass",
    "map_namedtuple_to_dataclass",
    "map_list_of_dicts_to_dataclasses",
    "map_list_of_tuples_to_dataclasses",
    "map_list_of_namedtuples_to_dataclasses",
]


def create_all_none_dataclass(dataclass_type: Type) -> Optional[Any]:
    """Create a dataclass instance with all fields set to None.

    Args:
        dataclass_type: The type of the dataclass to create

    Returns:
        An instance of the dataclass with all fields set to None,
        or None if dataclass_type is None
    """
    if dataclass_type is None:
        return None

    dataclass_fields = get_dataclass_field_list(classtype=dataclass_type)
    return dataclass_type(**{field: None for field in dataclass_fields})


def create_dataclass_with_defaults(dataclass_type: Type) -> Optional[Any]:
    """Create a dataclass instance using field defaults where available.

    For fields without defaults, sets them to None.

    Args:
        dataclass_type: The type of the dataclass to create

    Returns:
        An instance of the dataclass with fields set to their defaults,
        or None if dataclass_type is None

    Example:
        @dataclass
        class Config:
            name: str = "default"
            count: int = 0
            optional: str = None

        config = create_dataclass_with_defaults(Config)
        # config.name == "default", config.count == 0, config.optional == None
    """
    if dataclass_type is None:
        return None

    defaults = get_field_defaults(classtype=dataclass_type)
    field_names = get_dataclass_field_list(classtype=dataclass_type)

    values = {field: defaults.get(field) for field in field_names}
    return dataclass_type(**values)


def get_field_defaults(classtype: Type) -> Dict[str, Any]:
    """Get field default values from a dataclass type.

    Evaluates both field.default and field.default_factory.

    Args:
        classtype: The dataclass type to extract defaults from

    Returns:
        Dictionary mapping field names to their default values

    Example:
        @dataclass
        class Example:
            name: str = "test"
            items: List[str] = field(default_factory=list)
            required: int  # No default

        defaults = get_field_defaults(Example)
        # {'name': 'test', 'items': []}
    """
    defaults = {}
    for f in fields(class_or_instance=classtype):
        if f.default != dataclasses.MISSING:
            defaults[f.name] = f.default
        elif f.default_factory != dataclasses.MISSING:
            defaults[f.name] = f.default_factory()

    return defaults


def get_dataclass_field_types(classtype: Type) -> Dict[str, Type]:
    """Get field type annotations from a dataclass type.

    Args:
        classtype: The dataclass type to extract field types from

    Returns:
        Dictionary mapping field names to their type annotations

    Example:
        @dataclass
        class User:
            name: str
            age: int
            active: bool

        types = get_dataclass_field_types(User)
        # {'name': <class 'str'>, 'age': <class 'int'>, 'active': <class 'bool'>}
    """
    return {f.name: f.type for f in fields(class_or_instance=classtype)}


def get_required_fields(classtype: Type) -> List[str]:
    """Get list of required fields (fields without defaults).

    Args:
        classtype: The dataclass type to analyze

    Returns:
        List of field names that have no default value

    Example:
        @dataclass
        class User:
            name: str           # Required
            age: int            # Required
            active: bool = True # Optional (has default)

        required = get_required_fields(User)
        # ['name', 'age']
    """
    return [
        f.name for f in fields(class_or_instance=classtype)
        if f.default == dataclasses.MISSING
        and f.default_factory == dataclasses.MISSING
    ]


def get_optional_fields(classtype: Type) -> List[str]:
    """Get list of optional fields (fields with defaults).

    Args:
        classtype: The dataclass type to analyze

    Returns:
        List of field names that have default values

    Example:
        @dataclass
        class User:
            name: str           # Required
            age: int            # Required
            active: bool = True # Optional (has default)

        optional = get_optional_fields(User)
        # ['active']
    """
    return [
        f.name for f in fields(class_or_instance=classtype)
        if f.default != dataclasses.MISSING
        or f.default_factory != dataclasses.MISSING
    ]


def _apply_field_defaults(
    dataclass_type: Type,
    values: Dict[str, Any],
) -> Dict[str, Any]:
    """Apply dataclass field defaults for missing or None values.

    Internal helper function used by mapping functions.

    Args:
        dataclass_type: The dataclass type
        values: Dictionary of field values (may be incomplete)

    Returns:
        Dictionary with defaults applied for missing/None fields
    """
    defaults = get_field_defaults(classtype=dataclass_type)

    for field_name in get_dataclass_field_list(classtype=dataclass_type):
        if field_name not in values or values[field_name] is None:
            if field_name in defaults:
                values[field_name] = defaults[field_name]

    return values


def is_dataclass(classtype: object | Type) -> bool:
    """Check if a class is a dataclass.

    Args:
        classtype: The class to check

    Returns:
        True if classtype is a dataclass, False otherwise

    Example:
        @dataclass
        class Point:
            x: int
            y: int

        print(is_dataclass(Point))  # True
    """
    return dataclasses.is_dataclass(obj=classtype)


def is_dataclass_object_all_none(
    obj_dataclass: Any,
    consider_empty_as_none: bool = True,
) -> bool:
    """Check if all fields in a dataclass instance are None.

    Recursively checks nested dataclasses. Returns False as soon as a
    non-None value is found.

    Args:
        obj_dataclass: The object to check. Can be a dataclass instance or any other type.
        consider_empty_as_none: If True, empty collections (list, dict, set) are
                               considered as None

    Returns:
        True if all fields are None (or empty if consider_empty_as_none is True),
        False otherwise
    """
    if obj_dataclass is None:
        return True

    if not is_dataclass(classtype=obj_dataclass):
        if not consider_empty_as_none:
            return False
        else:
            return is_empty(obj=obj_dataclass)

    for fieldname in get_dataclass_field_list(classtype=obj_dataclass):
        value = getattr(obj_dataclass, fieldname)

        # If the field is a dataclass, recurse!
        if is_dataclass(classtype=value):
            if not is_dataclass_object_all_none(obj_dataclass=value, consider_empty_as_none=consider_empty_as_none):
                return False

        elif value is not None:
            if not consider_empty_as_none:
                return False
            else:
                if not is_empty(value):
                    return False

    # If we reach here, all fields are None
    return True


def get_dataclass_field_list(classtype: object | Type) -> List[str]:
    """Get a list of field names from a dataclass type.

    Args:
        classtype: The dataclass type to extract the field names from

    Returns:
        A list of field names
    """
    return [f.name for f in fields(class_or_instance=classtype)]


def map_dict_to_dataclass(
    record: Optional[Dict[str, Any]],
    dataclass_type: Type,
    mapping: Optional[Dict[str, str]] = None,
    apply_defaults: bool = False,
) -> Optional[Any]:
    """Map a dictionary record to a dataclass instance.

    Given a dictionary record and a dataclass_type, this function maps the
    values in the record to the fields in the dataclass. If a mapping is
    provided, it uses it to map row keys to dataclass fields.

    Args:
        record: A dictionary containing the record data
        dataclass_type: The type of the dataclass to map the record to
        mapping: Optional dictionary mapping dataclass fields to row keys
        apply_defaults: If True, use dataclass field defaults for missing/None values

    Returns:
        An instance of dataclass_type with fields populated from the record

    Example:
        @dataclass
        class User:
            name: str
            active: bool = True
            role: str = "user"

        # Without defaults
        user1 = map_dict_to_dataclass({'name': 'Alice'}, User, apply_defaults=False)
        # user1.name == 'Alice', user1.active == None, user1.role == None

        # With defaults
        user2 = map_dict_to_dataclass({'name': 'Bob'}, User, apply_defaults=True)
        # user2.name == 'Bob', user2.active == True, user2.role == 'user'
    """
    if dataclass_type is None:
        return None

    # Handle None values for record
    if record is None:
        if apply_defaults:
            return create_dataclass_with_defaults(dataclass_type)
        return create_all_none_dataclass(dataclass_type)

    values = {}
    dataclass_fields = get_dataclass_field_list(classtype=dataclass_type)

    for dc_field in dataclass_fields:
        # Try to get the corresponding column name from mapping
        column_name: str | None = mapping.get(dc_field) if mapping else dc_field
        if column_name is None:
            column_name = dc_field

        if column_name in record:
            values[dc_field] = record.get(column_name, None) if record else None
        else:
            # If the field doesn't exist in either the mapping or the row
            # Don't set it yet - let defaults handle it
            pass

    # Apply field defaults if requested
    if apply_defaults:
        values = _apply_field_defaults(dataclass_type, values)
    else:
        # Ensure all fields are present (set to None if missing)
        for dc_field in dataclass_fields:
            if dc_field not in values:
                values[dc_field] = None

    return dataclass_type(**values)


def map_tuple_to_dataclass(
    record: Optional[tuple],
    dataclass_type: Type,
    field_order: Optional[List[str]] = None,
    apply_defaults: bool = False,
) -> Optional[Any]:
    """Map a tuple record to a dataclass instance.

    Converts a positional tuple to a dataclass by mapping tuple positions
    to dataclass fields. Field order must be provided explicitly or will
    use the dataclass field definition order.

    Args:
        record: A tuple containing the record data
        dataclass_type: The type of the dataclass to map the record to
        field_order: Optional list of field names in the order they appear in the tuple.
                    If None, uses the dataclass field definition order.
        apply_defaults: If True, use dataclass field defaults for missing/None values

    Returns:
        An instance of dataclass_type with fields populated from the tuple

    Raises:
        ValueError: If tuple length doesn't match field_order length

    Example:
        @dataclass
        class User:
            name: str
            age: int
            active: bool = True

        # Using default field order (name, age, active)
        user1 = map_tuple_to_dataclass(('Alice', 30, False), User)
        # user1.name == 'Alice', user1.age == 30, user1.active == False

        # Using explicit field order
        user2 = map_tuple_to_dataclass(
            (30, 'Bob'), User, field_order=['age', 'name'], apply_defaults=True
        )
        # user2.name == 'Bob', user2.age == 30, user2.active == True (default)
    """
    if dataclass_type is None:
        return None

    # Handle None values for record
    if record is None:
        if apply_defaults:
            return create_dataclass_with_defaults(dataclass_type)
        return create_all_none_dataclass(dataclass_type)

    # Get field order (use provided or dataclass definition order)
    if field_order is None:
        field_order = get_dataclass_field_list(classtype=dataclass_type)

    # Validate tuple length matches field order
    if len(record) != len(field_order):
        raise ValueError(
            f"Tuple length ({len(record)}) does not match field_order length ({len(field_order)}). "
            f"Expected fields: {field_order}"
        )

    # Convert tuple to dictionary using field_order
    values = {field_name: record[i] for i, field_name in enumerate(field_order)}

    # Apply field defaults if requested
    if apply_defaults:
        values = _apply_field_defaults(dataclass_type, values)

    return dataclass_type(**values)


def map_namedtuple_to_dataclass(
    record: Optional[Any],
    dataclass_type: Type,
    mapping: Optional[Dict[str, str]] = None,
    apply_defaults: bool = False,
) -> Optional[Any]:
    """Map a named tuple record to a dataclass instance.

    Converts a named tuple to a dataclass by mapping named tuple fields
    to dataclass fields. Supports field name remapping via mapping parameter.

    Args:
        record: A named tuple containing the record data
        dataclass_type: The type of the dataclass to map the record to
        mapping: Optional dictionary mapping dataclass fields to named tuple fields.
                Format: {dataclass_field: namedtuple_field}
        apply_defaults: If True, use dataclass field defaults for missing/None values

    Returns:
        An instance of dataclass_type with fields populated from the named tuple

    Raises:
        ValueError: If record is not a named tuple (missing _fields attribute)

    Example:
        from collections import namedtuple

        @dataclass
        class User:
            name: str
            age: int
            active: bool = True

        Person = namedtuple('Person', ['full_name', 'years', 'status'])
        person = Person('Alice', 30, True)

        # With field mapping
        user = map_namedtuple_to_dataclass(
            person, User,
            mapping={'name': 'full_name', 'age': 'years', 'active': 'status'}
        )
        # user.name == 'Alice', user.age == 30, user.active == True
    """
    if dataclass_type is None:
        return None

    # Handle None values for record
    if record is None:
        if apply_defaults:
            return create_dataclass_with_defaults(dataclass_type)
        return create_all_none_dataclass(dataclass_type)

    # Validate that record is a named tuple
    if not hasattr(record, '_fields'):
        raise ValueError(
            f"Record must be a named tuple (with _fields attribute), got {type(record)}"
        )

    # Optimized path: no mapping, direct attribute access
    if mapping is None:
        values = {}
        dataclass_fields = get_dataclass_field_list(classtype=dataclass_type)

        for dc_field in dataclass_fields:
            if hasattr(record, dc_field):
                values[dc_field] = getattr(record, dc_field)

        # Apply field defaults if requested
        if apply_defaults:
            values = _apply_field_defaults(dataclass_type, values)
        else:
            # Ensure all fields are present (set to None if missing)
            for dc_field in dataclass_fields:
                if dc_field not in values:
                    values[dc_field] = None

        return dataclass_type(**values)

    # Fallback path: mapping provided, use dict conversion
    # Convert named tuple to dictionary
    # Use _asdict() if available (standard namedtuple), otherwise manual conversion
    if hasattr(record, '_asdict'):
        record_dict = record._asdict()
    else:
        record_dict = {f: getattr(record, f) for f in record._fields}

    # Use existing dict mapping logic
    return map_dict_to_dataclass(
        record=record_dict,
        dataclass_type=dataclass_type,
        mapping=mapping,
        apply_defaults=apply_defaults,
    )


def map_list_of_dicts_to_dataclasses(
    records: Optional[List[Dict[str, Any]]],
    dataclass_type: Type,
    mapping: Optional[Dict[str, str]] = None,
    apply_defaults: bool = False,
) -> List[Any]:
    """Map a list of dictionary records to a list of dataclass instances.

    Batch conversion utility for converting multiple dictionary records.

    Args:
        records: List of dictionaries containing record data
        dataclass_type: The type of the dataclass to map each record to
        mapping: Optional dictionary mapping dataclass fields to dict keys
        apply_defaults: If True, use dataclass field defaults for missing/None values

    Returns:
        List of dataclass instances

    Example:
        @dataclass
        class User:
            name: str
            age: int

        records = [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]
        users = map_list_of_dicts_to_dataclasses(records, User)
        # [User(name='Alice', age=30), User(name='Bob', age=25)]
    """
    if records is None:
        return []

    return [
        map_dict_to_dataclass(record, dataclass_type, mapping, apply_defaults)
        for record in records
    ]


def map_list_of_tuples_to_dataclasses(
    records: Optional[List[tuple]],
    dataclass_type: Type,
    field_order: Optional[List[str]] = None,
    apply_defaults: bool = False,
) -> List[Any]:
    """Map a list of tuple records to a list of dataclass instances.

    Batch conversion utility for converting multiple tuple records.

    Args:
        records: List of tuples containing record data
        dataclass_type: The type of the dataclass to map each record to
        field_order: Optional list of field names in the order they appear in tuples
        apply_defaults: If True, use dataclass field defaults for missing/None values

    Returns:
        List of dataclass instances

    Example:
        @dataclass
        class User:
            name: str
            age: int

        records = [('Alice', 30), ('Bob', 25)]
        users = map_list_of_tuples_to_dataclasses(records, User, field_order=['name', 'age'])
        # [User(name='Alice', age=30), User(name='Bob', age=25)]
    """
    if records is None:
        return []

    return [
        map_tuple_to_dataclass(record, dataclass_type, field_order, apply_defaults)
        for record in records
    ]


def map_list_of_namedtuples_to_dataclasses(
    records: Optional[List[Any]],
    dataclass_type: Type,
    mapping: Optional[Dict[str, str]] = None,
    apply_defaults: bool = False,
) -> List[Any]:
    """Map a list of named tuple records to a list of dataclass instances.

    Batch conversion utility for converting multiple named tuple records.

    Args:
        records: List of named tuples containing record data
        dataclass_type: The type of the dataclass to map each record to
        mapping: Optional dictionary mapping dataclass fields to named tuple fields
        apply_defaults: If True, use dataclass field defaults for missing/None values

    Returns:
        List of dataclass instances

    Example:
        from collections import namedtuple

        @dataclass
        class User:
            name: str
            age: int

        Person = namedtuple('Person', ['name', 'age'])
        records = [Person('Alice', 30), Person('Bob', 25)]
        users = map_list_of_namedtuples_to_dataclasses(records, User)
        # [User(name='Alice', age=30), User(name='Bob', age=25)]
    """
    if records is None:
        return []

    return [
        map_namedtuple_to_dataclass(record, dataclass_type, mapping, apply_defaults)
        for record in records
    ]
