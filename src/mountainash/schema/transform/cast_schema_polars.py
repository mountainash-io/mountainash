"""
Polars-specific column transformation strategy.

Implements column transformations using Polars expressions and select() API.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.lazy_imports import import_polars
from .base_schema_transform_strategy import BaseCastSchemaStrategy


if TYPE_CHECKING:
    import polars as pl
    from mountainash.core.types import PolarsFrame, PolarsLazyFrame
    from mountainash.schema.config import SchemaConfig, SchemaField



class CastSchemaPolars(BaseCastSchemaStrategy):
    """
    Polars DataFrame column transformation strategy.

    Uses Polars expressions for efficient column operations:
    - Rename: col.alias()
    - Cast: col.cast()
    - Null fill: col.fill_null()
    - Defaults: pl.lit().alias()
    """

    @classmethod
    def _apply(cls,
               df: 'PolarsFrame',
               config: 'SchemaConfig') -> 'PolarsFrame':
        """
        Apply column transformations to Polars DataFrame.

        Transformation order:
        1. Replace missing_values with null (schema-level)
        2. Apply type casting with boolean value conversion (field-level)
        3. Apply null filling
        4. Apply renaming

        Args:
            df: Polars DataFrame
            config: SchemaConfig with transformation specs

        Returns:
            Transformed Polars DataFrame
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Step 1: Apply missing_values replacement (schema-level)
        if config.source_schema and config.source_schema.missing_values:
            df = cls._replace_missing_values(df, config.source_schema.missing_values)

        expressions = []
        processed_target_names = set()

        # Process explicitly mapped columns
        for source_col, spec in config.columns.items():
            target_name = spec.get("rename", source_col)

            # Handle missing columns
            if source_col not in df.columns:
                if "default" in spec:
                    # Add missing column with default value
                    expressions.append(pl.lit(spec["default"]).alias(target_name))
                    processed_target_names.add(target_name)
                elif config.strict:
                    # Strict mode: raise error for missing columns without defaults
                    raise ValueError(
                        f"Column '{source_col}' not found in DataFrame. "
                        f"Available columns: {df.columns}"
                    )
                # Lenient mode: skip missing columns
                continue

            # Start with the source column
            expr = pl.col(source_col)

            # Step 2: Apply type casting with boolean value conversion
            if "cast" in spec:
                # Get field definition for boolean value conversion
                field = None
                if config.source_schema:
                    field = config.source_schema.get_field(source_col)

                expr = cls._apply_cast(expr, spec["cast"], field)

            # Step 3: Apply null filling if specified (for existing columns)
            if "null_fill" in spec:
                expr = expr.fill_null(spec["null_fill"])

            # Step 4: Apply renaming (or keep original name)
            expressions.append(expr.alias(target_name))
            processed_target_names.add(target_name)

        # Add unmapped columns if keep_only_mapped is False
        if not config.keep_only_mapped:
            mapped_sources = set(config.columns.keys())
            for col in df.columns:
                if col not in mapped_sources and col not in processed_target_names:
                    expressions.append(pl.col(col))

        return df.select(expressions)

    @staticmethod
    def _apply_cast(expr: 'pl.Expr', cast_type: str, field: 'SchemaField' = None) -> 'pl.Expr':
        """
        Apply type casting to Polars expression using centralized type system.

        HYBRID STRATEGY: Skips custom types (safe_float, xml_string, etc.) as they
        are handled at the edges (Python layer) by ingress/egress helpers.
        Only applies NATIVE types (integer, string, boolean, etc.) using vectorized
        DataFrame operations for optimal performance.

        For boolean types, applies custom true_values/false_values conversion
        if specified in the field definition.

        Args:
            expr: Polars expression to cast
            cast_type: Target type (universal type or backend-specific)
            field: Optional SchemaField with boolean value definitions

        Returns:
            Casted Polars expression (or original if custom type)

        Raises:
            ValueError: If cast_type cannot be converted to Polars type
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

        try:
            # Normalize the type string and get corresponding Polars type
            universal_type = normalize_type(cast_type)

            # Special handling for boolean types with custom values
            if universal_type == "boolean" and field and (field.true_values or field.false_values):
                # Apply boolean value conversion
                # The result is already boolean, so we don't need to cast afterward
                return CastSchemaPolars._convert_boolean_values(expr, field)

            # For non-boolean types (or boolean without custom values), apply standard cast
            polars_type = get_polars_type(universal_type)
            return expr.cast(polars_type, strict=False)

        except (ValueError, KeyError) as e:
            # Provide helpful error message
            raise ValueError(
                f"Cannot cast to type '{cast_type}': {e}. "
                f"See schema_config.types for supported types."
            ) from e

    @staticmethod
    def _replace_missing_values(df: 'PolarsFrame', missing_values: list[str]) -> 'PolarsFrame':
        """
        Replace schema-level missing values with null across string columns only.

        Note: missing_values only applies to string/categorical columns since
        Frictionless spec defines them as string markers. Numeric/date columns
        are left unchanged to avoid type comparison errors.

        Args:
            df: Polars DataFrame
            missing_values: List of string values to treat as null

        Returns:
            DataFrame with missing values replaced by null in string columns
        """
        pl = import_polars()
        if not missing_values:
            return df

        # Build replacement expressions for all columns
        expressions = []
        for col_name in df.columns:
            expr = pl.col(col_name)
            dtype = df[col_name].dtype

            # Only apply missing_values replacement to string-like columns
            # Check for Utf8, String, Categorical to avoid type comparison errors
            is_string_like = (
                dtype == pl.Utf8 or
                dtype == pl.String or
                dtype == pl.Categorical or
                str(dtype).startswith('Utf8') or
                str(dtype).startswith('String') or
                str(dtype).startswith('Categorical')
            )

            if is_string_like:
                # For each missing value, replace it with null
                for missing_val in missing_values:
                    # Use when-then to replace matching values with null
                    expr = pl.when(expr == missing_val).then(None).otherwise(expr)

            expressions.append(expr.alias(col_name))

        return df.select(expressions)

    @staticmethod
    def _convert_boolean_values(expr: 'pl.Expr', field: 'SchemaField') -> 'pl.Expr':
        """
        Convert string values to boolean using custom true_values/false_values.

        Args:
            expr: Polars expression (typically string column)
            field: SchemaField with true_values and/or false_values

        Returns:
            Expression with boolean values mapped

        Example:
            field.true_values = ["yes", "Y", "true", "1"]
            field.false_values = ["no", "N", "false", "0"]
            "yes" → True, "no" → False, "maybe" → None
        """
        pl = import_polars()

        # Build a when-then chain for all mappings
        # We need to check true_values, then false_values, then default to None

        # Build condition for true values
        if field.true_values:
            true_condition = expr.is_in(field.true_values)
        else:
            true_condition = pl.lit(False)  # Never matches

        # Build condition for false values
        if field.false_values:
            false_condition = expr.is_in(field.false_values)
        else:
            false_condition = pl.lit(False)  # Never matches

        # Create the expression: if in true_values -> True, elif in false_values -> False, else None
        return (
            pl.when(true_condition)
            .then(True)
            .when(false_condition)
            .then(False)
            .otherwise(None)
        )


class CastSchemaPolarsLazy(BaseCastSchemaStrategy):
    """
    Polars LazyFrame column transformation strategy.

    Uses the same Polars expressions as CastSchemaPolars since
    LazyFrame supports the same select() API.
    """

    @classmethod
    def _apply(cls,
               df: 'PolarsLazyFrame',
               config: 'SchemaConfig') -> 'PolarsLazyFrame':
        """
        Apply column transformations to Polars LazyFrame.

        Transformation order:
        1. Replace missing_values with null (schema-level)
        2. Apply type casting with boolean value conversion (field-level)
        3. Apply null filling
        4. Apply renaming

        Args:
            df: Polars LazyFrame
            config: SchemaConfig with transformation specs

        Returns:
            Transformed Polars LazyFrame
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Step 1: Apply missing_values replacement (schema-level)
        # Note: This won't work for LazyFrame since we can't access df.columns
        # We'll skip this for LazyFrame and only apply during column processing
        # Users should use DataFrame for missing_values functionality

        expressions = []
        processed_target_names = set()

        # Process explicitly mapped columns
        for source_col, spec in config.columns.items():
            target_name = spec.get("rename", source_col)

            # Handle missing columns with default values
            # Note: For LazyFrame, we can't check columns without collecting
            # So we assume the column exists and let Polars handle missing columns
            if "default" in spec:
                # Try to use the source column, fallback to default if it doesn't exist
                # This is a limitation of LazyFrame - we can't check columns without collecting
                try:
                    expr = pl.col(source_col)
                except Exception:
                    expr = pl.lit(spec["default"])
            else:
                expr = pl.col(source_col)

            # Step 2: Apply type casting with boolean value conversion
            if "cast" in spec:
                # Get field definition for boolean value conversion
                field = None
                if config.source_schema:
                    field = config.source_schema.get_field(source_col)

                expr = CastSchemaPolars._apply_cast(expr, spec["cast"], field)

            # Step 3: Apply null filling if specified
            if "null_fill" in spec:
                expr = expr.fill_null(spec["null_fill"])

            # Step 4: Apply renaming (or keep original name)
            expressions.append(expr.alias(target_name))
            processed_target_names.add(target_name)

        # Add unmapped columns if keep_only_mapped is False
        # For LazyFrame, we use pl.all() to select all columns
        # and then exclude the ones we've already processed
        if not config.keep_only_mapped:
            mapped_sources = set(config.columns.keys())
            # Use pl.all().exclude() to get unmapped columns
            expressions.append(pl.all().exclude(list(mapped_sources)))

        return df.select(expressions)
