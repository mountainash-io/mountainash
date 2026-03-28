"""
Pandas-specific column transformation strategy.

Implements column transformations using pandas DataFrame API.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.lazy_imports import import_pandas
from .base_schema_transform_strategy import BaseCastSchemaStrategy


if TYPE_CHECKING:
    import pandas as pd
    from mountainash.core.types import PandasFrame
    from mountainash.schema.config import SchemaConfig, SchemaField



class CastSchemaPandas(BaseCastSchemaStrategy):
    """
    Pandas DataFrame column transformation strategy.

    Uses pandas API for column operations:
    - Rename: df.rename(columns={...}) or df[new_name] = df[old_name]
    - Cast: series.astype()
    - Null fill: series.fillna()
    - Defaults: df[col] = default_value
    """

    @classmethod
    def _apply(cls,
               df: 'PandasFrame',
               config: 'SchemaConfig') -> 'PandasFrame':
        """
        Apply column transformations to pandas DataFrame.

        Transformation order:
        1. Replace missing_values with null (schema-level)
        2. Apply type casting with boolean value conversion (field-level)
        3. Apply null filling
        4. Apply renaming

        Args:
            df: Pandas DataFrame
            config: SchemaConfig with transformation specs

        Returns:
            Transformed pandas DataFrame
        """
        pd = import_pandas()
        if pd is None:
            raise ImportError("pandas is required for this operation")

        # Create a copy to avoid modifying original
        result = df.copy()

        # Step 1: Apply missing_values replacement (schema-level)
        if config.source_schema and config.source_schema.missing_values:
            result = cls._replace_missing_values(result, config.source_schema.missing_values)

        # Track columns to keep
        columns_to_keep = []

        # Process explicitly mapped columns
        for source_col, spec in config.columns.items():
            target_name = spec.get("rename", source_col)

            # Handle missing columns
            if source_col not in result.columns:
                if "default" in spec:
                    # Add column with default value
                    result[target_name] = spec["default"]
                    columns_to_keep.append(target_name)
                elif config.strict:
                    # Strict mode: raise error for missing columns without defaults
                    raise ValueError(
                        f"Column '{source_col}' not found in DataFrame. "
                        f"Available columns: {list(result.columns)}"
                    )
                # Lenient mode: skip missing columns
                continue

            # Start with the source column
            series = result[source_col]

            # Step 2: Apply type casting with boolean value conversion
            if "cast" in spec:
                # Get field definition for boolean value conversion
                field = None
                if config.source_schema:
                    field = config.source_schema.get_field(source_col)

                series = cls._apply_cast(series, spec["cast"], field)

            # Step 3: Apply null filling
            if "null_fill" in spec:
                series = series.fillna(spec["null_fill"])

            # Step 4: Rename if needed
            if target_name != source_col:
                result[target_name] = series
                columns_to_keep.append(target_name)
            else:
                result[source_col] = series
                if source_col not in columns_to_keep:
                    columns_to_keep.append(source_col)

        # Add unmapped columns if keep_only_mapped is False
        if not config.keep_only_mapped:
            mapped_sources = set(config.columns.keys())
            for col in df.columns:
                if col not in mapped_sources and col not in columns_to_keep:
                    columns_to_keep.append(col)

        # Select final columns in order
        return result[columns_to_keep]

    @staticmethod
    def _apply_cast(series: 'pd.Series', cast_type: str, field: 'SchemaField' = None) -> 'pd.Series':
        """
        Apply type casting to pandas Series using centralized type system.

        HYBRID STRATEGY: Skips custom types (safe_float, xml_string, etc.) as they
        are handled at the edges (Python layer) by ingress/egress helpers.
        Only applies NATIVE types (integer, string, boolean, etc.) using vectorized
        DataFrame operations for optimal performance.

        For boolean types, applies custom true_values/false_values conversion
        if specified in the field definition.

        Args:
            series: Pandas Series to cast
            cast_type: Target type (universal type or backend-specific)
            field: Optional SchemaField with boolean value definitions

        Returns:
            Casted pandas Series (or original if custom type)

        Raises:
            ValueError: If cast_type cannot be converted to pandas dtype
        """
        from mountainash.schema.config.types import normalize_type, UNIVERSAL_TO_PANDAS
        from mountainash.schema.config.custom_types import CustomTypeRegistry
        import logging

        logger = logging.getLogger(__name__)

        # HYBRID STRATEGY: Check if this is a custom type
        # Custom types are handled at edges (Python layer), not in DataFrame
        if not CustomTypeRegistry.is_native_type(cast_type):
            logger.debug(
                f"Skipping custom type '{cast_type}' - will be handled at edges "
                f"(Python layer) for optimal performance"
            )
            return series  # Return series unchanged

        try:
            # Normalize the type string and get corresponding pandas dtype
            universal_type = normalize_type(cast_type)

            # Special handling for boolean types with custom values
            if universal_type == "boolean" and field and (field.true_values or field.false_values):
                # Apply boolean value conversion
                # The result is already boolean, so we don't need to cast afterward
                return CastSchemaPandas._convert_boolean_values(series, field)

            # For non-boolean types (or boolean without custom values), apply standard cast
            pandas_dtype = UNIVERSAL_TO_PANDAS[universal_type]
            return series.astype(pandas_dtype)

        except (ValueError, KeyError) as e:
            # Provide helpful error message
            raise ValueError(
                f"Cannot cast to type '{cast_type}': {e}. "
                f"See schema_config.types for supported types."
            ) from e

    @staticmethod
    def _replace_missing_values(df: 'PandasFrame', missing_values: list[str]) -> 'PandasFrame':
        """
        Replace schema-level missing values with null across string columns only.

        Note: missing_values only applies to string/object columns since
        Frictionless spec defines them as string markers. Numeric/date columns
        are left unchanged to ensure type safety and consistent behavior.

        Args:
            df: Pandas DataFrame
            missing_values: List of string values to treat as null

        Returns:
            DataFrame with missing values replaced by None in string columns
        """
        pd = import_pandas()
        if not missing_values:
            return df

        # Only apply to string/object columns for type safety
        # Get string-like columns (object, string dtypes)
        string_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()

        if not string_cols:
            return df

        # Create a copy and replace only in string columns
        result = df.copy()
        result[string_cols] = result[string_cols].replace(missing_values, None)
        return result

    @staticmethod
    def _convert_boolean_values(series: 'pd.Series', field: 'SchemaField') -> 'pd.Series':
        """
        Convert string values to boolean using custom true_values/false_values.

        Args:
            series: Pandas Series (typically string column)
            field: SchemaField with true_values and/or false_values

        Returns:
            Series with boolean values mapped

        Example:
            field.true_values = ["yes", "Y", "true", "1"]
            field.false_values = ["no", "N", "false", "0"]
            "yes" → True, "no" → False, "maybe" → None
        """
        pd = import_pandas()

        # Create a mapping dict
        mapping = {}

        if field.true_values:
            for val in field.true_values:
                mapping[val] = True

        if field.false_values:
            for val in field.false_values:
                mapping[val] = False

        # Apply mapping, unmapped values become None
        return series.map(mapping)
