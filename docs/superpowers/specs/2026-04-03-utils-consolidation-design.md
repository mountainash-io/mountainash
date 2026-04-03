# Utils Consolidation Design

> **Date:** 2026-04-03
> **Status:** Approved

## Goal

Consolidate all 5 modules from `mountainash-utils-dataclasses` into `mountainash.pydata`, refactored from stateless utility classes to plain module-level functions, organized by concern within the data pipeline.

## Rationale

`mountainash-utils-dataclasses` has been a dumping ground for utilities that are too small to standalone as packages. These utilities are all Python-data-level operations — structure mapping, value validation, data sanitization, and collection inspection — that serve the same concerns as mountainash's pydata module: preparing, validating, and converting Python data.

Rather than maintaining a separate package for these, they belong inside mountainash alongside pydata, where they can integrate with typespec, conform, and the ingress/egress pipeline.

## Source Inventory

| Source module | Functions | Current usage in mountainash-expressions |
|---------------|-----------|------------------------------------------|
| `dataclass_utils.py` | 15 functions: creation, introspection, dict/tuple/namedtuple mapping | Egress: `map_list_of_namedtuples_to_dataclasses()` |
| `pydantic_utils.py` | 9 functions: mirrors dataclass API for Pydantic models | Egress: `map_list_of_namedtuples_to_pydantic()` |
| `enum_utils.py` | 16 functions: introspection, validation, alias resolution | Not yet used directly |
| `collection_utils.py` | 1 function: container emptiness checking | Used internally by dataclass_utils |
| `xml_utils.py` | 5 functions: XML entity restoration + XSD validation stub | Not yet used directly |

## Target Package Structure

```
pydata/
├── __init__.py           # Updated re-exports
├── constants.py          # (existing)
├── ingress/              # (existing) Python -> DataFrame
├── egress/               # (existing) DataFrame -> Python
├── mappers/              # Python data <-> typed Python structures
│   ├── __init__.py       # Re-exports key functions
│   ├── dataclass_mapping.py    # 15 functions from DataclassUtils
│   └── pydantic_mapping.py     # 9 functions from PydanticUtils
├── sanitizers/           # Data cleansing, pre/post-processing
│   ├── __init__.py       # Re-exports key functions
│   └── xml_sanitizer.py        # 5 functions from XmlUtils + XSD stub
└── utils/                # Low-level helpers for pydata operations
    ├── __init__.py       # Re-exports key functions
    ├── collection_helpers.py   # 1 function from CollectionUtils
    └── enum_helpers.py         # 16 functions from EnumUtils
```

## Refactoring: Classes to Functions

All 5 source modules use stateless `@classmethod`-only classes as namespaces. These are refactored to plain module-level functions, consistent with mountainash's style (typespec, conform, etc. are all plain functions).

### dataclass_mapping.py

Functions (all prefixed signatures unchanged, just no `cls` parameter):

**Creation:**
- `create_all_none_dataclass(dataclass_type)` — Instance with all fields None
- `create_dataclass_with_defaults(dataclass_type)` — Instance using field defaults

**Introspection:**
- `get_dataclass_field_list(classtype)` — Field names
- `get_dataclass_field_types(classtype)` — Field name -> type mapping
- `get_field_defaults(classtype)` — Field name -> default value mapping
- `get_required_fields(classtype)` — Fields without defaults
- `get_optional_fields(classtype)` — Fields with defaults
- `is_dataclass(classtype)` — Type check
- `is_dataclass_object_all_none(obj, consider_empty_as_none=True)` — Recursive null check

**Single-record mapping:**
- `map_dict_to_dataclass(record, dataclass_type, mapping=None, apply_defaults=False)`
- `map_tuple_to_dataclass(record, dataclass_type, field_order=None, apply_defaults=False)`
- `map_namedtuple_to_dataclass(record, dataclass_type, mapping=None, apply_defaults=False)`

**Batch mapping:**
- `map_list_of_dicts_to_dataclasses(records, dataclass_type, mapping=None, apply_defaults=False)`
- `map_list_of_tuples_to_dataclasses(records, dataclass_type, field_order=None, apply_defaults=False)`
- `map_list_of_namedtuples_to_dataclasses(records, dataclass_type, mapping=None, apply_defaults=False)`

**Internal helper:**
- `_apply_field_defaults(dataclass_type, values)` — Module-private helper

### pydantic_mapping.py

Functions:

**Internal helpers:**
- `_check_pydantic_available()` — Import guard
- `_is_pydantic_model(model_class)` — v1/v2 detection
- `_get_pydantic_field_names(model_class)` — v1/v2 field extraction

**Single-record mapping:**
- `map_dict_to_pydantic(record, model_class, mapping=None)`
- `map_tuple_to_pydantic(record, model_class, field_order=None)`
- `map_namedtuple_to_pydantic(record, model_class, mapping=None)`

**Batch mapping:**
- `map_list_of_dicts_to_pydantic(records, model_class, mapping=None)`
- `map_list_of_tuples_to_pydantic(records, model_class, field_order=None)`
- `map_list_of_namedtuples_to_pydantic(records, model_class, mapping=None)`

### collection_helpers.py

- `is_empty(obj)` — Check if object is an empty container (strings excluded)

### enum_helpers.py

**Type checking:**
- `is_enum(classtype)`

**Member extraction:**
- `member_identities(enumclass)` — Set of enum instances
- `member_names(enumclass)` — Set of name strings
- `member_values(enumclass)` — Set of primitive values

**Validation:**
- `is_valid_member_name(enumclass, name)`
- `is_valid_member_value(enumclass, value)`
- `is_valid_member_identity(enumclass, instance)`

**Lookup (alias-aware):**
- `find_member(enumclass, value)` — Canonical member by value
- `find_member_name(enumclass, value)` — Canonical name by value
- `find_all_member_names(enumclass, value)` — All names including aliases
- `find_member_names_dict(enumclass, value)` — {name: member} dict

**Backward-compatible extraction:**
- `get_enum_attribute_names(enumclass)` — Names as list
- `get_enum_values(enumclass)` — Values as list
- `get_enum_values_set(enumclass)` — Values as set
- `get_enum_values_tuple(enumclass)` — Values as tuple
- `get_enum_values_dict(enumclass)` — {name: value} dict

### xml_sanitizer.py

- `restore_special_characters(value)` — Type-aware recursive XML entity restoration
- `_restore_special_characters_str(value)` — String restoration
- `_restore_special_characters_list(value)` — List restoration
- `_restore_special_characters_dict(value)` — Dict restoration
- `_restore_special_characters_set(value)` — Set restoration
- `validate_file_xsd(file_path, xsd_path)` — Stub (not yet implemented)

## Dependencies

- `universal_pathlib` added to pyproject.toml (required by xml_sanitizer XSD validation stub)
- `pydantic` already a dependency
- No other new external dependencies

## Internal Dependency Rewiring

- `dataclass_mapping.py` imports `is_empty` from `pydata.utils.collection_helpers` (was `CollectionUtils.is_empty`)
- Egress files (`egress_to_pythondata.py`, `egress_pydata_from_polars.py`) updated to import from `pydata.mappers` instead of `mountainash_utils_dataclasses`
- Test skip guards removed (functions are now always available — no optional external package)

## Tests

All existing tests from `mountainash-utils-dataclasses/tests/` move to `tests/pydata/` under matching subdirectories:

| Source test | Target test |
|-------------|-------------|
| `test_dataclass_utils.py` | `tests/pydata/mappers/test_dataclass_mapping.py` |
| `test_new_dataclass_utils.py` | Merged into `tests/pydata/mappers/test_dataclass_mapping.py` |
| `test_dataclass_structure_mapping.py` | Merged into `tests/pydata/mappers/test_dataclass_mapping.py` |
| `test_pydantic_utils.py` | `tests/pydata/mappers/test_pydantic_mapping.py` |
| `test_container_utils.py` | `tests/pydata/utils/test_collection_helpers.py` |
| `test_enum_utils.py` | `tests/pydata/utils/test_enum_helpers.py` |
| `test_xml_utils.py` | `tests/pydata/sanitizers/test_xml_sanitizer.py` |
| `test_error_conditions.py` | Distributed into relevant test files above |
| `conftest.py` + `fixtures/xml_samples.py` | `tests/pydata/conftest.py` + `tests/pydata/sanitizers/fixtures/xml_samples.py` |

Test content updated: `DataclassUtils.method()` calls become `method()` function calls with updated imports.

## Scope Boundaries

**In scope:**
- Move all 5 modules into pydata with function refactoring
- Rewire egress imports
- Move and update all tests
- Update pyproject.toml dependencies

**Out of scope:**
- Updating other mountainash packages that import from mountainash-utils-dataclasses (handled separately)
- Deprecating or archiving mountainash-utils-dataclasses
- Integrating enum_helpers with TypeSpec FieldConstraints.enum (future work)
- Implementing XSD/JSON Schema validation (future work)

## Future Considerations

- **Schema validation in sanitizers (PROPOSED):** Add XSD and JSON Schema validation to `pydata/sanitizers/`, connecting to TypeSpec for schema-aware validation pipelines. This would allow validating incoming XML/JSON data against formal schemas before ingress, and validating outgoing data before egress.
- **Enum integration with TypeSpec:** enum_helpers could integrate with `FieldConstraints.enum` / `enum_weights` for runtime validation of categorical DataFrame columns against their TypeSpec-declared valid values.
- **Additional sanitizers:** The sanitizers submodule could grow to handle other data cleansing patterns — HTML entity decoding, Unicode normalization, whitespace trimming — as reusable pipeline components.
