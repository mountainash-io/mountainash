# Capability Declaration Architecture — Design

**Date:** 2026-08-07
**Status:** Approved design (rev 3), pending implementation plan
**Scope:** Expression + relation capability declarations, `core/capabilities` mechanism/data split
**Review history:**
- rev 1 → codex (gpt-5.6-sol) adversarial design review: rework; 2 blockers + 5 majors adjudicated (2 findings rejected with evidence) and folded into rev 2.
- rev 2 → GLM-5.2 adversarial design review: approve-with-changes; 14 findings, all accepted and folded into rev 3.
- Adjudication notes for both rounds at end.

## Problem

Capability declarations (CapabilityFact data registered into `CapabilityRegistry`)
have accreted across three homes with four naming axes and no governing contract:

| Current file (in `expressions/backends/expression_systems/`) | Fact grain | Naming axis |
|---|---|---|
| `arithmetic_option_capabilities.py` | option-value + semantic + rounding | option domain |
| `string_option_capabilities.py` | option-value + positional + op-level wildcard | option domain |
| `datetime_option_capabilities.py` | option-value (units) | option domain |
| `datetime_value_class_capabilities_ma.py` | value-class | value-class × spec-source |
| `datetime_value_class_capabilities_substrait.py` | value-class | value-class × spec-source |
| `strptime_format_capabilities.py` | op-level wildcard | param name |
| `ibis_capabilities.py` | LITERAL_ONLY expr facts | backend |

Specific defects:

1. **Four naming axes** for one kind of artifact (domain / value-class / param / backend).
2. **Split declaration homes.** Ibis expr facts are extracted import-safe
   (`ibis_capabilities.py`), but polars and narwhals facts live inline as
   `CAPABILITIES` class attributes on `{polars,narwhals}/base.py`. The
   relations spine (`relations/backends/relation_systems/`) mirrors the same
   asymmetry (inline `CAPABILITIES` + one extracted
   `ibis_relation_capabilities.py`).
3. **Registration is an import side effect** — `CapabilityRegistry.register_backend(...)`
   at module bottom. No contract governs what a declaration module exposes.
4. **`core_facts.py` is a declaration module in disguise** with three special
   cases: a `register_core_polymorphic_facts()` function instead of data, a
   `_REGISTERED` idempotence flag, and double invocation (bootstrap calls it
   AND `expression_systems/base.py` re-imports and calls it in a bottom-of-file
   tail).
5. **Tests import private symbols** (`_BROKEN_STRING_OPS_BY_BACKEND`,
   `_OP_LEVEL_FKEYS` from the string module) — no public declaration surface.
6. Shared idioms (`_SINCE`, `_fact` builders, family-default vs
   dialect-refinement discipline, probe-matrix docstrings) are re-invented per
   file, unenforced.
7. `core/capabilities` mixes mechanism (schema, registry, identity,
   value_classes, bootstrap) with data (`core_facts.py`, `divergences.py`).
8. **Audit provenance is prose.** Probe dates, library versions, and fixture
   coverage live only in docstrings; "honored" is representable only as fact
   absence; fact retirement (upstream fixed it) is bare deletion that erases
   when, against which versions, and on what evidence support returned.
   Capabilities churn with every backend release, so this history is the
   audit trail — it must be typed data, mechanically extractable.

## Design forces

1. **Churn ergonomics.** Facts flip on every backend release. Adding,
   amending, or retiring a fact after a version bump must have exactly one
   obvious file and one obvious shape, and touch the minimum artifact set.
2. **Mechanical extractability.** Backend-issue audits must be enumerable by
   typed field — backend, dialect, domain, spec source, since-date,
   upstream_ref, probe provenance, retirement history — for reporting and
   testing. Nothing audit-relevant may live only in prose.

## Design

### 1. Governing protocol — `core/capabilities/declarations.py` (new)

The contract every declaration module satisfies. Owned by the spine because it
has two consumers (expressions, relations).

```python
class FactSource(Enum):
    SUBSTRAIT = "substrait"     # FKEY_SUBSTRAIT_* / SUBSTRAIT_* enums
    MOUNTAINASH = "mountainash" # FKEY_MOUNTAINASH_* / RKEY_MOUNTAINASH_* enums

class Domain(Enum):
    STRING = "string"
    ARITHMETIC = "arithmetic"
    DATETIME = "datetime"
    LIST = "list"
    SET = "set"
    TERNARY = "ternary"
    RELATION = "relation"
    # closed set; extended only when a new FKEY/RKEY category lands.
    # Classification is mechanical: operation_key's enum name → Domain
    # (FKEY_*_SCALAR_STRING → STRING, FKEY_*_SCALAR_DATETIME → DATETIME,
    #  RKEY_* → RELATION, ...). One classifier function, one table.

@dataclass(frozen=True)
class ProbeEvidence:
    """Structured empirical basis for ONE probe wave (defect 8)."""
    probe_date: str                       # YYYY-MM-DD, validated like `since`
    library_versions: tuple[tuple[str, str], ...]  # (("ibis", "12.0.0"), ...)
    fixtures: tuple[str, ...]             # fixture/dialect slice probed

@dataclass(frozen=True)
class CapabilityDeclaration:
    """One backend's facts, from one source, one domain, one probe wave."""
    backend: CONST_BACKEND
    domain: Domain
    source: FactSource
    facts: tuple[CapabilityFact, ...]
    evidence: ProbeEvidence | None = None # None only if every fact probe_exempt
    # __post_init__ enforces, at construction (fail-at-import discipline):
    #   - every fact.backend is declaration.backend
    #   - every fact.operation_key's enum classifies to declaration.source
    #   - every fact.operation_key's enum classifies to declaration.domain
    #     (same mechanical classifier; symmetric with source)
    #   - evidence is None only if every fact is probe_exempt

class CapabilityDeclarationModule(Protocol):
    """Shape of a declaration module (checked by an integrity guard)."""
    DECLARATIONS: tuple[CapabilityDeclaration, ...]
```

All names exported from `mountainash.core.capabilities`.

**Declaration identity is `(backend, source, domain, wave)`.** A module MAY
emit multiple declarations for the same `(backend, source, domain)` — one per
probe wave, each with its own `ProbeEvidence` (e.g. narwhals'
family-LITERAL_ONLY block and the later `_POLARS_BACKED_FIXED` refinement
block are two waves). The guard asserts evidence-distinctness within a
module for same-key declarations. A module mixing MA and Substrait facts (or
two domains) declares them in SEPARATE `CapabilityDeclaration` entries; the
classifiers reject mixed tuples. Physical file-per-source split is NOT
required for backend modules (precedent: `ibis_capabilities.py` mixes
sources today; provenance is typed on the declaration) — it IS preserved
where it already exists (`datetime/` value-class modules).

Protocol rules (machine-enforced where marked):

- **Import-safe** [enforced]. Definition (matching the codebase's actual
  invariant): a declaration module imports cleanly and yields its full
  `DECLARATIONS` when the OPTIONAL backends (`ibis`, `narwhals`) are not
  installed. `polars` is a core dependency and exempt — the parent package
  chain (`mountainash` → `expressions` → `backends`) imports it
  unconditionally and legitimately. Guard: fresh subprocess with `ibis` and
  `narwhals` blocked via an import hook, import every discovered declaration
  module, assert `DECLARATIONS` complete.
- **No side effects** [enforced]: modules expose `DECLARATIONS`; they never
  call `CapabilityRegistry.register_backend` themselves. Registration is
  bootstrap's job. Guard: import all declaration modules in a subprocess and
  assert the registry's internal maps (inspected directly, not via `facts()`,
  which would trigger autoload) are empty.
- **Backend / source / domain / evidence match** [enforced]:
  `CapabilityDeclaration.__post_init__` as above.
- **Well-formed surface** [enforced]: every discovered module exposes
  `DECLARATIONS: tuple[CapabilityDeclaration, ...]`; missing or ill-typed
  fails bootstrap and the guard.
- **Provenance idioms** [documented, package docstring]: probe-matrix
  docstring remains as human-readable narrative (the machine-readable subset
  now lives in `ProbeEvidence`); family-default vs dialect-refinement
  discipline (ibis: family-default `dialect=None` fact AND concrete-dialect
  fact, except family-supported ops with dialect-only gaps, per the strptime
  precedent; narwhals: per-dialect facts only, never a family default).

### 2. Registration flow

**Discovery, not manifest.** `bootstrap.py` drops `_DECLARATION_MODULES`.
It discovers every module under the two capability package roots
(`mountainash.expressions.backends.capabilities`,
`mountainash.relations.backends.capabilities`) via
`pkgutil.walk_packages`, in sorted order, imports each, reads
`DECLARATIONS`, and registers `register_backend(d.backend, d.facts)` for
each declaration. A new declaration file cannot be forgotten
(closed-by-default); a module missing `DECLARATIONS` raises.

Exemptions from the `DECLARATIONS` requirement, both explicit in bootstrap:
- `__init__.py` files (package docstring + public surface only);
- modules whose leaf name starts with `_` (local helpers, e.g. a
  `datetime/_builders.py` shared by the datetime declaration modules).
  `pkgutil.walk_packages` does NOT skip these by itself — bootstrap and the
  guard filter them by name. Helpers shared across BOTH roots still belong
  in `core/capabilities` (mechanism); underscore modules are for
  package-local data-building only, and the no-side-effect guard still
  imports them (they must not register anything).

**Declaration retention.** The registry retains the declarations themselves:
`_declarations: tuple[CapabilityDeclaration, ...]` accumulated at
registration, exposed via the audit accessors (§5). `snapshot()/restore()`
carry `_declarations` alongside the fact maps and load state — the audit
surface never re-imports modules to reconstruct provenance (which would
bypass ISOLATED and re-trigger FAILED imports).

**Load-state machine (replaces the rev-1 boolean).** The registry owns one
explicit state:

```
UNINITIALIZED --autoload succeeds--> LOADED
UNINITIALIZED --autoload raises----> FAILED   (exception cached)
FAILED        --any query----------> re-raise cached exception
UNINITIALIZED/LOADED/FAILED --reset()--> ISOLATED   (autoload disabled)
ISOLATED      --restore(snapshot)--> snapshot's recorded state
```

- Query surfaces (`capability_for`, `facts`, `residue_for`, `router_facts`,
  `validate_plan_capabilities`) autoload ONLY from `UNINITIALIZED`, under a
  `threading.RLock`. Cross-thread: first thread loads, others block until
  LOADED/FAILED. Same-thread re-entry during loading is unreachable in
  practice (declaration modules are side-effect-free and never query), and
  the RLock makes it a no-op rather than a deadlock if that invariant is
  ever violated.
- `load_all_capability_declarations()` (kept for enumerating consumers) is
  the same operation autoload calls: from `UNINITIALIZED` it loads →
  `LOADED`/`FAILED`; from `LOADED` it is a no-op; from `FAILED` it re-raises
  the cached exception; from `ISOLATED` it raises `RuntimeError` — a test
  must `restore()` first (loading into an isolated registry would destroy
  the isolation it asked for).
- `reset()` → `ISOLATED`: test-only operation. The documented idiom is
  snapshot → reset → … → restore; calling `reset()` with no prior snapshot
  leaves the process in ISOLATED with no way back to autoload — by design,
  and documented on `reset()` itself.
- `snapshot()` captures fact maps + `_kinds` + `_declarations` + state
  verbatim; `restore()` reinstates all of them. State is never inferred from
  map contents.

Registration remains entry-point-independent and import-order-proof.

`expression_systems/base.py` loses its bottom-of-file
`register_core_polymorphic_facts()` tail. `core_facts.py` is deleted (§6).

**Ordering determinism.** Enumeration surfaces stop depending on
registration order: `facts()` returns deterministically sorted results —
total key `(operation_key name, param, backend, dialect, option_value,
value_class name)` with `None` normalized — `router_facts()` likewise;
`residue_for()` asserts no two facts collide on (operation_key, param) at
equal dialect-specificity instead of silently last-wins. Module discovery
order is sorted and therefore stable, but no behavior may rely on it.

### 3. New homes

```
src/mountainash/expressions/backends/capabilities/
    __init__.py                      # package docstring = protocol rules; public surface
    string.py                        # ← string_option_capabilities.py
    arithmetic.py                    # ← arithmetic_option_capabilities.py
    datetime/
        __init__.py
        options.py                   # ← datetime_option_capabilities.py
        value_classes_ma.py          # ← datetime_value_class_capabilities_ma.py
        value_classes_substrait.py   # ← datetime_value_class_capabilities_substrait.py
        strptime.py                  # ← strptime_format_capabilities.py
    polymorphic.py                   # ← core/capabilities/core_facts.py (as data)
    polars.py                        # ← extracted from polars/base.py CAPABILITIES
    narwhals.py                      # ← extracted from narwhals/base.py CAPABILITIES
    ibis.py                          # ← ibis_capabilities.py

src/mountainash/relations/backends/capabilities/
    __init__.py
    polars.py                        # ← extracted from relation_systems/polars/base.py
    narwhals.py                      # ← extracted from relation_systems/narwhals/base.py
    ibis.py                          # ← ibis_relation_capabilities.py
```

**Placement decision table** — every fact grain has exactly one owner. The
table below IS the guard's configuration (single source — no separately
maintained guard map): the guard derives each fact's grain from its fields
(`option_value` set / `value_class` set / `param == WILDCARD_PARAM` /
level+annotation) and its root-class from `operation_key`'s enum membership
(FKEY → expression root, RKEY → relation root), then checks the owning
module against the table:

| Fact grain | Discriminator | Owner |
|---|---|---|
| Option-value fact (`option_value` set) | option domain of the op | domain module (`string`, `arithmetic`, `datetime/options`) |
| Value-class fact (`value_class` set) | op's spec source | `datetime/value_classes_ma.py` or `datetime/value_classes_substrait.py` |
| Op-level wildcard (`param == "*"`, GATE) | op's domain | domain module (e.g. `datetime/strptime`, `string` op-level block) |
| Positional-arg option fact | op's domain | domain module |
| LITERAL_ONLY / expr-argument fact | the restricted backend | backend module (`polars`, `narwhals`, `ibis`) |
| POLYMORPHIC marker fact | cross-family AST-shape semantics | `polymorphic.py` |
| Relation fact (any grain; RKEY) | backend | `relations/backends/capabilities/{backend}.py` |
| ROUTER_METADATA / MATERIALIZE_RESIDUE | the routed/enriched backend | backend module (root per FKEY/RKEY as above) |

Expression-system classes keep working: `{polars,narwhals,ibis}/base.py`
import their `CAPABILITIES` tuple from the new modules (as `ibis/base.py`
already does today) instead of declaring inline. Native imports stay in the
system classes. Same for the relation-system base classes.

Old files are **deleted** — clean cutover, no shims, no re-exports:
the seven `expression_systems/*_capabilities.py` root files,
`relation_systems/ibis_relation_capabilities.py`, and
`core/capabilities/core_facts.py`.

### 4. Retirement lifecycle — `core/capabilities/retired.py` (new)

Retirement becomes a first-class move, not a deletion. When a backend
release fixes a limitation:

1. The `CapabilityFact` leaves its declaration module.
2. A `RetiredFact` enters the `RETIRED_FACTS` catalog:

```python
@dataclass(frozen=True)
class RetiredFact:
    operation_key: Any
    param: str
    backend: CONST_BACKEND
    dialect: str | None
    option_value: str | None
    value_class: ValueClass | None        # mirrors CapabilityFact — value-class
                                          # retirements are NOT squeezed into
                                          # option_value (disjoint keyspaces)
    level: CapabilityLevel                # what was declared
    since: str                            # original declaration date
    retired_on: str                       # YYYY-MM-DD
    fixed_in_versions: tuple[tuple[str, str], ...]  # (("narwhals","2.19.0"),)
                                          # typed — joinable with
                                          # ProbeEvidence.library_versions
    upstream_ref: str | None              # carried over from the fact
    note: str                             # what the retirement probe observed
```

Catalog placement mirrors `divergences.py`: cross-backend audit data,
core-owned, never registered into the registry, never gates. Reports and
audits enumerate active facts (registry) + retired facts (catalog) for the
full history. The guard asserts no key is simultaneously active and retired,
checking BOTH active maps with the matching key shape:
`(op, param, backend, dialect, option_value)` against `_facts` and
`(op, param, backend, dialect, value_class)` against `_value_class_facts`.

**Two churn modes for "upstream fixed it":**
- **Retire** (fact removed): the flow above — one edit in the declaration
  module, one appended `RetiredFact`, matching test-matrix update (the
  census/integrity suites force the test-side edit).
- **Invert** (fact superseded by a dialect-scoped `EXPR_CAPABLE` refinement,
  e.g. narwhals' polars-backed `str.contains` fix): by design this is
  captured as a NEW refinement fact whose declaration carries the fix-wave
  `ProbeEvidence` (probe date + library versions) and the fact's
  `upstream_ref` — no `RetiredFact` is written because nothing left the
  registry. Prose `fixed_in` in the message is narrative only; the typed
  record is the refinement declaration's evidence.

### 5. Public surface

- `capabilities/string.py` exports `BROKEN_STRING_OPS_BY_BACKEND` and
  `OP_LEVEL_FKEYS` publicly (underscores dropped). The three importers update:
  `tests/expressions/argument_types/test_arg_types_string.py`,
  `tests/expressions/argument_types/test_op_level_gate_probes.py`,
  `tests/fixtures/capability_census.py`.
- `ibis.py` keeps `IBIS_EXPR_CAPABILITIES` (consumed by `ibis/base.py`);
  `polars.py` / `narwhals.py` export equivalently named tuples for their base
  classes.
- Each declaration module's `DECLARATIONS` is the canonical enumeration
  surface; ad-hoc private-tuple exports beyond the above are not added.
- Audit accessors on the spine, backed by the retained `_declarations` (§2):
  enumerate declarations (backend, domain, source, evidence, facts) and
  retired facts — the typed reporting surface for backend-issue audits.

### 6. `core/capabilities` — mechanism/data split

**Mechanism (stays):** `schema.py`, `registry.py`, `identity.py`,
`value_classes.py`, `bootstrap.py`, new `declarations.py`.

**Data relocations / non-relocations:**

- `core_facts.py` → `expressions/backends/capabilities/polymorphic.py` as an
  ordinary declaration module: `DECLARATIONS` with one `CapabilityDeclaration`
  per (family × domain) — SET (`IS_IN`/`IS_NOT_IN`) and TERNARY
  (`COLLECT_VALUES`) separately, for polars/ibis/narwhals (source=MOUNTAINASH,
  evidence=None — probe-exempt by design), honoring the domain-homogeneity
  invariant. Function, `_REGISTERED` flag, and the `base.py`
  tail deleted.
- `divergences.py` **stays in `core/capabilities`** — deliberately. Different
  artifact: `DivergenceFact` catalog, never registered, never gates; drives
  declaration-driven xfails and the generated catalog; 7+ consumers. It does
  NOT adopt the `DECLARATIONS` protocol.
- `retired.py` joins as the second core-owned catalog (§4), same rationale.

**Targeted mechanism improvements:**

1. **Registry load-state machine + RLock + declaration retention** (§2).
2. **Value-class lookup index**: `_value_class_fact` currently linear-scans
   every value-class fact per lookup, twice (dialect then family slice).
   Re-key `_value_class_facts` as
   `(op, param, backend, dialect) → tuple[CapabilityFact, ...]` buckets at
   registration; lookup becomes two dict hits + predicate matches over the
   bucket. The two-distinct-classes-match error is computed per bucket; the
   duplicate-registration error is preserved. `snapshot/restore/reset` and
   `facts()` iterate bucket values.
3. **Deterministic enumeration** (§2 ordering determinism).

**Reviewed, deliberately untouched:** `identity.py` (KNOWN_DIALECTS
exhaustiveness note is load-bearing), `value_classes.py` predicate registry,
`schema.py` validation rules, `_validate_fact`'s gateability/annotation
checks, SERIALIZE/EXECUTE namespace machinery.

### 7. Testing

- **Protocol guard test** (new, `tests/core/`), all closed-by-default over
  DISCOVERED modules (not a hand-maintained list):
  - every non-exempt module under the two capability roots exposes
    well-typed `DECLARATIONS`; exempt modules (`__init__`, `_`-prefixed
    helpers) register nothing;
  - backend / source / domain / evidence invariants (constructed, but
    asserted end-to-end); evidence-distinctness for same-key declarations
    within a module;
  - placement decision table (§3): grain + root-class derived from the fact
    itself; the table is the only configuration;
  - import-safety: fresh subprocess, `ibis`/`narwhals` import-blocked, all
    modules import and yield complete `DECLARATIONS`;
  - no-side-effect: subprocess imports all modules (helpers included),
    registry maps empty until bootstrap;
  - active-vs-retired disjointness over BOTH keyspaces (§4).
- **Fact-identity preservation**: existing capability census, integrity
  guards, upstream-join, and closure tests enumerate via bootstrap and must
  pass unchanged — the drift detector for the move.
- **Registry state-machine tests**: autoload-once semantics; FAILED caches
  and re-raises; ISOLATED suppresses autoload (the reset idiom) and
  `load_all` raises in it; snapshot/restore round-trips fact maps +
  declarations + state; concurrent first-query safety.
- **Smoke**: full capability-related selection plus one end-to-end expression
  compile per backend exercising a gated path (proves autoload fires on
  production paths).

## Migration map

| From | To |
|---|---|
| `expression_systems/arithmetic_option_capabilities.py` | `expressions/backends/capabilities/arithmetic.py` |
| `expression_systems/string_option_capabilities.py` | `expressions/backends/capabilities/string.py` |
| `expression_systems/datetime_option_capabilities.py` | `expressions/backends/capabilities/datetime/options.py` |
| `expression_systems/datetime_value_class_capabilities_ma.py` | `expressions/backends/capabilities/datetime/value_classes_ma.py` |
| `expression_systems/datetime_value_class_capabilities_substrait.py` | `expressions/backends/capabilities/datetime/value_classes_substrait.py` |
| `expression_systems/strptime_format_capabilities.py` | `expressions/backends/capabilities/datetime/strptime.py` |
| `expression_systems/ibis_capabilities.py` | `expressions/backends/capabilities/ibis.py` |
| `expression_systems/polars/base.py::CAPABILITIES` (inline) | `expressions/backends/capabilities/polars.py` |
| `expression_systems/narwhals/base.py::CAPABILITIES` (inline) | `expressions/backends/capabilities/narwhals.py` |
| `core/capabilities/core_facts.py` | `expressions/backends/capabilities/polymorphic.py` |
| `relation_systems/ibis_relation_capabilities.py` | `relations/backends/capabilities/ibis.py` |
| `relation_systems/polars/base.py::CAPABILITIES` (inline) | `relations/backends/capabilities/polars.py` |
| `relation_systems/narwhals/base.py::CAPABILITIES` (inline) | `relations/backends/capabilities/narwhals.py` |

Every migrated module converts to the `DECLARATIONS` contract (facts split
into per-source/per-domain/per-wave declarations where mixed); all
module-scope `register_backend` calls removed; probe-matrix docstrings move
verbatim AND their machine-readable subset (probe date, library versions,
fixture slice) is transcribed into `ProbeEvidence`. `_DECLARATION_MODULES`
is deleted in favor of discovery.

**Test-side and generated artifacts in scope:**
- Update the three private-symbol importers (§5).
- **Census `node_id` lockstep**: `capability_census.py` builds `node_id`
  strings embedding the old private symbol names (e.g.
  `_BROKEN_STRING_OPS_BY_BACKEND[...]`); the rename changes these ids, so
  every consumer matching on `node_id` (committed census report, closure
  tests) updates in the same commit — not merely a report regeneration.
- Update stale path references to old module names in comments/docstrings
  (e.g. `expsys_ib_ext_ma_scalar_datetime.py`, `expsys_ib_scalar_datetime.py`
  reference `datetime_value_class_capabilities_*.py`).
- Regenerate `tests/_spine_expectation_census.md` (source paths/line numbers
  change); census regeneration is an explicit acceptance step.
- `tests/fixtures/capability_census.py` / `capability_gating.py` keep
  working via registry enumeration — verify, don't assume.

## Risks

- **Registry state machine touches query paths.** Cost: one state check per
  query under no contention. Risk: tests that reset and expect emptiness —
  handled by ISOLATED semantics; the guard suite covers the idiom explicitly.
- **Fact-identity drift during the polars/narwhals inline extraction**
  (~250 lines of fact data leaving class bodies). Mechanical; census /
  integrity / closure suites enumerate exact facts and fail loudly on drift.
- **`_call_with_expr_support` and other runtime consumers** query the
  registry in production; the per-backend end-to-end smoke proves autoload
  fires on those paths.
- **Discovery imports everything non-exempt under the roots** — a stray
  helper must use the `_` prefix or bootstrap fails loudly (preferable to
  silent omission).

## Adjudication notes

### Round 1 (codex, gpt-5.6-sol)
- **F1 accepted, corrected**: import-safety redefined to the codebase's real
  invariant (optional backends absent; polars core-exempt); subprocess guard.
- **F2 accepted**: explicit load-state machine; state in snapshots; ISOLATED
  disables autoload. Never inferred from map contents.
- **F3 accepted as option (a)**: typed `domain`/`source`/`ProbeEvidence` on
  declarations + `RETIRED_FACTS` catalog. Full observation-record system
  (deriving test dispositions from canonical records) rejected — the
  OPTION_DISPOSITIONS ↔ facts bidirectional agreement is deliberate
  double-entry bookkeeping; collapsing it removes the independence that
  gives the check value.
- **F4 accepted**: placement decision table, guard-enforced.
- **F5 rejected as file split; accepted as logical split**: per-source
  `CapabilityDeclaration` entries + mechanical source classifier. Precedent:
  `ibis_capabilities.py` mixes sources today; the file-level rule was only
  ever asserted for value-class modules (and is preserved there).
- **F6 accepted**: discovery replaces the manifest.
- **F7 accepted, reduced**: lock + state machine + cached failure; no
  staging registry (bootstrap failure is process-fatal by design).
- **F8 rejected** (see F3), except the retirement-lifecycle gap → §4.
- **F9 accepted**: deterministic enumeration; residue collision assert.
- **F10 accepted**: test-side artifacts added to migration map.

### Round 2 (GLM-5.2) — all 14 accepted
- **G1**: `RetiredFact.value_class` field; disjointness guard checks both
  active keyspaces.
- **G2**: `FAILED` state added to the diagram; transitions specified.
- **G3**: registry retains `_declarations`; snapshot/restore carry them;
  audit accessors never re-import.
- **G4**: declaration identity `(backend, source, domain, wave)`; multiple
  declarations per key allowed, one per `ProbeEvidence` wave;
  evidence-distinctness guard.
- **G5 + G14**: `Domain` enum (closed set) + mechanical domain classifier in
  `__post_init__`, symmetric with source.
- **G6**: `_`-prefixed helper-module exemption, explicitly filtered by
  bootstrap/guard (walk_packages does not skip them itself); cross-root
  helpers stay in `core/capabilities`.
- **G7**: decision table is the guard's only configuration; grain and
  root-class derived from fact fields and enum membership.
- **G8**: `fixed_in_versions` typed, joinable with
  `ProbeEvidence.library_versions`.
- **G9**: `value_class` appended to the total sort key.
- **G10**: `load_all` transitions specified (no-op from LOADED, re-raise
  from FAILED, RuntimeError from ISOLATED); snapshot-before-reset documented
  on `reset()`.
- **G11**: RLock named; mid-load re-entry unreachability stated.
- **G12**: invert-mode churn documented — captured by the refinement
  declaration's `ProbeEvidence` + `upstream_ref` by design.
- **G13**: census `node_id` consumer-lockstep called out in migration map.
