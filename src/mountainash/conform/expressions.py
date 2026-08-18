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

import dataclasses
import enum
import warnings
from dataclasses import dataclass, field as dataclass_field
from typing import TYPE_CHECKING, Any, Callable, Mapping, Optional, Sequence, Union

from mountainash.conform.contract import ConformContract, resolve_contract
from mountainash.conform.errors import (
    ConformError,
    ExactFieldCountError,
    ExtraFieldsError,
    MissingFieldsError,
    NoMatchingFieldsError,
)

if TYPE_CHECKING:
    from mountainash.conform.drift import ConformDrift, KeyDrift
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.spec import FieldSpec, ForeignKey, TypeSpec

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
            pre-compile → report ``UNKNOWN``). For ``type_action == "null_fill"``
            this is always a concrete dtype or ``UNDETERMINED`` — never
            ``PASSTHROUGH``, since there is no source column to pass through.
        renamed: ``True`` when ``source_name != field.name``; drives the
            open-mode drop of the original source column.
        type_action: The per-field build policy driving ``_build_field_expr``.
            Four values come from the data_type dimension (item 48 Task 6):
            ``"coerce"`` (default, today's behaviour — cast to the declared
            type), ``"evolve"`` (no cast, output keeps the source/actual
            type), ``"discard_value"`` (cast with null-on-failure), or
            ``"discard_row"`` (same null-cast, plus the source registers in
            ``row_filter_sources`` for a row-drop predicate) — only set to
            one of these four when unsafe-cast drift was actually detected
            against ``actual_dtypes`` evidence. A fifth value,
            ``"null_fill"`` (item 48 Task 10), comes from the
            missing_columns dimension instead: the field's declared source
            root is entirely absent, so there is no source to cast at all —
            ``_build_field_expr`` emits a typed null literal instead of
            resolving/transforming a source column.
        effective_type: The post-policy canonical type when it diverges from
            ``declared_type`` (currently only set for ``type_action ==
            "evolve"``, where it holds the source's actual dtype). ``None``
            means the declared type applies as-is.
    """

    field: "FieldSpec"
    source_name: str
    declared_type: DeclaredType
    renamed: bool
    type_action: str = "coerce"
    effective_type: Optional[Any] = None


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
        drift: The :class:`~mountainash.conform.drift.ConformDrift` report
            assembled during this call (item 48 Task 6), or ``None`` when no
            assessment ran at all — i.e. ``available_columns`` was not
            provided (no column-dimension guard) and ``actual_dtypes`` was
            not provided (no data_type assessment). This is honest
            non-assessment, not "assessed clean" (mirrors the
            ``key_changes`` None-vs-``[]`` distinction on ``ConformDrift``
            itself). A freeze-policy violation raises ``SchemaDriftError``
            instead of returning, so a non-``None`` ``drift`` here always
            represents a non-raising (or non-frozen) outcome.
        row_filter_sources: ``(source_name, declared_canonical_type)`` pairs
            needing a discard-row predicate — populated when the data_type
            dimension resolves to ``"discard_row"`` for a field. Consumers
            (the DAG visitor / ``Relation.conform``) build the actual
            row-drop filter; this evaluator only records which sources need
            one.
    """

    fields_match: str
    emitted: list[EmittedField]
    renamed_sources: set[str]
    drift: Optional["ConformDrift"] = None
    row_filter_sources: list[tuple[str, Any]] = dataclass_field(default_factory=list)

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

    ``drift`` and ``row_filter_sources`` are pass-through copies of the
    same-named :class:`ConformOutputContract` attributes (item 48 Task 7) —
    execute-mode callers (``UnifiedRelationVisitor.apply_conform``) consume
    them without needing to call ``resolve_conform_output`` separately.
    Both default to their "nothing assessed" values (``None`` / ``[]``) so
    existing callers that don't pass ``actual_dtypes``/``contract`` see no
    behaviour change.
    """

    exprs: list  # mountainash expressions
    fields_match: str  # resolved mode (never None)
    renamed_sources: set = dataclass_field(default_factory=set)
    drift: Optional["ConformDrift"] = None
    row_filter_sources: list = dataclass_field(default_factory=list)


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


def _raise_drift(
    *,
    missing_columns: Optional[Sequence[str]] = None,
    extra_columns: Optional[Sequence[str]] = None,
    type_mismatches: Optional[Sequence[Any]] = None,
    key_changes: Optional[Sequence[Any]] = None,
    node_identity: Optional[tuple] = None,
) -> None:
    """Raise ``SchemaDriftError`` for an explicit-contract freeze violation.

    Called for non-preset contracts (``from_preset=False``) where a frozen
    dimension tripped: column-dimension violations (``missing_columns`` /
    ``extra_columns``, from the fieldsMatch guard), the data_type dimension
    (``type_mismatches``, from the Task 6 detection loop), or the keys
    dimension (``key_changes``, item 48 PR-D). Exactly one of the four is
    populated per call site — each call raises immediately for the one
    dimension it represents, so the resulting ``ConformDrift`` only ever
    carries that single dimension's entries (the other three stay
    empty/``[]``/``None``).
    """
    from mountainash.conform.drift import ColumnDrift, ConformDrift
    from mountainash.conform.errors import SchemaDriftError

    node_id, resource_name, spec_name = (
        node_identity if node_identity is not None else (None, None, None)
    )
    drift = ConformDrift(
        node_id=node_id,
        resource_name=resource_name,
        spec_name=spec_name,
        extra_columns=[
            ColumnDrift(name=n, action="freeze") for n in (extra_columns or [])
        ],
        missing_columns=[
            ColumnDrift(name=n, action="freeze") for n in (missing_columns or [])
        ],
        type_mismatches=list(type_mismatches or []),
        key_changes=list(key_changes) if key_changes is not None else None,
    )
    if extra_columns:
        dimension = "extra_columns"
    elif missing_columns:
        dimension = "missing_columns"
    elif key_changes:
        dimension = "keys"
    else:
        dimension = "data_type"
    raise SchemaDriftError(f"{dimension} drift under freeze policy", drift=drift)


def _resolve_declared_type(fld: "FieldSpec", source_name: str) -> DeclaredType:
    """Compute the stage-5 declared output type for one field.

    Mirrors ``_build_field_expr`` stage 5's branch selection verbatim (the
    same mutually-exclusive conditions on ``fld.type``/``fld.categories``/
    ``fld.format``) but returns a type token instead of building an
    expression. Single source of truth shared by ``resolve_conform_output``
    (populates ``EmittedField.declared_type``, sentinels included — used by
    schema inference) and ``_declared_canonical`` (item 48 Task 6 data_type
    drift detection, which only wants a concrete dtype or ``None``).

    ``source_name`` is the *resolved* source for this emission (positional
    for ``"exact"`` mode, ``fld.source_name`` otherwise) — dotted-ness is
    derived from it, not from ``fld.source_name`` directly, so behaviour is
    unchanged from the pre-extraction inline version.
    """
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.typespec.universal_types import UniversalType, to_canonical

    is_dotted = "." in source_name

    if fld.type == UniversalType.ARRAY:
        # Stage 5a: list split + element cast → to_canonical(ARRAY)
        return to_canonical(UniversalType.ARRAY)  # type: ignore[return-value]
    if fld.categories is not None:
        # Stage 5b: categorical → Polars Categorical/Enum; dtype registry
        # maps pl.Categorical/pl.Enum to canonical STRING (target_polars.py:30-31)
        return MountainashDtype.STRING
    if fld.type in {
        UniversalType.DATE, UniversalType.DATETIME, UniversalType.TIME,
    } and fld.format not in ("default", None, "any"):
        # Stage 5b temporal custom format: to_date/to_datetime/to_time
        canon = to_canonical(fld.type)
        return canon if canon is not None else UNDETERMINED
    if fld.type == UniversalType.BOOLEAN:
        # Stage 5c: boolean mapping → to_canonical(BOOLEAN)
        canon = to_canonical(UniversalType.BOOLEAN)
        return canon if canon is not None else UNDETERMINED
    if fld.type and fld.type != UniversalType.ANY:
        # Stage 5d: default canonical cast
        canon = to_canonical(fld.type)
        return canon if canon is not None else PASSTHROUGH
    # ANY / None — no cast in stage 5
    if fld.null_fill is not None or is_dotted:
        # null_fill: coalesce may coerce the dtype
        # dotted: nested field type ≠ struct root type
        return UNDETERMINED
    # Non-dotted ANY with no output-affecting transform → passthrough
    return PASSTHROUGH


def _declared_canonical(fld: "FieldSpec") -> Optional["MountainashDtype"]:
    """The concrete canonical declared dtype for ``fld``, or ``None``.

    Reuses :func:`_resolve_declared_type` (shared with
    ``EmittedField.declared_type``) but collapses the ``PASSTHROUGH`` /
    ``UNDETERMINED`` sentinels to ``None`` — item 48 Task 6's data_type drift
    detection only ever compares against a concrete declared dtype;
    "no predictable declared type" means "no assessment possible", the same
    honesty rule applied to missing actual-dtype evidence.
    """
    from mountainash.core.dtypes import MountainashDtype

    declared = _resolve_declared_type(fld, fld.source_name)
    return declared if isinstance(declared, MountainashDtype) else None


def resolve_conform_output(
    spec: "TypeSpec",
    available_columns: Optional[Sequence[str]] = None,
    *,
    actual_dtypes: Optional[Mapping[str, Any]] = None,
    contract: Optional[ConformContract] = None,
    node_identity: Optional[tuple] = None,
    raise_on_freeze: bool = True,
    key_fks: Optional[Sequence["ForeignKey"]] = None,
    key_resource_name: Optional[str] = None,
    schema_of: Optional[Callable[[str], Mapping[str, Any]]] = None,
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
        actual_dtypes: Optional ``{column_name: MountainashDtype}`` evidence
            (item 48 Task 6) driving data_type drift detection. Missing
            entries, and entries whose value is a
            :class:`~mountainash.relations.schema_inference.SchemaTypeStatus`
            sentinel (e.g. ``UNKNOWN``), are treated as "no evidence" — no
            assessment, not a false-positive drift. Dotted (struct) sources
            are always excluded from type detection: the struct ROOT's
            actual dtype is never compared to a nested field's declared type.
        contract: The resolved :class:`ConformContract` driving the guard.
            When ``None`` (the default), one is derived internally via
            ``resolve_contract(fields_match)`` — i.e. the plain
            ``fields_match`` preset with no explicit layering.
        node_identity: Optional ``(node_id, resource_name, spec_name)``
            pass-through for the ``ConformDrift`` reports this call may
            build or raise. ``None`` (the default) leaves all three identity
            fields ``None`` — the DAG visitor supplies real identity in a
            later task (item 48 Task 7).
        raise_on_freeze: When ``True`` (the default, execute-time behaviour —
            ``UnifiedRelationVisitor.apply_conform``), a non-preset
            (``from_preset=False``) contract's ``freeze`` policy raises
            ``SchemaDriftError`` as documented below. When ``False``
            (build-time callers: ``infer_schema``'s ``ConformRelNode``
            branch and ``Relation.assess_drift()``, item 48 Task 9), those
            same ``freeze`` violations are folded into the returned
            ``drift`` report instead of raising — inference and pre-flight
            assessment must never raise ``SchemaDriftError`` (R1/R2: build
            time stays non-fatal). This only gates the *explicit-contract*
            freeze raises (the ``_raise_drift`` call sites); the
            preset-provenance legacy errors (``MissingFieldsError`` /
            ``ExtraFieldsError``) are a separate, older structural-guard
            concern and are unaffected by this flag.
        key_fks: Optional list of :class:`~mountainash.typespec.spec.ForeignKey`
            declared with this resource as the child side (item 48 PR-D,
            the ``keys`` dimension). ``None`` (the default — no DAG/FK
            context available) means key drift is NOT ASSESSED at all;
            ``ConformDrift.key_changes`` stays ``None``. An empty list
            means key drift WAS assessed and no FKs are declared —
            ``key_changes`` becomes ``[]`` (assessed clean). Only ``keys``
            child-scoped: FKs where this resource is the *reference*
            (parent) side are not evaluated here (finding 9 — a
            documented future consideration).
        key_resource_name: The child resource name used to resolve a
            self-referencing FK's target (``fk.reference.resource == ""``
            normalises to this name, mirroring
            ``RelationDAG.add_constraint``'s self-edge rule).
        schema_of: Optional ``name -> {column: dtype}`` resolver (typically
            ``RelationDAG.schema``) used to look up the FK's reference-side
            schema for ``dangling_reference``/``fk_type_mismatch``
            detection. A ``KeyError`` from this callable is treated as
            "reference resource not resolvable" (``dangling_reference``).

    Returns:
        A :class:`ConformOutputContract` with ``fields_match``, ``emitted``
        (one :class:`EmittedField` per included field), ``renamed_sources``,
        ``drift``, and ``row_filter_sources``.

    Raises:
        ConformError: Invalid ``fields_match`` value, or ``available_columns``
            not provided when required.
        ExactFieldCountError: ``fields_match="exact"`` and column count
            does not match spec field count.
        MissingFieldsError: ``fields_match`` in ``{"equal", "subset"}`` and
            required source columns are absent (preset-provenance contract).
            Dotted (struct) sources are validated on their root column.
        ExtraFieldsError: ``fields_match`` in ``{"equal", "superset"}`` and
            unmapped columns are present (preset-provenance contract).
            Dotted (struct) sources are validated on their root column.
        NoMatchingFieldsError: ``fields_match="partial"`` and zero spec
            fields match available columns.
        SchemaDriftError: A non-preset (``from_preset=False``) contract has
            a frozen dimension (``extra_columns``, ``missing_columns``,
            ``data_type``, or ``keys``) that tripped.
    """
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

    if contract is None:
        contract = resolve_contract(fields_match)

    # Column-dimension drift, hoisted so it survives past the guard block
    # (positional/"exact" mapping never populates these; both stay empty).
    missing: list[str] = []
    extra: list[str] = []

    if available_columns is not None:
        available_set: set[str] = set(available_columns)
        # Source names the spec expects to find in the data
        spec_source_names = {f.source_name for f in spec.fields}
        # Guard pass/fail is computed on dotted ROOTS, consistent with
        # skip/extract below. Full dotted paths remain on
        # EmittedField.source_name (item 48 nested diagnostics).
        spec_source_roots = {_source_root(name) for name in spec_source_names}

        if contract.count_must_match and len(available_columns) != len(spec.fields):
            raise ExactFieldCountError(
                expected_count=len(spec.fields), actual_count=len(available_columns),
            )
        if contract.mapping == "by_name":
            if contract.minimum_overlap and len(
                spec_source_roots & available_set
            ) < contract.minimum_overlap:
                raise NoMatchingFieldsError(
                    spec_fields=sorted(spec_source_names),
                    available_columns=sorted(available_set),
                )
            missing = sorted(spec_source_roots - available_set)
            extra = sorted(available_set - spec_source_roots)
            if contract.missing_columns == "freeze" and missing:
                if contract.from_preset:
                    raise MissingFieldsError(missing_fields=missing, fields_match=fields_match)
                if raise_on_freeze:
                    _raise_drift(missing_columns=missing, node_identity=node_identity)
            if contract.extra_columns == "freeze" and extra:
                if contract.from_preset:
                    raise ExtraFieldsError(extra_fields=extra, fields_match=fields_match)
                if raise_on_freeze:
                    _raise_drift(extra_columns=extra, node_identity=node_identity)
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

        # Skip fields whose source isn't available (open/partial/superset) —
        # or, when the contract says so, emit a typed null instead of
        # skipping (missing_columns="null_fill", item 48 Task 10). Only an
        # explicit contract layer can select "null_fill": none of the six
        # fields_match presets do (contract.py FIELDS_MATCH_PRESETS all use
        # "skip" or "freeze"), so this branch never fires for preset-only
        # contracts.
        if available_set is not None:
            if _source_root(source_name) not in available_set:
                if contract.missing_columns == "null_fill":
                    declared_canon = _declared_canonical(fld)
                    emitted.append(EmittedField(
                        field=fld,
                        source_name=source_name,
                        declared_type=(
                            declared_canon
                            if declared_canon is not None
                            else UNDETERMINED
                        ),
                        renamed=False,  # no source column exists to drop
                        type_action="null_fill",
                    ))
                continue

        # Track renames (non-dotted source only)
        is_dotted = "." in source_name
        renamed = (not is_dotted) and (source_name != fld.name)
        if renamed:
            renamed_sources.add(source_name)

        # Compute declared_type — mirrors stage-5 branch selection verbatim
        # (the same mutually-exclusive branches, but returns a type token
        # instead of building an expression).
        declared: DeclaredType = _resolve_declared_type(fld, source_name)

        emitted.append(EmittedField(
            field=fld,
            source_name=source_name,
            declared_type=declared,
            renamed=renamed,
        ))

    # --- 4. data_type drift detection + policy (item 48 Task 6) ---
    #
    # Canonical-space only: compares MountainashDtype evidence, never
    # compiles or inspects backend expressions. Dotted (struct) sources are
    # excluded up front — the struct ROOT's actual dtype is never the same
    # domain as a nested field's declared type (finding 10). Missing/UNKNOWN
    # actual-dtype evidence is treated as "cannot assess", not drift — the
    # honest best-effort-introspection default (R1/R2).
    from mountainash.conform.drift import ColumnDrift, ConformDrift, KeyDrift, TypeDrift
    from mountainash.core.dtypes import CastSafety, MountainashDtype, classify_cast
    from mountainash.relations.schema_inference import SchemaTypeStatus

    type_mismatches: list[TypeDrift] = []
    row_filter_sources: list[tuple[str, Any]] = []
    resolved_emitted: list[EmittedField] = []
    for em in emitted:
        if "." in em.source_name or em.type_action == "null_fill":
            # Dotted sources are out of scope (finding 10). null_fill fields
            # (item 48 Task 10) have no source column at all -- `actual_dtypes`
            # and `available_columns` are expected to agree, but this guard
            # keeps a stale/inconsistent `actual_dtypes` entry from
            # clobbering the null_fill type_action set above.
            resolved_emitted.append(em)
            continue
        declared_canon = _declared_canonical(em.field)
        actual = (actual_dtypes or {}).get(em.source_name)
        if (
            declared_canon is None
            or actual is None
            or isinstance(actual, SchemaTypeStatus)
        ):
            resolved_emitted.append(em)
            continue
        if classify_cast(actual, declared_canon) is CastSafety.SAFE:
            resolved_emitted.append(em)
            continue

        action = contract.data_type
        type_mismatches.append(TypeDrift(
            name=em.field.name, declared=declared_canon, actual=actual,
            safety=CastSafety.UNSAFE.value, action=action,
        ))
        if action == "evolve":
            em = dataclasses.replace(em, type_action="evolve", effective_type=actual)
        elif action == "discard_value":
            em = dataclasses.replace(em, type_action="discard_value")
        elif action == "discard_row":
            em = dataclasses.replace(em, type_action="discard_value")
            row_filter_sources.append((em.source_name, declared_canon))
        # "coerce" (default) and "freeze" (about to raise) leave em as-is.
        resolved_emitted.append(em)
    emitted = resolved_emitted

    if contract.data_type == "freeze" and type_mismatches and raise_on_freeze:
        _raise_drift(type_mismatches=type_mismatches, node_identity=node_identity)

    # --- 4b. Key (FK) drift detection + policy (item 48 PR-D) ---
    #
    # Child-scoped only (finding 9): evaluates FKs declared with *this*
    # resource as the child side (``key_fks`` — already pre-filtered by the
    # caller via ``RelationDAG.constraints_for``). Parent-side/inbound
    # references are not evaluated here — a documented future
    # consideration. Only runs when ``key_fks`` is not ``None`` — i.e. a
    # DAG/FK context was actually supplied (mirrors the data_type
    # dimension's "no actual_dtypes -> no assessment" honesty rule).
    # ``key_fks == []`` (context present, zero declared FKs) still counts
    # as an assessment -- ``key_changes`` becomes ``[]`` (assessed clean),
    # never ``None``.
    key_changes: Optional[list["KeyDrift"]] = None
    if key_fks is not None:
        key_changes = []
        emitted_by_name = {em.field.name: em for em in emitted}
        output_names = set(emitted_by_name)
        for fk in key_fks:
            target: Optional[str] = fk.reference.resource or key_resource_name

            # fk_field_dropped: this FK's own fields are no longer present
            # in the conformed output (declared-but-dropped by a
            # skip/discard policy, or never a spec field at all).
            dropped = [f for f in fk.fields if f not in output_names]
            if dropped:
                key_changes.append(KeyDrift(
                    kind="fk_field_dropped", fields=dropped,
                    reference=target, action=contract.keys,
                ))
                continue

            # dangling_reference: no resolvable target name (self-ref FK
            # with no key_resource_name supplied), or the referenced
            # resource/fields aren't resolvable via schema_of.
            if target is None:
                key_changes.append(KeyDrift(
                    kind="dangling_reference", fields=list(fk.fields),
                    reference=target, action=contract.keys,
                ))
                continue
            try:
                parent_schema = schema_of(target) if schema_of is not None else {}
            except KeyError:
                key_changes.append(KeyDrift(
                    kind="dangling_reference", fields=list(fk.fields),
                    reference=target, action=contract.keys,
                ))
                continue
            if any(f not in parent_schema for f in fk.reference.fields):
                key_changes.append(KeyDrift(
                    kind="dangling_reference", fields=list(fk.fields),
                    reference=target, action=contract.keys,
                ))
                continue

            # fk_type_mismatch (finding 8): only when BOTH sides' canonical
            # dtypes are known — missing/UNKNOWN evidence is "cannot
            # assess", same honesty rule as the data_type dimension above.
            for local_field, ref_field in zip(fk.fields, fk.reference.fields):
                child_em = emitted_by_name.get(local_field)
                child_dtype: Optional["MountainashDtype"] = None
                if child_em is not None:
                    if child_em.type_action == "evolve" and child_em.effective_type is not None:
                        child_dtype = child_em.effective_type
                    elif isinstance(child_em.declared_type, MountainashDtype):
                        child_dtype = child_em.declared_type
                parent_dtype = parent_schema.get(ref_field)
                if (
                    child_dtype is None
                    or parent_dtype is None
                    or isinstance(parent_dtype, SchemaTypeStatus)
                ):
                    continue
                if classify_cast(child_dtype, parent_dtype) is CastSafety.UNSAFE:
                    key_changes.append(KeyDrift(
                        kind="fk_type_mismatch", fields=[local_field],
                        reference=target, declared=parent_dtype,
                        actual=child_dtype, action=contract.keys,
                    ))

        if contract.keys == "freeze" and key_changes and raise_on_freeze:
            _raise_drift(key_changes=key_changes, node_identity=node_identity)

    # --- 5. Assemble the non-raising drift report ---
    #
    # None (not an empty ConformDrift) when nothing was assessed at all —
    # honest non-assessment mirrors ConformDrift.key_changes' None-vs-[]
    # distinction. A freeze violation always raises above rather than
    # reaching here, so a populated drift here never itself represents a
    # frozen violation.
    drift: Optional[ConformDrift] = None
    if available_set is not None or actual_dtypes is not None or key_changes is not None:
        node_id, resource_name, spec_name = (
            node_identity if node_identity is not None else (None, None, None)
        )
        drift = ConformDrift(
            node_id=node_id,
            resource_name=resource_name,
            spec_name=spec_name,
            extra_columns=[
                ColumnDrift(name=n, action=contract.extra_columns) for n in extra
            ],
            missing_columns=[
                ColumnDrift(name=n, action=contract.missing_columns) for n in missing
            ],
            type_mismatches=type_mismatches,
            key_changes=key_changes,
        )

    return ConformOutputContract(
        fields_match=fields_match,
        emitted=emitted,
        renamed_sources=renamed_sources,
        drift=drift,
        row_filter_sources=row_filter_sources,
    )


# ---------------------------------------------------------------------------
# _build_field_expr — transform stages 1-6 (single unified function)
# ---------------------------------------------------------------------------

def _build_field_expr(
    field: "FieldSpec",
    source_name: str,
    schema_missing_values: Sequence[str] = (),
    *,
    type_action: str = "coerce",
    declared_type: Optional["DeclaredType"] = None,
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

    ``type_action == "null_fill"`` (item 48 Task 10) bypasses the whole
    pipeline above: there is no source column to resolve at all (the
    declared field's source root is absent from the input), so stages 1-5
    are skipped entirely in favour of a typed null literal.

    Args:
        field: The FieldSpec to build an expression for.
        source_name: The resolved source column name (positional for exact
            mode; full dotted path for struct access). Unused when
            ``type_action == "null_fill"`` — there is no source column.
        schema_missing_values: Schema-level missingValues, threaded so stage
            2's field-level-override-else-schema-level resolution works.
            Defaults to an empty tuple (no schema-level sentinels).
        type_action: The per-field build policy for this field (see
            ``EmittedField.type_action``). Stage 5d (the default canonical
            cast — list/categorical/custom-format-temporal/boolean fields
            have their own bespoke stage-5 transforms and don't yet consume
            this) branches on the four data_type values: ``"coerce"``
            (default) casts as today; ``"evolve"`` skips the cast entirely;
            ``"discard_value"``/``"discard_row"`` cast with null-on-failure.
            ``"null_fill"`` short-circuits before stage 1 (see above).
        declared_type: The field's resolved declared type (a concrete
            :class:`MountainashDtype` or a sentinel) — only consumed when
            ``type_action == "null_fill"``, where a concrete dtype drives
            the typed null's cast; a sentinel (no predictable declared
            type) leaves the null uncast.

    Returns:
        A backend-agnostic mountainash expression ready to be collected.
    """
    import mountainash as ma
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
        CaseFailureBehaviour,
    )
    from mountainash.typespec.universal_types import UniversalType, to_canonical

    fld = field

    # missing_columns="null_fill" (item 48 Task 10): the declared field's
    # source root is entirely absent from the input -- there is no column
    # to resolve, parse, or cast-from. Build a TYPED null literal instead:
    # an untyped null is rejected by some backends (e.g. Ibis/DuckDB reject
    # an ambiguous NULL-typed column), so the null is cast to the declared
    # canonical dtype whenever one is known (PASSTHROUGH/UNDETERMINED
    # sentinels leave it uncast -- there is nothing to cast to).
    if type_action == "null_fill":
        expr = ma.lit(None)
        if isinstance(declared_type, MountainashDtype):
            expr = expr.cast(declared_type)
        return expr.name.alias(fld.name)

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
        from mountainash.typespec._categorical import categorical_values
        cat_values = categorical_values(fld.categories)

        # OBJECT has no scalar base cast; categories still take precedence
        # over object_fields for this degenerate declaration.
        if fld.type and fld.type not in (UniversalType.ANY, UniversalType.OBJECT):
            canon = to_canonical(fld.type)
            if canon is not None:
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
    # Stage 5e: STRUCT — cast an already-struct-typed source column to the
    # fully nested typed struct (item 102). Source is assumed to already be
    # native struct/dict-shaped; this is not a JSON-string parse path.
    elif fld.type == UniversalType.OBJECT and fld.object_fields:
        from mountainash.core.dtypes import TypeTarget
        from mountainash.typespec.converters import _resolve_struct_inner

        native_struct = _resolve_struct_inner(
            fld.name, fld.object_fields, TypeTarget.POLARS, None
        )
        expr = expr.cast(native_struct)


    # Stage 5d: DEFAULT TYPE CAST
    # Branches on type_action (item 48 Task 6 data_type policy): "coerce"
    # (default) casts as always; "evolve" skips the cast (output keeps the
    # source/actual type); anything else ("discard_value"/"discard_row")
    # casts with null-on-failure so unsafe values become null instead of
    # raising.
    elif fld.type and fld.type != UniversalType.ANY:
        canon = to_canonical(fld.type)
        if canon is not None:
            if type_action == "coerce":
                expr = expr.cast(canon)
            elif type_action == "evolve":
                pass  # no cast — output keeps the source's actual type
            else:  # "discard_value" / "discard_row"
                expr = expr.cast(canon, failure_behavior=CaseFailureBehaviour.NULL)

    expr = expr.name.alias(fld.name)
    return expr


# ---------------------------------------------------------------------------
# _build_conform_exprs — public API (signature-preserving refactor)
# ---------------------------------------------------------------------------

def _build_conform_exprs(
    spec: "TypeSpec",
    *,
    available_columns: Optional[Sequence[str]] = None,
    actual_dtypes: Optional[Mapping[str, Any]] = None,
    contract: Optional[ConformContract] = None,
    node_identity: Optional[tuple] = None,
    key_fks: Optional[Sequence["ForeignKey"]] = None,
    key_resource_name: Optional[str] = None,
    schema_of: Optional[Callable[[str], Mapping[str, Any]]] = None,
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
        actual_dtypes: Optional ``{column_name: MountainashDtype}`` evidence
            (item 48 Task 6/7) driving data_type drift detection. Passed
            through verbatim to :func:`resolve_conform_output`.
        contract: The resolved :class:`ConformContract` driving the
            fieldsMatch guard and the data_type/keys policy. ``None`` (the
            default) derives one internally via ``resolve_contract`` from
            ``spec.fields_match`` — unchanged behaviour for callers that
            don't pass an explicit contract (item 48 Task 7).
        node_identity: Optional ``(node_id, resource_name, spec_name)``
            pass-through for the ``ConformDrift`` report this call may build
            or raise. Passed through verbatim to :func:`resolve_conform_output`.
        key_fks: Optional pre-filtered (child-scoped) foreign keys driving
            the ``keys`` dimension (item 48 PR-D). Passed through verbatim
            to :func:`resolve_conform_output` — ``None`` means key drift is
            not assessed at all.
        key_resource_name: Child resource name for self-referencing FK
            resolution. Passed through verbatim to
            :func:`resolve_conform_output`.
        schema_of: Optional reference-side schema resolver. Passed through
            verbatim to :func:`resolve_conform_output`.

    Returns:
        A :class:`ConformResult` containing:
        - ``exprs`` — list of mountainash expressions, one per matched field
        - ``fields_match`` — the resolved mode string (never ``None``)
        - ``renamed_sources`` — set of source column names that were aliased
          to a different target name (used by callers to drop originals in
          ``"open"`` mode)
        - ``drift`` — the :class:`~mountainash.conform.drift.ConformDrift`
          assembled during this call, or ``None`` when nothing was assessed
          (mirrors :attr:`ConformOutputContract.drift`)
        - ``row_filter_sources`` — ``(source_name, declared_type)`` pairs
          needing a discard-row predicate (mirrors
          :attr:`ConformOutputContract.row_filter_sources`)

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
        SchemaDriftError: A non-preset (``from_preset=False``) contract has
            a frozen dimension that tripped (item 48 Task 7).
    """
    # Resolve schema-level missingValues once.
    # The Frictionless default is [""] but TypeSpec.missing_values defaults
    # to [""] via its factory.  We only activate the sentinel pipeline when
    # the spec carries a non-empty list — an explicit empty list [] or None
    # both mean "no sentinels".  This avoids emitting is_in([""])  on
    # already-typed (non-string) columns where the comparison would raise.
    schema_missing_values: list = spec.missing_values or []

    # Resolve the structural contract (which fields to emit, source names,
    # rename tracking, declared types, data_type drift/policy) — pure, no
    # expressions built here. Named `output_contract` (not `contract`) to
    # keep the ConformOutputContract distinct from the ConformContract
    # parameter above — the two types share a name-root but are not
    # interchangeable.
    output_contract = resolve_conform_output(
        spec,
        available_columns=available_columns,
        actual_dtypes=actual_dtypes,
        contract=contract,
        node_identity=node_identity,
        key_fks=key_fks,
        key_resource_name=key_resource_name,
        schema_of=schema_of,
    )

    # Build one expression per emitted field. em.type_action (item 48 Task 6)
    # drives stage 5d's cast-vs-skip-vs-null-on-failure branch; it is
    # "coerce" (the pre-Task-6 default) unless actual_dtypes/contract
    # evidence produced a data_type policy override above.
    exprs: list[Any] = []
    for em in output_contract.emitted:
        expr = _build_field_expr(
            em.field, em.source_name, schema_missing_values,
            type_action=em.type_action,
            declared_type=em.declared_type,
        )
        exprs.append(expr)

    return ConformResult(
        exprs=exprs,
        fields_match=output_contract.fields_match,
        renamed_sources=output_contract.renamed_sources,
        drift=output_contract.drift,
        row_filter_sources=output_contract.row_filter_sources,
    )
