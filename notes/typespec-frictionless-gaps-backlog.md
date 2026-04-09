# TypeSpec ↔ Frictionless — Deferred Low-Severity Gaps

These gaps were deferred from the 2026-04-07 Frictionless Data Package implementation work because they are Low priority and do not block descriptor round-trip in practice. They can be picked up as standalone follow-ups.

(Source audit: `notes/typespec-frictionless-gaps.md`, gap numbers refer to the consolidated checklist there.)

---

## Gap 2 — `$schema` not modelled

**Severity:** Low

**Location:** `spec.py:127-140` (absent)

**Description:**
`$schema` — missing from `TypeSpec` and both converter functions.
The spec allows (and recommends) a `$schema` URI property. Neither `TypeSpec` (`spec.py:127-140`) nor the converters model or pass it through. Silently dropped on import.

**Notes:** Interoperability; no data loss.

---

## Gap 5 — `example` not modelled

**Severity:** Low

**Location:** `spec.py:68-88` (absent)

**Description:**
`example` (field-level) — missing from `FieldSpec` and both converter functions.
The spec defines a field-level `example` property. `FieldSpec` (`spec.py:68-88`) has no `example` attribute; it is silently dropped on import.

**Notes:** Documentation field; no semantic impact.

---

## Gap 6 — `rdfType` not modelled

**Severity:** Low

**Location:** `spec.py:68-88` (absent)

**Description:**
`rdfType` (field-level) — missing from `FieldSpec` and both converter functions.
The spec defines an `rdfType` URI property for semantic annotation. `FieldSpec` (`spec.py:68-88`) has no `rdf_type` attribute; silently dropped on import.

**Notes:** Semantic annotation; no data loss.

---

## Gap 8 — `categoriesOrdered` not modelled

**Severity:** Low

**Location:** `spec.py:68-88` (absent)

**Description:**
`categoriesOrdered` (field-level) — missing from `FieldSpec` and both converter functions.
Companion boolean to `categories`. Not modelled in `FieldSpec` (`spec.py:68-88`); silently dropped on import.

**Notes:** Only meaningful alongside `categories`; gap 7 (`categories`) was fixed in the 2026-04-07 batch.

---

## Gap 11 — `number.*` / `integer.*` / `list.*` type-specific properties not modelled

**Severity:** Low

**Location:** `spec.py:68-88` (absent)

**Description:**
Type-specific field properties — none are modelled in `FieldSpec` and none are round-tripped:

- `number.decimalChar` / `number.groupChar` / `number.bareNumber` — number field formatting properties; not modelled.
- `integer.groupChar` / `integer.bareNumber` — integer field formatting properties; not modelled.
- `list.delimiter` / `list.itemType` — list field properties; not modelled.

**Notes:** These are lower-priority for a data schema library (they affect parsing, not schema semantics), but are noted for completeness.
