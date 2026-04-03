"""Enum introspection and validation helpers for pydata operations."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Set, Tuple, Type

__all__ = [
    "is_enum",
    "member_identities",
    "member_names",
    "member_values",
    "is_valid_member_name",
    "is_valid_member_value",
    "is_valid_member_identity",
    "find_member",
    "find_member_name",
    "find_all_member_names",
    "find_member_names_dict",
    "get_enum_attribute_names",
    "get_enum_values",
    "get_enum_values_set",
    "get_enum_values_tuple",
    "get_enum_values_dict",
]


def is_enum(classtype: Type) -> bool:
    """Check if a class is an Enum.

    Args:
        classtype: The class to check

    Returns:
        True if classtype is an enum, False otherwise

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        print(is_enum(Color))  # True
    """
    try:
        return issubclass(classtype, Enum)
    except Exception:
        return False


def member_identities(enumclass: Type[Enum]) -> Set[Enum]:
    """Get all enum member instances (identities).

    Always returns the enum instances themselves, regardless of their values.
    Use this for identity-based enums where the instance is the meaningful value.

    Args:
        enumclass: The Enum class to get member instances for

    Returns:
        A set of all enum member instances

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2

        identities = member_identities(Color)
        # {<Color.RED: 1>, <Color.GREEN: 2>}
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    return set(enumclass.__members__.values())


def member_names(enumclass: Type[Enum]) -> Set[str]:
    """Get all enum member names.

    Args:
        enumclass: The Enum class to get member names for

    Returns:
        A set of all enum member names

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2

        names = member_names(Color)
        # {'RED', 'GREEN'}
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    return set(enumclass.__members__.keys())


def member_values(enumclass: Type[Enum]) -> Set[Any]:
    """Get all enum member values (primitives).

    Extracts the .value attribute from each enum member. Use this for
    value-based enums (StrEnum, IntEnum) where the primitive value is meaningful.

    Args:
        enumclass: The Enum class to get member values for

    Returns:
        A set of all enum member values

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2

        values = member_values(Color)
        # {1, 2}
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    return {member.value for member in enumclass.__members__.values()}


def is_valid_member_name(enumclass: Type[Enum], name: str) -> bool:
    """Check if a name is a valid enum member name.

    Args:
        enumclass: The Enum class to check against
        name: The name to validate

    Returns:
        True if name is a valid enum member name, False otherwise

    Example:
        class Color(Enum):
            RED = 1

        is_valid_member_name(Color, 'RED')   # True
        is_valid_member_name(Color, 'BLUE')  # False
    """
    if not is_enum(enumclass):
        return False

    try:
        return name in enumclass.__members__
    except TypeError:
        # Handle unhashable types (lists, dicts, etc.)
        return False


def is_valid_member_value(enumclass: Type[Enum], value: Any) -> bool:
    """Check if a value is a valid enum member value (primitive).

    Checks against the .value attribute of enum members.

    Args:
        enumclass: The Enum class to check against
        value: The value to validate

    Returns:
        True if value is a valid enum member value, False otherwise

    Example:
        class Color(Enum):
            RED = 1

        is_valid_member_value(Color, 1)   # True
        is_valid_member_value(Color, 99)  # False
    """
    if not is_enum(enumclass):
        return False

    try:
        return value in {member.value for member in enumclass.__members__.values()}
    except TypeError:
        # Handle unhashable values
        # Fallback to iteration for unhashable types
        for member in enumclass.__members__.values():
            if member.value == value:
                return True
        return False


def is_valid_member_identity(enumclass: Type[Enum], instance: Any) -> bool:
    """Check if an instance is a valid enum member (identity check).

    Checks if the given instance is one of the enum members themselves.

    Args:
        enumclass: The Enum class to check against
        instance: The instance to validate

    Returns:
        True if instance is a valid enum member, False otherwise

    Example:
        class Color(Enum):
            RED = 1

        is_valid_member_identity(Color, Color.RED)  # True
        is_valid_member_identity(Color, 1)          # False
    """
    if not is_enum(enumclass):
        return False

    return instance in enumclass.__members__.values()


def find_member(enumclass: Type[Enum], value: Any) -> Any:
    """Find enum member by value (returns canonical member for aliases).

    Performs reverse lookup from value to enum member. For aliases (multiple
    members with the same value), returns the canonical (first-defined) member.
    Use find_all_member_names() to get all members including aliases.

    Args:
        enumclass: The Enum class to search
        value: The value to lookup

    Returns:
        The enum member with the given value, or None if not found

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Status(Enum):
            PENDING = 1
            WAITING = 1  # Alias for PENDING
            APPROVED = 2

        find_member(Status, 1)   # Returns Status.PENDING (canonical)
        find_member(Status, 2)   # Returns Status.APPROVED
        find_member(Status, 99)  # Returns None
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    try:
        return enumclass(value)
    except (ValueError, KeyError):
        return None


def find_member_name(enumclass: Type[Enum], value: Any) -> Any:
    """Find canonical member name by value.

    Returns the name of the canonical (first-defined) member with the given value.
    For aliases, returns the canonical member name only.

    Args:
        enumclass: The Enum class to search
        value: The value to lookup

    Returns:
        The member name as a string, or None if not found

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Status(Enum):
            PENDING = 1
            WAITING = 1  # Alias for PENDING
            APPROVED = 2

        find_member_name(Status, 1)   # Returns "PENDING"
        find_member_name(Status, 2)   # Returns "APPROVED"
        find_member_name(Status, 99)  # Returns None
    """
    member = find_member(enumclass, value)
    return member.name if member is not None else None


def find_all_member_names(enumclass: Type[Enum], value: Any) -> Set[str]:
    """Find all member names with the given value (including aliases).

    Returns all member names (including aliases) that have the specified value.
    For enums without aliases, returns a set with a single name.

    Args:
        enumclass: The Enum class to search
        value: The value to lookup

    Returns:
        A set of all member names with the given value, or empty set if not found

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Status(Enum):
            PENDING = 1
            WAITING = 1  # Alias for PENDING
            QUEUED = 1   # Alias for PENDING
            APPROVED = 2

        find_all_member_names(Status, 1)
        # Returns {"PENDING", "WAITING", "QUEUED"}

        find_all_member_names(Status, 2)
        # Returns {"APPROVED"}

        find_all_member_names(Status, 99)
        # Returns set()
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    matching_names = set()

    try:
        # Iterate through items to include aliases
        # __members__ includes all names, even aliases
        for name, member in enumclass.__members__.items():
            if member.value == value:
                matching_names.add(name)
    except TypeError:
        # Fallback for unhashable values
        for name, member in enumclass.__members__.items():
            try:
                if member.value == value:
                    matching_names.add(name)
            except Exception:
                # Skip members that can't be compared
                continue

    return matching_names


def find_member_names_dict(enumclass: Type[Enum], value: Any) -> Dict[str, Enum]:
    """Find all member names mapped to their member for the given value.

    Returns a dictionary mapping all member names (including aliases) to their
    member object for the specified value. Since aliases are the same object,
    all names will map to the canonical member instance.

    Args:
        enumclass: The Enum class to search
        value: The value to lookup

    Returns:
        A dict of {name: member} for all names with the given value,
        or empty dict if not found

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Status(Enum):
            PENDING = 1
            WAITING = 1  # Alias for PENDING
            QUEUED = 1   # Alias for PENDING
            APPROVED = 2

        find_member_names_dict(Status, 1)
        # Returns {"PENDING": Status.PENDING,
        #          "WAITING": Status.PENDING,
        #          "QUEUED": Status.PENDING}

        find_member_names_dict(Status, 2)
        # Returns {"APPROVED": Status.APPROVED}

        find_member_names_dict(Status, 99)
        # Returns {}
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    matching_dict = {}

    try:
        # Iterate through items to include aliases
        # __members__ includes all names, even aliases
        for name, member in enumclass.__members__.items():
            if member.value == value:
                matching_dict[name] = member
    except TypeError:
        # Fallback for unhashable values
        for name, member in enumclass.__members__.items():
            try:
                if member.value == value:
                    matching_dict[name] = member
            except Exception:
                # Skip members that can't be compared
                continue

    return matching_dict


def get_enum_attribute_names(enumclass: Type[Enum]) -> List[str]:
    """Get a list of all attribute names from an Enum class.

    Args:
        enumclass: The Enum class to get attribute names for

    Returns:
        A list of all attribute names of the Enum

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        print(get_enum_attribute_names(Color))
        # ["RED", "GREEN", "BLUE"]
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    return [enum_member.name for enum_member in list(enumclass)]


def get_enum_values(enumclass: Type[Enum]) -> List[Any]:
    """Get a list of all values from an Enum class.

    Extracts the .value attribute from each enum member.

    Args:
        enumclass: The Enum class to get values for

    Returns:
        A list of all values of the Enum

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        print(get_enum_values(Color))
        # [1, 2, 3]
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    return [enum_member.value for enum_member in list(enumclass)]


def get_enum_values_set(enumclass: Type[Enum]) -> Set[Any]:
    """Get a set of all values from an Enum class.

    Extracts the .value attribute from each enum member.

    Args:
        enumclass: The Enum class to get values for

    Returns:
        A set of all values of the Enum

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        print(get_enum_values_set(Color))
        # {1, 2, 3}
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    return {enum_member.value for enum_member in list(enumclass)}


def get_enum_values_tuple(enumclass: Type[Enum]) -> Tuple[Any, ...]:
    """Get a tuple of all values from an Enum class.

    Extracts the .value attribute from each enum member.

    Args:
        enumclass: The Enum class to get values for

    Returns:
        A tuple of all values of the Enum

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        print(get_enum_values_tuple(Color))
        # (1, 2, 3)
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    return tuple([enum_member.value for enum_member in list(enumclass)])


def get_enum_values_dict(enumclass: Type[Enum]) -> Dict[str, Any]:
    """Get a dict of {name: value} pairs from an Enum class.

    Extracts the .value attribute from each enum member.

    Args:
        enumclass: The Enum class to get values for

    Returns:
        A dict of {name: value} pairs for the Enum

    Raises:
        ValueError: If enumclass is not a subclass of Enum

    Example:
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        print(get_enum_values_dict(Color))
        # {'RED': 1, 'GREEN': 2, 'BLUE': 3}
    """
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")

    return {enum_member.name: enum_member.value for enum_member in list(enumclass)}
