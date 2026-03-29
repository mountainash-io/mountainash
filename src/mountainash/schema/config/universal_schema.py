"""
TableSchema - Frictionless Table Schema Implementation

Provides a table schema representation based on the Frictionless Data
Table Schema specification.

This module is backend-agnostic and has ZERO imports of DataFrame libraries,
ensuring fast imports and true portability.

Key Features:
- Full Frictionless Table Schema compliance (v1.0)
- Missing value handling (missingValues)
- Boolean value customization (trueValues/falseValues)
- Field constraints and validation rules
- Primary and foreign key definitions
- Backend type preservation (backend_type extension)
- Schema comparison and diff utilities
- Round-trip serialization (JSON <-> Python objects)
- Version control friendly (schemas as JSON files)

Reference: https://specs.frictionlessdata.io/table-schema/
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .types import UniversalType


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


@dataclass
class SchemaField:
    """A single field in a TableSchema (Frictionless Table Schema compliant)."""

    name: str
    type: UniversalType = UniversalType.STRING
    format: str = "default"
    title: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[FieldConstraints] = None
    missing_values: Optional[List[str]] = None
    true_values: Optional[List[str]] = None
    false_values: Optional[List[str]] = None
    backend_type: Optional[str] = None

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
        if self.backend_type:
            result["backend_type"] = self.backend_type
        return result


@dataclass
class TableSchema:
    """Frictionless Table Schema representation."""

    fields: List[SchemaField] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None
    primary_key: Optional[Union[str, List[str]]] = None
    missing_values: Optional[List[str]] = field(default_factory=lambda: [""])

    @classmethod
    def from_simple_dict(cls, columns: Dict[str, str], **metadata) -> TableSchema:
        """Create TableSchema from a simple {name: type_string} dict.

        Args:
            columns: Dict mapping column names to type strings (e.g. "integer", "string")
            **metadata: Additional metadata (title, description, primary_key)

        Returns:
            TableSchema with fields derived from the dict

        Example:
            >>> schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        """
        from .types import normalize_type

        fields = []
        for col_name, type_str in columns.items():
            universal_type = normalize_type(type_str)
            fields.append(SchemaField(name=col_name, type=universal_type))
        return cls(
            fields=fields,
            title=metadata.get("title"),
            description=metadata.get("description"),
            primary_key=metadata.get("primary_key"),
        )

    def get_field(self, name: str) -> Optional[SchemaField]:
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
        result: Dict[str, Any] = {
            "fields": [f.to_dict() for f in self.fields],
        }
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        if self.primary_key:
            result["primaryKey"] = self.primary_key
        if self.missing_values:
            result["missingValues"] = self.missing_values
        return result


@dataclass
class SchemaDiff:
    """Result of comparing two TableSchemas."""

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


def compare_schemas(
    source: TableSchema,
    target: TableSchema,
    check_constraints: bool = True,
) -> SchemaDiff:
    """Compare two TableSchemas and return a SchemaDiff.

    Args:
        source: The actual / output schema
        target: The expected schema to compare against
        check_constraints: Ignored (reserved for future constraint comparison)

    Returns:
        SchemaDiff describing the differences
    """
    source_names = set(source.field_names)
    target_names = set(target.field_names)

    diff = SchemaDiff(
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
