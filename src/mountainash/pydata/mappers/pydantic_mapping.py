"""Pydantic model mapping functions.

Provides functions for creating, mapping, and validating Pydantic model
instances from pure Python data structures (dicts, tuples, named tuples).

Works with both Pydantic v1 and v2. Pydantic must be installed to use
these functions.
"""
from __future__ import annotations

from typing import Dict, Any, Type, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel

__all__ = [
    "map_dict_to_pydantic",
    "map_tuple_to_pydantic",
    "map_namedtuple_to_pydantic",
    "map_list_of_dicts_to_pydantic",
    "map_list_of_tuples_to_pydantic",
    "map_list_of_namedtuples_to_pydantic",
]


def _check_pydantic_available():
    """Check if Pydantic is available and raise helpful error if not."""
    try:
        import pydantic  # noqa: F401
        return True
    except ImportError:
        raise ImportError(
            "Pydantic is not installed. Install it with: pip install pydantic"
        )


def _is_pydantic_model(model_class: Type) -> bool:
    """Check if a class is a Pydantic model.

    Args:
        model_class: The class to check

    Returns:
        True if model_class is a Pydantic BaseModel subclass, False otherwise
    """
    try:
        # Check for Pydantic v2 and v1 indicators
        return (
            hasattr(model_class, 'model_fields') or  # Pydantic v2
            hasattr(model_class, '__fields__')  # Pydantic v1
        )
    except Exception:
        return False


def _get_pydantic_field_names(model_class: Type) -> List[str]:
    """Get field names from a Pydantic model.

    Works with both Pydantic v1 and v2.

    Args:
        model_class: The Pydantic model class

    Returns:
        List of field names
    """
    _check_pydantic_available()

    # Pydantic v2
    if hasattr(model_class, 'model_fields'):
        return list(model_class.model_fields.keys())
    # Pydantic v1
    elif hasattr(model_class, '__fields__'):
        return list(model_class.__fields__.keys())
    else:
        raise ValueError(f"{model_class} is not a valid Pydantic model")


def map_dict_to_pydantic(
    record: Optional[Dict[str, Any]],
    model_class: Type["BaseModel"],
    mapping: Optional[Dict[str, str]] = None,
) -> Optional[Any]:
    """Map a dictionary record to a Pydantic model instance.

    Pydantic handles validation and type conversion automatically.

    Args:
        record: A dictionary containing the record data
        model_class: The Pydantic model class to instantiate
        mapping: Optional dictionary mapping model fields to dict keys
                Format: {model_field: dict_key}

    Returns:
        An instance of model_class with fields populated and validated

    Raises:
        ImportError: If pydantic is not installed
        ValidationError: If the data doesn't match the model schema (Pydantic error)

    Example:
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int
            active: bool = True

        # Without mapping
        user = map_dict_to_pydantic({'name': 'Alice', 'age': 30}, User)
        # user.name == 'Alice', user.age == 30, user.active == True (default)

        # With field mapping
        user = map_dict_to_pydantic(
            {'full_name': 'Bob', 'years': 25},
            User,
            mapping={'name': 'full_name', 'age': 'years'}
        )
        # user.name == 'Bob', user.age == 25
    """
    _check_pydantic_available()

    if model_class is None or record is None:
        return None

    # If no mapping, use record as-is
    if mapping is None:
        return model_class(**record)

    # Apply mapping to create transformed dict
    values = {}
    field_names = _get_pydantic_field_names(model_class)

    for model_field in field_names:
        # Try to get the corresponding key from mapping
        dict_key = mapping.get(model_field, model_field)

        if dict_key in record:
            values[model_field] = record[dict_key]

    # Pydantic handles validation and defaults
    return model_class(**values)


def map_tuple_to_pydantic(
    record: Optional[tuple],
    model_class: Type["BaseModel"],
    field_order: Optional[List[str]] = None,
) -> Optional[Any]:
    """Map a tuple record to a Pydantic model instance.

    Converts a positional tuple to a Pydantic model by mapping tuple positions
    to model fields.

    Args:
        record: A tuple containing the record data
        model_class: The Pydantic model class to instantiate
        field_order: Optional list of field names in the order they appear in the tuple.
                    If None, uses the model's field definition order.

    Returns:
        An instance of model_class with fields populated and validated

    Raises:
        ImportError: If pydantic is not installed
        ValueError: If tuple length doesn't match field_order length
        ValidationError: If the data doesn't match the model schema (Pydantic error)

    Example:
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int
            active: bool

        # Using default field order
        user = map_tuple_to_pydantic(('Alice', 30, True), User)
        # user.name == 'Alice', user.age == 30, user.active == True

        # Using explicit field order
        user = map_tuple_to_pydantic(
            (30, 'Bob', False),
            User,
            field_order=['age', 'name', 'active']
        )
        # user.name == 'Bob', user.age == 30, user.active == False
    """
    _check_pydantic_available()

    if model_class is None or record is None:
        return None

    # Get field order (use provided or model field order)
    if field_order is None:
        field_order = _get_pydantic_field_names(model_class)

    # Validate tuple length matches field order
    if len(record) != len(field_order):
        raise ValueError(
            f"Tuple length ({len(record)}) does not match field_order length ({len(field_order)}). "
            f"Expected fields: {field_order}"
        )

    # Convert tuple to dictionary using field_order
    values = {field_name: record[i] for i, field_name in enumerate(field_order)}

    # Pydantic handles validation and defaults
    return model_class(**values)


def map_namedtuple_to_pydantic(
    record: Optional[Any],
    model_class: Type["BaseModel"],
    mapping: Optional[Dict[str, str]] = None,
) -> Optional[Any]:
    """Map a named tuple record to a Pydantic model instance.

    Converts a named tuple to a Pydantic model by mapping named tuple fields
    to model fields. Supports field name remapping via mapping parameter.

    Args:
        record: A named tuple containing the record data
        model_class: The Pydantic model class to instantiate
        mapping: Optional dictionary mapping model fields to named tuple fields.
                Format: {model_field: namedtuple_field}

    Returns:
        An instance of model_class with fields populated and validated

    Raises:
        ImportError: If pydantic is not installed
        ValueError: If record is not a named tuple (missing _fields attribute)
        ValidationError: If the data doesn't match the model schema (Pydantic error)

    Example:
        from collections import namedtuple
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int
            active: bool = True

        Person = namedtuple('Person', ['full_name', 'years', 'status'])
        person = Person('Alice', 30, True)

        # With field mapping
        user = map_namedtuple_to_pydantic(
            person,
            User,
            mapping={'name': 'full_name', 'age': 'years', 'active': 'status'}
        )
        # user.name == 'Alice', user.age == 30, user.active == True

        # Without mapping (field names must match)
        PersonExact = namedtuple('PersonExact', ['name', 'age', 'active'])
        person_exact = PersonExact('Bob', 25, False)
        user = map_namedtuple_to_pydantic(person_exact, User)
        # user.name == 'Bob', user.age == 25, user.active == False
    """
    _check_pydantic_available()

    if model_class is None or record is None:
        return None

    # Validate that record is a named tuple
    if not hasattr(record, '_fields'):
        raise ValueError(
            f"Record must be a named tuple (with _fields attribute), got {type(record)}"
        )

    # Optimized path: no mapping, direct attribute access
    if mapping is None:
        values = {}
        field_names = _get_pydantic_field_names(model_class)

        for model_field in field_names:
            if hasattr(record, model_field):
                values[model_field] = getattr(record, model_field)

        # Pydantic handles validation and defaults
        return model_class(**values)

    # Fallback path: mapping provided, use dict conversion
    # Convert named tuple to dictionary
    # Use _asdict() if available (standard namedtuple), otherwise manual conversion
    if hasattr(record, '_asdict'):
        record_dict = record._asdict()
    else:
        record_dict = {field: getattr(record, field) for field in record._fields}

    # Use existing dict mapping logic
    return map_dict_to_pydantic(
        record=record_dict,
        model_class=model_class,
        mapping=mapping,
    )


def map_list_of_dicts_to_pydantic(
    records: Optional[List[Dict[str, Any]]],
    model_class: Type["BaseModel"],
    mapping: Optional[Dict[str, str]] = None,
) -> List[Any]:
    """Map a list of dictionary records to a list of Pydantic model instances.

    Batch conversion utility for converting multiple dictionary records.

    Args:
        records: List of dictionaries containing record data
        model_class: The Pydantic model class to instantiate
        mapping: Optional dictionary mapping model fields to dict keys

    Returns:
        List of Pydantic model instances

    Raises:
        ImportError: If pydantic is not installed
        ValidationError: If any record doesn't match the model schema

    Example:
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int

        records = [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]
        users = map_list_of_dicts_to_pydantic(records, User)
        # [User(name='Alice', age=30), User(name='Bob', age=25)]
    """
    _check_pydantic_available()

    if records is None:
        return []

    return [
        map_dict_to_pydantic(record, model_class, mapping)
        for record in records
    ]


def map_list_of_tuples_to_pydantic(
    records: Optional[List[tuple]],
    model_class: Type["BaseModel"],
    field_order: Optional[List[str]] = None,
) -> List[Any]:
    """Map a list of tuple records to a list of Pydantic model instances.

    Batch conversion utility for converting multiple tuple records.

    Args:
        records: List of tuples containing record data
        model_class: The Pydantic model class to instantiate
        field_order: Optional list of field names in the order they appear in tuples

    Returns:
        List of Pydantic model instances

    Raises:
        ImportError: If pydantic is not installed
        ValueError: If any tuple length doesn't match field_order length
        ValidationError: If any record doesn't match the model schema

    Example:
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int

        records = [('Alice', 30), ('Bob', 25)]
        users = map_list_of_tuples_to_pydantic(records, User, field_order=['name', 'age'])
        # [User(name='Alice', age=30), User(name='Bob', age=25)]
    """
    _check_pydantic_available()

    if records is None:
        return []

    return [
        map_tuple_to_pydantic(record, model_class, field_order)
        for record in records
    ]


def map_list_of_namedtuples_to_pydantic(
    records: Optional[List[Any]],
    model_class: Type["BaseModel"],
    mapping: Optional[Dict[str, str]] = None,
) -> List[Any]:
    """Map a list of named tuple records to a list of Pydantic model instances.

    Batch conversion utility for converting multiple named tuple records.

    Args:
        records: List of named tuples containing record data
        model_class: The Pydantic model class to instantiate
        mapping: Optional dictionary mapping model fields to named tuple fields

    Returns:
        List of Pydantic model instances

    Raises:
        ImportError: If pydantic is not installed
        ValueError: If any record is not a named tuple
        ValidationError: If any record doesn't match the model schema

    Example:
        from collections import namedtuple
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int

        Person = namedtuple('Person', ['name', 'age'])
        records = [Person('Alice', 30), Person('Bob', 25)]
        users = map_list_of_namedtuples_to_pydantic(records, User)
        # [User(name='Alice', age=30), User(name='Bob', age=25)]
    """
    _check_pydantic_available()

    if records is None:
        return []

    return [
        map_namedtuple_to_pydantic(record, model_class, mapping)
        for record in records
    ]
