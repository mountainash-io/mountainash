"""
Backend-Agnostic Column Transformation Configuration System

Provides DataFrame-independent column mapping, casting, and null handling
that can be defined once and applied to DataFrames of any backend
(pandas, polars, ibis, pyarrow, narwhals).

TODO: Support Columns slectors API!

Uses TableSchema for schema-driven transformations with validation.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, Optional, Union, List, Tuple, Literal
from dataclasses import dataclass
from difflib import SequenceMatcher
import json
import logging

# from .universal_schema import TableSchema, SchemaField, compare_schemas

if TYPE_CHECKING:
    from mountainash.dataframes.core.typing import SupportedDataFrames
    import polars as pl

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Individual validation issue from schema validation."""
    type: str  # 'missing_columns', 'extra_columns', 'type_mismatch'
    severity: str  # 'error', 'warning', 'info'
    message: str
    columns: Optional[List[str]] = None
    details: Optional[Any] = None


@dataclass
class ValidationResult:
    """Result of schema validation against a DataFrame."""
    valid: bool
    issues: List[ValidationIssue]

    def log_issues(self):
        """Log all issues at appropriate levels."""
        for issue in self.issues:
            if issue.severity == 'error':
                logger.error(issue.message)
            elif issue.severity == 'warning':
                logger.warning(issue.message)
            else:
                logger.info(issue.message)


class SchemaConfig:
    """
    Backend-agnostic column transformation configuration.

    Enhanced with TableSchema integration for schema-driven transformations.

    Works with any DataFrame backend: pandas, polars, ibis, pyarrow, narwhals.

    Two modes of operation:
    1. **Legacy mode**: Direct column transformations via columns dict
    2. **Schema mode**: Schema-driven transformations via source_schema and target_schema

    Supports:
    - Column renaming (mapping field names)
    - Type casting (universal type names)
    - Null value filling
    - Default values for missing columns
    - Column filtering (keep only mapped vs all columns)
    - Schema validation and prediction

    Example (Legacy mode):
        >>> config = SchemaConfig(columns={
        ...     "user_id": {"rename": "id", "cast": "integer"},
        ...     "name": {"rename": "full_name"},
        ...     "age": {"cast": "integer", "null_fill": 0}
        ... })

    Example (Schema mode):
        >>> source = TableSchema.from_simple_dict({"user_id": "integer", "name": "string"})
        >>> target = TableSchema.from_simple_dict({"id": "integer", "full_name": "string"})
        >>> config = SchemaConfig.from_schemas(source, target)
    """

    def __init__(self,
                 columns: Optional[Dict[str, Dict[str, Any]]] = None,
                 keep_only_mapped: bool = False,
                 strict: bool = False,
                 source_schema: Optional[TableSchema] = None,
                 target_schema: Optional[TableSchema] = None):
        """
        Create column transformation configuration.

        Args:
            columns: Dict mapping source_column -> transformation spec
            keep_only_mapped: If True, keep only explicitly mapped columns
            strict: If True, raise errors for missing columns without defaults.
                   If False (default), silently skip missing columns.
            source_schema: Optional TableSchema describing expected input
            target_schema: Optional TableSchema describing desired output

        Transformation spec format:
            {
                "rename": "new_name",        # Optional: new column name
                "cast": "integer|number|string|boolean|date|datetime",  # Universal type
                "null_fill": value,          # Optional: value to replace nulls
                "default": value             # Optional: default value if column missing
            }

        Strict mode behavior:
            - strict=False (default): Missing columns without defaults are skipped
            - strict=True: Missing columns without defaults raise ValueError
        """
        self.columns = columns or {}
        self.keep_only_mapped = keep_only_mapped
        self.strict = strict
        self.source_schema = source_schema
        self.target_schema = target_schema

    @classmethod
    def from_schemas(
        cls,
        source_schema: TableSchema,
        target_schema: TableSchema,
        fuzzy_match_threshold: float = 0.6,
        auto_cast: bool = True,
        keep_unmapped_source: bool = False
    ) -> 'SchemaConfig':
        """
        Create SchemaConfig from source and target schemas with automatic mapping.

        Uses fuzzy string matching to automatically map columns between schemas.
        Generates transformation rules based on schema differences.

        Args:
            source_schema: Schema describing input DataFrame
            target_schema: Schema describing desired output DataFrame
            fuzzy_match_threshold: Minimum similarity ratio for fuzzy matching (0.0-1.0)
            auto_cast: Automatically generate cast rules for type mismatches
            keep_unmapped_source: Keep source columns not mapped to target

        Returns:
            SchemaConfig with auto-generated column mappings

        Example:
            >>> source = TableSchema.from_simple_dict({
            ...     "user_id": "integer",
            ...     "user_name": "string",
            ...     "user_email": "string"
            ... })
            >>> target = TableSchema.from_simple_dict({
            ...     "id": "integer",
            ...     "name": "string",
            ...     "email": "string"
            ... })
            >>> config = SchemaConfig.from_schemas(source, target)
            >>> # Auto-generates: user_id->id, user_name->name, user_email->email
        """
        columns = {}

        # Build mapping: source_field_name -> target_field
        source_to_target_map = cls._fuzzy_match_fields(
            source_schema.fields,
            target_schema.fields,
            fuzzy_match_threshold
        )

        # Generate transformation rules
        for source_field_name, target_field in source_to_target_map.items():
            source_field = source_schema.get_field(source_field_name)

            transform_spec = {}

            # Add rename if names differ
            if source_field.name != target_field.name:
                transform_spec["rename"] = target_field.name

            # Add cast if types differ and auto_cast enabled
            if auto_cast and source_field.type != target_field.type:
                transform_spec["cast"] = target_field.type

            # Only add to columns if there's a transformation
            if transform_spec:
                columns[source_field.name] = transform_spec

        # Handle unmapped target fields (need default values)
        mapped_target_names = {spec.get("rename", src) for src, spec in columns.items()}
        for target_field in target_schema.fields:
            if target_field.name not in mapped_target_names:
                # Target field not mapped from source - will need default value
                logger.warning(
                    f"Target field '{target_field.name}' has no source mapping. "
                    f"Will require default value or will be missing."
                )

        keep_only_mapped = not keep_unmapped_source

        return cls(
            columns=columns,
            keep_only_mapped=keep_only_mapped,
            strict=False,  # Don't be strict with auto-generated configs
            source_schema=source_schema,
            target_schema=target_schema
        )

    @staticmethod
    def _fuzzy_match_fields(
        source_fields: List[SchemaField],
        target_fields: List[SchemaField],
        threshold: float = 0.6
    ) -> Dict[str, SchemaField]:
        """
        Fuzzy match source fields to target fields by name similarity.

        Uses SequenceMatcher for string similarity. Prefers exact matches,
        then falls back to fuzzy matching above threshold.

        Args:
            source_fields: List of source schema fields
            target_fields: List of target schema fields
            threshold: Minimum similarity ratio (0.0-1.0)

        Returns:
            Dict mapping source_field_name -> matched_target_field
        """
        mapping = {}
        unmatched_targets = list(target_fields)

        # Pass 1: Exact matches
        for source_field in source_fields:
            for target_field in list(unmatched_targets):
                if source_field.name == target_field.name:
                    mapping[source_field.name] = target_field
                    unmatched_targets.remove(target_field)
                    break

        # Pass 2: Fuzzy matches for remaining fields
        unmatched_sources = [f for f in source_fields if f.name not in mapping]

        for source_field in unmatched_sources:
            best_match = None
            best_ratio = threshold

            for target_field in unmatched_targets:
                # Calculate similarity
                ratio = SequenceMatcher(
                    None,
                    source_field.name.lower(),
                    target_field.name.lower()
                ).ratio()

                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = target_field

            if best_match:
                mapping[source_field.name] = best_match
                unmatched_targets.remove(best_match)
                logger.info(
                    f"Fuzzy matched '{source_field.name}' -> '{best_match.name}' "
                    f"(similarity: {best_ratio:.2f})"
                )

        return mapping

    def predict_output_schema(self, input_schema: Optional[TableSchema] = None) -> TableSchema:
        """
        Predict the output schema after applying this configuration.

        Args:
            input_schema: Schema of input DataFrame. If None, uses self.source_schema.

        Returns:
            Predicted output schema (TableSchema)

        Raises:
            ValueError: If no input schema provided and no source_schema set

        Example:
            >>> config = SchemaConfig(columns={
            ...     "old_id": {"rename": "id", "cast": "integer"},
            ...     "name": {"cast": "string"}
            ... })
            >>> input_schema = TableSchema.from_simple_dict({
            ...     "old_id": "number",
            ...     "name": "string",
            ...     "extra": "boolean"
            ... })
            >>> output_schema = config.predict_output_schema(input_schema)
            >>> output_schema.field_names
            ['id', 'name', 'extra']  # or ['id', 'name'] if keep_only_mapped=True
        """
        if input_schema is None:
            if self.source_schema is None:
                raise ValueError(
                    "No input schema provided and no source_schema set. "
                    "Provide input_schema or set source_schema in constructor."
                )
            input_schema = self.source_schema

        # Predict output based on transformations in columns
        output_fields = []

        # Track which source fields were mapped
        mapped_source_fields = set()

        # Apply transformations
        for source_field_name, transform_spec in self.columns.items():
            # Find source field
            source_field = input_schema.get_field(source_field_name)

            if source_field is None:
                # Source field doesn't exist
                if "default" in transform_spec:
                    # Create new field with default value
                    output_name = transform_spec.get("rename", source_field_name)
                    output_type = transform_spec.get("cast", "any")
                    output_fields.append(SchemaField(
                        name=output_name,
                        type=output_type
                    ))
                    continue  # Skip to next field
                elif self.strict:
                    raise ValueError(f"Required source field '{source_field_name}' not found in input schema")
                # else: skip missing field
                continue

            mapped_source_fields.add(source_field_name)

            # Determine output name
            output_name = transform_spec.get("rename", source_field.name)

            # Determine output type
            output_type = transform_spec.get("cast", source_field.type)

            # Create output field
            output_field = SchemaField(
                name=output_name,
                type=output_type,
                format=source_field.format,
                constraints=source_field.constraints,
                description=source_field.description
            )
            output_fields.append(output_field)

        # Add unmapped fields if not filtering
        if not self.keep_only_mapped:
            for source_field in input_schema.fields:
                if source_field.name not in mapped_source_fields:
                    # Pass through unchanged
                    output_fields.append(source_field)

        return TableSchema(
            fields=output_fields,
            title=input_schema.title,
            description=f"Predicted output from {input_schema.title or 'input schema'}"
        )

    def validate_against_schemas(
        self,
        check_source: bool = True,
        check_target: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Validate that this configuration is compatible with its schemas.

        Checks:
        - All source columns in config exist in source_schema
        - All target columns in config match target_schema types
        - Required target fields have mappings
        - Type conversions are safe (if schemas have types)

        Args:
            check_source: Validate against source_schema
            check_target: Validate against target_schema

        Returns:
            Tuple of (is_valid, list_of_error_messages)

        Example:
            >>> config = SchemaConfig.from_schemas(source, target)
            >>> is_valid, errors = config.validate_against_schemas()
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"Validation error: {error}")
        """
        errors = []

        if check_source and self.source_schema:
            # Check all source columns exist
            logger.debug(f"Validating source columns: {list(self.columns.keys())}")
            for source_col in self.columns.keys():
                field = self.source_schema.get_field(source_col)
                if field is None:
                    logger.debug(f"Source column '{source_col}' NOT found in schema")
                    errors.append(f"Source column '{source_col}' not found in source_schema")
                else:
                    logger.debug(f"Source column '{source_col}' found in schema")

        if check_target and self.target_schema:
            # Build predicted output schema
            try:
                predicted_output = self.predict_output_schema()
            except ValueError as e:
                errors.append(f"Cannot predict output schema: {e}")
                return False, errors

            # Compare with target schema
            diff = compare_schemas(predicted_output, self.target_schema, check_constraints=False)

            if diff.missing_columns:
                errors.append(f"Missing required target columns: {diff.missing_columns}")

            if diff.type_mismatches:
                for col, predicted_type, target_type in diff.type_mismatches:
                    errors.append(
                        f"Type mismatch for '{col}': "
                        f"predicted={predicted_type}, target={target_type}"
                    )

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_against_dataframe(
        self,
        df: 'SupportedDataFrames',
        mode: Literal['source', 'target'] = 'source'
    ) -> ValidationResult:
        """
        Validate schema against DataFrame.

        Compares the DataFrame's actual structure against the source_schema or
        target_schema (based on mode parameter). Checks for missing columns,
        extra columns, and type mismatches.

        Strict mode (self.strict=True):
            - Raises ValueError on any mismatch
            - Fails fast with detailed error message

        Lenient mode (self.strict=False, default):
            - Returns ValidationResult with issues
            - Logs warnings but does not raise
            - Allows processing to continue

        Args:
            df: DataFrame to validate against schema
            mode: Which schema to validate against:
                - 'source': Validate against source_schema
                - 'target': Validate against target_schema

        Returns:
            ValidationResult with validation results

        Raises:
            ValueError: If strict=True and validation fails
            ValueError: If requested schema (source/target) is not set

        Example:
            >>> config = SchemaConfig(
            ...     columns={"id": {"cast": "integer"}},
            ...     source_schema=source_schema,
            ...     strict=True
            ... )
            >>> result = config.validate_against_dataframe(df, mode='source')
            >>> if not result.valid:
            ...     result.log_issues()
        """
        # Determine which schema to validate against
        if mode == 'source':
            schema = self.source_schema
            schema_name = 'source_schema'
        else:  # mode == 'target'
            schema = self.target_schema
            schema_name = 'target_schema'

        if schema is None:
            raise ValueError(
                f"Cannot validate against {schema_name}: {schema_name} is not set. "
                f"Provide {schema_name} when creating SchemaConfig."
            )

        # Get DataFrame columns and types using extract_schema_from_dataframe
        # This is backend-agnostic and already handles all DataFrame types
        from .extractors import extract_schema_from_dataframe

        # Extract actual schema from DataFrame
        try:
            actual_schema = extract_schema_from_dataframe(df, include_backend_types=False)
        except Exception as e:
            raise ValueError(f"Could not extract schema from DataFrame: {e}")

        df_columns = set(field.name for field in actual_schema.fields)
        schema_columns = set(field.name for field in schema.fields)

        issues = []

        # Check for missing columns
        missing_columns = schema_columns - df_columns
        if missing_columns:
            severity = 'error' if self.strict else 'warning'
            issues.append(ValidationIssue(
                type='missing_columns',
                severity=severity,
                message=f"Missing required columns: {sorted(missing_columns)}. "
                        f"DataFrame has: {sorted(df_columns)}",
                columns=sorted(missing_columns)
            ))

        # Check for extra columns (only in strict mode)
        if self.strict:
            extra_columns = df_columns - schema_columns
            if extra_columns:
                issues.append(ValidationIssue(
                    type='extra_columns',
                    severity='warning',
                    message=f"DataFrame has extra columns not in schema: {sorted(extra_columns)}",
                    columns=sorted(extra_columns)
                ))

        # Check type mismatches (for columns that exist in both)
        common_columns = df_columns & schema_columns
        if common_columns:
            for col in common_columns:
                actual_field = actual_schema.get_field(col)
                expected_field = schema.get_field(col)

                if actual_field and expected_field:
                    actual_type = actual_field.type
                    expected_type = expected_field.type

                    # Simple type name comparison
                    if not self._types_compatible(actual_type, expected_type):
                        severity = 'warning'  # Type mismatches are warnings even in strict mode
                        issues.append(ValidationIssue(
                            type='type_mismatch',
                            severity='warning',
                            message=f"Type mismatch for column '{col}': "
                                    f"DataFrame has '{actual_type}', schema expects '{expected_type}'",
                            columns=[col],
                            details={'df_type': actual_type, 'schema_type': expected_type}
                        ))

        # Determine if validation passed
        valid = len([issue for issue in issues if issue.severity == 'error']) == 0

        result = ValidationResult(valid=valid, issues=issues)

        # In strict mode, raise on any errors
        if self.strict and not valid:
            error_messages = [issue.message for issue in issues if issue.severity == 'error']
            raise ValueError(
                f"Schema validation failed ({len(error_messages)} error(s)):\n" +
                "\n".join(f"  - {msg}" for msg in error_messages)
            )

        return result

    @staticmethod
    def _types_compatible(df_type: Any, schema_type: str) -> bool:
        """
        Check if DataFrame type is compatible with schema type.

        This is a basic compatibility check. More sophisticated type checking
        could be added in the future (e.g., checking if Int64 is compatible with "integer").

        Args:
            df_type: Type from DataFrame (could be various backend types)
            schema_type: Universal type name from schema

        Returns:
            True if types are compatible, False otherwise
        """
        # Convert df_type to string for comparison
        df_type_str = str(df_type).lower()

        # Basic type mapping
        type_keywords = {
            'integer': ['int', 'integer'],
            'number': ['float', 'double', 'number', 'decimal'],
            'string': ['str', 'string', 'utf8', 'object'],
            'boolean': ['bool', 'boolean'],
            'date': ['date'],
            'datetime': ['datetime', 'timestamp'],
        }

        if schema_type.lower() in type_keywords:
            keywords = type_keywords[schema_type.lower()]
            return any(keyword in df_type_str for keyword in keywords)

        # If we can't determine, assume compatible (lenient default)
        return True

    @classmethod
    def from_json(cls, json_str: str) -> 'SchemaConfig':
        """
        Create configuration from JSON string.

        Supports three formats:

        1. Full format with schemas:
        {
            "columns": {"old": {"rename": "new", "cast": "integer"}},
            "keep_only_mapped": true,
            "source_schema": {...},  # Frictionless Table Schema
            "target_schema": {...}
        }

        2. Legacy full format:
        {
            "columns": {"old": {"rename": "new"}},
            "keep_only_mapped": true
        }

        3. Simple format (renaming only):
        {"old_name": "new_name", "another_old": "another_new"}
        """
        data = json.loads(json_str)

        # Check for schema format
        source_schema = None
        target_schema = None
        if "source_schema" in data:
            source_schema = TableSchema.from_dict(data["source_schema"])
        if "target_schema" in data:
            target_schema = TableSchema.from_dict(data["target_schema"])

        # Detect format: simple dict format vs full config format
        if 'columns' in data or 'keep_only_mapped' in data or 'strict' in data:
            # Full format
            return cls(
                columns=data.get('columns', {}),
                keep_only_mapped=data.get('keep_only_mapped', False),
                strict=data.get('strict', False),
                source_schema=source_schema,
                target_schema=target_schema
            )
        else:
            # Simple format: {"old_name": "new_name", ...}
            columns = {}
            for old_name, new_name in data.items():
                if isinstance(new_name, str):
                    columns[old_name] = {"rename": new_name}
                else:
                    raise ValueError(
                        f"Simple format requires string values, "
                        f"got {type(new_name)} for '{old_name}'"
                    )

            return cls(columns=columns, keep_only_mapped=True)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SchemaConfig':
        """
        Create configuration from dictionary.

        Supports four formats:
        1. Full format with schemas: {"columns": {...}, "source_schema": {...}, "target_schema": {...}}
        2. Full format: {"columns": {...}, "keep_only_mapped": bool, "strict": bool}
        3. Columns-only format: {"old_name": {"rename": "new_name", "cast": "integer"}, ...}
        4. Simple rename format: {"old_name": "new_name", ...}
        """
        # Extract schemas if present
        source_schema = None
        target_schema = None
        if "source_schema" in config_dict:
            source_schema = TableSchema.from_dict(config_dict["source_schema"])
        if "target_schema" in config_dict:
            target_schema = TableSchema.from_dict(config_dict["target_schema"])

        # Validate keys and values for formats 3 and 4 (column mappings without "columns" wrapper)
        # Formats 1 and 2 have "columns" key and will be validated separately
        if 'columns' not in config_dict:
            # Filter out schema and metadata keys for validation
            column_keys = {k for k in config_dict.keys()
                          if k not in {'source_schema', 'target_schema', 'keep_only_mapped', 'strict'}}

            for key in column_keys:
                value = config_dict[key]

                # Validate key is a string
                if not isinstance(key, str):
                    raise ValueError(
                        f"Column names must be strings, got {type(key).__name__} for key {key}"
                    )

                # Validate value is not None
                if value is None:
                    raise ValueError(
                        f"Column transformation values cannot be None for column '{key}'"
                    )

                # Validate value is string or dict
                if not isinstance(value, (str, dict)):
                    raise ValueError(
                        f"Column transformation values must be string or dict, "
                        f"got {type(value).__name__} for column '{key}'"
                    )

        # Detect format
        if 'columns' in config_dict or 'keep_only_mapped' in config_dict or 'strict' in config_dict:
            # Format 1 or 2: Full format
            return cls(
                columns=config_dict.get('columns', {}),
                keep_only_mapped=config_dict.get('keep_only_mapped', False),
                strict=config_dict.get('strict', False),
                source_schema=source_schema,
                target_schema=target_schema
            )

        # Check first value to distinguish between formats 3 and 4
        if not config_dict:
            return cls(columns={}, keep_only_mapped=False)

        first_value = next(iter(config_dict.values()))

        if isinstance(first_value, dict):
            # Format 3: Columns-only format
            return cls(
                columns=config_dict,
                keep_only_mapped=False,
                source_schema=source_schema,
                target_schema=target_schema
            )
        elif isinstance(first_value, str):
            # Format 4: Simple rename format
            columns = {old_name: {"rename": new_name}
                      for old_name, new_name in config_dict.items()}
            return cls(
                columns=columns,
                keep_only_mapped=True,
                source_schema=source_schema,
                target_schema=target_schema
            )
        else:
            raise ValueError(
                f"Invalid dict format. Expected string or dict values, "
                f"got {type(first_value)} for first entry"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        result = {
            "columns": self.columns,
            "keep_only_mapped": self.keep_only_mapped,
            "strict": self.strict
        }

        # Add schemas if present
        if self.source_schema:
            result["source_schema"] = self.source_schema.to_dict()
        if self.target_schema:
            result["target_schema"] = self.target_schema.to_dict()

        return result

    def to_json(self) -> str:
        """Export configuration as JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def separate_conversions(self) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        Separate conversions into THREE tiers for vectorized hybrid strategy.

        This is a KEY METHOD for the THREE-TIER hybrid architecture:
        - Python-only custom: Apply at edges (Python layer) - semantic logic without vectorization
        - Narwhals custom: Apply in DataFrame (vectorized expressions) - semantic logic WITH vectorization
        - Native conversions: Apply in DataFrame (vectorized operations) - structural types

        The three-tier strategy provides optimal performance:
        - Narwhals vectorization: 2.5-10x faster than Python custom converters
        - Native operations: Already vectorized

        Returns:
            Tuple of (python_only_custom, narwhals_custom, native_conversions)

            python_only_custom: Dict of columns with custom type converters (no Narwhals implementation)
                - Apply at EDGES (Python layer, row-by-row)
                - Examples: custom types without vectorization

            narwhals_custom: Dict of columns with Narwhals-vectorized custom converters
                - Apply in CENTER (DataFrame layer, vectorized expressions)
                - Examples: safe_float, xml_string, rich_boolean (vectorized!)

            native_conversions: Dict of columns with native type conversions
                - Apply in CENTER (DataFrame layer, vectorized operations)
                - Examples: string→integer, float→boolean, rename, null_fill

        Example:
            >>> config = SchemaConfig(columns={
            ...     "id": {"cast": "integer"},              # Native
            ...     "amount": {"cast": "safe_float"},       # Narwhals custom (vectorized!)
            ...     "custom": {"cast": "python_only_type"}, # Python-only custom
            ...     "name": {"rename": "full_name"}         # Native (no cast)
            ... })
            >>> python_custom, narwhals_custom, native = config.separate_conversions()
            >>> narwhals_custom
            {'amount': {'cast': 'safe_float'}}
            >>> python_custom
            {'custom': {'cast': 'python_only_type'}}
            >>> native
            {'id': {'cast': 'integer'}, 'name': {'rename': 'full_name'}}
        """
        from .custom_types import CustomTypeRegistry

        python_only_custom = {}
        narwhals_custom = {}
        native_conversions = {}

        for col_name, spec in self.columns.items():
            # Check if this column has a cast operation
            if "cast" not in spec:
                # No casting - all other operations are native (rename, null_fill, etc.)
                native_conversions[col_name] = spec
                continue

            cast_type = spec["cast"]

            # Determine if cast type is custom or native
            if CustomTypeRegistry.has_converter(cast_type):
                # Custom converter - check if vectorized
                if CustomTypeRegistry.is_vectorized(cast_type):
                    # Narwhals vectorized custom type - apply in DataFrame (fast!)
                    narwhals_custom[col_name] = spec
                    logger.debug(
                        f"Column '{col_name}' uses vectorized custom type '{cast_type}' - "
                        f"will apply in DataFrame (vectorized Narwhals expressions)"
                    )
                else:
                    # Python-only custom type - apply at edges (Python layer)
                    python_only_custom[col_name] = spec
                    logger.debug(
                        f"Column '{col_name}' uses Python-only custom type '{cast_type}' - "
                        f"will apply at edges (Python layer)"
                    )
            else:
                # Native type - apply in DataFrame (vectorized operations)
                native_conversions[col_name] = spec
                logger.debug(
                    f"Column '{col_name}' uses native type '{cast_type}' - "
                    f"will apply in DataFrame (vectorized)"
                )

        logger.info(
            f"Separated conversions: {len(python_only_custom)} Python-only custom, "
            f"{len(narwhals_custom)} Narwhals custom (vectorized), "
            f"{len(native_conversions)} native"
        )

        return python_only_custom, narwhals_custom, native_conversions

    def apply(self, df: 'SupportedDataFrames') -> 'SupportedDataFrames':
        """
        Apply this configuration to a DataFrame (any backend).

        Automatically detects the DataFrame backend and applies transformations
        using the appropriate strategy.

        **Note**: This method will be deprecated in favor of explicit
        transform strategies in a future version.

        Args:
            df: Input DataFrame (pandas, polars, ibis, pyarrow, or narwhals)

        Returns:
            Transformed DataFrame (same backend as input)

        Example:
            >>> config = SchemaConfig(columns={"old": {"rename": "new"}})
            >>> result = config.apply(any_dataframe)
        """
        # Import factory here to avoid circular dependency
        from mountainash.schema.transform import SchemaTransformFactory

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        return strategy.apply(df, self)


def init_column_config(
    config: Union[SchemaConfig, Dict[str, Any], str],
    keep_only_mapped: Optional[bool] = None
) -> SchemaConfig:
    """
    Normalize column configuration to SchemaConfig instance.

    Args:
        config: SchemaConfig, dict, or JSON string
        keep_only_mapped: Override keep_only_mapped setting

    Returns:
        SchemaConfig instance
    """
    # Normalize config to SchemaConfig
    if isinstance(config, SchemaConfig):
        # Already a config, just apply override if specified
        if keep_only_mapped is not None:
            config.keep_only_mapped = keep_only_mapped
        return config

    if isinstance(config, str):
        config = SchemaConfig.from_json(config)
    elif isinstance(config, dict):
        config = SchemaConfig.from_dict(config)
    else:
        raise ValueError("Config must be SchemaConfig, dict, or JSON string")

    # Override if set
    if keep_only_mapped is not None:
        config.keep_only_mapped = keep_only_mapped

    return config


def apply_column_config(
    df: 'SupportedDataFrames',
    config: Union[SchemaConfig, Dict[str, Any], str]
) -> 'SupportedDataFrames':
    """
    Apply column transformation configuration to a DataFrame (any backend).

    Backend-agnostic function that auto-detects the DataFrame type and
    applies transformations using the appropriate strategy.

    Supports:
    - Column renaming ("rename")
    - Type casting ("cast") - universal type names like "integer", "number", "string", "boolean"
    - Null filling ("null_fill") - replace nulls in existing columns
    - Default values ("default") - add missing columns with default values

    Args:
        df: Input DataFrame (pandas, polars, ibis, pyarrow, narwhals)
        config: SchemaConfig, dict, or JSON string

    Returns:
        Transformed DataFrame (same backend as input)

    Example:
        >>> config = {"user_id": {"rename": "id", "cast": "integer"}}
        >>> result = apply_column_config(any_df, config)
    """
    # Normalize config to SchemaConfig
    normalized_config = init_column_config(config)

    # Use factory to get appropriate strategy
    from mountainash.schema.transform import SchemaTransformFactory

    factory = SchemaTransformFactory()
    strategy = factory.get_strategy(df)
    return strategy.apply(df, normalized_config)


# Convenience functions for common patterns
def create_rename_config(
    mapping: Dict[str, str],
    keep_only_mapped: bool = False
) -> SchemaConfig:
    """
    Create configuration for simple column renaming.

    Args:
        mapping: Dict of old_name -> new_name
        keep_only_mapped: Whether to keep only mapped columns

    Example:
        >>> config = create_rename_config({"old_id": "user_id", "old_email": "email"})
    """
    columns = {old: {"rename": new} for old, new in mapping.items()}
    return SchemaConfig(columns=columns, keep_only_mapped=keep_only_mapped)


def create_cast_config(
    casting: Dict[str, str],
    keep_only_mapped: bool = False
) -> SchemaConfig:
    """
    Create configuration for type casting without renaming.

    Args:
        casting: Dict of column_name -> universal_type_name
        keep_only_mapped: Whether to keep only mapped columns

    Example:
        >>> config = create_cast_config({"user_id": "integer", "score": "number"})
    """
    columns = {col: {"cast": cast_type} for col, cast_type in casting.items()}
    return SchemaConfig(columns=columns, keep_only_mapped=keep_only_mapped)


__all__ = [
    "SchemaConfig",
    "ValidationIssue",
    "ValidationResult",
    "init_column_config",
    "apply_column_config",
    "create_rename_config",
    "create_cast_config",
]
