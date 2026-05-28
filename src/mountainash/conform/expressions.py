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

        # Stage 3: NULL FILL — replace nulls with default value
        if fld.null_fill is not None:
            expr = ma.coalesce(expr, ma.lit(fld.null_fill))

        # Stage 4a: BOOLEAN — trueValues/falseValues mapping
        # Frictionless Table Schema §boolean: string values are "to be cast
        # to their logical representation as booleans."
        # Uses cast(str).is_in() so it works on both string and boolean sources.
        if fld.type == UniversalType.BOOLEAN:
            true_vals = fld.true_values or ["true", "True", "TRUE", "1"]
            false_vals = fld.false_values or ["false", "False", "FALSE", "0"]
            str_expr = expr.cast(bridge_type(UniversalType.STRING))
            expr = (
                ma.when(str_expr.is_in(*true_vals)).then(ma.lit(True))
                .when(str_expr.is_in(*false_vals)).then(ma.lit(False))
                .otherwise(ma.lit(None))
            )
        elif fld.type and fld.type != UniversalType.ANY:
            expr = expr.cast(bridge_type(fld.type))

        expr = expr.name.alias(fld.name)
        exprs.append(expr)

    return ConformResult(
        exprs=exprs,
        fields_match=fields_match,
        renamed_sources=renamed_sources,
    )
