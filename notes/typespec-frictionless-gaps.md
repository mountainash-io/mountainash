# TypeSpec ↔ Frictionless Round-trip Gap Audit

Audited against: Frictionless Data Package Standard — Table Schema spec (v2.0)
Audit date: 2026-04-07
Files audited:
- `src/mountainash/typespec/spec.py`
- `src/mountainash/typespec/frictionless.py`

---

## Summary

The converter handles the core fields well. The primary gaps are three missing
schema-level properties (`$schema`, `fieldsMatch`, `uniqueKeys`), two missing
field-level properties (`example`, `rdfType`, `categories`,
`categoriesOrdered`), a naming mismatch for `boolean` field helpers
(`true_values`/`false_values` are modelled in `FieldSpec` but serialised with
the wrong key names), and several type-specific field properties that are not
modelled at all.

---

## Schema-level properties

### Round-tripped correctly
- `fields` — exported/imported via `typespec_to_frictionless` / `typespec_from_frictionless`
- `title` — exported at `frictionless.py:96`, imported at `frictionless.py:195`
- `description` — exported at `frictionless.py:97`, imported at `frictionless.py:196`
- `primaryKey` — exported at `frictionless.py:98`, imported at `frictionless.py:197`
- `foreignKeys` — exported at `frictionless.py:100-110`, imported at `frictionless.py:205-219`
- `missingValues` (schema-level) — imported at `frictionless.py:198`; exported only via `FieldSpec.to_dict` (on `TypeSpec.to_dict`), not via `typespec_to_frictionless`

### Gap: `missingValues` serialisation asymmetry
- [ ] **`missingValues` (schema-level) — not emitted by `typespec_to_frictionless`.**
  `typespec_from_frictionless` reads `descriptor.get("missingValues")` (`frictionless.py:198`) and stores it on `TypeSpec.missing_values`, but `typespec_to_frictionless` never writes it back into the descriptor (`frictionless.py:76-156`). It is only written in `TypeSpec.to_dict` (`spec.py:207-210`), which is a different, non-Frictionless code path. Round-trip is broken: export → import will lose the schema-level `missingValues`.

### Gap: `$schema` — not modelled
- [ ] **`$schema` — missing from `TypeSpec` and both converter functions.**
  The spec allows (and recommends) a `$schema` URI property. Neither `TypeSpec` (`spec.py:127-140`) nor the converters model or pass it through. Silently dropped on import.

### Gap: `fieldsMatch` — not modelled
- [ ] **`fieldsMatch` — missing from `TypeSpec` and both converter functions.**
  The spec defines five match modes (`exact`, `equal`, `subset`, `superset`, `partial`). Not modelled in `TypeSpec` (`spec.py:127-140`); silently dropped on import (`frictionless.py:194-202`).

### Gap: `uniqueKeys` — not modelled
- [ ] **`uniqueKeys` — missing from `TypeSpec` and both converter functions.**
  The spec defines composite unique-key constraints separate from `constraints.unique`. Not modelled in `TypeSpec` (`spec.py:127-140`); silently dropped on import.

---

## Field-level properties

### Round-tripped correctly
- `name` — exported at `frictionless.py:123`, imported at `frictionless.py:224`
- `type` — exported at `frictionless.py:124`, imported at `frictionless.py:225-226`
- `format` — exported at `frictionless.py:127-128`, imported at `frictionless.py:228`
- `title` — exported at `frictionless.py:129-130`, imported at `frictionless.py:229`
- `description` — exported at `frictionless.py:131-132`, imported at `frictionless.py:230`
- `missingValues` (field-level) — exported at `frictionless.py:137-138`, imported at `frictionless.py:231`
- `constraints.required` — exported/imported via `_constraints_to_dict` / `_parse_constraints` (`frictionless.py:31-32`, `frictionless.py:60`)
- `constraints.unique` — exported/imported (`frictionless.py:33-34`, `frictionless.py:61`)
- `constraints.minimum` — exported/imported (`frictionless.py:35-36`, `frictionless.py:62`)
- `constraints.maximum` — exported/imported (`frictionless.py:37-38`, `frictionless.py:63`)
- `constraints.minLength` — exported/imported (`frictionless.py:39-40`, `frictionless.py:64`)
- `constraints.maxLength` — exported/imported (`frictionless.py:41-42`, `frictionless.py:65`)
- `constraints.pattern` — exported/imported (`frictionless.py:43-44`, `frictionless.py:66`)
- `constraints.enum` — exported/imported (`frictionless.py:45-46`, `frictionless.py:67`)

### Gap: `example` — not modelled
- [ ] **`example` (field-level) — missing from `FieldSpec` and both converter functions.**
  The spec defines a field-level `example` property. `FieldSpec` (`spec.py:68-88`) has no `example` attribute; it is silently dropped on import.

### Gap: `rdfType` — not modelled
- [ ] **`rdfType` (field-level) — missing from `FieldSpec` and both converter functions.**
  The spec defines an `rdfType` URI property for semantic annotation. `FieldSpec` (`spec.py:68-88`) has no `rdf_type` attribute; silently dropped on import.

### Gap: `categories` — not modelled
- [ ] **`categories` (field-level) — missing from `FieldSpec` and both converter functions.**
  The spec defines a `categories` property for `string`/`integer` fields (array of values or array of `{value, label}` objects). `FieldSpec` (`spec.py:68-88`) has no `categories` attribute; silently dropped on import.
  Note: `constraints.enum_weights` is a mountainash extension that partially overlaps with this concept but is semantically different; it stores weights, not labels. These are distinct.

### Gap: `categoriesOrdered` — not modelled
- [ ] **`categoriesOrdered` (field-level) — missing from `FieldSpec` and both converter functions.**
  Companion boolean to `categories`. Not modelled in `FieldSpec` (`spec.py:68-88`); silently dropped on import.

### Gap: `trueValues`/`falseValues` naming mismatch
- [ ] **`true_values`/`false_values` (field-level) — modelled in `FieldSpec` but never serialised.**
  `FieldSpec` has `true_values: Optional[List[str]]` and `false_values: Optional[List[str]]` (`spec.py:83-84`) which map to the spec's `trueValues`/`falseValues` for `boolean` fields. However:
  1. `typespec_to_frictionless` never writes these fields (`frictionless.py:120-152`).
  2. `typespec_from_frictionless` never reads them (`frictionless.py:222-254`).
  3. `FieldSpec.to_dict` (`spec.py:99-123`) also does not emit them.
  The fields are entirely dead: populated on `FieldSpec` construction only, never round-tripped.

### Gap: `backend_type` — mountainash-internal field emitted as top-level
- [ ] **`backend_type` — emitted as a top-level field key (not under `x-mountainash`).**
  `FieldSpec.to_dict` (`spec.py:118-119`) emits `backend_type` directly into the field dict alongside standard Frictionless properties. This violates the extension convention: mountainash-internal fields should be placed under `x-mountainash`. Additionally, `typespec_to_frictionless` (`frictionless.py:120-152`) does NOT emit `backend_type` at all, so the two serialisation paths disagree. `typespec_from_frictionless` also does not read it back.

---

## Type-specific field properties (not modelled)

These are properties that apply only to certain field types in the spec. None are modelled in `FieldSpec` and none are round-tripped.

- [ ] **`number.decimalChar` / `number.groupChar` / `number.bareNumber`** — number field formatting properties; not modelled.
- [ ] **`integer.groupChar` / `integer.bareNumber`** — integer field formatting properties; not modelled.
- [ ] **`list.delimiter` / `list.itemType`** — list field properties; not modelled.

These are lower-priority for a data schema library (they affect parsing, not schema semantics), but are noted for completeness.

---

## Mountainash extensions round-trip status

These are not Frictionless spec fields but are correctly placed under `x-mountainash`.

- `rename_from` — round-tripped correctly via `x-mountainash` (`frictionless.py:142-143`, `frictionless.py:235`)
- `null_fill` — round-tripped correctly via `x-mountainash` (`frictionless.py:144-145`, `frictionless.py:236`)
- `custom_cast` — round-tripped correctly via `x-mountainash` (`frictionless.py:146-147`, `frictionless.py:237`)
- `constraints.enum_weights` — round-tripped correctly via `x-mountainash` (`frictionless.py:148-149`, `frictionless.py:238`)
- `keep_only_mapped` (spec-level) — round-tripped correctly via `x-mountainash` (`frictionless.py:114-116`, `frictionless.py:202`)

---

## Gap checklist (consolidated)

| # | Field | Location | Severity | Notes |
|---|-------|----------|----------|-------|
| 1 | `missingValues` (schema-level) not emitted by `typespec_to_frictionless` | `frictionless.py:76-156` (absent) | High | Breaks round-trip for schema-level missing values |
| 2 | `$schema` not modelled | `spec.py:127-140` (absent) | Low | Interoperability; no data loss |
| 3 | `fieldsMatch` not modelled | `spec.py:127-140` (absent) | Medium | Silently lost; affects consumers that enforce field matching |
| 4 | `uniqueKeys` not modelled | `spec.py:127-140` (absent) | Medium | Distinct from `constraints.unique`; multi-field uniqueness lost |
| 5 | `example` not modelled | `spec.py:68-88` (absent) | Low | Documentation field; no semantic impact |
| 6 | `rdfType` not modelled | `spec.py:68-88` (absent) | Low | Semantic annotation; no data loss |
| 7 | `categories` not modelled | `spec.py:68-88` (absent) | Medium | Overlaps with `constraints.enum` but richer (labels, categorical loading hint) |
| 8 | `categoriesOrdered` not modelled | `spec.py:68-88` (absent) | Low | Only meaningful alongside `categories` |
| 9 | `true_values`/`false_values` modelled but never serialised | `frictionless.py:120-152` (absent), `frictionless.py:222-254` (absent) | High | Fields exist on `FieldSpec` but are dead — never exported or imported |
| 10 | `backend_type` emitted at top-level in `FieldSpec.to_dict`, not in `typespec_to_frictionless`, and never imported | `spec.py:118-119`, `frictionless.py:120-152` (absent) | Medium | Two serialisation paths disagree; should move under `x-mountainash` |
| 11 | `number.*` / `integer.*` / `list.*` type-specific properties not modelled | `spec.py:68-88` (absent) | Low | Parsing properties; deferred scope |
