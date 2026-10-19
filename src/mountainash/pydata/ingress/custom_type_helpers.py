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

# Private column-name prefix for custom results awaiting placement (see apply_hybrid_conversion).
_STAGE_PREFIX = "__mountainash_custom__:"


def separate_conversions(
    spec: "TypeSpec",
) -> Tuple[Dict[str, "FieldSpec"], Dict[str, "FieldSpec"], Dict[str, "FieldSpec"]]:
    """
    Separate a TypeSpec into three conversion tiers.

    This is a standalone replacement for SchemaConfig.separate_conversions() that
    operates on TypeSpec/FieldSpec instead of raw dicts.

    Returns:
        (python_only, narwhals, native) — three dictionaries keyed by contextual
        target field name.

    Example:
        >>> spec = TypeSpec(fields={
        ...     "amount": FieldSpec(type=UniversalType.ANY, custom_cast="safe_float"),
        ...     "id": FieldSpec(type=UniversalType.INTEGER),
        ... })
        >>> python_only, narwhals, native = separate_conversions(spec)
    """
    from mountainash.typespec.custom_types import CustomTypeRegistry

    python_only: Dict[str, "FieldSpec"] = {}
    narwhals: Dict[str, "FieldSpec"] = {}
    native: Dict[str, "FieldSpec"] = {}

    for field_name, field in spec.fields.items():
        cast_type = field.custom_cast
        if cast_type is None or not CustomTypeRegistry.has_converter(cast_type):
            native[field_name] = field
        elif CustomTypeRegistry.is_vectorized(cast_type):
            narwhals[field_name] = field
        else:
            python_only[field_name] = field
    return python_only, narwhals, native


def apply_custom_converters_to_dict(
    data_dict: Dict[str, Any],
    custom_conversions: Dict[str, "FieldSpec"],
    *,
    keep_sources: bool = False,
) -> Dict[str, Any]:
    """
    Apply custom type converters to a single dictionary.

    This is TIER 3 (Python layer) of the hybrid strategy:
    - Apply ONLY custom converters (safe_float, xml_string, etc.)
    - Leave native conversions for DataFrame layer (FAST!)

    Every declaration reads its source (``rename_from`` or its target name) from
    the unchanged input row, so the result does not depend on key order. Source
    keys consumed under another name are dropped unless ``keep_sources`` is set.

    Args:
        data_dict: Dictionary of source field name -> value
        custom_conversions: Mapping of contextual target names to FieldSpec,
                           returned by separate_conversions().
        keep_sources: Keep consumed source keys alongside the converted targets.

    Returns:
        Dictionary with custom conversions applied and aliases renamed

    Example:
        >>> field = FieldSpec(type=UniversalType.ANY, custom_cast="safe_float")
        >>> result = apply_custom_converters_to_dict({"amount": "42.5"}, {"amount": field})
        >>> result["amount"]
        42.5
    """
    from mountainash.typespec.custom_types import CustomTypeRegistry

    converted: Dict[str, Any] = {}
    for target_name, field_spec in custom_conversions.items():
        source_name = field_spec.rename_from or target_name
        if source_name not in data_dict:
            continue
        value = data_dict[source_name]
        cast_type = field_spec.custom_cast
        if cast_type is not None:
            try:
                value = CustomTypeRegistry.convert(
                    value,
                    cast_type,
                    field_name=source_name,
                    raise_on_error=False,
                )
            except Exception as e:
                logger.warning(
                    f"Custom conversion failed for field '{source_name}' "
                    f"with type '{cast_type}': {e}. Using original value."
                )
        converted[target_name] = value

    consumed = set() if keep_sources else {
        field.rename_from for field in custom_conversions.values()
        if field.rename_from is not None
    } - custom_conversions.keys()
    result = {name: value for name, value in data_dict.items() if name not in consumed}
    result.update(converted)
    return result


def apply_custom_converters_to_dicts(
    data_dicts: List[Dict[str, Any]],
    custom_conversions: Dict[str, "FieldSpec"],
) -> List[Dict[str, Any]]:
    """
    Apply custom type converters to a list of dictionaries.

    This is TIER 3 (Python layer) of the hybrid strategy.

    Args:
        data_dicts: List of dictionaries
        custom_conversions: Mapping of contextual target names to FieldSpec.
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

    TIER 1 uses the shared conform expressions for native casting, rename and
    null filling. Target resolution precedes execution so invalid overrides
    cannot be swallowed by the existing best-effort execution policy.

    Args:
        df: Polars DataFrame
        native_conversions: Mapping of contextual target names to FieldSpec,
                            returned by separate_conversions().

    Returns:
        DataFrame with native conversions applied
    """

    if not native_conversions:
        return df

    import mountainash as ma
    from mountainash.typespec.spec import TypeSpec
    from mountainash.conform.expressions import _build_conform_exprs
    from mountainash.core.dtypes import TypeTarget
    from mountainash.typespec.source_shape import extract_source_shapes

    native_spec = TypeSpec(fields=native_conversions, fields_match="open")
    conform_result = _build_conform_exprs(
        native_spec, available_columns=df.columns, actual_shapes=extract_source_shapes(df),
        type_target=TypeTarget.POLARS,
    )
    try:
        df = ma.relation(df).with_columns(*conform_result.exprs).to_polars()
    except Exception as e:
        logger.warning(
            f"Error applying native operations via expressions: {e}. "
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

    All converters read the unchanged input columns and are applied together,
    so a target named like another declaration's source cannot affect it.

    Args:
        df: DataFrame to transform
        narwhals_custom: Mapping of contextual target names to FieldSpec
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

    exprs = []
    for target_name, field_spec in narwhals_custom.items():
        cast_type = field_spec.custom_cast

        narwhals_converter = CustomTypeRegistry.get_narwhals_converter(cast_type)
        if narwhals_converter is None:
            logger.warning(
                f"Column '{target_name}' marked as Narwhals custom type '{cast_type}' "
                "but no Narwhals converter found - skipping"
            )
            continue

        source_name = field_spec.rename_from or target_name
        exprs.append(narwhals_converter(source_name)(nw_df).alias(target_name))
        logger.debug(
            f"Applied Narwhals custom converter '{cast_type}' to column '{source_name}' "
            f"→ '{target_name}' (vectorized)"
        )
    if exprs:
        nw_df = nw_df.with_columns(*exprs)

    result = nw_df.to_native() if was_native else nw_df
    return result


def _source_schema_overrides(
    source_spec: Optional["TypeSpec"] = None,
    *,
    model_spec: Optional["TypeSpec"] = None,
) -> Dict[str, Any]:
    """Resolve source declarations without inspecting values or target specs."""
    if source_spec is None and model_spec is None:
        return {}

    from mountainash.typespec.converters import to_polars_schema
    from mountainash.typespec.spec import TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    # Automatic model evidence is scalar only; nested ingress is a separate concern.
    scalar_types = {
        UniversalType.STRING, UniversalType.INTEGER, UniversalType.NUMBER,
        UniversalType.BOOLEAN, UniversalType.DATE, UniversalType.DATETIME,
        UniversalType.TIME, UniversalType.DURATION, UniversalType.YEAR,
        UniversalType.YEARMONTH,
    }
    fields = {
        field.rename_from or name: field
        for name, field in model_spec.fields.items()
        if field.type in scalar_types
    } if model_spec is not None else {}
    if source_spec is not None:
        for name, field in source_spec.fields.items():
            if (
                field.type != UniversalType.ANY
                or field.dtype is not None
                or field.backend_type
                or field.categories is not None
            ):
                source_name = field.rename_from or name
                fields[source_name] = field
    if not fields:
        return {}
    source_fields = {
        name: field.variant(rename_from=None)
        for name, field in fields.items()
    }
    return to_polars_schema(TypeSpec(fields=source_fields))


def apply_hybrid_conversion(
    data_dicts: List[Dict[str, Any]],
    spec: Optional["TypeSpec"] = None,
    *,
    schema_overrides: Optional[Dict[str, Any]] = None,
    inline_conform: bool = True,
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
        - Apply NATIVE conversions (string→int, vectorized via Relation.conform())
        - Apply other native operations (rename, null_fill)

    Args:
        data_dicts: List of dictionaries to convert
        spec: Optional TypeSpec with field specifications
        schema_overrides: Native source dtypes, independent of conversion targets.
        inline_conform: Whether to run target conversion stages.

    Returns:
        Polars DataFrame with hybrid conversions applied
    """
    from mountainash.core.lazy_imports import import_polars

    pl = import_polars()
    if pl is None:
        raise ImportError("polars is required for this operation")

    if spec is None or not inline_conform:
        return pl.DataFrame(data_dicts, strict=False, schema_overrides=schema_overrides)

    # STEP 1: Separate conversions into THREE tiers
    python_only, narwhals_custom, native = separate_conversions(spec)

    logger.info(
        f"Three-tier conversion: {len(python_only)} Python-only custom, "
        f"{len(narwhals_custom)} Narwhals custom (vectorized), "
        f"{len(native)} native conversions"
    )

    # Custom conversions are staged under private names and moved into place
    # only after every tier has read its sources, so a converted target named
    # like another declaration's source cannot overwrite that source.
    staged_python = {
        _STAGE_PREFIX + name: field.variant(rename_from=field.rename_from or name)
        for name, field in python_only.items()
    }
    staged_narwhals = {
        _STAGE_PREFIX + name: field.variant(rename_from=field.rename_from or name)
        for name, field in narwhals_custom.items()
    }

    # STEP 2: Apply PYTHON-ONLY custom converters at edges (TIER 3)
    if python_only:
        data_dicts = [
            apply_custom_converters_to_dict(row, staged_python, keep_sources=True)
            for row in data_dicts
        ]
        logger.debug(f"Applied Python-only custom converters to {len(data_dicts)} records")

    # STEP 3: Create DataFrame
    df = pl.DataFrame(data_dicts, strict=False, schema_overrides=schema_overrides)

    # STEP 4: Apply NARWHALS CUSTOM converters (TIER 2 — vectorized expressions)
    if narwhals_custom:
        df = _apply_narwhals_custom_converters(df, staged_narwhals)
        logger.debug(f"Applied {len(narwhals_custom)} Narwhals custom converters (vectorized)")

    # STEP 5: Apply NATIVE operations via expressions (TIER 1)
    if native:
        df = apply_native_conversions_to_dataframe(df, native)

    # STEP 6: Move staged custom results to their targets; drop sources that
    # only Python-layer renames consumed (they were renamed, not copied).
    staged = [name for name in (*staged_python, *staged_narwhals) if name in df.columns]
    if staged:
        df = df.with_columns(
            pl.col(name).alias(name.removeprefix(_STAGE_PREFIX)) for name in staged
        ).drop(staged)
        renamed_away = {
            field.rename_from for field in python_only.values() if field.rename_from is not None
        } - spec.fields.keys() - {
            field.rename_from or name
            for name, field in {**narwhals_custom, **native}.items()
        }
        df = df.drop([name for name in renamed_away if name in df.columns])

    return df


__all__ = [
    "separate_conversions",
    "apply_custom_converters_to_dict",
    "apply_custom_converters_to_dicts",
    "apply_native_conversions_to_dataframe",
    "_apply_narwhals_custom_converters",
    "apply_hybrid_conversion",
]
