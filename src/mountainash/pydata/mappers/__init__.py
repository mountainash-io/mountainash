"""Python data <-> typed Python structure mapping."""
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
from mountainash.pydata.mappers.pydantic_mapping import (
    map_dict_to_pydantic,
    map_tuple_to_pydantic,
    map_namedtuple_to_pydantic,
    map_list_of_dicts_to_pydantic,
    map_list_of_tuples_to_pydantic,
    map_list_of_namedtuples_to_pydantic,
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
    "map_dict_to_pydantic",
    "map_tuple_to_pydantic",
    "map_namedtuple_to_pydantic",
    "map_list_of_dicts_to_pydantic",
    "map_list_of_tuples_to_pydantic",
    "map_list_of_namedtuples_to_pydantic",
]
