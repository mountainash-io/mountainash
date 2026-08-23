"""
TypeSpec — Core data classes for schema definition.

Replaces TableSchema, SchemaField, and SchemaDiff from the old schema module.

This module is backend-agnostic and has ZERO imports of DataFrame libraries,
ensuring fast imports and true portability.

Key Features:
- Full Frictionless Table Schema compliance (v1.0)
- rename_from for column aliasing (source_name property)
- null_fill for default null replacement
- Schema comparison and diff utilities
- Round-trip serialization (dict <-> Python objects)
- Lazy frictionless import/export (Task 3 will provide frictionless.py)

Reference: https://specs.frictionlessdata.io/table-schema/
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from mountainash.typespec.errors import (
    IncompatibleFieldPropertiesError,
    InvalidKeyShapeError,
)
from mountainash.typespec.universal_types import UniversalType, parse_universal


@dataclass
class LabeledValue:
    """A value with an optional human-readable label.

    Shared typed shape for Frictionless v2's missingValues and categories
    labeled-object forms. ``value``'s Python type follows the property that
    carries it: always str for missing values (Frictionless requires
    string-typed sentinels so comparison happens before casting); the
    field's declared type for categories (e.g. int for an integer field).
    """

    value: Any
    label: Optional[str] = None


MissingValue = Union[str, LabeledValue]


def _validate_key_shape(value: Any, label: str) -> None:
    """Module-private helper shared by TypeSpec, ForeignKey, and
    ForeignKeyReference — every key-shaped field validates through this one
    function. Raises InvalidKeyShapeError unless ``value`` is a list[str]."""
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise InvalidKeyShapeError(label, value, "list[str]")


@dataclass
class FieldConstraints:
    """Constraints for a schema field (Frictionless Table Schema compliant)."""

    required: bool = False
    unique: bool = False
    minimum: Optional[Any] = None
    maximum: Optional[Any] = None
    exclusive_minimum: Optional[Any] = None  # standard v2 property
    exclusive_maximum: Optional[Any] = None  # standard v2 property
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: Optional[List[Any]] = None
    enum_weights: Optional[Dict[str, float]] = None  # x-mountainash extension
    json_schema: Optional[Dict[str, Any]] = None  # standard v2 property


@dataclass
class ForeignKeyReference:
    """Reference target for a foreign key (Frictionless Table Schema compliant).

    Attributes:
        resource: Name of the referenced table. ``None`` for self-referencing.
        fields: Field name(s) in the referenced table.
    """
    resource: Optional[str]  # None = self-reference
    fields: List[str]

    def __post_init__(self) -> None:
        _validate_key_shape(self.fields, "foreign_key.reference.fields")


@dataclass
class ForeignKey:
    """Foreign key constraint (Frictionless Table Schema compliant).

    Attributes:
        fields: Field name(s) in this table.
        reference: The target table and fields being referenced.
    """
    fields: List[str]
    reference: ForeignKeyReference

    def __post_init__(self) -> None:
        _validate_key_shape(self.fields, "foreign_key.fields")


@dataclass
class FieldSpec:
    """A single field in a TypeSpec (Frictionless Table Schema compliant).

    Extends the old SchemaField with:
    - rename_from: Optional source column name (for aliasing)
    - null_fill: Optional default value to replace nulls
    """

    name: str
    type: UniversalType = UniversalType.ANY
    format: str = "default"
    title: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[FieldConstraints] = None
    missing_values: Optional[List[MissingValue]] = None
    true_values: Optional[List[str]] = None
    false_values: Optional[List[str]] = None
    categories: Optional[List[Union[Any, LabeledValue]]] = None  # array of values or LabeledValue
    categories_ordered: Optional[bool] = None
    example: Optional[Any] = None
    rdf_type: Optional[str] = None
    decimal_char: Optional[str] = None
    group_char: Optional[str] = None
    bare_number: Optional[bool] = None
    item_type: Optional[str] = None  # valid only when type is LIST or ARRAY (decision 14)
    object_fields: Optional[List["FieldSpec"]] = None  # x-mountainash: OBJECT inner-field schema
    item_object_fields: Optional[List["FieldSpec"]] = None  # x-mountainash: ARRAY item struct schema
    delimiter: Optional[str] = None  # valid only when type is LIST or ARRAY (decision 14)
    backend_type: Optional[str] = None
    null_fill: Any = None
    rename_from: Optional[str] = None
    custom_cast: Optional[str] = None

    # Interim (Unit B -> Unit C) property/type compatibility for
    # item_type/delimiter. See decision 14: native list extraction always
    # emits ARRAY (never LIST — a native dtype cannot prove lexical LIST
    # intent), and conform's pre-existing ARRAY/item_type split branch
    # (backlog item 109) still keys on type == ARRAY. __post_init__ therefore
    # checks membership in (LIST, ARRAY), not LIST alone; Unit C narrows this
    # back to (LIST,) once ARRAY stops carrying these properties.
    def __post_init__(self) -> None:
        list_like = (UniversalType.LIST, UniversalType.ARRAY)
        if self.item_type is not None and self.type not in list_like:
            raise IncompatibleFieldPropertiesError(self.name, "item_type", self.type, list_like)
        if self.delimiter is not None and self.type not in list_like:
            raise IncompatibleFieldPropertiesError(self.name, "delimiter", self.type, list_like)
        if self.item_object_fields is not None and self.type is not UniversalType.ARRAY:
            raise IncompatibleFieldPropertiesError(
                self.name, "item_object_fields", self.type, (UniversalType.ARRAY,)
            )
        if self.object_fields is not None and self.type is not UniversalType.OBJECT:
            raise IncompatibleFieldPropertiesError(
                self.name, "object_fields", self.type, (UniversalType.OBJECT,)
            )

    @property
    def source_name(self) -> str:
        """The name of this column in the source data.

        Returns rename_from if set (i.e. the source has a different column
        name), otherwise falls back to name.
        """
        return self.rename_from if self.rename_from is not None else self.name


@dataclass
class TypeSpec:
    """Schema definition for a dataset (Frictionless Table Schema representation).

    Replaces the old TableSchema with additional features.
    """

    fields: List[FieldSpec] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None
    primary_key: Optional[List[str]] = None
    foreign_keys: Optional[List[ForeignKey]] = None
    missing_values: Optional[List[MissingValue]] = field(default_factory=lambda: [""])
    fields_match: str = "exact"  # exact/equal/subset/superset/partial/open
    unique_keys: Optional[List[List[str]]] = None  # Gap 4: composite unique-key constraints
    schema_url: Optional[str] = None
    contract: Optional[Dict[str, str]] = None  # item 48: reconciliation contract, layered
                                                # under conform(contract=...) overrides

    def __post_init__(self) -> None:
        # An explicitly-empty dict carries no dimensions and must never be
        # mistaken for an explicit layer downstream (resolve_contract flips
        # `from_preset=False` on any non-None contract) — normalise to None.
        if self.contract is not None and len(self.contract) == 0:
            self.contract = None
        if self.primary_key is not None:
            _validate_key_shape(self.primary_key, "primary_key")
        if self.unique_keys is not None:
            for i, uk in enumerate(self.unique_keys):
                _validate_key_shape(uk, f"unique_keys[{i}]")

    @classmethod
    def from_simple_dict(cls, columns: Dict[str, str], **metadata: Any) -> TypeSpec:
        """Create TypeSpec from a simple {name: type_string} dict.

        Args:
            columns: Dict mapping column names to type strings (e.g. "integer", "string")
            **metadata: Additional metadata (title, description, primary_key)

        Returns:
            TypeSpec with fields derived from the dict

        Example:
            >>> spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        """
        fields = []
        for col_name, type_str in columns.items():
            universal_type = parse_universal(type_str)
            fields.append(FieldSpec(name=col_name, type=universal_type))
        return cls(
            fields=fields,
            title=metadata.get("title"),
            description=metadata.get("description"),
            primary_key=metadata.get("primary_key"),
        )

    @classmethod
    def from_frictionless(cls, descriptor: Dict[str, Any]) -> TypeSpec:
        """Create TypeSpec from a Frictionless Table Schema descriptor dict.

        Delegates to the frictionless module (Task 3).
        """
        from mountainash.typespec.frictionless import typespec_from_frictionless
        return typespec_from_frictionless(descriptor)

    def to_frictionless(self) -> Dict[str, Any]:
        """Convert TypeSpec to a Frictionless Table Schema descriptor dict.

        Delegates to the frictionless module (Task 3).
        """
        from mountainash.typespec.frictionless import typespec_to_frictionless
        return typespec_to_frictionless(self)

    def to_contract(self, *, name: Optional[str] = None) -> Any:
        """Generate a native BaseDataContract subclass from this spec.

        Lazy import (same pattern as from_frictionless) — typespec has no
        static dependency on datacontracts.
        """
        from mountainash.datacontracts.compiler import contract_from_typespec
        return contract_from_typespec(self, name=name)

    def get_field(self, name: str) -> Optional[FieldSpec]:
        """Get a field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    @property
    def field_names(self) -> List[str]:
        """Get list of field names."""
        return [f.name for f in self.fields]


@dataclass
class SpecDiff:
    """Result of comparing two TypeSpecs."""

    added_fields: List[str] = field(default_factory=list)
    removed_fields: List[str] = field(default_factory=list)
    type_changes: Dict[str, tuple] = field(default_factory=dict)
    is_compatible: bool = True

    @property
    def has_changes(self) -> bool:
        return bool(self.added_fields or self.removed_fields or self.type_changes)

    # ---- Aliases for validator compatibility ----

    @property
    def missing_columns(self) -> List[str]:
        """Columns present in expected (target) but absent in actual (source)."""
        return self.added_fields

    @property
    def extra_columns(self) -> List[str]:
        """Columns present in actual (source) but absent in expected (target)."""
        return self.removed_fields

    @property
    def type_mismatches(self) -> List[tuple]:
        """List of (column, actual_type, expected_type) tuples."""
        return [(col, actual, expected) for col, (actual, expected) in self.type_changes.items()]


def compare_specs(
    source: TypeSpec,
    target: TypeSpec,
    check_constraints: bool = True,
) -> SpecDiff:
    """Compare two TypeSpecs and return a SpecDiff.

    Args:
        source: The actual / output spec
        target: The expected spec to compare against
        check_constraints: Ignored (reserved for future constraint comparison)

    Returns:
        SpecDiff describing the differences
    """
    source_names = set(source.field_names)
    target_names = set(target.field_names)

    diff = SpecDiff(
        # Fields in target but not in source → missing from actual output
        added_fields=sorted(target_names - source_names),
        # Fields in source but not in target → extra in actual output
        removed_fields=sorted(source_names - target_names),
    )

    # Check type changes for common fields
    for name in source_names & target_names:
        source_field = source.get_field(name)
        target_field = target.get_field(name)
        if source_field and target_field and source_field.type != target_field.type:
            diff.type_changes[name] = (source_field.type, target_field.type)

    diff.is_compatible = not diff.added_fields and not diff.type_changes
    return diff


__all__ = [
    "LabeledValue",
    "MissingValue",
    "FieldConstraints",
    "ForeignKeyReference",
    "ForeignKey",
    "FieldSpec",
    "TypeSpec",
    "SpecDiff",
    "compare_specs",
]
