"""Conform expression builder — the single authoritative interpreter of
the Frictionless Table Schema transform pipeline.

This module builds backend-agnostic mountainash expressions that transform
source data to match a TypeSpec schema.  It is the core of the conform
pipeline, used by ``Relation.conform()``, the DAG visitor's
``apply_conform()``, pydata ingress/egress, and ``custom_type_helpers``.

The 7-stage pipeline processes each field in order:

  0. FIELDS-MATCH GUARD — validate source columns against fieldsMatch mode
  1. RESOLVE SOURCE    — ``col(source_name)`` or positional for exact mode;
                         struct field access for dotted names
  2. MISSING VALUES    — sentinel strings -> null (Frictionless §missingValues)
  3. STRING PARSING    — numeric format normalisation (§number, §integer):
                         bareNumber strip, groupChar remove, decimalChar replace
  4. NULL FILL         — ``coalesce(expr, lit(null_fill))``
  5. TYPE CAST         — boolean (§boolean trueValues/falseValues)
                         temporal format (§datetime/date/time)
                         categories (§categories/categoriesOrdered)
                         list split + element cast (§list)
                         default canonical-dtype cast (``to_canonical``)
  6. ALIAS             — ``expr.name.alias(target_name)``

Ordering invariants:
  - Stage 2 MUST precede stages 3-5 (Frictionless spec: missingValues
    conversion happens before any type-specific string conversion)
  - Stage 3 MUST precede stage 5 (strings cleaned before casting)
  - Stage 4 (null fill) sits between parsing and casting so that fill
    values are applied to the parsed-but-not-yet-cast column; callers
    needing post-cast null fill should use the typed source directly
  - Stage 5 branches are mutually exclusive per field
  - Stage 6 always runs last

Reference: https://datapackage.org/standard/table-schema/

See also:
  - mountainash-central/04.planning/mountainash/superpowers/
    specs/2026-05-29-conform-full-typespec-runtime-design.md
"""
from __future__ import annotations

import enum
import warnings
from dataclasses import dataclass, field as dataclass_field
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from mountainash.conform.errors import (
    ConformError,
    ExactFieldCountError,
    ExtraFieldsError,
    MissingFieldsError,
    NoMatchingFieldsError,
)

if TYPE_CHECKING:
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.spec import FieldSpec, TypeSpec

_VALID_FIELDS_MATCH = frozenset(
    {"open", "exact", "equal", "subset", "superset", "partial"}
)


# ---------------------------------------------------------------------------
# Declared-type representation
# ---------------------------------------------------------------------------

class _DeclaredTypeSentinel(enum.Enum):
    """Sentinels for the declared_type field on EmittedField.

    PASSTHROUGH — no cast is emitted; the output dtype equals the source
        column's type. Consumers (e.g. schema inference) should resolve
        this against the input schema.

    UNDETERMINED — the output dtype cannot be predicted pre-compile.
        Includes: ANY + null_fill (coalesce may coerce the dtype);
        dotted source with ANY type (nested field type ≠ struct root type);
        categorical fields on backends other than Polars.
        Consumers should report UNKNOWN / SchemaTypeStatus.UNKNOWN.
    """

    PASSTHROUGH = "PASSTHROUGH"
    UNDETERMINED = "UNDETERMINED"


PASSTHROUGH = _DeclaredTypeSentinel.PASSTHROUGH
UNDETERMINED = _DeclaredTypeSentinel.UNDETERMINED

# Union of all valid declared_type values: a concrete dtype or a sentinel.
DeclaredType = Union["MountainashDtype", _DeclaredTypeSentinel]


# ---------------------------------------------------------------------------
# Output contract data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EmittedField:
    """One field that conform will emit, with its structural metadata.

    Attributes:
        field: The FieldSpec that produced this output column.
        source_name: Resolved source column name. For ``"exact"`` mode this is
            the positional name; for dotted sources the full dotted path is
            preserved (e.g. ``"payload.id"``).
        declared_type: The output dtype that ``_build_field_expr`` will produce
            for this field: a concrete :class:`MountainashDtype`, ``PASSTHROUGH``
            (resolve against input schema), or ``UNDETERMINED`` (cannot predict
            pre-compile → report ``UNKNOWN``).
        renamed: ``True`` when ``source_name != field.name``; drives the
            open-mode drop of the original source column.
    """

    field: "FieldSpec"
    source_name: str
    declared_type: DeclaredType
    renamed: bool


@dataclass(frozen=True)
class ConformOutputContract:
    """The pure structural decision of what conform will produce.

    This is the single source of truth for which columns conform emits,
    their names, source columns, and declared output types — without
    executing any backend operations.

    Attributes:
        fields_match: Resolved mode string (never ``None``).
        emitted: Ordered list of :class:`EmittedField`; only fields whose
            source root is present in ``available_columns`` are included.
        renamed_sources: Set of source column names that will be aliased to
            a different target name (used by open-mode callers to drop
            originals).
    """

    fields_match: str
    emitted: list[EmittedField]
    renamed_sources: set[str]

    @property
    def keeps_unmapped(self) -> bool:
        """``True`` for open mode (with_columns); ``False`` for select modes."""
        return self.fields_match == "open"


# ---------------------------------------------------------------------------
# ConformResult (unchanged public type returned by _build_conform_exprs)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# resolve_conform_output — structural decision (pure, no expression building)
# ---------------------------------------------------------------------------


def _source_root(source_name: str) -> str:
    """Root column of a possibly-dotted (struct) source name.

    ``"payload.id"`` -> ``"payload"``; a flat name is the identity. Shared
    by the fields_match guard and the skip/extract logic so the two can
    never disagree about what "present" means, and a reusable module-level
    primitive for declared-vs-actual diffing (item 48).
    """
    return source_name.split(".", 1)[0] if "." in source_name else source_name


def resolve_conform_output(
    spec: "TypeSpec",
    *,
    available_columns: Optional[Sequence[str]],
) -> ConformOutputContract:
    """Resolve the output contract for a TypeSpec conformance operation.

    This is the single source of truth for *what columns conform emits*:
    which spec fields are included, their source column names, their declared
    output types, and the rename tracking needed for open-mode drop.

    It owns the structural decisions extracted from ``_build_conform_exprs``:
    - ``fields_match`` resolution and validation
    - The four validation guards (raises :class:`ExactFieldCountError`,
      :class:`MissingFieldsError`, :class:`ExtraFieldsError`,
      :class:`NoMatchingFieldsError` unchanged)
    - Per-field source resolution (``fld.source_name``; positional for
      ``"exact"``; dotted path preserved)
    - Skip-on-absent (root col not in ``available_set``)
    - Rename tracking (``source_name != field.name``)
    - ``declared_type`` per field (mirrors stage-5 branch selection in
      ``_build_field_expr`` without building expressions)

    It does **not** build any expressions; the transform stages (2-6) remain
    in ``_build_field_expr``.

    Args:
        spec: The TypeSpec describing the target schema.
        available_columns: Ordered column names from the source data.
            Required for all ``fieldsMatch`` modes except ``"open"``.
            Sequence order matters for ``"exact"`` (positional mapping).

    Returns:
        A :class:`ConformOutputContract` with ``fields_match``, ``emitted``
        (one :class:`EmittedField` per included field), and ``renamed_sources``.

    Raises:
        ConformError: Invalid ``fields_match`` value, or ``available_columns``
            not provided when required.
        ExactFieldCountError: ``fields_match="exact"`` and column count
            does not match spec field count.
        MissingFieldsError: ``fields_match`` in ``{"equal", "subset"}`` and
            required source columns are absent. Dotted (struct) sources are
            validated on their root column.
        ExtraFieldsError: ``fields_match`` in ``{"equal", "superset"}`` and
            unmapped columns are present. Dotted (struct) sources are
            validated on their root column.
        NoMatchingFieldsError: ``fields_match="partial"`` and zero spec
            fields match available columns.
    """
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.universal_types import UniversalType, to_canonical

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
        # Guard pass/fail is computed on dotted ROOTS, consistent with
        # skip/extract below. Full dotted paths remain on
        # EmittedField.source_name (item 48 nested diagnostics).
        spec_source_roots = {_source_root(name) for name in spec_source_names}

        if fields_match == "exact":
            if len(available_columns) != len(spec.fields):
                raise ExactFieldCountError(
                    expected_count=len(spec.fields),
                    actual_count=len(available_columns),
                )

        elif fields_match == "equal":
            missing = sorted(spec_source_roots - available_set)
            if missing:
                raise MissingFieldsError(
                    missing_fields=missing, fields_match=fields_match,
                )
            extra = sorted(available_set - spec_source_roots)
            if extra:
                raise ExtraFieldsError(
                    extra_fields=extra, fields_match=fields_match,
                )

        elif fields_match == "subset":
            missing = sorted(spec_source_roots - available_set)
            if missing:
                raise MissingFieldsError(
                    missing_fields=missing, fields_match=fields_match,
                )

        elif fields_match == "superset":
            extra = sorted(available_set - spec_source_roots)
            if extra:
                raise ExtraFieldsError(
                    extra_fields=extra, fields_match=fields_match,
                )

        elif fields_match == "partial":
            if not spec_source_roots & available_set:
                raise NoMatchingFieldsError(
                    spec_fields=sorted(spec_source_names),
                    available_columns=sorted(available_set),
                )
        # "open" — no guard
    else:
        available_set = None  # type: ignore[assignment]

    # --- 3. Resolve per-field source names, skip-on-absent, rename tracking ---
    emitted: list[EmittedField] = []
    renamed_sources: set[str] = set()

    for idx, fld in enumerate(spec.fields):
        # Determine source column name
        if fields_match == "exact":
            # Positional mapping: use the i-th available column
            source_name = available_columns[idx]  # type: ignore[index]
        else:
            source_name = fld.source_name

        # Skip fields whose source isn't available (open/partial/superset)
        if available_set is not None:
            if _source_root(source_name) not in available_set:
                continue

        # Track renames (non-dotted source only)
        is_dotted = "." in source_name
        renamed = (not is_dotted) and (source_name != fld.name)
        if renamed:
            renamed_sources.add(source_name)

        # Compute declared_type — mirrors stage-5 branch selection verbatim
        # (the same mutually-exclusive branches, but returns a type token
        # instead of building an expression).
        if fld.type == UniversalType.ARRAY:
            # Stage 5a: list split + element cast → to_canonical(ARRAY)
            declared: DeclaredType = to_canonical(UniversalType.ARRAY)  # type: ignore[assignment]
        elif fld.categories is not None:
            # Stage 5b: categorical → Polars Categorical/Enum; dtype registry
            # maps pl.Categorical/pl.Enum to canonical STRING (target_polars.py:30-31)
            declared = MountainashDtype.STRING
        elif fld.type in {
            UniversalType.DATE, UniversalType.DATETIME, UniversalType.TIME,
        } and fld.format not in ("default", None, "any"):
            # Stage 5b temporal custom format: to_date/to_datetime/to_time
            canon = to_canonical(fld.type)
            declared = canon if canon is not None else UNDETERMINED  # type: ignore[assignment]
        elif fld.type == UniversalType.BOOLEAN:
            # Stage 5c: boolean mapping → to_canonical(BOOLEAN)
            canon = to_canonical(UniversalType.BOOLEAN)
            declared = canon if canon is not None else UNDETERMINED  # type: ignore[assignment]
        elif fld.type and fld.type != UniversalType.ANY:
            # Stage 5d: default canonical cast
            canon = to_canonical(fld.type)
            declared = canon if canon is not None else PASSTHROUGH  # type: ignore[assignment]
        else:
            # ANY / None — no cast in stage 5
            if fld.null_fill is not None or is_dotted:
                # null_fill: coalesce may coerce the dtype
                # dotted: nested field type ≠ struct root type
                declared = UNDETERMINED
            else:
                # Non-dotted ANY with no output-affecting transform → passthrough
                declared = PASSTHROUGH

        emitted.append(EmittedField(
            field=fld,
            source_name=source_name,
            declared_type=declared,
            renamed=renamed,
        ))

    return ConformOutputContract(
        fields_match=fields_match,
        emitted=emitted,
        renamed_sources=renamed_sources,
    )


# ---------------------------------------------------------------------------
# _build_field_expr — transform stages 1-6 (single unified function)
# ---------------------------------------------------------------------------

def _build_field_expr(
    field: "FieldSpec",
    source_name: str,
    schema_missing_values: Sequence[str] = (),
) -> Any:
    """Build the conform transform expression (stages 1-6) for one field.

    Contains the full transform pipeline:
      1. Source resolution (col(source_name) or struct field access for
         dotted names)
      2. Missing values (sentinel strings → null; Frictionless §missingValues)
      3. String parsing (numeric format normalisation: bareNumber, groupChar,
         decimalChar)
      4. Null fill (coalesce)
      5. Type cast (list / categorical / temporal / boolean / default)
      6. Alias (``expr.name.alias(field.name)``)

    Args:
        field: The FieldSpec to build an expression for.
        source_name: The resolved source column name (positional for exact
            mode; full dotted path for struct access).
        schema_missing_values: Schema-level missingValues, threaded so stage
            2's field-level-override-else-schema-level resolution works.
            Defaults to an empty tuple (no schema-level sentinels).

    Returns:
        A backend-agnostic mountainash expression ready to be collected.
    """
    import mountainash as ma
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.universal_types import UniversalType, to_canonical

    fld = field

    # Stage 1: RESOLVE SOURCE — col(source_name) or struct field access
    is_dotted = "." in source_name
    if is_dotted:
        parts = source_name.split(".")
        expr = ma.col(parts[0])
        for part in parts[1:]:
            expr = expr.struct.field(part)
    else:
        expr = ma.col(source_name)

    # Types eligible for missingValues sentinel replacement.
    # Non-scalar types (ARRAY, OBJECT, ANY) are excluded because
    # is_in on those types may raise backend errors.
    _SCALAR_TYPES = {
        UniversalType.STRING, UniversalType.NUMBER, UniversalType.INTEGER,
        UniversalType.BOOLEAN, UniversalType.DATE, UniversalType.DATETIME,
        UniversalType.TIME, UniversalType.YEAR, UniversalType.YEARMONTH,
        UniversalType.DURATION,
    }

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
                    stacklevel=3,
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
            from mountainash.core.dtypes import (
                MountainashDtype,
                TypeTarget,
                registry,
            )
            from mountainash.typespec.universal_types import (
                parse_universal,
                to_canonical,
            )

            import polars as pl

            item_canon = to_canonical(parse_universal(item_type_str))
            if item_canon is None:
                item_canon = MountainashDtype.STRING
            polars_type = registry.to_native_schema(
                item_canon, TypeTarget.POLARS
            )
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
            canon = to_canonical(fld.type)
            if canon is not None:  # ANY -> no cast (guard already excludes ANY)
                expr = expr.cast(canon)

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
    # str.to_datetime/str.to_time.  "any" falls through to the canonical
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
        str_expr = expr.cast(MountainashDtype.STRING)
        expr = (
            ma.when(str_expr.is_in(*true_vals)).then(ma.lit(True))
            .when(str_expr.is_in(*false_vals)).then(ma.lit(False))
            .otherwise(ma.lit(None))
        )

    # Stage 5d: DEFAULT TYPE CAST
    elif fld.type and fld.type != UniversalType.ANY:
        canon = to_canonical(fld.type)
        if canon is not None:
            expr = expr.cast(canon)

    expr = expr.name.alias(fld.name)
    return expr


# ---------------------------------------------------------------------------
# _build_conform_exprs — public API (signature-preserving refactor)
# ---------------------------------------------------------------------------

def _build_conform_exprs(
    spec: "TypeSpec",
    *,
    available_columns: Optional[Sequence[str]] = None,
) -> ConformResult:
    """Build the expression list for a TypeSpec conformance projection.

    Constructs one mountainash expression per spec field, chaining the
    stages documented in the module docstring.  The expressions are
    backend-agnostic — they compile to Polars, Ibis, or Narwhals when
    a terminal (e.g. ``.to_polars()``) triggers the visitor.

    Args:
        spec: The TypeSpec describing the target schema.  Key attributes
            consumed: ``fields``, ``fields_match``, ``missing_values``.
        available_columns: Ordered column names from the source data.
            Required for all ``fieldsMatch`` modes except ``"open"``.
            Sequence order matters for ``"exact"`` (positional mapping).

    Returns:
        A :class:`ConformResult` containing:
        - ``exprs`` — list of mountainash expressions, one per matched field
        - ``fields_match`` — the resolved mode string (never ``None``)
        - ``renamed_sources`` — set of source column names that were aliased
          to a different target name (used by callers to drop originals in
          ``"open"`` mode)

    Raises:
        ConformError: Invalid ``fields_match`` value, or ``available_columns``
            not provided when required.
        ExactFieldCountError: ``fields_match="exact"`` and column count
            does not match spec field count.
        MissingFieldsError: ``fields_match`` in ``{"equal", "subset"}`` and
            required source columns are absent.
        ExtraFieldsError: ``fields_match`` in ``{"equal", "superset"}`` and
            unmapped columns are present.
        NoMatchingFieldsError: ``fields_match="partial"`` and zero spec
            fields match available columns.
    """
    # Resolve schema-level missingValues once.
    # The Frictionless default is [""] but TypeSpec.missing_values defaults
    # to [""] via its factory.  We only activate the sentinel pipeline when
    # the spec carries a non-empty list — an explicit empty list [] or None
    # both mean "no sentinels".  This avoids emitting is_in([""])  on
    # already-typed (non-string) columns where the comparison would raise.
    schema_missing_values: list = spec.missing_values or []

    # Resolve the structural contract (which fields to emit, source names,
    # rename tracking, declared types) — pure, no expressions built here.
    contract = resolve_conform_output(spec, available_columns=available_columns)

    # Build one expression per emitted field.
    exprs: list[Any] = []
    for em in contract.emitted:
        expr = _build_field_expr(
            em.field, em.source_name, schema_missing_values
        )
        exprs.append(expr)

    return ConformResult(
        exprs=exprs,
        fields_match=contract.fields_match,
        renamed_sources=contract.renamed_sources,
    )
