"""Shared conform expression builder.

Builds expression lists from TypeSpec fields. Used by both
Relation.conform() and the DAG visitor's apply_conform.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field as dataclass_field
from typing import TYPE_CHECKING, Any, Optional, Sequence

from mountainash.conform.errors import (
    ConformError,
    ExactFieldCountError,
    ExtraFieldsError,
    MissingFieldsError,
    NoMatchingFieldsError,
)

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec

_VALID_FIELDS_MATCH = frozenset(
    {"open", "exact", "equal", "subset", "superset", "partial"}
)


@dataclass
class ConformResult:
    """Result of building conform expressions.

    Callers use fields_match to dispatch select() vs with_columns():
    - "open" → with_columns (keeps unmapped) + drop renamed sources
    - all others → select (projection, drops unmapped)
    """

    exprs: list  # mountainash expressions
    fields_match: str  # resolved mode (never None)
    renamed_sources: set = dataclass_field(default_factory=set)


def _build_conform_exprs(
    spec: "TypeSpec",
    *,
    available_columns: Optional[Sequence[str]] = None,
) -> ConformResult:
    """Build the expression list for a TypeSpec conformance projection.

    For each field in the spec, constructs an expression chain:
    col(source) -> coalesce(fill) -> cast(type) -> alias(target)

    Produces exactly one expression per field in the spec (or fewer when
    fields are skipped due to the fieldsMatch mode).

    Args:
        spec: The TypeSpec describing the target schema.
        available_columns: Ordered column names from the source data.
            Required for all fieldsMatch modes except "open".
            Sequence preserves order (needed for "exact" positional mapping).

    Returns:
        ConformResult with expressions, resolved fields_match mode,
        and set of renamed source columns.
    """
    import mountainash as ma
    from mountainash.typespec.type_bridge import bridge_type
    from mountainash.typespec.universal_types import UniversalType

    # --- 1. Resolve and validate fields_match mode ---
    fields_match = spec.fields_match if spec.fields_match is not None else "open"
    if fields_match not in _VALID_FIELDS_MATCH:
        raise ConformError(
            f"Invalid fields_match={fields_match!r}. "
            f"Must be one of: {sorted(_VALID_FIELDS_MATCH)}"
        )

    # --- 2. Enforce fieldsMatch guard ---
    if fields_match != "open" and available_columns is None:
        raise ConformError(
            f"fieldsMatch={fields_match!r} requires available_columns to be "
            f"provided. Only 'open' mode works without column information."
        )

    if available_columns is not None:
        available_set: set[str] = set(available_columns)
        # Source names the spec expects to find in the data
        spec_source_names = {f.source_name for f in spec.fields}

        if fields_match == "exact":
            if len(available_columns) != len(spec.fields):
                raise ExactFieldCountError(
                    expected_count=len(spec.fields),
                    actual_count=len(available_columns),
                )

        elif fields_match == "equal":
            missing = sorted(spec_source_names - available_set)
            if missing:
                raise MissingFieldsError(
                    missing_fields=missing, fields_match=fields_match,
                )
            extra = sorted(available_set - spec_source_names)
            if extra:
                raise ExtraFieldsError(
                    extra_fields=extra, fields_match=fields_match,
                )

        elif fields_match == "subset":
            missing = sorted(spec_source_names - available_set)
            if missing:
                raise MissingFieldsError(
                    missing_fields=missing, fields_match=fields_match,
                )

        elif fields_match == "superset":
            extra = sorted(available_set - spec_source_names)
            if extra:
                raise ExtraFieldsError(
                    extra_fields=extra, fields_match=fields_match,
                )

        elif fields_match == "partial":
            if not spec_source_names & available_set:
                raise NoMatchingFieldsError(
                    spec_fields=sorted(spec_source_names),
                    available_columns=sorted(available_set),
                )
        # "open" — no guard
    else:
        available_set = None  # type: ignore[assignment]

    # --- 3. Build per-field expressions ---
    exprs: list[Any] = []
    renamed_sources: set[str] = set()

    # Resolve schema-level missingValues once.
    # The Frictionless default is [""] but TypeSpec.missing_values defaults
    # to [""] via its factory.  We only activate the sentinel pipeline when
    # the spec carries a non-empty list — an explicit empty list [] or None
    # both mean "no sentinels".  This avoids emitting is_in([""])  on
    # already-typed (non-string) columns where the comparison would raise.
    schema_missing_values: list[str] = spec.missing_values or []

    # Types eligible for missingValues sentinel replacement.
    # Non-scalar types (ARRAY, OBJECT, ANY) are excluded because
    # is_in on those types may raise backend errors.
    _SCALAR_TYPES = {
        UniversalType.STRING, UniversalType.NUMBER, UniversalType.INTEGER,
        UniversalType.BOOLEAN, UniversalType.DATE, UniversalType.DATETIME,
        UniversalType.TIME, UniversalType.YEAR, UniversalType.YEARMONTH,
        UniversalType.DURATION,
    }

    for idx, fld in enumerate(spec.fields):
        # Determine source column name
        if fields_match == "exact":
            # Positional mapping: use the i-th available column
            source_name = available_columns[idx]  # type: ignore[index]
        else:
            source_name = fld.source_name

        # Skip fields whose source isn't available (open/partial/superset)
        if available_set is not None:
            root_col = (
                source_name.split(".")[0] if "." in source_name else source_name
            )
            if root_col not in available_set:
                continue

        # Build the expression
        is_dotted = "." in source_name
        if is_dotted:
            parts = source_name.split(".")
            expr = ma.col(parts[0])
            for part in parts[1:]:
                expr = expr.struct.field(part)
        else:
            expr = ma.col(source_name)
            if source_name != fld.name:
                renamed_sources.add(source_name)

        # Stage 2: MISSING VALUES — sentinel strings → null
        # Frictionless Table Schema §missingValues: conversion to null MUST
        # happen before any type-specific string conversion.
        # Field-level missing_values completely replaces schema-level.
        sentinels = (
            fld.missing_values
            if fld.missing_values is not None
            else schema_missing_values
        )
        # Only emit sentinel replacement when:
        # 1. There are sentinel values to check, AND
        # 2. The field is a scalar type (not array/object/any), AND
        # 3. The sentinel list is explicitly set beyond the Frictionless
        #    default [""] — OR the field is already string-typed.
        # The default [""] only makes sense for string-sourced data;
        # emitting is_in([""]) on a non-string column raises at runtime.
        _has_explicit_sentinels = (
            fld.missing_values is not None  # field-level always explicit
            or sentinels != [""]            # schema-level beyond default
        )
        _sentinel_applicable = (
            _has_explicit_sentinels or fld.type == UniversalType.STRING
        )
        if sentinels and fld.type in _SCALAR_TYPES and _sentinel_applicable:
            # Warn if boolean field's sentinels overlap with true/false values
            if fld.type == UniversalType.BOOLEAN:
                true_vals = fld.true_values or [
                    "true", "True", "TRUE", "1",
                ]
                false_vals = fld.false_values or [
                    "false", "False", "FALSE", "0",
                ]
                overlap = set(sentinels) & set(true_vals + false_vals)
                if overlap:
                    warnings.warn(
                        f"Field {fld.name!r}: missingValues {sorted(overlap)} "
                        f"overlap with trueValues/falseValues — these values "
                        f"will become null, not boolean.",
                        UserWarning,
                        stacklevel=2,
                    )
            expr = (
                ma.when(expr.is_in(*sentinels))
                .then(ma.lit(None))
                .otherwise(expr)
            )

        # Stage 3: STRING PARSING — numeric format normalization
        # Frictionless Table Schema §number, §integer
        # Only emitted when non-default values are set.
        # Order: bareNumber strip → groupChar remove → decimalChar normalize
        if fld.type in (UniversalType.NUMBER, UniversalType.INTEGER):
            if fld.bare_number is False:
                # Strip leading non-numeric chars (except -, +, .)
                expr = expr.str.regexp_replace(r"^[^\d\-+.]+", "")
                # Strip trailing non-numeric chars
                expr = expr.str.regexp_replace(r"[^\d.]+$", "")
            if fld.group_char is not None:
                expr = expr.str.replace(fld.group_char, "")
            if fld.decimal_char is not None and fld.decimal_char != ".":
                expr = expr.str.replace(fld.decimal_char, ".")

        # Stage 4: NULL FILL — replace nulls with default value
        if fld.null_fill is not None:
            expr = ma.coalesce(expr, ma.lit(fld.null_fill))

        # Stage 5a: LIST — split delimited string and cast elements
        # Frictionless Table Schema §list: an ordered one-level depth
        # collection of primitive values serialised as a delimited string.
        # delimiter defaults to ","; itemType defaults to "string".
        # List elements get raw casts only — no full scalar pipeline.
        #
        # Uses mountainash str.string_split for the split.  Element-level
        # casting uses list.agg with a native pl.element().cast() expression
        # — acknowledged as Polars-specific, same as the categorical stage.
        if fld.type == UniversalType.ARRAY:
            delimiter = fld.delimiter or ","
            expr = expr.str.string_split(ma.lit(delimiter))

            # Cast each element to itemType (skip if string — already correct)
            item_type_str = fld.item_type or "string"
            if item_type_str != "string":
                from mountainash.typespec.universal_types import (
                    get_polars_type,
                    normalize_type as _norm,
                )

                import polars as pl

                item_utype = _norm(item_type_str)
                polars_type = get_polars_type(item_utype)
                expr = expr.list.agg(
                    ma.native(pl.element().cast(polars_type))
                )

        # Stage 5b: CATEGORIES — base cast then categorical wrapper
        # Frictionless Table Schema §categories, §categoriesOrdered:
        # categories can be a simple array ["a", "b"] or object array
        # [{"value": 0, "label": "Low"}, ...].  categoriesOrdered=true
        # means the order defines natural sort order.
        # Backend mapping: Polars Enum (ordered) / Categorical (unordered).
        # Other backends fall through to base type cast only.
        elif fld.categories is not None:
            # Extract values from categories (handles both simple and object forms)
            cat_values: list[Any] = []
            for cat in fld.categories:
                if isinstance(cat, dict):
                    cat_values.append(cat["value"])
                else:
                    cat_values.append(cat)

            # Step 1: base type cast (if needed)
            if fld.type and fld.type != UniversalType.ANY:
                expr = expr.cast(bridge_type(fld.type))

            # Step 2: categorical wrapper (Polars-specific)
            # This uses native Polars types — acknowledged as a known
            # divergence from backend-agnosticism.  Abstraction via the
            # expression type system is deferred.
            import polars as pl

            if fld.categories_ordered:
                cat_str_values = [str(v) for v in cat_values]
                expr = expr.cast(pl.Enum(cat_str_values))
            else:
                expr = expr.cast(pl.Categorical)

        # Stage 5b: TEMPORAL — custom format parsing
        # Frictionless Table Schema §date, §datetime, §time: when format is
        # a strptime pattern (not "default" or None), parse via str.to_date/
        # str.to_datetime/str.to_time.  "any" falls through to bridge_type
        # cast (best-effort; Frictionless marks "any" as NOT RECOMMENDED).
        elif fld.type in {
            UniversalType.DATE, UniversalType.DATETIME, UniversalType.TIME,
        } and fld.format not in ("default", None, "any"):
            if fld.type == UniversalType.DATE:
                expr = expr.str.to_date(fld.format)
            elif fld.type == UniversalType.DATETIME:
                expr = expr.str.to_datetime(fld.format)
            else:  # TIME
                expr = expr.str.to_time(fld.format)

        # Stage 5c: BOOLEAN — trueValues/falseValues mapping
        # Frictionless Table Schema §boolean: string values are "to be cast
        # to their logical representation as booleans."
        # Uses cast(str).is_in() so it works on both string and boolean sources.
        elif fld.type == UniversalType.BOOLEAN:
            true_vals = fld.true_values or ["true", "True", "TRUE", "1"]
            false_vals = fld.false_values or ["false", "False", "FALSE", "0"]
            str_expr = expr.cast(bridge_type(UniversalType.STRING))
            expr = (
                ma.when(str_expr.is_in(*true_vals)).then(ma.lit(True))
                .when(str_expr.is_in(*false_vals)).then(ma.lit(False))
                .otherwise(ma.lit(None))
            )

        # Stage 5d: DEFAULT TYPE CAST
        elif fld.type and fld.type != UniversalType.ANY:
            expr = expr.cast(bridge_type(fld.type))

        expr = expr.name.alias(fld.name)
        exprs.append(expr)

    return ConformResult(
        exprs=exprs,
        fields_match=fields_match,
        renamed_sources=renamed_sources,
    )
