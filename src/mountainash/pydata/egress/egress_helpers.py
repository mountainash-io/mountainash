"""
Helper functions for hybrid conversion strategy in egress (DataFrame → Python data).

Implements the THREE-TIER HYBRID ARCHITECTURE for egress:
- TIER 1 (DataFrame layer): Apply NATIVE conversions (vectorized, FAST!)
- TIER 2 (Extraction): Efficient bulk extraction to Python data
- TIER 3 (Python layer): Apply CUSTOM converters after extraction

This is the reverse of ingress:
- Ingress: Python → (custom) → DataFrame → (native) → Final DataFrame
- Egress: DataFrame → (native) → Temp DataFrame → (extract) → Python → (custom) → Final Python

Performance: ~10x faster than applying custom conversions in DataFrame!
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
import logging

if TYPE_CHECKING:
    from mountainash.schema.config import SchemaConfig
    from mountainash.core.types import SupportedDataFrames


from mountainash.schema.config import SchemaConfig
from mountainash.schema.transform import SchemaTransformFactory

logger = logging.getLogger(__name__)


def apply_native_conversions_for_egress(
    df: 'SupportedDataFrames',
    schema_config: Optional['SchemaConfig'] = None
) -> 'SupportedDataFrames':
    """
    Apply NATIVE conversions in DataFrame before extraction (TIER 1).

    This applies only native type conversions that can be done efficiently
    in the DataFrame using vectorized operations. Custom converters are
    skipped here and will be applied after extraction.

    Args:
        df: Input DataFrame (any backend)
        schema_config: Schema configuration with conversions

    Returns:
        DataFrame with native conversions applied

    Example:
        >>> config = SchemaConfig(columns={
        ...     "id": {"cast": "integer"},           # Native - apply here
        ...     "amount": {"cast": "safe_float"},    # Custom - skip here
        ... })
        >>> df = apply_native_conversions_for_egress(df, config)
        >>> # Only 'id' cast applied, 'amount' left for post-extraction
    """
    if schema_config is None:
        return df

    # Separate conversions into three tiers
    python_only_custom, narwhals_custom, native_convs = schema_config.separate_conversions()

    # For egress, combine all custom types (both Python-only and Narwhals)
    # because they'll be applied as Python converters after extraction
    custom_convs = {**python_only_custom, **narwhals_custom}

    logger.info(
        f"Egress hybrid: {len(native_convs)} native conversions in DataFrame, "
        f"{len(custom_convs)} custom conversions deferred to Python layer "
        f"(Python-only: {len(python_only_custom)}, Narwhals: {len(narwhals_custom)})"
    )

    # Build a config that applies ALL operations but removes custom casts
    # This ensures operations like rename work even for columns with custom casts


    native_only_columns = {}
    for col_name, spec in schema_config.columns.items():
        # Copy the spec
        native_spec = spec.copy()

        # If this column has a custom cast, remove it from the spec
        if "cast" in native_spec and col_name in custom_convs:
            # Custom cast - remove it, but keep other operations (rename, null_fill, etc.)
            del native_spec["cast"]

        # Only include if there are remaining operations to perform
        if native_spec:
            native_only_columns[col_name] = native_spec

    # Apply native operations if any
    if native_only_columns:
        native_config = SchemaConfig(
            columns=native_only_columns,
            keep_only_mapped=schema_config.keep_only_mapped,
            strict=schema_config.strict
        )

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        df = strategy.apply(df, native_config)

        logger.debug(f"Applied native operations to DataFrame")

    return df


def apply_custom_converters_to_python_data(
    data: List[Any],
    schema_config: Optional['SchemaConfig'] = None,
    data_format: str = "dict"
) -> List[Any]:
    """
    Apply CUSTOM converters to extracted Python data (TIER 3).

    This applies custom type converters after data has been extracted from
    the DataFrame. Works with both dictionaries and named tuples.

    IMPORTANT: After native conversions (which includes renames), the extracted
    data uses TARGET column names. We need to map custom conversions from
    source names to target names to match the data.

    Args:
        data: List of dicts or named tuples extracted from DataFrame
        schema_config: Schema configuration with conversions
        data_format: Format of data - "dict" or "namedtuple"

    Returns:
        List with custom conversions applied

    Example:
        >>> config = SchemaConfig(columns={
        ...     "amount": {"cast": "safe_float"}
        ... })
        >>> data = [{"amount": "42.5"}, {"amount": "99.9"}]
        >>> result = apply_custom_converters_to_python_data(data, config, "dict")
        >>> result
        [{'amount': 42.5}, {'amount': 99.9}]
    """
    logger.debug(f"EGRESS TRACE: apply_custom_converters_to_python_data called")
    logger.debug(f"  schema_config: {schema_config}")
    logger.debug(f"  data_format: {data_format}")
    logger.debug(f"  data length: {len(data) if data else 0}")

    if schema_config is None or not data:
        logger.debug(f"  Returning early: schema_config={schema_config}, data={data}")
        return data

    # Separate conversions - for egress, combine all custom types
    python_only_custom, narwhals_custom, _ = schema_config.separate_conversions()
    custom_convs = {**python_only_custom, **narwhals_custom}

    logger.debug(f"  Custom conversions: {custom_convs}")

    if not custom_convs:
        # No custom conversions to apply
        logger.debug(f"  No custom conversions, returning unchanged")
        return data

    logger.info(f"Applying {len(custom_convs)} custom converters to {len(data)} records")

    # Map custom conversions from source names to target names
    # (DataFrame columns have been renamed by native conversions)
    target_custom_convs = {}
    for source_col, spec in custom_convs.items():
        target_col = spec.get("rename", source_col)
        target_custom_convs[target_col] = spec

    from mountainash.schema.config.custom_types import CustomTypeRegistry

    # Apply conversions based on data format
    if data_format == "dict":
        return _apply_custom_to_dicts(data, target_custom_convs)
    elif data_format == "namedtuple":
        return _apply_custom_to_namedtuples(data, target_custom_convs)
    else:
        logger.warning(f"Unknown data format '{data_format}', returning data unchanged")
        return data


def _apply_custom_to_dicts(
    data_dicts: List[Dict[str, Any]],
    custom_conversions: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Apply custom converters to list of dictionaries.

    Args:
        data_dicts: List of dictionaries
        custom_conversions: Dict of columns with custom converters

    Returns:
        List of dictionaries with custom conversions applied
    """
    from mountainash.schema.config.custom_types import CustomTypeRegistry

    converted_data = []

    for row_dict in data_dicts:
        converted_row = {}

        for field_name, value in row_dict.items():
            # Check if this field needs custom conversion
            if field_name in custom_conversions:
                spec = custom_conversions[field_name]

                # Apply custom converter if configured
                if "cast" in spec:
                    cast_type = spec["cast"]
                    try:
                        value = CustomTypeRegistry.convert(
                            value,
                            cast_type,
                            field_name=field_name,
                            raise_on_error=False
                        )
                    except Exception as e:
                        logger.warning(
                            f"Custom conversion failed for field '{field_name}' "
                            f"with type '{cast_type}': {e}. Using original value."
                        )

            converted_row[field_name] = value

        converted_data.append(converted_row)

    return converted_data


def _apply_custom_to_namedtuples(
    named_tuples: List[Any],
    custom_conversions: Dict[str, Dict[str, Any]]
) -> List[Any]:
    """
    Apply custom converters to list of named tuples.

    Args:
        named_tuples: List of named tuples
        custom_conversions: Dict of columns with custom converters

    Returns:
        List of named tuples with custom conversions applied
    """
    from mountainash.schema.config.custom_types import CustomTypeRegistry

    if not named_tuples:
        return named_tuples

    # Get field names from first named tuple
    first_tuple = named_tuples[0]
    if not hasattr(first_tuple, '_fields'):
        logger.warning("Data does not appear to be named tuples, returning unchanged")
        return named_tuples

    field_names = first_tuple._fields
    TupleClass = type(first_tuple)

    # Determine which fields need custom conversion
    fields_to_convert = {
        idx: (field_name, custom_conversions[field_name])
        for idx, field_name in enumerate(field_names)
        if field_name in custom_conversions and "cast" in custom_conversions[field_name]
    }

    if not fields_to_convert:
        return named_tuples

    # Apply conversions
    converted_data = []

    for nt in named_tuples:
        # Convert to list for modification
        values = list(nt)

        # Apply custom converters to specific fields
        for idx, (field_name, spec) in fields_to_convert.items():
            cast_type = spec["cast"]
            try:
                values[idx] = CustomTypeRegistry.convert(
                    values[idx],
                    cast_type,
                    field_name=field_name,
                    raise_on_error=False
                )
            except Exception as e:
                logger.warning(
                    f"Custom conversion failed for field '{field_name}' "
                    f"with type '{cast_type}': {e}. Using original value."
                )

        # Reconstruct named tuple
        converted_data.append(TupleClass(*values))

    return converted_data


def apply_hybrid_egress_conversion(
    df: 'SupportedDataFrames',
    schema_config: Optional['SchemaConfig'] = None,
    extract_func: Optional[Any] = None,
    data_format: str = "dict"
) -> List[Any]:
    """
    Apply complete hybrid egress conversion strategy.

    Implements the THREE-TIER HYBRID ARCHITECTURE:

    TIER 1 (DataFrame Layer - CENTER):
        - Apply NATIVE conversions (string→int, vectorized!)
        - Keep DataFrame operations fast

    TIER 2 (Extraction - BOUNDARY):
        - Efficient bulk extraction from DataFrame
        - Convert to Python data structures

    TIER 3 (Python Layer - EDGES):
        - Apply CUSTOM converters (safe_float, xml_string, etc.)
        - Semantic transformations in Python

    This is ~10x faster than applying custom conversions in DataFrame!

    Args:
        df: Input DataFrame (any backend)
        schema_config: Optional schema configuration
        extract_func: Function to extract data from DataFrame
                     Should return List[Dict] or List[NamedTuple]
        data_format: Format of extracted data - "dict" or "namedtuple"

    Returns:
        List of Python data structures with all conversions applied

    Example:
        >>> config = SchemaConfig(columns={
        ...     "id": {"cast": "integer"},           # Native
        ...     "amount": {"cast": "safe_float"},    # Custom
        ... })
        >>> result = apply_hybrid_egress_conversion(
        ...     df, config, extract_func=lambda d: d.to_dicts(), data_format="dict"
        ... )
    """
    if schema_config is None:
        # No conversions - just extract
        if extract_func:
            return extract_func(df)
        else:
            raise ValueError("Must provide either schema_config or extract_func")

    # STEP 1: Apply NATIVE conversions in DataFrame (TIER 1, vectorized!)
    df = apply_native_conversions_for_egress(df, schema_config)

    # STEP 2: Extract data from DataFrame (TIER 2)
    if extract_func is None:
        raise ValueError("extract_func is required for hybrid egress conversion")

    data = extract_func(df)

    if not data:
        return data

    # STEP 3: Apply CUSTOM converters to Python data (TIER 3)
    # For egress, combine all custom types (both Python-only and Narwhals)
    python_only_custom, narwhals_custom, _ = schema_config.separate_conversions()
    custom_convs = {**python_only_custom, **narwhals_custom}

    if custom_convs:
        data = apply_custom_converters_to_python_data(data, schema_config, data_format)
        logger.debug(f"Applied custom converters to {len(data)} records")

    return data


__all__ = [
    "apply_native_conversions_for_egress",
    "apply_custom_converters_to_python_data",
    "apply_hybrid_egress_conversion",
]
