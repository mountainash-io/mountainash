"""
Ibis-specific column transformation strategy.

Implements column transformations using Ibis expression API.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional


from mountainash.core.lazy_imports import import_ibis
from .base_schema_transform_strategy import BaseCastSchemaStrategy

if TYPE_CHECKING:
    from mountainash.core.types import IbisTable
    from mountainash.schema.config import SchemaConfig, SchemaField



class CastSchemaIbis(BaseCastSchemaStrategy):
    """
    Ibis Table column transformation strategy.

    Uses Ibis expression API for column operations:
    - Rename: expr.name(new_name)
    - Cast: expr.cast(type)
    - Null fill: expr.fill_null(value)
    - Defaults: ibis.literal(value).name(col_name)

    Works with all Ibis backends (SQL databases, DuckDB, etc.)
    """

    @classmethod
    def _lit(cls, value: Any, alias: Optional[str] = None) -> Any:
        """
        Create an Ibis literal expression.

        Args:
            value: Value to convert to Ibis literal

        Returns:
            Ibis literal expression
        """
        ibis = import_ibis()
        if ibis is None:
            raise ImportError("ibis is required for this operation")

        if alias:
            return ibis.literal(value).alias(alias)
        else:
            return ibis.literal(value)


    @classmethod
    def _col(cls, column: str, alias: Optional[str] = None) -> Any:
        """
        Create an Ibis column expression.

        Args:
            value: Value to convert to Ibis literal

        Returns:
            Ibis literal expression
        """
        ibis = import_ibis()
        if ibis is None:
            raise ImportError("ibis is required for this operation")

        if alias:
            return ibis.col(column).alias(alias)
        else:
            return ibis.col(column)

    @classmethod
    def _fill_null(cls, expr: str, value: Any) -> Any:
        """
        Create an Ibis column expression.

        Args:
            value: Value to convert to Ibis literal

        Returns:
            Ibis literal expression
        """

        return expr.fill_null(value)


    @classmethod
    def _apply(cls,
               df: 'IbisTable',
               config: 'SchemaConfig') -> 'IbisTable':
        """
        Apply column transformations to Ibis Table.

        Transformation order:
        1. Replace missing_values with null (schema-level)
        2. Apply type casting with boolean value conversion (field-level)
        3. Apply null filling
        4. Apply renaming

        Args:
            df: Ibis Table
            config: ColumnTransformConfig with transformation specs

        Returns:
            Transformed Ibis Table
        """
        ibis = import_ibis()
        if ibis is None:
            raise ImportError("ibis is required for this operation")

        # Step 1: Apply missing_values replacement (schema-level)
        if config.source_schema and config.source_schema.missing_values:
            df = cls._replace_missing_values(df, config.source_schema.missing_values)

        selections = []
        processed_target_names = set()

        # Process explicitly mapped columns
        for source_col, spec in config.columns.items():
            target_name = spec.get("rename", source_col)

            # Handle missing columns
            if source_col not in df.columns:

                if "default" in spec:
                    # Create a literal column with default value
                    selections.append(cls._lit( spec["default"], alias = target_name))
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
            expr = cls._col(source_col)

            # Step 2: Apply type casting with boolean value conversion
            if "cast" in spec:
                # Get field definition for boolean value conversion
                field = None
                if config.source_schema:
                    field = config.source_schema.get_field(source_col)

                expr = cls._apply_cast(expr, spec["cast"], field)

            # Apply null filling
            if "null_fill" in spec:
                expr = cls._fill_null(expr, spec["null_fill"])

            # Apply renaming
            selections.append(expr.name(target_name))
            processed_target_names.add(target_name)

        # Add unmapped columns if keep_only_mapped is False
        if not config.keep_only_mapped:
            mapped_sources = set(config.columns.keys())
            for col in df.columns:
                if col not in mapped_sources and col not in processed_target_names:
                    selections.append(cls._col(col))

        # Select columns
        return df.select(selections)

    @staticmethod
    def _apply_cast(expr: Any, cast_type: str, field: 'SchemaField' = None) -> Any:
        """
        Apply type casting using Ibis with centralized type system.

        HYBRID STRATEGY: Skips custom types (safe_float, xml_string, etc.) as they
        are handled at the edges (Python layer) by ingress/egress helpers.
        Only applies NATIVE types (integer, string, boolean, etc.) using vectorized
        DataFrame operations for optimal performance.

        For boolean types, applies custom true_values/false_values conversion
        if specified in the field definition.

        Args:
            expr: Ibis expression to cast
            cast_type: Target type (universal type or backend-specific)
            field: Optional SchemaField with boolean value definitions

        Returns:
            Casted Ibis expression (or original if custom type)

        Raises:
            ValueError: If cast_type cannot be converted to Ibis type
        """
        from mountainash.schema.config.types import normalize_type, UNIVERSAL_TO_IBIS
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
            # Normalize the type string and get corresponding Ibis type
            universal_type = normalize_type(cast_type)

            # Special handling for boolean types with custom values
            if universal_type == "boolean" and field and (field.true_values or field.false_values):
                # Apply boolean value conversion
                # The result is already boolean, so we don't need to cast afterward
                return CastSchemaIbis._convert_boolean_values(expr, field)

            # For non-boolean types (or boolean without custom values), apply standard cast
            ibis_type = UNIVERSAL_TO_IBIS[universal_type]

            return expr.cast(ibis_type)

        except (ValueError, KeyError) as e:
            # Provide helpful error message
            raise ValueError(
                f"Cannot cast to type '{cast_type}': {e}. "
                f"See schema_config.types for supported types."
            ) from e

    @staticmethod
    def _replace_missing_values(df: 'IbisTable', missing_values: list[str]) -> 'IbisTable':
        """
        Replace schema-level missing values with null across string columns only.

        Note: missing_values only applies to string columns since
        Frictionless spec defines them as string markers. Numeric/date columns
        are left unchanged to ensure type safety and consistent behavior.

        Args:
            df: Ibis Table
            missing_values: List of string values to treat as null

        Returns:
            Table with missing values replaced by None in string columns
        """
        ibis = import_ibis()
        if not missing_values:
            return df

        # Build selection expressions for all columns
        selections = []
        for col_name in df.columns:
            expr = df[col_name]

            # Get column type from schema
            col_type = df[col_name].type()

            # Only apply to string columns
            # Ibis has String type
            is_string_like = col_type.is_string()

            if is_string_like:
                # Chain case statements for each missing value marker
                for missing_val in missing_values:
                    expr = ibis.case().when(expr == missing_val, None).else_(expr).end()

            selections.append(expr.name(col_name))

        return df.select(selections)

    @staticmethod
    def _convert_boolean_values(expr: Any, field: 'SchemaField') -> Any:
        """
        Convert string values to boolean using custom true_values/false_values.

        Uses Ibis case expressions for SQL compatibility.

        Args:
            expr: Ibis expression (typically string column)
            field: SchemaField with true_values and/or false_values

        Returns:
            Expression with boolean values mapped

        Example:
            field.true_values = ["yes", "Y", "true", "1"]
            field.false_values = ["no", "N", "false", "0"]
            "yes" → True, "no" → False, "maybe" → None
        """
        ibis = import_ibis()

        # Build case expression
        case = ibis.case()

        # Add true value conditions
        if field.true_values:
            for val in field.true_values:
                case = case.when(expr == val, True)

        # Add false value conditions
        if field.false_values:
            for val in field.false_values:
                case = case.when(expr == val, False)

        # Unmapped values become None
        return case.else_(None).end()
