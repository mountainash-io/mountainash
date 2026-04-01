"""SchemaBuilder — deferred schema definition, extraction, and validation.

Wraps existing SchemaConfig + CastSchemaFactory + extractors + validators
behind a build-then-execute API.

The SchemaBuilder spec uses **target-oriented** keys: each key is the desired
output column name.  The optional ``"rename"`` value names the *source* column
in the input DataFrame that should be mapped to that output name.

This is the inverse of SchemaConfig's source-oriented convention, so
SchemaBuilder translates before delegating to SchemaConfig.
"""
from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.core.types import SupportedDataFrames


class SchemaBuilder:
    """Deferred schema definition with terminal methods.

    Build phase: ``ma.schema({...})`` creates a SchemaBuilder holding the spec.
    Execute phase: ``.apply(df)`` constructs a SchemaConfig, detects the
    backend, and transforms.

    Also provides class methods for extraction and validation.
    """

    def __init__(self, spec: Dict[str, Dict[str, Any]]) -> None:
        self._spec = spec

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def columns(self) -> List[str]:
        """Column names defined in this schema (target names)."""
        return list(self._spec.keys())

    @property
    def transforms(self) -> Dict[str, Dict[str, Any]]:
        """Summary of planned transforms per column."""
        return dict(self._spec)

    # ------------------------------------------------------------------
    # Spec translation: target-oriented → source-oriented (SchemaConfig)
    # ------------------------------------------------------------------

    def _to_schema_config_columns(self) -> Dict[str, Dict[str, Any]]:
        """Translate the target-oriented spec into SchemaConfig's source-oriented format.

        SchemaBuilder spec:
            ``{"target_name": {"rename": "source_name", "cast": "integer"}}``

        SchemaConfig columns:
            ``{"source_name": {"rename": "target_name", "cast": "integer"}}``

        When no ``"rename"`` key is present the target name IS the source name,
        so the entry is passed through unchanged.
        """
        config_columns: Dict[str, Dict[str, Any]] = {}

        for target_name, target_spec in self._spec.items():
            spec_copy = dict(target_spec)
            source_name = spec_copy.pop("rename", None)

            if source_name is not None:
                # Rename: source_name → target_name
                config_columns[source_name] = {**spec_copy, "rename": target_name}
            else:
                # No rename — key is both source and target
                config_columns[target_name] = spec_copy

        return config_columns

    # ------------------------------------------------------------------
    # Terminal: apply
    # ------------------------------------------------------------------

    def apply(
        self,
        df: SupportedDataFrames,
        *,
        strict: bool = False,
    ) -> SupportedDataFrames:
        """Apply this schema transform to a DataFrame.

        Args:
            df: Any supported DataFrame backend.
            strict: If *True*, raise on missing columns.  If *False*
                (default), silently skip missing columns.

        Returns:
            Transformed DataFrame (same backend as input).
        """
        from mountainash.schema.config.schema_config import SchemaConfig

        config_columns = self._to_schema_config_columns()
        config = SchemaConfig(columns=config_columns, strict=strict)
        return config.apply(df)

    # ------------------------------------------------------------------
    # Terminal: extract (classmethod)
    # ------------------------------------------------------------------

    @classmethod
    def extract(cls, source: Any) -> SchemaBuilder:
        """Extract a schema from a DataFrame, dataclass, or Pydantic model."""
        from mountainash.schema.config.extractors import (
            extract_schema_from_dataframe,
            from_dataclass,
        )

        if isinstance(source, type):
            import dataclasses
            if dataclasses.is_dataclass(source):
                table_schema = from_dataclass(source)
                return cls._from_table_schema(table_schema)
            if hasattr(source, "__pydantic_core_schema__") or hasattr(source, "__fields__"):
                from mountainash.schema.config.extractors import from_pydantic
                table_schema = from_pydantic(source)
                return cls._from_table_schema(table_schema)

        table_schema = extract_schema_from_dataframe(source)
        return cls._from_table_schema(table_schema)

    @classmethod
    def _from_table_schema(cls, table_schema: Any) -> SchemaBuilder:
        """Convert a TableSchema to a SchemaBuilder spec."""
        spec: Dict[str, Dict[str, Any]] = {}
        for field in table_schema.fields:
            field_spec: Dict[str, Any] = {}
            if field.type:
                field_spec["cast"] = field.type
            spec[field.name] = field_spec
        return cls(spec)

    # ------------------------------------------------------------------
    # Terminal: validate
    # ------------------------------------------------------------------

    def validate(self, df: SupportedDataFrames) -> Any:
        """Validate a DataFrame against this schema.

        Currently checks for missing columns only. Does not validate
        type compatibility (e.g. whether a cast would succeed).
        """
        from mountainash.schema.config.schema_config import ValidationResult, ValidationIssue

        issues: List[ValidationIssue] = []

        if hasattr(df, "columns"):
            df_columns = set(df.columns)
        else:
            df_columns = set()

        for col_name, col_spec in self._spec.items():
            source_name = col_spec.get("rename", col_name)
            if source_name not in df_columns:
                issues.append(ValidationIssue(
                    type="missing_columns",
                    severity="error",
                    message=f"Column '{source_name}' not found in DataFrame",
                    columns=[source_name],
                ))

        is_valid = len(issues) == 0
        return ValidationResult(valid=is_valid, issues=issues)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"SchemaBuilder(columns={self.columns})"
