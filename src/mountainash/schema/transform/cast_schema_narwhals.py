"""
Narwhals universal column transformation strategy.

Implements column transformations using Narwhals universal DataFrame API.
Works as a fallback for any backend supported by Narwhals.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.lazy_imports import import_narwhals
from .base_schema_transform_strategy import BaseCastSchemaStrategy

if TYPE_CHECKING:
    from mountainash.core.types import NarwhalsFrame, NarwhalsLazyFrame
    from mountainash.schema.config import SchemaConfig, SchemaField



class CastSchemaNarwhals(BaseCastSchemaStrategy):
    """
    Narwhals universal column transformation strategy.

    Uses Narwhals API which provides a common interface across:
    - pandas
    - polars
    - pyarrow
    - any other backend Narwhals supports

    Note: Some features may have limitations due to Narwhals abstraction.
    """

    @classmethod
    def _apply(cls,
               df: 'NarwhalsFrame | NarwhalsLazyFrame',
               config: 'SchemaConfig') -> 'NarwhalsFrame | NarwhalsLazyFrame':
        """
        Apply column transformations using Narwhals universal API.

        Transformation order:
        1. Replace missing_values with null (schema-level)
        2. Apply type casting with boolean value conversion (field-level)
        3. Apply null filling
        4. Apply renaming

        Args:
            df: Narwhals DataFrame or LazyFrame
            config: SchemaConfig with transformation specs

        Returns:
            Transformed DataFrame (same type as input)
        """
        nw = import_narwhals()
        if nw is None:
            raise ImportError("narwhals is required for this operation")

        # Wrap in Narwhals if not already wrapped
        from mountainash.core.types import is_narwhals_dataframe, is_narwhals_lazyframe
        nw_df = nw.from_native(df) if not (is_narwhals_dataframe(df) or is_narwhals_lazyframe(df)) else df

        # Step 1: Apply missing_values replacement (schema-level)
        if config.source_schema and config.source_schema.missing_values:
            nw_df = cls._replace_missing_values(nw_df, config.source_schema.missing_values)

        expressions = []
        processed_target_names = set()

        # Process explicitly mapped columns
        for source_col, spec in config.columns.items():
            target_name = spec.get("rename", source_col)

            # Handle missing columns
            if source_col not in nw_df.columns:
                if "default" in spec:
                    # Add missing column with default value using nw.lit()
                    expr = nw.lit(spec["default"]).alias(target_name)
                    expressions.append(expr)
                    processed_target_names.add(target_name)
                elif config.strict:
                    # Strict mode: raise error for missing columns without defaults
                    raise ValueError(
                        f"Column '{source_col}' not found in DataFrame. "
                        f"Available columns: {nw_df.columns}"
                    )
                # Lenient mode: skip missing columns
                continue

            # Start with the source column
            expr = nw.col(source_col)

            # Step 2: Apply type casting with boolean value conversion
            if "cast" in spec:
                # Get field definition for boolean value conversion
                field = None
                if config.source_schema:
                    field = config.source_schema.get_field(source_col)

                expr = cls._apply_cast(expr, spec["cast"], field)

            # Apply null filling
            if "null_fill" in spec:
                expr = expr.fill_null(spec["null_fill"])

            # Apply renaming
            expressions.append(expr.alias(target_name))
            processed_target_names.add(target_name)

        # Add unmapped columns if keep_only_mapped is False
        if not config.keep_only_mapped:
            mapped_sources = set(config.columns.keys())
            for col in nw_df.columns:
                if col not in mapped_sources and col not in processed_target_names:
                    expressions.append(nw.col(col))

        # Select columns and return native
        result = nw_df.select(expressions)
        return result.to_native()

    @staticmethod
    def _apply_cast(expr: Any, cast_type: str, field: 'SchemaField' = None) -> Any:
        """
        Apply type casting using Narwhals with centralized type system.

        HYBRID STRATEGY: Skips custom types (safe_float, xml_string, etc.) as they
        are handled at the edges (Python layer) by ingress/egress helpers.
        Only applies NATIVE types (integer, string, boolean, etc.) using vectorized
        DataFrame operations for optimal performance.

        For boolean types, applies custom true_values/false_values conversion
        if specified in the field definition.

        Narwhals uses Polars-style types, so we leverage get_polars_type()
        and convert to Narwhals types.

        Args:
            expr: Narwhals expression to cast
            cast_type: Target type (universal type or backend-specific)
            field: Optional SchemaField with boolean value definitions

        Returns:
            Casted Narwhals expression (or original if custom type)

        Raises:
            ValueError: If cast_type cannot be converted to Narwhals type
        """
        from mountainash.schema.config.types import get_polars_type, normalize_type
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
            return expr  # Return expression unchanged

        nw = import_narwhals()

        try:
            # Normalize type and get Polars type (Narwhals uses same types)
            universal_type = normalize_type(cast_type)

            # Special handling for boolean types with custom values
            if universal_type == "boolean" and field and (field.true_values or field.false_values):
                # Apply boolean value conversion
                # The result is already boolean, so we don't need to cast afterward
                return CastSchemaNarwhals._convert_boolean_values(expr, field)

            # For non-boolean types (or boolean without custom values), apply standard cast
            polars_type = get_polars_type(universal_type)

            # Map Polars types to Narwhals types
            # Narwhals exposes similar types as attributes
            type_name = str(polars_type)  # e.g., "Int64", "Utf8", etc.

            # Map common Polars type names to Narwhals
            type_mapping = {
                "Int64": nw.Int64,
                "Utf8": nw.String,
                "Float64": nw.Float64,
                "Boolean": nw.Boolean,
                "Date": nw.Date,
                "Datetime": nw.Datetime,
            }

            narwhals_type = type_mapping.get(type_name)
            if narwhals_type is None:
                # Try direct attribute access for other types
                narwhals_type = getattr(nw, type_name, None)

            if narwhals_type is None:
                raise ValueError(f"Cannot map Polars type '{type_name}' to Narwhals")

            return expr.cast(narwhals_type)

        except (ValueError, KeyError, AttributeError) as e:
            # Provide helpful error message
            raise ValueError(
                f"Cannot cast to type '{cast_type}': {e}. "
                f"See schema_config.types for supported types."
            ) from e

    @staticmethod
    def _replace_missing_values(df: Any, missing_values: list[str]) -> Any:
        """
        Replace schema-level missing values with null across string columns only.

        Note: missing_values only applies to string columns since
        Frictionless spec defines them as string markers. Numeric/date columns
        are left unchanged to ensure type safety and consistent behavior.

        Uses Narwhals universal API to work across all backends.

        Args:
            df: Narwhals DataFrame or LazyFrame
            missing_values: List of string values to treat as null

        Returns:
            DataFrame with missing values replaced by None in string columns
        """
        nw = import_narwhals()
        if not missing_values:
            return df

        # Build expressions to replace missing values with null for each column
        expressions = []
        for col_name in df.columns:
            expr = nw.col(col_name)

            # Get column dtype - Narwhals exposes schema
            dtype = df.schema[col_name]

            # Only apply to string-like columns
            # Check for String type in Narwhals (unified across backends)
            is_string_like = dtype == nw.String

            if is_string_like:
                # Chain when().then().otherwise() for each missing value marker
                for missing_val in missing_values:
                    expr = nw.when(expr == missing_val).then(None).otherwise(expr)

            expressions.append(expr.alias(col_name))

        return df.select(expressions)

    @staticmethod
    def _convert_boolean_values(expr: Any, field: 'SchemaField') -> Any:
        """
        Convert string values to boolean using custom true_values/false_values.

        Uses Narwhals universal API for compatibility across backends.

        Args:
            expr: Narwhals expression (typically string column)
            field: SchemaField with true_values and/or false_values

        Returns:
            Expression with boolean values mapped

        Example:
            field.true_values = ["yes", "Y", "true", "1"]
            field.false_values = ["no", "N", "false", "0"]
            "yes" → True, "no" → False, "maybe" → None
        """
        nw = import_narwhals()

        # Build boolean condition using is_in() for membership testing
        true_condition = expr.is_in(field.true_values) if field.true_values else nw.lit(False)
        false_condition = expr.is_in(field.false_values) if field.false_values else nw.lit(False)

        # Return boolean result: True if in true_values, False if in false_values, None otherwise
        # Note: Narwhals requires nested when() statements, not chained .when().then().when()
        return nw.when(true_condition).then(True).otherwise(
            nw.when(false_condition).then(False).otherwise(None)
        )
