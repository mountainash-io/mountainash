# Utils Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move all 5 utility modules from `mountainash-utils-dataclasses` into `mountainash.pydata` as plain functions, organized into mappers/, sanitizers/, and utils/ subdirectories.

**Architecture:** Each source utility class is refactored to a module of plain functions. Internal dependencies are rewired (e.g., `CollectionUtils.is_empty` → `is_empty` import). Egress files that imported from `mountainash_utils_dataclasses` are rewired to import from the new `pydata.mappers` location. Test skip guards for the optional external package are removed.

**Tech Stack:** Python 3.10+, pytest, universal_pathlib (for XSD stub), pydantic (already a dep)

**Source package:** `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/`

---

## File Structure

### New files to create

| File | Responsibility |
|------|---------------|
| `src/mountainash/pydata/utils/__init__.py` | Re-exports from collection_helpers and enum_helpers |
| `src/mountainash/pydata/utils/collection_helpers.py` | `is_empty()` function |
| `src/mountainash/pydata/utils/enum_helpers.py` | 16 enum introspection/validation functions |
| `src/mountainash/pydata/mappers/__init__.py` | Re-exports from dataclass_mapping and pydantic_mapping |
| `src/mountainash/pydata/mappers/dataclass_mapping.py` | 16 dataclass creation/introspection/mapping functions |
| `src/mountainash/pydata/mappers/pydantic_mapping.py` | 9 Pydantic model mapping functions |
| `src/mountainash/pydata/sanitizers/__init__.py` | Re-exports from xml_sanitizer |
| `src/mountainash/pydata/sanitizers/xml_sanitizer.py` | XML entity restoration + XSD validation stub |
| `tests/pydata/utils/__init__.py` | Test package marker |
| `tests/pydata/utils/test_collection_helpers.py` | Collection emptiness tests |
| `tests/pydata/utils/test_enum_helpers.py` | Enum utility tests |
| `tests/pydata/mappers/__init__.py` | Test package marker |
| `tests/pydata/mappers/test_dataclass_mapping.py` | Dataclass mapping tests (merged from 3 source files) |
| `tests/pydata/mappers/test_pydantic_mapping.py` | Pydantic mapping tests |
| `tests/pydata/sanitizers/__init__.py` | Test package marker |
| `tests/pydata/sanitizers/test_xml_sanitizer.py` | XML sanitizer tests |
| `tests/pydata/sanitizers/fixtures/__init__.py` | Test fixtures package marker |
| `tests/pydata/sanitizers/fixtures/xml_samples.py` | XML test sample data |

### Files to modify

| File | Change |
|------|--------|
| `src/mountainash/pydata/egress/egress_to_pythondata.py:15` | Replace `mountainash_utils_dataclasses` import with `pydata.mappers` |
| `src/mountainash/pydata/egress/egress_pydata_from_polars.py:283,354` | Replace runtime `mountainash_utils_dataclasses` imports with `pydata.mappers` |
| `tests/pydata/test_pydata_roundtrips.py:18-22` | Remove `HAS_UTILS_DATACLASSES` guard, remove skip decorators |
| `tests/pydata/test_egress_all.py:16-20` | Remove `HAS_UTILS_DATACLASSES` guard, remove skip decorators |
| `pyproject.toml:28-34` | Add `universal-pathlib>=0.2.0` to dependencies |

---

### Task 1: collection_helpers — implementation and tests

**Files:**
- Create: `src/mountainash/pydata/utils/__init__.py`
- Create: `src/mountainash/pydata/utils/collection_helpers.py`
- Create: `tests/pydata/utils/__init__.py`
- Create: `tests/pydata/utils/test_collection_helpers.py`

This is the foundation — `dataclass_mapping` depends on `is_empty`.

- [ ] **Step 1: Create the utils `__init__.py` package marker**

```python
# src/mountainash/pydata/utils/__init__.py
"""Low-level helpers for pydata operations."""
from __future__ import annotations

from mountainash.pydata.utils.collection_helpers import is_empty

__all__ = [
    "is_empty",
]
```

- [ ] **Step 2: Create `collection_helpers.py` with `is_empty` function**

```python
# src/mountainash/pydata/utils/collection_helpers.py
"""Container emptiness checking.

Provides a single function `is_empty` that checks whether a Python object
is an empty container (list, dict, set, tuple, etc.).  Strings are explicitly
excluded — an empty string returns False.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence, Set


def is_empty(obj: Any) -> bool:
    """Check if an object is an empty container.

    Checks if the object is a container type (Mapping, Sequence, Set) and
    whether it is empty. Strings are explicitly excluded and never considered
    empty containers.

    Args:
        obj: The object to check

    Returns:
        True if obj is an empty container (list, dict, set, tuple, etc.),
        False otherwise. Always returns False for strings and non-containers.

    Example:
        >>> is_empty([])       # True
        >>> is_empty({})       # True
        >>> is_empty("")       # False (strings excluded)
        >>> is_empty([1, 2])   # False
        >>> is_empty(None)     # False
        >>> is_empty(0)        # False
    """
    if isinstance(obj, str):
        return False  # Treat all strings as non-empty
    elif isinstance(obj, (Mapping, Sequence, Set)):
        return len(obj) == 0
    else:
        return False


__all__ = ["is_empty"]
```

- [ ] **Step 3: Create the test `__init__.py` package marker**

```python
# tests/pydata/utils/__init__.py
```

Empty file.

- [ ] **Step 4: Create `test_collection_helpers.py`**

```python
# tests/pydata/utils/test_collection_helpers.py
"""Tests for mountainash.pydata.utils.collection_helpers."""
from __future__ import annotations

import pytest

from mountainash.pydata.utils.collection_helpers import is_empty


# Parametrized data: (name, obj, expected)
test_data = [
    ("empty_list", [], True),
    ("empty_dict", {}, True),
    ("empty_set", set(), True),
    ("empty_tuple", (), True),
    ("empty_object", object(), False),
    ("empty_string", "", False),
    ("zero", 0, False),
    ("none", None, False),
    ("false", False, False),
    ("true", True, False),
    ("nonempty_list", ["A"], False),
    ("nonempty_dict1", {"A"}, False),
    ("nonempty_dict2", {"A": "A"}, False),
    ("nonempty_set", set("A"), False),
    ("nonempty_tuple", ("A",), False),
    ("nonempty_string", "A", False),
    ("nonempty_int", 10, False),
]


class TestIsEmpty:
    """Test the is_empty function."""

    @pytest.mark.parametrize("name, obj, expected", test_data)
    def test_parametrized(self, name, obj, expected):
        result = is_empty(obj)
        assert result == expected, f"Failed for {name}: expected {expected}, got {result}"

    def test_empty_list(self):
        assert is_empty([]) is True

    def test_nonempty_list(self):
        assert is_empty([1, 2, 3]) is False
        assert is_empty(["a"]) is False

    def test_empty_dict(self):
        assert is_empty({}) is True

    def test_nonempty_dict(self):
        assert is_empty({"key": "value"}) is False
        assert is_empty({1: 2}) is False

    def test_empty_set(self):
        assert is_empty(set()) is True

    def test_nonempty_set(self):
        assert is_empty({1, 2, 3}) is False
        assert is_empty({"a"}) is False

    def test_empty_tuple(self):
        assert is_empty(()) is True

    def test_nonempty_tuple(self):
        assert is_empty((1, 2, 3)) is False
        assert is_empty(("a",)) is False

    def test_strings_never_empty(self):
        assert is_empty("") is False
        assert is_empty("hello") is False
        assert is_empty(" ") is False

    def test_non_containers(self):
        assert is_empty(None) is False
        assert is_empty(0) is False
        assert is_empty(1) is False
        assert is_empty(True) is False
        assert is_empty(False) is False
        assert is_empty(object()) is False

    def test_nested_empty_containers(self):
        assert is_empty([[]]) is False
        assert is_empty([{}]) is False
        assert is_empty({"key": []}) is False


class TestIsEmptyEdgeCases:
    """Test edge cases for is_empty."""

    def test_custom_sequence(self):
        class CustomSequence:
            def __init__(self, items):
                self.items = items
            def __len__(self):
                return len(self.items)
            def __getitem__(self, index):
                return self.items[index]

        custom = CustomSequence([])
        assert is_empty(custom) is False

    def test_range_object(self):
        assert is_empty(range(0)) is True
        assert is_empty(range(5)) is False

    def test_bytes_and_bytearray(self):
        assert is_empty(b"") is True
        assert is_empty(b"hello") is False
        assert is_empty(bytearray()) is True
        assert is_empty(bytearray(b"hello")) is False
```

- [ ] **Step 5: Run tests to verify**

Run: `hatch run test:test-target-quick tests/pydata/utils/test_collection_helpers.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/pydata/utils/__init__.py src/mountainash/pydata/utils/collection_helpers.py tests/pydata/utils/__init__.py tests/pydata/utils/test_collection_helpers.py
git commit -m "feat(pydata): add collection_helpers — is_empty function from utils-dataclasses"
```

---

### Task 2: enum_helpers — implementation and tests

**Files:**
- Create: `src/mountainash/pydata/utils/enum_helpers.py`
- Modify: `src/mountainash/pydata/utils/__init__.py`
- Create: `tests/pydata/utils/test_enum_helpers.py`

- [ ] **Step 1: Create `enum_helpers.py`**

Copy the entire content of `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/src/mountainash_utils_dataclasses/enum_utils.py` into `src/mountainash/pydata/utils/enum_helpers.py`, then refactor:

1. Remove the `class EnumUtils:` wrapper
2. Convert all `@classmethod` methods to plain functions (remove `cls` parameter)
3. Update all internal `cls.method()` calls to plain `method()` calls
4. Add module docstring and `__all__`

The resulting file should have these functions:
- `is_enum(classtype)`
- `member_identities(enumclass)`
- `member_names(enumclass)`
- `member_values(enumclass)`
- `is_valid_member_name(enumclass, name)`
- `is_valid_member_value(enumclass, value)`
- `is_valid_member_identity(enumclass, instance)`
- `find_member(enumclass, value)`
- `find_member_name(enumclass, value)`
- `find_all_member_names(enumclass, value)`
- `find_member_names_dict(enumclass, value)`
- `get_enum_attribute_names(enumclass)`
- `get_enum_values(enumclass)`
- `get_enum_values_set(enumclass)`
- `get_enum_values_tuple(enumclass)`
- `get_enum_values_dict(enumclass)`

Key internal call rewiring:
- `cls.is_enum(...)` → `is_enum(...)`
- `cls.find_member(...)` → `find_member(...)`
- `cls.get_dataclass_field_list(...)` → `get_dataclass_field_list(...)`

```python
# src/mountainash/pydata/utils/enum_helpers.py
"""Enum introspection, validation, and extraction utilities.

Provides functions for working with Python Enum types: extracting values,
names, and identities; validating membership; resolving aliases; and
converting to various collection types.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Set, Tuple, Type


def is_enum(classtype: Type) -> bool:
    """Check if a class is an Enum."""
    try:
        return issubclass(classtype, Enum)
    except Exception:
        return False


def member_identities(enumclass: Type[Enum]) -> Set[Enum]:
    """Get all enum member instances (identities)."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    return set(enumclass.__members__.values())


def member_names(enumclass: Type[Enum]) -> Set[str]:
    """Get all enum member names."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    return set(enumclass.__members__.keys())


def member_values(enumclass: Type[Enum]) -> Set[Any]:
    """Get all enum member values (primitives)."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    return {member.value for member in enumclass.__members__.values()}


def is_valid_member_name(enumclass: Type[Enum], name: str) -> bool:
    """Check if a name is a valid enum member name."""
    if not is_enum(enumclass):
        return False
    try:
        return name in enumclass.__members__
    except TypeError:
        return False


def is_valid_member_value(enumclass: Type[Enum], value: Any) -> bool:
    """Check if a value is a valid enum member value (primitive)."""
    if not is_enum(enumclass):
        return False
    try:
        return value in {member.value for member in enumclass.__members__.values()}
    except TypeError:
        for member in enumclass.__members__.values():
            if member.value == value:
                return True
        return False


def is_valid_member_identity(enumclass: Type[Enum], instance: Any) -> bool:
    """Check if an instance is a valid enum member (identity check)."""
    if not is_enum(enumclass):
        return False
    return instance in enumclass.__members__.values()


def find_member(enumclass: Type[Enum], value: Any) -> Any:
    """Find enum member by value (returns canonical member for aliases)."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    try:
        return enumclass(value)
    except (ValueError, KeyError):
        return None


def find_member_name(enumclass: Type[Enum], value: Any) -> Any:
    """Find canonical member name by value."""
    member = find_member(enumclass, value)
    return member.name if member is not None else None


def find_all_member_names(enumclass: Type[Enum], value: Any) -> Set[str]:
    """Find all member names with the given value (including aliases)."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    matching_names = set()
    try:
        for name, member in enumclass.__members__.items():
            if member.value == value:
                matching_names.add(name)
    except TypeError:
        for name, member in enumclass.__members__.items():
            try:
                if member.value == value:
                    matching_names.add(name)
            except Exception:
                continue
    return matching_names


def find_member_names_dict(enumclass: Type[Enum], value: Any) -> Dict[str, Enum]:
    """Find all member names mapped to their member for the given value."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    matching_dict = {}
    try:
        for name, member in enumclass.__members__.items():
            if member.value == value:
                matching_dict[name] = member
    except TypeError:
        for name, member in enumclass.__members__.items():
            try:
                if member.value == value:
                    matching_dict[name] = member
            except Exception:
                continue
    return matching_dict


def get_enum_attribute_names(enumclass: Type[Enum]) -> List[str]:
    """Get a list of all attribute names from an Enum class."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    return [enum_member.name for enum_member in list(enumclass)]


def get_enum_values(enumclass: Type[Enum]) -> List[Any]:
    """Get a list of all values from an Enum class."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    return [enum_member.value for enum_member in list(enumclass)]


def get_enum_values_set(enumclass: Type[Enum]) -> Set[Any]:
    """Get a set of all values from an Enum class."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    return {enum_member.value for enum_member in list(enumclass)}


def get_enum_values_tuple(enumclass: Type[Enum]) -> Tuple[Any, ...]:
    """Get a tuple of all values from an Enum class."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    return tuple([enum_member.value for enum_member in list(enumclass)])


def get_enum_values_dict(enumclass: Type[Enum]) -> Dict[str, Any]:
    """Get a dict of {name: value} pairs from an Enum class."""
    if not is_enum(enumclass):
        raise ValueError("Class is not an Enum")
    return {enum_member.name: enum_member.value for enum_member in list(enumclass)}


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
```

- [ ] **Step 2: Update `utils/__init__.py` to re-export enum functions**

```python
# src/mountainash/pydata/utils/__init__.py
"""Low-level helpers for pydata operations."""
from __future__ import annotations

from mountainash.pydata.utils.collection_helpers import is_empty
from mountainash.pydata.utils.enum_helpers import (
    is_enum,
    member_identities,
    member_names,
    member_values,
    is_valid_member_name,
    is_valid_member_value,
    is_valid_member_identity,
    find_member,
    find_member_name,
    find_all_member_names,
    find_member_names_dict,
    get_enum_attribute_names,
    get_enum_values,
    get_enum_values_set,
    get_enum_values_tuple,
    get_enum_values_dict,
)

__all__ = [
    "is_empty",
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
```

- [ ] **Step 3: Create `test_enum_helpers.py`**

Copy the entire content of `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/tests/test_enum_utils.py` (1190 lines) into `tests/pydata/utils/test_enum_helpers.py`, then find-and-replace:

1. Replace `from mountainash_utils_dataclasses import EnumUtils` with `from mountainash.pydata.utils.enum_helpers import (is_enum, member_identities, member_names, member_values, is_valid_member_name, is_valid_member_value, is_valid_member_identity, find_member, find_member_name, find_all_member_names, find_member_names_dict, get_enum_attribute_names, get_enum_values, get_enum_values_set, get_enum_values_tuple, get_enum_values_dict)`
2. Replace all `EnumUtils.method_name(` with `method_name(` (drop the class prefix)

Also incorporate the enum error-condition tests from `test_error_conditions.py`:
- `test_is_enum_with_type_error` → `assert is_enum(None) is False`
- `test_enum_methods_error_handling` → the 5 `pytest.raises(ValueError)` calls with function names instead of `EnumUtils.method()`

- [ ] **Step 4: Run tests to verify**

Run: `hatch run test:test-target-quick tests/pydata/utils/ -v`
Expected: All tests PASS (collection_helpers + enum_helpers)

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/pydata/utils/enum_helpers.py src/mountainash/pydata/utils/__init__.py tests/pydata/utils/test_enum_helpers.py
git commit -m "feat(pydata): add enum_helpers — 16 enum introspection functions from utils-dataclasses"
```

---

### Task 3: dataclass_mapping — implementation and tests

**Files:**
- Create: `src/mountainash/pydata/mappers/__init__.py`
- Create: `src/mountainash/pydata/mappers/dataclass_mapping.py`
- Create: `tests/pydata/mappers/__init__.py`
- Create: `tests/pydata/mappers/test_dataclass_mapping.py`

- [ ] **Step 1: Create the mappers `__init__.py`**

```python
# src/mountainash/pydata/mappers/__init__.py
"""Python data <-> typed Python structure mapping.

Provides functions for converting between Python data structures (dicts, tuples,
named tuples) and typed structures (dataclasses, Pydantic models).
"""
from __future__ import annotations

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
```

- [ ] **Step 2: Create `dataclass_mapping.py`**

Copy the entire content of `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/src/mountainash_utils_dataclasses/dataclass_utils.py` into `src/mountainash/pydata/mappers/dataclass_mapping.py`, then refactor:

1. Remove the `class DataclassUtils:` wrapper
2. Convert all `@classmethod` methods to plain functions (remove `cls` parameter)
3. Replace `from .collection_utils import CollectionUtils` with `from mountainash.pydata.utils.collection_helpers import is_empty`
4. Replace all `CollectionUtils.is_empty(...)` with `is_empty(...)`
5. Replace all internal `cls.method()` calls with plain `method()` calls:
   - `cls.get_dataclass_field_list(...)` → `get_dataclass_field_list(...)`
   - `cls.get_field_defaults(...)` → `get_field_defaults(...)`
   - `cls.is_dataclass(...)` → `is_dataclass(...)`
   - `cls.is_dataclass_object_all_none(...)` → `is_dataclass_object_all_none(...)`
   - `cls.create_all_none_dataclass(...)` → `create_all_none_dataclass(...)`
   - `cls.create_dataclass_with_defaults(...)` → `create_dataclass_with_defaults(...)`
   - `cls._apply_field_defaults(...)` → `_apply_field_defaults(...)`
   - `cls.map_dict_to_dataclass(...)` → `map_dict_to_dataclass(...)`
   - `cls.map_tuple_to_dataclass(...)` → `map_tuple_to_dataclass(...)`
   - `cls.map_namedtuple_to_dataclass(...)` → `map_namedtuple_to_dataclass(...)`
6. Add module docstring and `__all__`

- [ ] **Step 3: Create test `__init__.py`**

```python
# tests/pydata/mappers/__init__.py
```

Empty file.

- [ ] **Step 4: Create `test_dataclass_mapping.py`**

Merge tests from these three source files into one:
- `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/tests/test_dataclass_utils.py` (235 lines)
- `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/tests/test_dataclass_structure_mapping.py` (508 lines)
- `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/tests/test_new_dataclass_utils.py` (283 lines)

Also incorporate the dataclass error-condition tests from `test_error_conditions.py` (lines 25-82, 111-140).

For all merged content:
1. Replace `from mountainash_utils_dataclasses import DataclassUtils` with individual function imports from `mountainash.pydata.mappers.dataclass_mapping`
2. Replace all `DataclassUtils.method_name(` with `method_name(`
3. Keep all fixture-defined dataclasses inline (each source file defines its own) — no conftest dependency needed
4. Remove any `from pytest_check import check` and replace `with check:` blocks with direct assertions

The import block should be:
```python
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
```

- [ ] **Step 5: Run tests to verify**

Run: `hatch run test:test-target-quick tests/pydata/mappers/test_dataclass_mapping.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/pydata/mappers/__init__.py src/mountainash/pydata/mappers/dataclass_mapping.py tests/pydata/mappers/__init__.py tests/pydata/mappers/test_dataclass_mapping.py
git commit -m "feat(pydata): add dataclass_mapping — 16 dataclass mapping functions from utils-dataclasses"
```

---

### Task 4: pydantic_mapping — implementation and tests

**Files:**
- Create: `src/mountainash/pydata/mappers/pydantic_mapping.py`
- Modify: `src/mountainash/pydata/mappers/__init__.py`
- Create: `tests/pydata/mappers/test_pydantic_mapping.py`

- [ ] **Step 1: Create `pydantic_mapping.py`**

Copy the entire content of `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/src/mountainash_utils_dataclasses/pydantic_utils.py` into `src/mountainash/pydata/mappers/pydantic_mapping.py`, then refactor:

1. Remove the `class PydanticUtils:` wrapper
2. Convert `@staticmethod` and `@classmethod` methods to plain functions (remove `cls` parameter)
3. Replace all internal `cls.method()` calls with plain `method()` calls:
   - `cls._check_pydantic_available()` → `_check_pydantic_available()`
   - `cls._get_pydantic_field_names(...)` → `_get_pydantic_field_names(...)`
   - `cls.map_dict_to_pydantic(...)` → `map_dict_to_pydantic(...)`
   - `cls.map_tuple_to_pydantic(...)` → `map_tuple_to_pydantic(...)`
   - `cls.map_namedtuple_to_pydantic(...)` → `map_namedtuple_to_pydantic(...)`
4. Add module docstring and `__all__`

- [ ] **Step 2: Update `mappers/__init__.py` to re-export pydantic functions**

Add after the existing dataclass imports:

```python
from mountainash.pydata.mappers.pydantic_mapping import (
    map_dict_to_pydantic,
    map_tuple_to_pydantic,
    map_namedtuple_to_pydantic,
    map_list_of_dicts_to_pydantic,
    map_list_of_tuples_to_pydantic,
    map_list_of_namedtuples_to_pydantic,
)
```

And add to `__all__`:
```python
    "map_dict_to_pydantic",
    "map_tuple_to_pydantic",
    "map_namedtuple_to_pydantic",
    "map_list_of_dicts_to_pydantic",
    "map_list_of_tuples_to_pydantic",
    "map_list_of_namedtuples_to_pydantic",
```

- [ ] **Step 3: Create `test_pydantic_mapping.py`**

Copy the entire content of `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/tests/test_pydantic_utils.py` (380 lines) into `tests/pydata/mappers/test_pydantic_mapping.py`, then:

1. Replace `from mountainash_utils_dataclasses import PydanticUtils` with individual function imports from `mountainash.pydata.mappers.pydantic_mapping`
2. Replace all `PydanticUtils.method_name(` with `method_name(`
3. Also replace `PydanticUtils._is_pydantic_model(` with `_is_pydantic_model(` and `PydanticUtils._get_pydantic_field_names(` with `_get_pydantic_field_names(`

The import block should be:
```python
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
```

- [ ] **Step 4: Run tests to verify**

Run: `hatch run test:test-target-quick tests/pydata/mappers/ -v`
Expected: All tests PASS (dataclass_mapping + pydantic_mapping)

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/pydata/mappers/pydantic_mapping.py src/mountainash/pydata/mappers/__init__.py tests/pydata/mappers/test_pydantic_mapping.py
git commit -m "feat(pydata): add pydantic_mapping — 9 Pydantic model mapping functions from utils-dataclasses"
```

---

### Task 5: xml_sanitizer — implementation and tests

**Files:**
- Create: `src/mountainash/pydata/sanitizers/__init__.py`
- Create: `src/mountainash/pydata/sanitizers/xml_sanitizer.py`
- Create: `tests/pydata/sanitizers/__init__.py`
- Create: `tests/pydata/sanitizers/fixtures/__init__.py`
- Create: `tests/pydata/sanitizers/fixtures/xml_samples.py`
- Create: `tests/pydata/sanitizers/test_xml_sanitizer.py`
- Modify: `pyproject.toml` — add `universal-pathlib` dependency

- [ ] **Step 1: Create the sanitizers `__init__.py`**

```python
# src/mountainash/pydata/sanitizers/__init__.py
"""Data cleansing and pre/post-processing for the pydata pipeline."""
from __future__ import annotations

from mountainash.pydata.sanitizers.xml_sanitizer import (
    restore_special_characters,
    validate_file_xsd,
)

__all__ = [
    "restore_special_characters",
    "validate_file_xsd",
]
```

- [ ] **Step 2: Create `xml_sanitizer.py`**

Copy the entire content of `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/src/mountainash_utils_dataclasses/xml_utils.py` into `src/mountainash/pydata/sanitizers/xml_sanitizer.py`, then refactor:

1. Remove the `class XmlUtils:` wrapper
2. Convert all `@staticmethod` methods to plain functions
3. Replace all internal `XmlUtils.restore_special_characters(...)` with `restore_special_characters(...)`
4. Replace all `XmlUtils._restore_special_characters_str(...)` etc. with `_restore_special_characters_str(...)`
5. Keep the `UPath` import from `upath`
6. The `validate_file_xsd` stub becomes a plain function (remove `self` parameter)
7. Add module docstring and `__all__`

```python
# src/mountainash/pydata/sanitizers/xml_sanitizer.py
"""XML data sanitization utilities.

Provides recursive XML entity restoration for strings, lists, dicts, and sets,
plus a stub for XSD validation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set

from upath import UPath


def _restore_special_characters_str(value: str) -> str:
    """Restore XML special characters in a string."""
    special_chars: list[str] = ["&lt;", "&gt;", "&amp;", "&apos;", "&quot;"]
    if any(char in value for char in special_chars):
        special_chars_dict: dict[str, str] = {
            "&lt;": "<",
            "&gt;": ">",
            "&amp;": "&",
            "&apos;": "'",
            "&quot;": "\"",
        }
        for encoded, char in special_chars_dict.items():
            value = value.replace(encoded, char)
    return value


def _restore_special_characters_list(value: List[Any]) -> List[Any]:
    """Restore XML entities in each element of a list."""
    return [restore_special_characters(v) for v in value]


def _restore_special_characters_dict(value: Dict[str, Any]) -> Dict[Any, Any]:
    """Restore XML entities in keys and values of a dictionary."""
    return {
        restore_special_characters(k): restore_special_characters(v)
        for k, v in value.items()
    }


def _restore_special_characters_set(value: Set[Any]) -> Set[Any]:
    """Restore XML entities in each element of a set."""
    new_set: set = set()
    for k in value:
        restored: Any = restore_special_characters(k)
        try:
            hash(restored)
            new_set.add(restored)
        except TypeError:
            raise TypeError(f"Set item {restored} is not hashable. The set was not valid")
    return new_set


def restore_special_characters(value: Any) -> Any:
    """Restore XML special characters in a value.

    Detects the type of the input value and calls the appropriate
    restoration helper. Supported types: str, list, dict, set.
    Other types are returned unchanged.
    """
    if isinstance(value, str):
        return _restore_special_characters_str(value)
    elif isinstance(value, list):
        return _restore_special_characters_list(value)
    elif isinstance(value, dict):
        return _restore_special_characters_dict(value)
    elif isinstance(value, set):
        return _restore_special_characters_set(value)
    else:
        return value


def validate_file_xsd(file_path: UPath | str, xsd_path: UPath | str) -> bool:
    """Validate an XML file against an XSD schema.

    Not yet implemented.
    """
    pass


__all__ = [
    "restore_special_characters",
    "validate_file_xsd",
]
```

- [ ] **Step 3: Add `universal-pathlib` to pyproject.toml dependencies**

In `pyproject.toml`, change:
```toml
dependencies = [
    "polars>=1.35.1",
    "narwhals>=1.0.0",
    "pydantic>=2.0.0",
    "typing_extensions>=4.0.0",
    "lazy_loader>=0.3",
]
```
to:
```toml
dependencies = [
    "polars>=1.35.1",
    "narwhals>=1.0.0",
    "pydantic>=2.0.0",
    "typing_extensions>=4.0.0",
    "lazy_loader>=0.3",
    "universal-pathlib>=0.2.0",
]
```

- [ ] **Step 4: Create test fixtures**

```python
# tests/pydata/sanitizers/__init__.py
```

Empty file.

```python
# tests/pydata/sanitizers/fixtures/__init__.py
```

Empty file.

Copy `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/tests/fixtures/xml_samples.py` verbatim to `tests/pydata/sanitizers/fixtures/xml_samples.py`. No changes needed — it contains only data, no imports from the utils package.

- [ ] **Step 5: Create `test_xml_sanitizer.py`**

Copy the entire content of `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/tests/test_xml_utils.py` (219 lines) into `tests/pydata/sanitizers/test_xml_sanitizer.py`, then:

1. Replace `from mountainash_utils_dataclasses import XmlUtils` with `from mountainash.pydata.sanitizers.xml_sanitizer import restore_special_characters, validate_file_xsd`
2. Replace all `XmlUtils.restore_special_characters(...)` with `restore_special_characters(...)`
3. Replace `XmlUtils()` instance creation in XSD tests with direct `validate_file_xsd(...)` calls
4. Replace `utils.valiate_file_xsd(...)` with `validate_file_xsd(...)`

Also copy the conftest fixtures that the xml tests use. Create a conftest at `tests/pydata/sanitizers/conftest.py` containing the `xml_entity_samples`, `xml_entities_mapping`, `edge_case_data`, and `error_case_data` fixtures from `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-dataclasses/tests/conftest.py` (lines 53-175 only — the XML-related fixtures).

- [ ] **Step 6: Run tests to verify**

Run: `hatch run test:test-target-quick tests/pydata/sanitizers/ -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/mountainash/pydata/sanitizers/ tests/pydata/sanitizers/ pyproject.toml
git commit -m "feat(pydata): add xml_sanitizer — XML entity restoration from utils-dataclasses"
```

---

### Task 6: Rewire egress imports

**Files:**
- Modify: `src/mountainash/pydata/egress/egress_to_pythondata.py:15`
- Modify: `src/mountainash/pydata/egress/egress_pydata_from_polars.py:282-288,352-359`
- Modify: `tests/pydata/test_pydata_roundtrips.py:18-22,114-116,137`
- Modify: `tests/pydata/test_egress_all.py:16-20,290-292`

- [ ] **Step 1: Rewire `egress_to_pythondata.py`**

Replace line 15:
```python
from mountainash_utils_dataclasses import DataclassUtils, PydanticUtils
```
with:
```python
from mountainash.pydata.mappers.dataclass_mapping import map_list_of_namedtuples_to_dataclasses
from mountainash.pydata.mappers.pydantic_mapping import map_list_of_namedtuples_to_pydantic
```

Replace line 209:
```python
        return DataclassUtils.map_list_of_namedtuples_to_dataclasses(
```
with:
```python
        return map_list_of_namedtuples_to_dataclasses(
```

Replace line 288:
```python
        return PydanticUtils.map_list_of_namedtuples_to_pydantic(
```
with:
```python
        return map_list_of_namedtuples_to_pydantic(
```

- [ ] **Step 2: Rewire `egress_pydata_from_polars.py`**

Replace lines 282-288 (dataclass method's try/except import):
```python
        try:
            from mountainash_utils_dataclasses import DataclassUtils
        except ImportError as e:
            raise ImportError(
                "mountainash-utils-dataclasses is required for dataclass conversion. "
                "Install it with: pip install mountainash-utils-dataclasses"
            ) from e
```
with:
```python
        from mountainash.pydata.mappers.dataclass_mapping import map_list_of_namedtuples_to_dataclasses
```

Replace line 324:
```python
        return DataclassUtils.map_list_of_namedtuples_to_dataclasses(
```
with:
```python
        return map_list_of_namedtuples_to_dataclasses(
```

Replace lines 353-359 (pydantic method's try/except import):
```python
        try:
            from mountainash_utils_dataclasses import PydanticUtils
        except ImportError as e:
            raise ImportError(
                "mountainash-utils-dataclasses is required for Pydantic conversion. "
                "Install it with: pip install mountainash-utils-dataclasses"
            ) from e
```
with:
```python
        from mountainash.pydata.mappers.pydantic_mapping import map_list_of_namedtuples_to_pydantic
```

Replace line 395:
```python
        return PydanticUtils.map_list_of_namedtuples_to_pydantic(
```
with:
```python
        return map_list_of_namedtuples_to_pydantic(
```

- [ ] **Step 3: Remove skip guards from `test_pydata_roundtrips.py`**

Remove lines 18-22:
```python
try:
    from mountainash_utils_dataclasses import DataclassUtils  # noqa: F401
    HAS_UTILS_DATACLASSES = True
except ImportError:
    HAS_UTILS_DATACLASSES = False
```

Remove or update the `@pytest.mark.skipif` decorators that reference `HAS_UTILS_DATACLASSES`:
- Line 114: Remove `@pytest.mark.skipif(not HAS_UTILS_DATACLASSES, reason="...")` 
- Line 137: Change `not HAS_PYDANTIC or not HAS_UTILS_DATACLASSES` to just `not HAS_PYDANTIC`

- [ ] **Step 4: Remove skip guards from `test_egress_all.py`**

Remove lines 16-20:
```python
try:
    from mountainash_utils_dataclasses import DataclassUtils  # noqa: F401
    HAS_UTILS_DATACLASSES = True
except ImportError:
    HAS_UTILS_DATACLASSES = False
```

Remove the `@pytest.mark.skipif` decorator at line 290-292 that references `HAS_UTILS_DATACLASSES`.

- [ ] **Step 5: Run all pydata tests to verify**

Run: `hatch run test:test-target-quick tests/pydata/ -v`
Expected: All tests PASS

- [ ] **Step 6: Run the full test suite to verify nothing else broke**

Run: `hatch run test:test-quick`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/mountainash/pydata/egress/egress_to_pythondata.py src/mountainash/pydata/egress/egress_pydata_from_polars.py tests/pydata/test_pydata_roundtrips.py tests/pydata/test_egress_all.py
git commit -m "refactor(pydata): rewire egress imports from mountainash_utils_dataclasses to pydata.mappers"
```
