"""
Helper functions for custom type conversion in ingress modules.

Implements the hybrid strategy for optimal performance:
- Custom converters: Apply at EDGES (Python layer, before DataFrame)
- Native conversions: Apply in CENTER (DataFrame layer, vectorized)

Declarations are unnamed: the conversion tiers are ``{target_name:
FieldDefinition}`` mappings, and a target reads its source column from
``definition.rename_from`` when set, otherwise from its own name. Every target
reads the unchanged input, so swaps and fan-out share one source safely.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
import logging



if TYPE_CHECKING:
    from mountainash.core.types import PolarsFrame
    from mountainash.typespec.spec import TableSchema, FieldDefinition

logger = logging.getLogger(__name__)


def source_column_name(target_name: str, definition: "FieldDefinition") -> str:
    """Source column a declared target reads: ``rename_from`` if set, else the target name."""
    return definition.rename_from if definition.rename_from is not None else target_name


def separate_conversions(
    schema: "TableSchema",
) -> Tuple[Dict[str, "FieldDefinition"], Dict[str, "FieldDefinition"], Dict[str, "FieldDefinition"]]:
    """
    Separate a TableSchema into three conversion tiers.

    Returns:
        (python_only, narwhals, native) — three dicts keyed by TARGET field name:

        - python_only: Fields with a custom_cast that has no Narwhals implementation
          (row-by-row Python conversion required)
        - narwhals: Fields with a custom_cast that has a vectorized Narwhals implementation
        - native: All other fields (no custom cast — handled by Relation.conform())

        The source column of each entry is ``source_column_name(target, definition)``.

    Example:
        >>> schema = TableSchema(fields={
        ...     # custom_cast takes routing precedence over type (here ANY):
        ...     "amount": FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float"),  # → narwhals
        ...     "id": FieldDefinition(type=UniversalType.INTEGER),    # → native
        ... })
        >>> python_only, narwhals, native = separate_conversions(schema)
    """
    from mountainash.typespec.custom_types import CustomTypeRegistry

    python_only: Dict[str, "FieldDefinition"] = {}
    narwhals: Dict[str, "FieldDefinition"] = {}
    native: Dict[str, "FieldDefinition"] = {}

    for name, definition in dict(schema.fields).items():
        cast_type = definition.custom_cast

        if cast_type is None:
            # No custom cast — route to native (Relation.conform() handles type + rename)
            native[name] = definition
            continue

        if CustomTypeRegistry.has_converter(cast_type):
            if CustomTypeRegistry.is_vectorized(cast_type):
                narwhals[name] = definition
            else:
                python_only[name] = definition
        else:
            # Unknown custom_cast — treat as native and let Relation.conform() handle it
            native[name] = definition

    return python_only, narwhals, native


def apply_custom_converters_to_dict(
    data_dict: Dict[str, Any],
    custom_conversions: Dict[str, "FieldDefinition"],
) -> Dict[str, Any]:
    """
    Apply custom type converters to a single dictionary.

    This is TIER 3 (Python layer) of the hybrid strategy:
    - Apply ONLY custom converters (safe_float, xml_string, etc.)
    - Leave native conversions for DataFrame layer (FAST!)

    Each target is converted once from the value of its source key in the
    unchanged input ``data_dict`` and stored under its target name, so a swap
    or a fan-out of one source never sees another target's output.

    Args:
        data_dict: Dictionary of field_name -> value
        custom_conversions: Dict of FieldDefinition keyed by target name, each
                           containing custom_cast. Returned by separate_conversions().

    Returns:
        New dictionary with custom conversions applied

    Example:
        >>> # custom_cast takes routing precedence over type (here ANY):
        >>> definition = FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float")
        >>> result = apply_custom_converters_to_dict({"amount": "42.5"}, {"amount": definition})
        >>> result["amount"]
        42.5
    """
    from mountainash.typespec.custom_types import CustomTypeRegistry

    converted_dict = dict(data_dict)

    for target_name, definition in custom_conversions.items():
        cast_type = definition.custom_cast
        if cast_type is None:
            continue
        source_name = source_column_name(target_name, definition)
        if source_name not in data_dict:
            continue
        value = data_dict[source_name]
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
        converted_dict[target_name] = value

    return converted_dict


def apply_custom_converters_to_dicts(
    data_dicts: List[Dict[str, Any]],
    custom_conversions: Dict[str, "FieldDefinition"],
) -> List[Dict[str, Any]]:
    """
    Apply custom type converters to a list of dictionaries.

    This is TIER 3 (Python layer) of the hybrid strategy.

    Args:
        data_dicts: List of dictionaries
        custom_conversions: Dict of FieldDefinition keyed by target name,
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
    native_conversions: Dict[str, "FieldDefinition"],
) -> "PolarsFrame":
    """
    Apply native type conversions to a DataFrame using vectorized operations.

    TIER 1 uses the shared conform expressions for native casting, rename and
    null filling. Target resolution precedes execution so invalid overrides
    cannot be swallowed by the existing best-effort execution policy.

    Args:
        df: Polars DataFrame
        native_conversions: Dict of FieldDefinition keyed by target name.
                           Returned by separate_conversions().

    Returns:
        DataFrame with native conversions applied
    """

    if not native_conversions:
        return df

    import mountainash as ma
    from mountainash.typespec.spec import TableSchema
    from mountainash.conform.expressions import _build_conform_exprs
    from mountainash.core.dtypes import TypeTarget
    from mountainash.typespec.source_shape import extract_source_shapes

    # Preserve columns outside the requested native conversions.
    native_schema = TableSchema(fields=native_conversions, fields_match="open")
    conform_result = _build_conform_exprs(
        native_schema, available_columns=df.columns, actual_shapes=extract_source_shapes(df),
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
    narwhals_custom: Dict[str, "FieldDefinition"],
) -> "PolarsFrame":
    """
    Apply Narwhals-vectorized custom converters to DataFrame.

    Follows the filter_expressions pattern:
    1. Convert to Narwhals if not already
    2. Apply Narwhals expressions (vectorized!)
    3. Convert back to native format

    Every target expression is built against the unchanged input frame and all
    are applied in one ``with_columns``, so swapped or fanned-out sources are
    read before any target replaces them.

    Args:
        df: DataFrame to transform
        narwhals_custom: Dict of FieldDefinition keyed by target name
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
    for target_name, definition in narwhals_custom.items():
        cast_type = definition.custom_cast
        source_name = source_column_name(target_name, definition)

        narwhals_converter = CustomTypeRegistry.get_narwhals_converter(cast_type)
        if narwhals_converter is None:
            logger.warning(
                f"Column '{source_name}' marked as Narwhals custom type '{cast_type}' "
                "but no Narwhals converter found - skipping"
            )
            continue

        expr_builder = narwhals_converter(source_name)
        exprs.append(expr_builder(nw_df).alias(target_name))

        logger.debug(
            f"Applied Narwhals custom converter '{cast_type}' to column '{source_name}' "
            f"→ '{target_name}' (vectorized)"
        )

    if exprs:
        nw_df = nw_df.with_columns(*exprs)

    result = nw_df.to_native() if was_native else nw_df
    return result


def _source_schema_overrides(
    source_table_schema: Optional["TableSchema"] = None,
    *,
    model_table_schema: Optional["TableSchema"] = None,
) -> Dict[str, Any]:
    """Resolve source declarations without inspecting values or target schemas."""
    if source_table_schema is None and model_table_schema is None:
        return {}

    from mountainash.typespec.converters import to_polars_schema
    from mountainash.typespec.spec import TableSchema
    from mountainash.typespec.universal_types import UniversalType

    # Automatic model evidence is scalar only; nested ingress is a separate concern.
    scalar_types = {
        UniversalType.STRING, UniversalType.INTEGER, UniversalType.NUMBER,
        UniversalType.BOOLEAN, UniversalType.DATE, UniversalType.DATETIME,
        UniversalType.TIME, UniversalType.DURATION, UniversalType.YEAR,
        UniversalType.YEARMONTH,
    }
    # Keyed by source column: resolve in the source namespace, since a target
    # alias can name another source field.
    fields = {
        source_column_name(name, definition): definition
        for name, definition in model_table_schema.fields.items()
        if definition.type in scalar_types
    } if model_table_schema is not None else {}
    if source_table_schema is not None:
        for name, definition in source_table_schema.fields.items():
            if (
                definition.type != UniversalType.ANY
                or definition.dtype is not None
                or definition.backend_type
                or definition.categories is not None
            ):
                fields[source_column_name(name, definition)] = definition
    if not fields:
        return {}
    return to_polars_schema(TableSchema(fields=fields))


def apply_hybrid_conversion(
    data_dicts: List[Dict[str, Any]],
    table_schema: Optional["TableSchema"] = None,
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
        table_schema: Optional TableSchema with field declarations
        schema_overrides: Native source dtypes, independent of conversion targets.
        inline_conform: Whether to run target conversion stages.

    Returns:
        Polars DataFrame with hybrid conversions applied
    """
    from mountainash.core.lazy_imports import import_polars

    pl = import_polars()
    if pl is None:
        raise ImportError("polars is required for this operation")

    if table_schema is None or not inline_conform:
        return pl.DataFrame(data_dicts, strict=False, schema_overrides=schema_overrides)

    # STEP 1: Separate conversions into THREE tiers
    python_only, narwhals_custom, native = separate_conversions(table_schema)

    logger.info(
        f"Three-tier conversion: {len(python_only)} Python-only custom, "
        f"{len(narwhals_custom)} Narwhals custom (vectorized), "
        f"{len(native)} native conversions"
    )

    # Python converters run before frame construction, but their targets must
    # not replace the input read by either of the vectorized tiers.
    source_overrides = schema_overrides
    converted_rows = data_dicts
    if python_only:
        converted_rows = apply_custom_converters_to_dicts(data_dicts, python_only)
        if schema_overrides:
            schema_overrides = {
                name: dtype for name, dtype in schema_overrides.items()
                if name not in python_only
            }
    df = pl.DataFrame(converted_rows, strict=False, schema_overrides=schema_overrides)
    if not narwhals_custom and not native:
        return df

    outputs = {name: df[name] for name in python_only if name in df.columns}
    if python_only:
        original_names = {name for row in data_dicts for name in row}
        source_names = {
            source_column_name(name, definition)
            for name, definition in (*narwhals_custom.items(), *native.items())
        }
        df = df.drop([name for name in python_only if name not in original_names and name in df.columns])
        restored_sources = [
            pl.Series(
                name, [row.get(name) for row in data_dicts],
                dtype=(source_overrides or {}).get(name), strict=False,
            )
            for name in python_only
            if name in source_names and name in original_names
        ]
        if restored_sources:
            df = df.with_columns(restored_sources)

    # Each tier evaluates against the same source; commit targets together.
    if narwhals_custom:
        converted = _apply_narwhals_custom_converters(df, narwhals_custom)
        outputs.update({name: converted[name] for name in narwhals_custom if name in converted.columns})
    if native:
        converted = apply_native_conversions_to_dataframe(df, native)
        outputs.update({name: converted[name] for name in native if name in converted.columns})
    return df.with_columns([outputs[name] for name in table_schema.fields if name in outputs])


def apply_hybrid_conversion_to_dataframe(
    df: "PolarsFrame", table_schema: "TableSchema",
) -> "PolarsFrame":
    """Convert a constructed source frame without round-tripping untouched columns.

    Frame-based ingress retains its existing conform projection/error policy.
    Custom outputs are evaluated on the original source, then attached under
    the target names selected by that projection.
    """
    from dataclasses import replace

    import mountainash as ma
    from mountainash.core.lazy_imports import import_polars
    from mountainash.typespec.spec import FieldDefinition

    python_only, narwhals_custom, _ = separate_conversions(table_schema)
    custom = python_only | narwhals_custom
    if not custom:
        return ma.relation(df).conform(table_schema).to_polars()

    pl = import_polars()
    outputs = []
    if python_only and df.height:
        source_names = list(dict.fromkeys(
            source_column_name(name, definition)
            for name, definition in python_only.items()
            if source_column_name(name, definition) in df.columns
        ))
        rows = apply_custom_converters_to_dicts(df.select(source_names).to_dicts(), python_only)
        outputs.extend(
            pl.Series(name, [row[name] for row in rows], strict=False)
            for name, definition in python_only.items()
            if source_column_name(name, definition) in df.columns
        )
    if narwhals_custom:
        converted = _apply_narwhals_custom_converters(df, narwhals_custom)
        outputs.extend(converted[name] for name in narwhals_custom if name in converted.columns)

    projection = replace(table_schema, fields={
        name: FieldDefinition(rename_from=definition.rename_from) if name in custom else definition
        for name, definition in table_schema.fields.items()
    })
    if not outputs:
        return ma.relation(df).conform(projection).to_polars()

    # Let conform own row filtering; carry source positions through that same
    # operation so custom results follow the surviving rows without re-evaluation.
    occupied = set(df.columns) | set(table_schema.fields) | {
        source_column_name(name, definition)
        for name, definition in table_schema.fields.items()
    }
    row_index = "__ma_pydata_row_index"
    while row_index in occupied:
        row_index += "_"
    projection.fields[row_index] = FieldDefinition()
    indexed = df.with_columns(pl.int_range(0, df.height, dtype=pl.Int64).alias(row_index))
    result = ma.relation(indexed).conform(projection).to_polars()
    indices = result[row_index]
    custom_outputs = [
        series.gather(indices) if result.height != df.height else series
        for series in outputs if series.name in result.columns
    ]
    return result.drop(row_index).with_columns(custom_outputs)


__all__ = [
    "source_column_name",
    "separate_conversions",
    "apply_custom_converters_to_dict",
    "apply_custom_converters_to_dicts",
    "apply_native_conversions_to_dataframe",
    "_apply_narwhals_custom_converters",
    "apply_hybrid_conversion",
]
