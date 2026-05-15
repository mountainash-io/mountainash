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
    from mountainash.core.types import SupportedDataFrames
    from mountainash.typespec.spec import TypeSpec, FieldSpec


from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.pydata.ingress.custom_type_helpers import separate_conversions

logger = logging.getLogger(__name__)


def apply_native_conversions_for_egress(
    df: 'SupportedDataFrames',
    spec: Optional['TypeSpec'] = None
) -> tuple:
    """
    Apply NATIVE conversions in DataFrame before extraction (TIER 1).

    This applies only native type conversions that can be done efficiently
    in the DataFrame using vectorized operations. Custom converters are
    skipped here and will be applied after extraction.

    Args:
        df: Input DataFrame (any backend)
        spec: TypeSpec configuration with field specifications

    Returns:
        Tuple of (df, python_only_custom) where python_only_custom is a
        dict[str, FieldSpec] of fields that need Python-layer conversion.

    Example:
        >>> spec = TypeSpec(fields=[
        ...     FieldSpec(name="id", type=UniversalType.INTEGER),   # Native
        ...     FieldSpec(name="amount", custom_cast="safe_float"), # Custom
        ... ])
        >>> df, python_only = apply_native_conversions_for_egress(df, spec)
        >>> # Only 'id' cast applied in DataFrame, 'amount' left for post-extraction
    """
    import polars as pl

    if spec is None:
        if not isinstance(df, pl.DataFrame):
            import mountainash as ma
            df = ma.relation(df).to_polars()
        return df, {}

    # Separate conversions into three tiers
    python_only, narwhals_custom, native = separate_conversions(spec)

    # For egress, both python_only and narwhals_custom are deferred to Python layer
    python_only_custom = {**python_only, **narwhals_custom}

    logger.info(
        f"Egress hybrid: {len(native)} native conversions in DataFrame, "
        f"{len(python_only_custom)} custom conversions deferred to Python layer "
        f"(Python-only: {len(python_only)}, Narwhals: {len(narwhals_custom)})"
    )

    # Build conform spec for all non-python-only fields
    conform_fields = [f for f in spec.fields if f.source_name not in python_only_custom]
    if conform_fields:
        conform_spec = TypeSpec(fields=conform_fields)
        import mountainash as ma
        df = ma.relation(df).conform(conform_spec).to_polars()
    elif not isinstance(df, pl.DataFrame):
        import mountainash as ma
        df = ma.relation(df).to_polars()

    return df, python_only_custom


def apply_custom_converters_to_python_data(
    data: List[Any],
    python_only_custom: Dict[str, 'FieldSpec'],
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
        python_only_custom: Dict of FieldSpec keyed by source_name (already separated)
        data_format: Format of data - "dict" or "namedtuple"

    Returns:
        List with custom conversions applied

    Example:
        >>> field = FieldSpec(name="amount", custom_cast="safe_float")
        >>> data = [{"amount": "42.5"}, {"amount": "99.9"}]
        >>> result = apply_custom_converters_to_python_data(data, {"amount": field}, "dict")
        >>> result
        [{'amount': 42.5}, {'amount': 99.9}]
    """
    logger.debug("EGRESS TRACE: apply_custom_converters_to_python_data called")
    logger.debug(f"  python_only_custom: {python_only_custom}")
    logger.debug(f"  data_format: {data_format}")
    logger.debug(f"  data length: {len(data) if data else 0}")

    if not python_only_custom or not data:
        logger.debug(f"  Returning early: python_only_custom={python_only_custom}, data={data}")
        return data

    logger.info(f"Applying {len(python_only_custom)} custom converters to {len(data)} records")

    # Map custom conversions from source names to target names
    # (DataFrame columns have been renamed by native conversions)
    target_custom_convs: Dict[str, 'FieldSpec'] = {}
    for source_name, field_spec in python_only_custom.items():
        target_name = field_spec.name  # FieldSpec.name is the target column name
        target_custom_convs[target_name] = field_spec

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
    custom_conversions: Dict[str, 'FieldSpec']
) -> List[Dict[str, Any]]:
    """
    Apply custom converters to list of dictionaries.

    Args:
        data_dicts: List of dictionaries
        custom_conversions: Dict of FieldSpec keyed by TARGET column name

    Returns:
        List of dictionaries with custom conversions applied
    """
    from mountainash.typespec.custom_types import CustomTypeRegistry

    converted_data = []

    for row_dict in data_dicts:
        converted_row = {}

        for field_name, value in row_dict.items():
            # Check if this field needs custom conversion
            if field_name in custom_conversions:
                field_spec = custom_conversions[field_name]
                cast_type = field_spec.custom_cast

                if cast_type is not None:
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
    custom_conversions: Dict[str, 'FieldSpec']
) -> List[Any]:
    """
    Apply custom converters to list of named tuples.

    Args:
        named_tuples: List of named tuples
        custom_conversions: Dict of FieldSpec keyed by TARGET column name

    Returns:
        List of named tuples with custom conversions applied
    """
    from mountainash.typespec.custom_types import CustomTypeRegistry

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
        if field_name in custom_conversions and custom_conversions[field_name].custom_cast is not None
    }

    if not fields_to_convert:
        return named_tuples

    # Apply conversions
    converted_data = []

    for nt in named_tuples:
        # Convert to list for modification
        values = list(nt)

        # Apply custom converters to specific fields
        for idx, (field_name, field_spec) in fields_to_convert.items():
            cast_type = field_spec.custom_cast
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
    spec: Optional['TypeSpec'] = None,
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
        spec: Optional TypeSpec configuration
        extract_func: Function to extract data from DataFrame
                     Should return List[Dict] or List[NamedTuple]
        data_format: Format of extracted data - "dict" or "namedtuple"

    Returns:
        List of Python data structures with all conversions applied

    Example:
        >>> spec = TypeSpec(fields=[
        ...     FieldSpec(name="id", type=UniversalType.INTEGER),   # Native
        ...     FieldSpec(name="amount", custom_cast="safe_float"), # Custom
        ... ])
        >>> result = apply_hybrid_egress_conversion(
        ...     df, spec, extract_func=lambda d: d.to_dicts(), data_format="dict"
        ... )
    """
    if spec is None:
        # No conversions - just extract
        if extract_func:
            return extract_func(df)
        else:
            raise ValueError("Must provide either spec or extract_func")

    if extract_func is None:
        raise ValueError("extract_func is required for hybrid egress conversion")

    # STEP 1: Apply NATIVE conversions in DataFrame (TIER 1, vectorized!)
    df, python_only_custom = apply_native_conversions_for_egress(df, spec)

    # STEP 2: Extract data from DataFrame (TIER 2)
    data = extract_func(df)

    if not data:
        return data

    # STEP 3: Apply CUSTOM converters to Python data (TIER 3)
    if python_only_custom:
        data = apply_custom_converters_to_python_data(data, python_only_custom, data_format)
        logger.debug(f"Applied custom converters to {len(data)} records")

    return data


__all__ = [
    "apply_native_conversions_for_egress",
    "apply_custom_converters_to_python_data",
    "apply_hybrid_egress_conversion",
]
