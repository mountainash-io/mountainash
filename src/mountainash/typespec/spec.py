"""
TypeSpec — Core data classes for schema definition.

Replaces TableSchema, SchemaField, and SchemaDiff from the old schema module.

This module is backend-agnostic and has ZERO imports of DataFrame libraries,
ensuring fast imports and true portability.

Key Features:
- Full Frictionless Table Schema compliance (v1.0)
- rename_from for column aliasing (source_name property)
- null_fill for default null replacement
- keep_only_mapped flag on TypeSpec
- Schema comparison and diff utilities
- Round-trip serialization (dict <-> Python objects)
- Lazy frictionless import/export (Task 3 will provide frictionless.py)

Reference: https://specs.frictionlessdata.io/table-schema/
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from mountainash.typespec.universal_types import UniversalType, normalize_type


@dataclass
class FieldConstraints:
    """Constraints for a schema field (Frictionless Table Schema compliant)."""

    required: bool = False
    unique: bool = False
    minimum: Optional[Any] = None
    maximum: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: Optional[List[Any]] = None
    enum_weights: Optional[Dict[str, float]] = None  # x-mountainash extension


@dataclass(frozen=True)
class UnnestConfig:
    """Configuration for unnesting a struct column during conformance."""
    column: str
    prefix: str = ""


@dataclass
class ForeignKeyReference:
    """Reference target for a foreign key (Frictionless Table Schema compliant).

    Attributes:
        resource: Name of the referenced table. Empty string for self-referencing.
        fields: Field name(s) in the referenced table.
    """
    resource: str
    fields: List[str]


@dataclass
class ForeignKey:
    """Foreign key constraint (Frictionless Table Schema compliant).

    Attributes:
        fields: Field name(s) in this table.
        reference: The target table and fields being referenced.
    """
    fields: List[str]
    reference: ForeignKeyReference


@dataclass
class FieldSpec:
    """A single field in a TypeSpec (Frictionless Table Schema compliant).

    Extends the old SchemaField with:
    - rename_from: Optional source column name (for aliasing)
    - null_fill: Optional default value to replace nulls
    """

    name: str
    type: UniversalType = UniversalType.STRING
    format: str = "default"
    title: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[FieldConstraints] = None
    missing_values: Optional[List[str]] = None
    true_values: Optional[List[str]] = None
    false_values: Optional[List[str]] = None
    categories: Optional[List[Any]] = None  # Gap 7: array of values or {value, label} dicts
    categories_ordered: Optional[bool] = None
    example: Optional[Any] = None
    rdf_type: Optional[str] = None
    decimal_char: Optional[str] = None
    group_char: Optional[str] = None
    bare_number: Optional[bool] = None
    item_type: Optional[str] = None
    delimiter: Optional[str] = None
    backend_type: Optional[str] = None
    null_fill: Any = None
    rename_from: Optional[str] = None
    custom_cast: Optional[str] = None
    multiply_by: Optional[float] = None
    coalesce_from: Optional[List[str]] = None
    duration_from: Optional[tuple] = None

    @property
    def source_name(self) -> str:
        """The name of this column in the source data.

        Returns rename_from if set (i.e. the source has a different column
        name), otherwise falls back to name.
        """
        return self.rename_from if self.rename_from is not None else self.name

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Frictionless-compatible dict."""
        result: Dict[str, Any] = {
            "name": self.name,
            "type": self.type.value if isinstance(self.type, UniversalType) else str(self.type),
        }
        if self.format != "default":
            result["format"] = self.format
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        if self.constraints:
            result["constraints"] = {
                k: v for k, v in self.constraints.__dict__.items() if v is not None and v is not False
            }
        if self.missing_values:
            result["missingValues"] = self.missing_values
        if self.categories_ordered is not None:
            result["categoriesOrdered"] = self.categories_ordered
        if self.example is not None:
            result["example"] = self.example
        if self.rdf_type is not None:
            result["rdfType"] = self.rdf_type
        if self.decimal_char is not None:
            result["decimalChar"] = self.decimal_char
        if self.group_char is not None:
            result["groupChar"] = self.group_char
        if self.bare_number is not None:
            result["bareNumber"] = self.bare_number
        if self.item_type is not None:
            result["itemType"] = self.item_type
        if self.delimiter is not None:
            result["delimiter"] = self.delimiter
        if self.backend_type:
            result["backend_type"] = self.backend_type
        if self.rename_from is not None:
            result["rename_from"] = self.rename_from
        if self.null_fill is not None:
            result["null_fill"] = self.null_fill
        return result


@dataclass
class TypeSpec:
    """Schema definition for a dataset (Frictionless Table Schema representation).

    Replaces the old TableSchema with additional features:
    - keep_only_mapped: when True, only mapped fields are kept during conform
    """

    fields: List[FieldSpec] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None
    primary_key: Optional[Union[str, List[str]]] = None
    foreign_keys: Optional[List[ForeignKey]] = None
    missing_values: Optional[List[str]] = field(default_factory=lambda: [""])
    keep_only_mapped: bool = False
    required_fields: Optional[List[str]] = None
    unnest_fields: Optional[List[Union[str, UnnestConfig]]] = None
    fields_match: Optional[str] = None  # Gap 3: exact/equal/subset/superset/partial
    unique_keys: Optional[List[List[str]]] = None  # Gap 4: composite unique-key constraints
    schema_url: Optional[str] = None

    @classmethod
    def from_simple_dict(cls, columns: Dict[str, str], **metadata: Any) -> TypeSpec:
        """Create TypeSpec from a simple {name: type_string} dict.

        Args:
            columns: Dict mapping column names to type strings (e.g. "integer", "string")
            **metadata: Additional metadata (title, description, primary_key,
                        keep_only_mapped)

        Returns:
            TypeSpec with fields derived from the dict

        Example:
            >>> spec = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        """
        fields = []
        for col_name, type_str in columns.items():
            universal_type = normalize_type(type_str)
            fields.append(FieldSpec(name=col_name, type=universal_type))
        return cls(
            fields=fields,
            title=metadata.get("title"),
            description=metadata.get("description"),
            primary_key=metadata.get("primary_key"),
            keep_only_mapped=metadata.get("keep_only_mapped", False),
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Frictionless-compatible dict."""
        result: Dict[str, Any] = {}
        if self.schema_url is not None:
            result["$schema"] = self.schema_url
        result["fields"] = [f.to_dict() for f in self.fields]
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        if self.primary_key:
            result["primaryKey"] = self.primary_key
        if self.missing_values:
            result["missingValues"] = self.missing_values
        if self.keep_only_mapped:
            result["keep_only_mapped"] = self.keep_only_mapped
        return result


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
    "FieldConstraints",
    "ForeignKeyReference",
    "ForeignKey",
    "FieldSpec",
    "TypeSpec",
    "SpecDiff",
    "compare_specs",
]
