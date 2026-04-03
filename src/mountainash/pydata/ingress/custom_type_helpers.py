"""
Helper functions for custom type conversion in ingress modules.

Implements the hybrid strategy for optimal performance:
- Custom converters: Apply at EDGES (Python layer, before DataFrame)
- Native conversions: Apply in CENTER (DataFrame layer, vectorized)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
import logging

if TYPE_CHECKING:
    from mountainash.core.types import PolarsFrame
    from mountainash.typespec.spec import TypeSpec, FieldSpec

logger = logging.getLogger(__name__)


def separate_conversions(
    spec: "TypeSpec",
) -> Tuple[Dict[str, "FieldSpec"], Dict[str, "FieldSpec"], Dict[str, "FieldSpec"]]:
    """
    Separate a TypeSpec into three conversion tiers.

    This is a standalone replacement for SchemaConfig.separate_conversions() that
    operates on TypeSpec/FieldSpec instead of raw dicts.

    Returns:
        (python_only, narwhals, native) — three dicts keyed by source_name:

        - python_only: Fields with a custom_cast that has no Narwhals implementation
          (row-by-row Python conversion required)
        - narwhals: Fields with a custom_cast that has a vectorized Narwhals implementation
        - native: All other fields (no custom cast — handled by compile_conform)

    Example:
        >>> spec = TypeSpec(fields=[
        ...     FieldSpec(name="amount", custom_cast="safe_float"),  # → narwhals
        ...     FieldSpec(name="id", type=UniversalType.INTEGER),    # → native
        ... ])
        >>> python_only, narwhals, native = separate_conversions(spec)
    """
    from mountainash.typespec.custom_types import CustomTypeRegistry

    python_only: Dict[str, "FieldSpec"] = {}
    narwhals: Dict[str, "FieldSpec"] = {}
    native: Dict[str, "FieldSpec"] = {}

    for field in spec.fields:
        cast_type = field.custom_cast

        if cast_type is None:
            # No custom cast — route to native (compile_conform handles type + rename)
            native[field.source_name] = field
            continue

        if CustomTypeRegistry.has_converter(cast_type):
            if CustomTypeRegistry.is_vectorized(cast_type):
                narwhals[field.source_name] = field
            else:
                python_only[field.source_name] = field
        else:
            # Unknown custom_cast — treat as native and let compile_conform handle it
            native[field.source_name] = field

    return python_only, narwhals, native


def apply_custom_converters_to_dict(
    data_dict: Dict[str, Any],
    custom_conversions: Dict[str, "FieldSpec"],
) -> Dict[str, Any]:
    """
    Apply custom type converters to a single dictionary.

    This is TIER 3 (Python layer) of the hybrid strategy:
    - Apply ONLY custom converters (safe_float, xml_string, etc.)
    - Leave native conversions for DataFrame layer (FAST!)

    Args:
        data_dict: Dictionary of field_name -> value
        custom_conversions: Dict of columns (keyed by source_name) with FieldSpec
                           containing custom_cast. Returned by separate_conversions().

    Returns:
        Dictionary with custom conversions applied

    Example:
        >>> field = FieldSpec(name="amount", custom_cast="safe_float")
        >>> result = apply_custom_converters_to_dict({"amount": "42.5"}, {"amount": field})
        >>> result["amount"]
        42.5
    """
    from mountainash.typespec.custom_types import CustomTypeRegistry

    converted_dict = {}

    for field_name, value in data_dict.items():
        if field_name in custom_conversions:
            field_spec = custom_conversions[field_name]
            cast_type = field_spec.custom_cast

            if cast_type is not None:
                try:
                    value = CustomTypeRegistry.convert(
                        value,
                        cast_type,
                        field_name=field_name,
                        raise_on_error=False,
                    )
                except Exception as e:
                    logger.warning(
                        f"Custom conversion failed for field '{field_name}' "
                        f"with type '{cast_type}': {e}. Using original value."
                    )

        converted_dict[field_name] = value

    return converted_dict


def apply_custom_converters_to_dicts(
    data_dicts: List[Dict[str, Any]],
    custom_conversions: Dict[str, "FieldSpec"],
) -> List[Dict[str, Any]]:
    """
    Apply custom type converters to a list of dictionaries.

    This is TIER 3 (Python layer) of the hybrid strategy.

    Args:
        data_dicts: List of dictionaries
        custom_conversions: Dict of columns (keyed by source_name) with FieldSpec
                           containing custom_cast.

    Returns:
        List of dictionaries with custom conversions applied
    """
    if not custom_conversions:
        return data_dicts

    return [
        apply_custom_converters_to_dict(data_dict, custom_conversions)
        for data_dict in data_dicts
    ]


def apply_native_conversions_to_dataframe(
    df: "PolarsFrame",
    native_conversions: Dict[str, "FieldSpec"],
) -> "PolarsFrame":
    """
    Apply native type conversions to a DataFrame using vectorized operations.

    This is TIER 1 (DataFrame layer) of the hybrid strategy:
    - Apply ONLY native conversions (string→int, float→bool)
    - Use vectorized operations (MUCH FASTER - 12x!)
    - Apply other native operations (rename, null_fill) via compile_conform

    Args:
        df: Polars DataFrame
        native_conversions: Dict of columns (keyed by source_name) with FieldSpec.
                           Returned by separate_conversions().

    Returns:
        DataFrame with native conversions applied
    """
    from mountainash.core.lazy_imports import import_polars
    from mountainash.typespec.universal_types import get_polars_type, UniversalType

    pl = import_polars()
    if pl is None:
        raise ImportError("polars is required for this operation")

    if not native_conversions:
        return df

    # Build cast dictionary for vectorized casting
    cast_dict = {}
    for col_name, field_spec in native_conversions.items():
        # Only cast if there's a non-ANY type declared and column exists
        if field_spec.type and field_spec.type != UniversalType.ANY and col_name in df.columns:
            cast_type_str = field_spec.type.value
            try:
                polars_type = get_polars_type(cast_type_str)
                cast_dict[col_name] = polars_type
            except (KeyError, ImportError) as e:
                logger.warning(
                    f"Could not get Polars type for '{cast_type_str}' "
                    f"(column '{col_name}'): {e}. Skipping cast."
                )

    # Apply vectorized cast (MUCH FASTER than element-wise!)
    if cast_dict:
        try:
            df = df.cast(cast_dict)
            logger.info(
                f"Applied native conversions (vectorized) to {len(cast_dict)} columns"
            )
        except Exception as e:
            logger.warning(
                f"Vectorized cast failed: {e}. "
                "Falling back to column-by-column casting."
            )
            for col_name, dtype in cast_dict.items():
                try:
                    df = df.with_columns(pl.col(col_name).cast(dtype))
                except Exception as col_error:
                    logger.warning(
                        f"Cast failed for column '{col_name}': {col_error}. "
                        "Keeping original type."
                    )

    # Apply other native operations (rename, null_fill) via compile_conform
    from mountainash.typespec.spec import TypeSpec
    from mountainash.conform.compiler import compile_conform

    native_spec = TypeSpec(
        fields=[f for f in native_conversions.values()],
        keep_only_mapped=False,
    )
    try:
        df = compile_conform(native_spec, df)
    except Exception as e:
        logger.warning(
            f"Error applying native operations via compile_conform: {e}. "
            "DataFrame may not have all operations applied."
        )

    return df


def _apply_narwhals_custom_converters(
    df: "PolarsFrame",
    narwhals_custom: Dict[str, "FieldSpec"],
) -> "PolarsFrame":
    """
    Apply Narwhals-vectorized custom converters to DataFrame.

    Follows the filter_expressions pattern:
    1. Convert to Narwhals if not already
    2. Apply Narwhals expressions (vectorized!)
    3. Convert back to native format

    Args:
        df: DataFrame to transform
        narwhals_custom: Dict of column specs (keyed by source_name) with FieldSpec
                        containing custom_cast.

    Returns:
        DataFrame with Narwhals custom conversions applied
    """
    from mountainash.core.lazy_imports import import_narwhals
    from mountainash.typespec.custom_types import CustomTypeRegistry

    nw = import_narwhals()
    if nw is None:
        raise ImportError("narwhals is required for vectorized custom type conversion")

    from mountainash.core.types import is_narwhals_dataframe, is_narwhals_lazyframe
    was_native = not (is_narwhals_dataframe(df) or is_narwhals_lazyframe(df))
    nw_df = nw.from_native(df) if was_native else df

    for col_name, field_spec in narwhals_custom.items():
        cast_type = field_spec.custom_cast

        narwhals_converter = CustomTypeRegistry.get_narwhals_converter(cast_type)
        if narwhals_converter is None:
            logger.warning(
                f"Column '{col_name}' marked as Narwhals custom type '{cast_type}' "
                "but no Narwhals converter found - skipping"
            )
            continue

        expr_builder = narwhals_converter(col_name)
        col_expr = expr_builder(nw_df)

        # Use field.name as target (handles rename_from aliasing)
        target_name = field_spec.name

        nw_df = nw_df.with_columns(col_expr.alias(target_name))

        logger.debug(
            f"Applied Narwhals custom converter '{cast_type}' to column '{col_name}' "
            f"→ '{target_name}' (vectorized)"
        )

    result = nw_df.to_native() if was_native else nw_df
    return result


def apply_hybrid_conversion(
    data_dicts: List[Dict[str, Any]],
    spec: Optional["TypeSpec"] = None,
) -> "PolarsFrame":
    """
    Apply THREE-TIER hybrid conversion strategy with Narwhals vectorization.

    This implements the VECTORIZED THREE-TIER HYBRID ARCHITECTURE:

    TIER 3 (Python Layer - EDGES):
        - Extract data from Python objects
        - Apply PYTHON-ONLY custom converters (no Narwhals implementation)
        - Leave vectorizable conversions for DataFrame

    TIER 2 (Narwhals Layer - CENTER):
        - Apply NARWHALS CUSTOM converters (vectorized expressions, 2.5-10x faster!)

    TIER 1 (DataFrame Layer - CENTER):
        - Apply NATIVE conversions (string→int, vectorized via compile_conform)
        - Apply other native operations (rename, null_fill)

    Args:
        data_dicts: List of dictionaries to convert
        spec: Optional TypeSpec with field specifications

    Returns:
        Polars DataFrame with hybrid conversions applied
    """
    from mountainash.core.lazy_imports import import_polars

    pl = import_polars()
    if pl is None:
        raise ImportError("polars is required for this operation")

    if spec is None:
        return pl.DataFrame(data_dicts, strict=False)

    # STEP 1: Separate conversions into THREE tiers
    python_only, narwhals_custom, native = separate_conversions(spec)

    logger.info(
        f"Three-tier conversion: {len(python_only)} Python-only custom, "
        f"{len(narwhals_custom)} Narwhals custom (vectorized), "
        f"{len(native)} native conversions"
    )

    # STEP 2: Apply PYTHON-ONLY custom converters at edges (TIER 3)
    if python_only:
        data_dicts = apply_custom_converters_to_dicts(data_dicts, python_only)
        logger.debug(f"Applied Python-only custom converters to {len(data_dicts)} records")

    # STEP 3: Create DataFrame
    df = pl.DataFrame(data_dicts, strict=False)

    # STEP 4: Apply NARWHALS CUSTOM converters (TIER 2 — vectorized expressions)
    if narwhals_custom:
        df = _apply_narwhals_custom_converters(df, narwhals_custom)
        logger.debug(f"Applied {len(narwhals_custom)} Narwhals custom converters (vectorized)")

    # STEP 5: Apply NATIVE operations via compile_conform (TIER 1)
    if native:
        from mountainash.typespec.spec import TypeSpec
        from mountainash.conform.compiler import compile_conform

        native_spec = TypeSpec(
            fields=[f for f in native.values()],
            keep_only_mapped=False,
        )
        try:
            df = compile_conform(native_spec, df)
        except Exception as e:
            logger.warning(
                f"Error applying native operations via compile_conform: {e}. "
                "DataFrame may not have all operations applied."
            )

    return df


__all__ = [
    "separate_conversions",
    "apply_custom_converters_to_dict",
    "apply_custom_converters_to_dicts",
    "apply_native_conversions_to_dataframe",
    "_apply_narwhals_custom_converters",
    "apply_hybrid_conversion",
]
