# Capability Declaration Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure all capability declarations into two protocol-governed packages (`expressions/backends/capabilities/`, `relations/backends/capabilities/`) with typed provenance, discovery-based registration, a registry load-state machine, and a retirement catalog — per the approved spec `docs/superpowers/specs/2026-08-07-capability-declaration-architecture-design.md` (rev 3).

**Architecture:** Declaration modules become side-effect-free data exposing `DECLARATIONS: tuple[CapabilityDeclaration, ...]`; `bootstrap.py` discovers and registers them; `CapabilityRegistry` gains an explicit UNINITIALIZED/LOADED/FAILED/ISOLATED state machine with query-time autoload, retained declarations for audit, and a bucketed value-class index. Old declaration files are deleted in one cutover task after all new modules exist.

**Tech Stack:** Python 3.12, dataclasses, `pkgutil.walk_packages`, `threading.RLock`, pytest, `uv run pytest`.

## Global Constraints

- **Branch/worktree:** all work on `feature/capability-declaration-architecture`, seeded from `origin/develop`, in a fresh worktree (Task 0). PR targets `develop`. Never commit to this repo's `develop`/`main` directly.
- **Test runner:** `uv run pytest <path> -x -q` for every test step. Do NOT run the project-wide suite in Tasks 1–11; the full capability selection runs once in Task 12.
- **Spec is authoritative:** `docs/superpowers/specs/2026-08-07-capability-declaration-architecture-design.md`. On any conflict between this plan and the spec, the spec wins; flag the conflict in the task report.
- **Conversion contract for every migrated declaration module (Tasks 5–10):**
  1. New module starts with `from __future__ import annotations`.
  2. Module docstring (probe matrices, family/dialect discipline, boundary rationale) moves VERBATIM from the old file, with one appended line: `Migrated from <old dotted path> (2026-08 capability-architecture PR).`
  3. All existing fact-building code (constants, `_fact` builders, dict tables, comprehensions) moves verbatim. Do not reformat, rename, or "improve" fact data — fact identity must be byte-equal.
  4. Every module-scope `CapabilityRegistry.register_backend(...)` call is REMOVED and replaced by `DECLARATIONS = (...)` entries per the task's table.
  5. Old files are NOT deleted in Tasks 5–10 (the equivalence tests compare against them); deletion happens in Task 11 only.
  6. No new module imports `polars`, `narwhals`, `ibis`, `pandas`, or `pyarrow`.
- **Fact grouping rule:** one `CapabilityDeclaration` per (backend × domain × source × probe wave) present in the module. `evidence=None` only when every fact in the declaration has `probe_exempt` set.
- **Evidence transcription:** `ProbeEvidence.probe_date` = the module's `_SINCE` (or the docstring's probe date where it differs, e.g. strptime's `2026-07-30`); `library_versions` = exactly what the docstring records (empty tuple when unrecorded — never fabricate); `fixtures` = the fixture column set of the docstring's probe matrix (empty tuple when there is no matrix).
- **Commit style:** `refactor(capabilities): <task summary>` one commit per task, from the worktree root.

---

### Task 0: Worktree, branch, spec commit, baseline

**Files:**
- Create: worktree at `../capability-arch` on branch `feature/capability-declaration-architecture`
- Commit: `docs/superpowers/specs/2026-08-07-capability-declaration-architecture-design.md`, `docs/superpowers/plans/2026-08-07-capability-declaration-architecture.md`

**Interfaces:**
- Produces: the working directory for all subsequent tasks; a recorded baseline of which capability test files exist on `develop`.

- [ ] **Step 1: Create the worktree off develop**

```bash
cd /Users/nathanielramm/orca/workspaces/mountainash/SP2-B
git fetch origin develop
git worktree add ../capability-arch -b feature/capability-declaration-architecture origin/develop
```

- [ ] **Step 2: Copy the spec and this plan into the new worktree and commit**

```bash
mkdir -p ../capability-arch/docs/superpowers/specs ../capability-arch/docs/superpowers/plans
cp docs/superpowers/specs/2026-08-07-capability-declaration-architecture-design.md ../capability-arch/docs/superpowers/specs/
cp docs/superpowers/plans/2026-08-07-capability-declaration-architecture.md ../capability-arch/docs/superpowers/plans/
cd ../capability-arch
git add docs/superpowers
git commit -m "docs(capabilities): declaration-architecture spec (rev 3) + implementation plan"
```

- [ ] **Step 3: Record the baseline test inventory**

The spec was designed against the SP2-B branch; `develop` may lack some closure/census tests. Record what exists:

```bash
ls tests/core/ tests/fixtures/ tests/expressions/argument_types/ | tee /tmp/capability-arch-baseline.txt
uv run pytest tests/core -k "capabilit" -q --collect-only | tail -5
```

Expected: a list of collected tests. If `tests/fixtures/capability_census.py` or `tests/core/test_capability_enforcement.py` is MISSING on develop, note it in the task report — later tasks that modify those files then skip the missing ones (and only those), reporting each skip.

- [ ] **Step 4: Verify the capability suite is green at baseline**

```bash
uv run pytest tests/core -k "capabilit or divergence" -q
```

Expected: PASS (record the count). This is the reference point for Task 12.

---

### Task 1: `declarations.py` — the governing protocol

**Files:**
- Create: `src/mountainash/core/capabilities/declarations.py`
- Modify: `src/mountainash/core/capabilities/__init__.py` (add exports)
- Test: `tests/core/test_capability_declarations.py`

**Interfaces:**
- Consumes: `CapabilityFact`, `WILDCARD_PARAM` from `mountainash.core.capabilities.schema`; `CONST_BACKEND` from `mountainash.core.constants`.
- Produces (later tasks rely on these EXACT names):
  - `FactSource(Enum)`: `SUBSTRAIT`, `MOUNTAINASH`
  - `Domain(Enum)`: `STRING`, `ARITHMETIC`, `DATETIME`, `LIST`, `SET`, `TERNARY`, `RELATION`
  - `classify_source(operation_key) -> FactSource`
  - `classify_domain(operation_key) -> Domain`
  - `ProbeEvidence(probe_date: str, library_versions: tuple[tuple[str, str], ...], fixtures: tuple[str, ...])`
  - `CapabilityDeclaration(backend, domain, source, facts, evidence=None)`
  - `CapabilityDeclarationModule(Protocol)` with `DECLARATIONS: tuple[CapabilityDeclaration, ...]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/core/test_capability_declarations.py
"""Protocol contract for capability declaration modules (spec rev 3, §1)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
    classify_domain,
    classify_source,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from mountainash.relations.core.relation_system.relation_mapping.enums import (
    RKEY_MOUNTAINASH_REL,
)


def _fact(op, backend, **kw):
    return CapabilityFact(
        operation_key=op, param="*", level=CapabilityLevel.UNSUPPORTED,
        backend=backend, message="t", since="2026-08-07",
        probe_exempt="test fact", **kw,
    )


def test_classify_source():
    assert classify_source(FK_STR.CENTER) is FactSource.SUBSTRAIT
    assert classify_source(FK_DT.ADD_DAYS) is FactSource.MOUNTAINASH
    assert classify_source(RKEY_MOUNTAINASH_REL.UNNEST) is FactSource.MOUNTAINASH


def test_classify_domain():
    assert classify_domain(FK_STR.CENTER) is Domain.STRING
    assert classify_domain(FK_DT.ADD_DAYS) is Domain.DATETIME
    assert classify_domain(RKEY_MOUNTAINASH_REL.UNNEST) is Domain.RELATION


def test_declaration_accepts_homogeneous_facts():
    d = CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=(_fact(FK_STR.CENTER, CONST_BACKEND.IBIS),),
    )
    assert d.evidence is None  # legal: the fact is probe_exempt


def test_declaration_rejects_backend_mismatch():
    with pytest.raises(ValueError, match="backend"):
        CapabilityDeclaration(
            backend=CONST_BACKEND.POLARS, domain=Domain.STRING,
            source=FactSource.SUBSTRAIT,
            facts=(_fact(FK_STR.CENTER, CONST_BACKEND.IBIS),),
        )


def test_declaration_rejects_source_mismatch():
    with pytest.raises(ValueError, match="source"):
        CapabilityDeclaration(
            backend=CONST_BACKEND.IBIS, domain=Domain.DATETIME,
            source=FactSource.SUBSTRAIT,  # FK_DT is MOUNTAINASH
            facts=(_fact(FK_DT.ADD_DAYS, CONST_BACKEND.IBIS),),
        )


def test_declaration_rejects_domain_mismatch():
    with pytest.raises(ValueError, match="domain"):
        CapabilityDeclaration(
            backend=CONST_BACKEND.IBIS, domain=Domain.STRING,  # FK_DT is DATETIME
            source=FactSource.MOUNTAINASH,
            facts=(_fact(FK_DT.ADD_DAYS, CONST_BACKEND.IBIS),),
        )


def test_declaration_requires_evidence_for_probed_facts():
    probed = CapabilityFact(
        operation_key=FK_STR.CENTER, param="*",
        level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.IBIS,
        message="t", since="2026-08-07",  # no probe_exempt
    )
    with pytest.raises(ValueError, match="evidence"):
        CapabilityDeclaration(
            backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
            source=FactSource.SUBSTRAIT, facts=(probed,),
        )
    # and with evidence it is accepted
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT, facts=(probed,),
        evidence=ProbeEvidence(
            probe_date="2026-08-07",
            library_versions=(("ibis", "12.0.0"),),
            fixtures=("ibis-duckdb",),
        ),
    )


def test_probe_evidence_validates_date():
    with pytest.raises(ValueError, match="probe_date"):
        ProbeEvidence(probe_date="not-a-date", library_versions=(), fixtures=())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/core/test_capability_declarations.py -x -q`
Expected: FAIL — `ModuleNotFoundError: mountainash.core.capabilities.declarations`

(If the RKEY enum import path differs on develop, find it with `grep -rn "class RKEY_MOUNTAINASH_REL" src/` and correct the test import — the class name is the contract, not the module path.)

- [ ] **Step 3: Implement `declarations.py`**

```python
# src/mountainash/core/capabilities/declarations.py
"""Governing protocol for capability declaration modules (spec rev 3, §1).

A declaration module is import-safe pure data: it exposes
``DECLARATIONS: tuple[CapabilityDeclaration, ...]`` and NEVER registers
anything itself — bootstrap discovers modules under the two capability
package roots and performs registration.

Declaration identity is (backend, source, domain, probe wave). A module may
emit several declarations for the same (backend, source, domain), one per
``ProbeEvidence`` wave.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from mountainash.core.capabilities.schema import CapabilityFact, _validate_since

if TYPE_CHECKING:
    from mountainash.core.constants import CONST_BACKEND


class FactSource(Enum):
    SUBSTRAIT = "substrait"
    MOUNTAINASH = "mountainash"


class Domain(Enum):
    STRING = "string"
    ARITHMETIC = "arithmetic"
    DATETIME = "datetime"
    LIST = "list"
    SET = "set"
    TERNARY = "ternary"
    RELATION = "relation"


# Enum-class-name suffix -> Domain. Extended only when a new FKEY/RKEY
# category gains declaration facts; classify_domain raises on unknowns so
# the extension is forced, not forgotten.
_DOMAIN_SUFFIXES: dict[str, Domain] = {
    "STRING": Domain.STRING,
    "ARITHMETIC": Domain.ARITHMETIC,
    "DATETIME": Domain.DATETIME,
    "LIST": Domain.LIST,
    "SET": Domain.SET,
    "TERNARY": Domain.TERNARY,
}


def classify_source(operation_key: Any) -> FactSource:
    name = type(operation_key).__name__
    if name.startswith("RKEY_"):
        return FactSource.MOUNTAINASH
    if name.startswith(("FKEY_SUBSTRAIT", "SUBSTRAIT")):
        return FactSource.SUBSTRAIT
    if name.startswith("FKEY_MOUNTAINASH"):
        return FactSource.MOUNTAINASH
    raise ValueError(f"cannot classify source of operation-key enum {name!r}")


def classify_domain(operation_key: Any) -> Domain:
    name = type(operation_key).__name__
    if name.startswith("RKEY_"):
        return Domain.RELATION
    for suffix, domain in _DOMAIN_SUFFIXES.items():
        if name.endswith(f"_{suffix}") or name.endswith(f"SCALAR_{suffix}"):
            return domain
    raise ValueError(
        f"cannot classify domain of operation-key enum {name!r}; extend "
        "Domain/_DOMAIN_SUFFIXES in core/capabilities/declarations.py"
    )


@dataclass(frozen=True)
class ProbeEvidence:
    """Structured empirical basis for ONE probe wave."""

    probe_date: str
    library_versions: tuple[tuple[str, str], ...]
    fixtures: tuple[str, ...]

    def __post_init__(self) -> None:
        try:
            _validate_since(self.probe_date, "ProbeEvidence")
        except ValueError:
            raise ValueError(
                f"ProbeEvidence: probe_date must be YYYY-MM-DD, got "
                f"{self.probe_date!r}"
            ) from None


@dataclass(frozen=True)
class CapabilityDeclaration:
    """One backend's facts, from one source, one domain, one probe wave."""

    backend: "CONST_BACKEND"
    domain: Domain
    source: FactSource
    facts: tuple[CapabilityFact, ...]
    evidence: ProbeEvidence | None = None

    def __post_init__(self) -> None:
        for fact in self.facts:
            if fact.backend is not self.backend:
                raise ValueError(
                    f"CapabilityDeclaration({self.backend}, {self.domain}): "
                    f"fact ({fact.operation_key}, {fact.param}) has backend "
                    f"{fact.backend}"
                )
            actual_source = classify_source(fact.operation_key)
            if actual_source is not self.source:
                raise ValueError(
                    f"CapabilityDeclaration({self.backend}, {self.domain}): "
                    f"fact ({fact.operation_key}, {fact.param}) classifies to "
                    f"source {actual_source}, declaration says {self.source}"
                )
            actual_domain = classify_domain(fact.operation_key)
            if actual_domain is not self.domain:
                raise ValueError(
                    f"CapabilityDeclaration({self.backend}, {self.domain}): "
                    f"fact ({fact.operation_key}, {fact.param}) classifies to "
                    f"domain {actual_domain}, declaration says {self.domain}"
                )
        if self.evidence is None and any(
            f.probe_exempt is None for f in self.facts
        ):
            raise ValueError(
                f"CapabilityDeclaration({self.backend}, {self.domain}): "
                "evidence may be None only when every fact is probe_exempt"
            )


@runtime_checkable
class CapabilityDeclarationModule(Protocol):
    """Shape of a declaration module (checked by the protocol guard)."""

    DECLARATIONS: tuple[CapabilityDeclaration, ...]
```

Check `schema.py` first: `_validate_since(since, owner)` exists at module level (line ~102). `CapabilityFact.probe_exempt` — verify the field name with `grep -n "probe_exempt" src/mountainash/core/capabilities/schema.py`; if the default is not `None` (e.g. empty string), adapt the evidence check to the actual falsy default.

- [ ] **Step 4: Export from the package `__init__`**

In `src/mountainash/core/capabilities/__init__.py` add to the imports and `__all__`:

```python
from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration,
    CapabilityDeclarationModule,
    Domain,
    FactSource,
    ProbeEvidence,
    classify_domain,
    classify_source,
)
```

and extend `__all__` with those seven names (keep it sorted).

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/core/test_capability_declarations.py -x -q`
Expected: PASS (8 tests)

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/core/capabilities/declarations.py src/mountainash/core/capabilities/__init__.py tests/core/test_capability_declarations.py
git commit -m "refactor(capabilities): CapabilityDeclaration protocol + source/domain classifiers"
```

---

### Task 2: `retired.py` — retirement catalog

**Files:**
- Create: `src/mountainash/core/capabilities/retired.py`
- Modify: `src/mountainash/core/capabilities/__init__.py` (export `RetiredFact`, `RETIRED_FACTS`)
- Test: `tests/core/test_capability_retired.py`

**Interfaces:**
- Consumes: `CapabilityLevel`, `ValueClass` from `schema`; `CONST_BACKEND`.
- Produces: `RetiredFact` dataclass (fields exactly as below); `RETIRED_FACTS: tuple[RetiredFact, ...]` (empty at introduction); `assert_no_active_retired_overlap(registry) -> None` used by the Task 11 guard.

- [ ] **Step 1: Write the failing tests**

```python
# tests/core/test_capability_retired.py
"""Retirement catalog (spec rev 3, §4)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.capabilities.retired import (
    RETIRED_FACTS,
    RetiredFact,
    assert_no_active_retired_overlap,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _retired(**kw):
    base = dict(
        operation_key=FK_STR.CENTER, param="length",
        backend=CONST_BACKEND.IBIS, dialect=None,
        option_value=None, value_class=None,
        level=CapabilityLevel.LITERAL_ONLY,
        since="2026-07-05", retired_on="2026-08-07",
        fixed_in_versions=(("ibis", "13.0.0"),),
        upstream_ref=None, note="probe honored dynamic length",
    )
    base.update(kw)
    return RetiredFact(**base)


def test_catalog_starts_empty():
    assert RETIRED_FACTS == ()


def test_retired_fact_validates_dates():
    with pytest.raises(ValueError):
        _retired(retired_on="08-07-2026")
    with pytest.raises(ValueError):
        _retired(since="bad")


def test_overlap_guard_detects_active_option_fact(monkeypatch):
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [
            CapabilityFact(
                operation_key=FK_STR.CENTER, param="length",
                level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.IBIS,
                message="t", since="2026-07-05", probe_exempt="test",
            )
        ])
        monkeypatch.setattr(
            "mountainash.core.capabilities.retired.RETIRED_FACTS", (_retired(),)
        )
        with pytest.raises(AssertionError, match="simultaneously active and retired"):
            assert_no_active_retired_overlap(CapabilityRegistry)
    finally:
        CapabilityRegistry.restore(snap)


def test_overlap_guard_passes_when_disjoint(monkeypatch):
    monkeypatch.setattr(
        "mountainash.core.capabilities.retired.RETIRED_FACTS", (_retired(),)
    )
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        assert_no_active_retired_overlap(CapabilityRegistry)
    finally:
        CapabilityRegistry.restore(snap)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/core/test_capability_retired.py -x -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `retired.py`**

```python
# src/mountainash/core/capabilities/retired.py
"""Retired-fact catalog (spec rev 3, §4).

Retirement is a MOVE, not a deletion: when a backend release fixes a
declared limitation, the CapabilityFact leaves its declaration module and a
RetiredFact is appended here. Like ``divergences.py``, this catalog is
core-owned audit data — never registered into the registry, never gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mountainash.core.capabilities.schema import (
    CapabilityLevel,
    ValueClass,
    _validate_since,
)

if TYPE_CHECKING:
    from mountainash.core.constants import CONST_BACKEND


@dataclass(frozen=True)
class RetiredFact:
    operation_key: Any
    param: str
    backend: "CONST_BACKEND"
    dialect: str | None
    option_value: str | None
    value_class: ValueClass | None   # mirrors CapabilityFact; value-class
                                     # retirements are NOT squeezed into
                                     # option_value (disjoint keyspaces)
    level: CapabilityLevel
    since: str                       # original declaration date
    retired_on: str
    fixed_in_versions: tuple[tuple[str, str], ...]  # (("narwhals","2.19.0"),)
    upstream_ref: str | None
    note: str

    def __post_init__(self) -> None:
        owner = f"RetiredFact({self.operation_key}, {self.param})"
        _validate_since(self.since, owner)
        _validate_since(self.retired_on, f"{owner}.retired_on")
        if self.option_value is not None and self.value_class is not None:
            raise ValueError(f"{owner}: option_value and value_class are exclusive")


RETIRED_FACTS: tuple[RetiredFact, ...] = ()


def assert_no_active_retired_overlap(registry: Any) -> None:
    """Guard: no fact key is simultaneously active and retired.

    Checks BOTH active keyspaces (spec §4): option-value facts against
    ``_facts`` and value-class facts against ``_value_class_facts``.
    """
    active_option = set(registry._facts)
    active_vclass = {
        (f.operation_key, f.param, f.backend, f.dialect, f.value_class)
        for bucket in registry._value_class_facts.values()
        for f in (bucket if isinstance(bucket, tuple) else (bucket,))
    }
    for r in RETIRED_FACTS:
        if r.value_class is not None:
            key = (r.operation_key, r.param, r.backend, r.dialect, r.value_class)
            assert key not in active_vclass, (
                f"{key} is simultaneously active and retired"
            )
        else:
            key = (r.operation_key, r.param, r.backend, r.dialect, r.option_value)
            assert key not in active_option, (
                f"{key} is simultaneously active and retired"
            )
```

(The `isinstance(bucket, tuple)` branch keeps the guard correct both before and after Task 3's bucket re-key.)

- [ ] **Step 4: Export `RetiredFact` and `RETIRED_FACTS` from `core/capabilities/__init__.py`** (same pattern as Task 1 Step 4).

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/core/test_capability_retired.py tests/core/test_capability_declarations.py -x -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/core/capabilities/retired.py src/mountainash/core/capabilities/__init__.py tests/core/test_capability_retired.py
git commit -m "refactor(capabilities): RetiredFact catalog + active/retired disjointness guard"
```

---

### Task 3: Registry — value-class bucket index + deterministic enumeration

**Files:**
- Modify: `src/mountainash/core/capabilities/registry.py`
- Test: `tests/core/test_capability_registry_enumeration.py` (new); existing `tests/core/test_capability_*` must stay green.

**Interfaces:**
- Consumes: current `CapabilityRegistry` internals (`_facts`, `_value_class_facts`, `_kinds`).
- Produces: `_value_class_facts: Dict[tuple[op, param, backend, dialect], tuple[CapabilityFact, ...]]` (bucketed); `facts()` sorted by the total key `(op-name, param, backend-value, dialect-or-"", option_value-or-"", value_class-name-or-"")`; `router_facts()` same ordering; `residue_for()` raising `ValueError` on an equal-specificity collision.

- [ ] **Step 1: Write the failing tests**

```python
# tests/core/test_capability_registry_enumeration.py
"""Deterministic enumeration + bucketed value-class index (spec rev 3, §2/§6)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)


@pytest.fixture
def isolated():
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        yield
    finally:
        CapabilityRegistry.restore(snap)


def _vc_fact(op, dialect=None, vc=ValueClass.DURATION_MULTIPLIER):
    return CapabilityFact(
        operation_key=op, param="every", level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS, dialect=dialect, value_class=vc,
        message="t", since="2026-08-07", probe_exempt="test",
    )


def test_value_class_lookup_still_resolves(isolated):
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_vc_fact(FK_DT.TRUNCATE)])
    fact = CapabilityRegistry.capability_for(
        FK_DT.TRUNCATE, "every", CONST_BACKEND.IBIS,
        dialect="ibis-duckdb", option_value="2d",
    )
    assert fact is not None and fact.value_class is ValueClass.DURATION_MULTIPLIER


def test_duplicate_value_class_key_rejected(isolated):
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_vc_fact(FK_DT.TRUNCATE)])
    with pytest.raises(ValueError, match="duplicate"):
        CapabilityRegistry.register_backend(
            CONST_BACKEND.IBIS, [_vc_fact(FK_DT.TRUNCATE)]
        )


def test_facts_enumeration_is_sorted_and_total(isolated):
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [
        _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.DURATION_MULTIPLIER),
        _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.POLARS_OFFSET),
    ])
    out = CapabilityRegistry.facts()
    assert [f.value_class for f in out] == sorted(
        [f.value_class for f in out], key=lambda v: v.value
    )
    # registration order reversed must give the same enumeration
    CapabilityRegistry.reset()
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [
        _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.POLARS_OFFSET),
        _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.DURATION_MULTIPLIER),
    ])
    assert CapabilityRegistry.facts() == out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/core/test_capability_registry_enumeration.py -x -q`
Expected: the sorted-enumeration test FAILS (current `facts()` is registration-ordered); the lookup/duplicate tests may already pass — that's fine, they pin behavior through the re-key.

- [ ] **Step 3: Re-key `_value_class_facts` into buckets**

In `registry.py`:

1. Change the type alias: `_ValueClassBucketKey = Tuple[Any, str, "CONST_BACKEND | str", Optional[str]]` and `_value_class_facts: Dict[_ValueClassBucketKey, Tuple[CapabilityFact, ...]] = {}`.
2. In `register_backend`, replace the value-class branch:

```python
if fact.value_class is not None:
    bkey = (fact.operation_key, fact.param, fact.backend, fact.dialect)
    bucket = cls._value_class_facts.get(bkey, ())
    if any(f.value_class is fact.value_class for f in bucket):
        raise ValueError(
            f"duplicate value-class CapabilityFact key: {bkey + (fact.value_class,)}"
        )
    cls._value_class_facts[bkey] = bucket + (fact,)
    continue
```

3. Rewrite `_value_class_fact` as two dict hits:

```python
@classmethod
def _value_class_fact(cls, operation_key, param, backend, dialect, value):
    from mountainash.core.capabilities.value_classes import matches

    for scope in (dialect, None):  # dialect slice before family slice
        bucket = cls._value_class_facts.get(
            (operation_key, param, backend, scope), ()
        )
        hits = [f for f in bucket if matches(f.value_class, value)]
        if len(hits) > 1:
            classes = sorted(f.value_class.value for f in hits)
            raise ValueError(
                f"two distinct value classes match {value!r} at "
                f"({operation_key}, {param}, {backend}, {scope}): {classes}"
            )
        if hits:
            return hits[0]
    return None
```

4. In `facts()`, iterate `*cls._facts.values()` plus every bucket member, then return sorted:

```python
def _enum_key(fact: CapabilityFact):
    return (
        str(getattr(fact.operation_key, "name", fact.operation_key)),
        fact.param,
        str(fact.backend.value if hasattr(fact.backend, "value") else fact.backend),
        fact.dialect or "",
        fact.option_value or "",
        fact.value_class.value if fact.value_class is not None else "",
    )
```

`return sorted(out, key=_enum_key)`. Apply the same `sorted(..., key=_enum_key)` to `router_facts()`'s tuple.

5. In `residue_for()`, replace silent overwrite with a collision check: before `out[(fact.operation_key, fact.param)] = fact`, if the key exists and the existing fact's dialect-specificity equals the new one (`(existing.dialect is None) == (fact.dialect is None)`), raise `ValueError(f"ambiguous MATERIALIZE_RESIDUE facts for {key}")`; if specificities differ, keep the dialect-scoped one.
6. `snapshot()/restore()/reset()` need no structural change (they already `dict(...)` the map — buckets are immutable tuples).

- [ ] **Step 4: Run the new and existing registry tests**

Run: `uv run pytest tests/core/test_capability_registry_enumeration.py tests/core -k "capabilit" -x -q`
Expected: PASS. If an existing test asserted registration-order enumeration, fix the TEST only if the order was incidental to its purpose; if the order was the contract under test, STOP and flag it in the task report (test-integrity rule).

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/core/capabilities/registry.py tests/core/test_capability_registry_enumeration.py
git commit -m "refactor(capabilities): bucketed value-class index + deterministic enumeration"
```

---

### Task 4: Registry — load-state machine, declaration retention, `register_declaration`

**Files:**
- Modify: `src/mountainash/core/capabilities/registry.py`, `src/mountainash/core/capabilities/bootstrap.py`
- Test: `tests/core/test_capability_load_state.py`

**Interfaces:**
- Consumes: Task 1's `CapabilityDeclaration`.
- Produces (Tasks 5–12 rely on these):
  - `CapabilityRegistry.register_declaration(decl: CapabilityDeclaration) -> None` — retains `decl` in `_declarations` and registers its facts.
  - `CapabilityRegistry.declarations() -> tuple[CapabilityDeclaration, ...]` — audit accessor.
  - `CapabilityRegistry._load_state` ∈ `_LoadState.{UNINITIALIZED, LOADED, FAILED, ISOLATED}`; autoload on query from UNINITIALIZED only, under `threading.RLock`.
  - `load_all_capability_declarations()` (bootstrap): UNINITIALIZED→load; LOADED→no-op; FAILED→re-raise cached; ISOLATED→`RuntimeError`.
  - `snapshot()/restore()` round-trip `_declarations` + state; `reset()` → ISOLATED.

- [ ] **Step 1: Write the failing tests**

```python
# tests/core/test_capability_load_state.py
"""Registry load-state machine (spec rev 3, §2)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Domain,
    FactSource,
)
from mountainash.core.capabilities.registry import _LoadState
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _decl():
    return CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=(CapabilityFact(
            operation_key=FK_STR.CENTER, param="length",
            level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.IBIS,
            message="t", since="2026-08-07", probe_exempt="test",
        ),),
    )


@pytest.fixture
def isolated():
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        yield
    finally:
        CapabilityRegistry.restore(snap)


def test_reset_enters_isolated_and_disables_autoload(isolated):
    assert CapabilityRegistry._load_state is _LoadState.ISOLATED
    # a query in ISOLATED must NOT repopulate production facts
    assert CapabilityRegistry.facts() == []


def test_register_declaration_retains_declaration(isolated):
    d = _decl()
    CapabilityRegistry.register_declaration(d)
    assert d in CapabilityRegistry.declarations()
    assert len(CapabilityRegistry.facts()) == 1


def test_snapshot_restore_round_trips_state_and_declarations(isolated):
    CapabilityRegistry.register_declaration(_decl())
    snap = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    assert CapabilityRegistry.declarations() == ()
    CapabilityRegistry.restore(snap)
    assert len(CapabilityRegistry.declarations()) == 1
    assert CapabilityRegistry._load_state is _LoadState.ISOLATED


def test_load_all_raises_in_isolated(isolated):
    from mountainash.core.capabilities import load_all_capability_declarations
    with pytest.raises(RuntimeError, match="ISOLATED"):
        load_all_capability_declarations()


def test_autoload_fires_from_uninitialized():
    # Fresh-process semantics can't be simulated after conftest imports, so
    # drive the transition directly: restore a pristine UNINITIALIZED state.
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry._facts = {}
        CapabilityRegistry._kinds = {}
        CapabilityRegistry._value_class_facts = {}
        CapabilityRegistry._declarations = ()
        CapabilityRegistry._load_state = _LoadState.UNINITIALIZED
        CapabilityRegistry._load_error = None
        facts = CapabilityRegistry.facts()
        assert CapabilityRegistry._load_state is _LoadState.LOADED
        assert len(facts) > 0  # production declarations landed
    finally:
        CapabilityRegistry.restore(snap)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/core/test_capability_load_state.py -x -q`
Expected: FAIL — `_LoadState` / `register_declaration` don't exist.

- [ ] **Step 3: Implement the state machine in `registry.py`**

Add near the top:

```python
import threading
from enum import Enum as _Enum


class _LoadState(_Enum):
    UNINITIALIZED = "uninitialized"
    LOADED = "loaded"
    FAILED = "failed"
    ISOLATED = "isolated"
```

Class attributes on `CapabilityRegistry`:

```python
_declarations: Tuple["CapabilityDeclaration", ...] = ()
_load_state: _LoadState = _LoadState.UNINITIALIZED
_load_error: BaseException | None = None
_load_lock = threading.RLock()
```

(`CapabilityDeclaration` imported under `TYPE_CHECKING` to avoid a cycle; at runtime `register_declaration` takes it duck-typed.)

New methods:

```python
@classmethod
def _ensure_loaded(cls) -> None:
    if cls._load_state is _LoadState.LOADED or cls._load_state is _LoadState.ISOLATED:
        return
    with cls._load_lock:
        if cls._load_state is _LoadState.FAILED:
            raise cls._load_error
        if cls._load_state is not _LoadState.UNINITIALIZED:
            return
        from mountainash.core.capabilities.bootstrap import _load_into_registry
        try:
            _load_into_registry()
        except BaseException as exc:
            cls._load_state = _LoadState.FAILED
            cls._load_error = exc
            raise
        cls._load_state = _LoadState.LOADED

@classmethod
def register_declaration(cls, declaration) -> None:
    cls.register_backend(declaration.backend, declaration.facts)
    cls._declarations = cls._declarations + (declaration,)

@classmethod
def declarations(cls):
    cls._ensure_loaded()
    return cls._declarations
```

Insert `cls._ensure_loaded()` as the FIRST line of `capability_for`, `facts`, `residue_for`, `router_facts`, and `validate_plan_capabilities`. (`residue_for` and `router_facts` call `facts()` internally — the state check is an idempotent early-return, so the double call is harmless.)

Update the isolation trio:

```python
@classmethod
def snapshot(cls):
    return (
        dict(cls._facts), dict(cls._kinds), dict(cls._value_class_facts),
        cls._declarations, cls._load_state, cls._load_error,
    )

@classmethod
def restore(cls, snapshot) -> None:
    facts, kinds, vclass, decls, state, err = snapshot
    cls._facts = dict(facts); cls._kinds = dict(kinds)
    cls._value_class_facts = dict(vclass)
    cls._declarations = decls
    cls._load_state = state; cls._load_error = err

@classmethod
def reset(cls) -> None:
    """Test-only. Enters ISOLATED (autoload disabled). Snapshot FIRST —
    without a restore there is no way back to autoload in this process."""
    cls._facts = {}; cls._kinds = {}; cls._value_class_facts = {}
    cls._declarations = ()
    cls._load_state = _LoadState.ISOLATED
    cls._load_error = None
```

`grep -rn "CapabilityRegistry.snapshot()\|CapabilityRegistry.restore(" tests/ src/` — snapshot consumers treat the token as opaque (documented), so the widened tuple is compatible; fix any test that unpacked it positionally and flag it in the report.

- [ ] **Step 4: Split bootstrap into state-machine-aware halves**

Rewrite `bootstrap.py`'s function (keep `_DECLARATION_MODULES` as-is for now — discovery arrives in Task 11):

```python
def _load_into_registry() -> None:
    """Import every declaration module and register (registry-internal hook;
    called ONLY by CapabilityRegistry under its load lock)."""
    for module in _DECLARATION_MODULES:
        importlib.import_module(module)
    from mountainash.core.capabilities.core_facts import register_core_polymorphic_facts
    register_core_polymorphic_facts()


def load_all_capability_declarations() -> None:
    """Public entry: enumerating consumers call this; queries autoload it."""
    from mountainash.core.capabilities.registry import CapabilityRegistry, _LoadState
    state = CapabilityRegistry._load_state
    if state is _LoadState.LOADED:
        return
    if state is _LoadState.ISOLATED:
        raise RuntimeError(
            "registry is ISOLATED (reset() without restore()); refusing to "
            "load production declarations into an isolated registry"
        )
    CapabilityRegistry._ensure_loaded()
```

Delete the old `_loaded` global.

- [ ] **Step 5: Run the new tests plus the enforcement suite**

Run: `uv run pytest tests/core/test_capability_load_state.py tests/core -k "capabilit" -x -q`
Expected: PASS — including the existing `isolated_registry` fixture tests (reset→ISOLATED preserves their semantics).

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/core/capabilities/registry.py src/mountainash/core/capabilities/bootstrap.py tests/core/test_capability_load_state.py
git commit -m "refactor(capabilities): registry load-state machine + declaration retention"
```

---

### Task 5: New package skeletons + `string.py`

**Files:**
- Create: `src/mountainash/expressions/backends/capabilities/__init__.py`, `.../capabilities/string.py`, `src/mountainash/relations/backends/capabilities/__init__.py`
- Test: `tests/core/test_capability_migration_equivalence.py` (new — grows one test per migration task)

**Interfaces:**
- Consumes: Task 1 protocol; old module `mountainash.expressions.backends.expression_systems.string_option_capabilities` (still present).
- Produces: `capabilities.string.DECLARATIONS`; public `BROKEN_STRING_OPS_BY_BACKEND`, `OP_LEVEL_FKEYS` (renamed from `_`-prefixed); package `__init__` docstrings stating the protocol rules.

- [ ] **Step 1: Create the two package `__init__.py` files**

`src/mountainash/expressions/backends/capabilities/__init__.py`:

```python
"""Capability declarations for expression backends (spec 2026-08-07).

PROTOCOL (machine-enforced by tests/core/test_capability_protocol_guard.py):
- Every non-exempt module here exposes
  ``DECLARATIONS: tuple[CapabilityDeclaration, ...]`` and registers NOTHING
  itself — bootstrap discovers this package and registers.
- Exempt from the DECLARATIONS requirement: ``__init__.py`` files and
  ``_``-prefixed helper modules (package-local data builders only).
- Import-safe: no module here imports ibis or narwhals (polars is a core
  dependency of the parent chain and exempt).
- One declaration per (backend x domain x source x probe wave); evidence is
  None only for fully probe_exempt waves.
- Placement (spec §3 decision table): domain modules (string, arithmetic,
  datetime/*, polymorphic) hold cross-backend facts about one operation
  domain; backend modules (polars, narwhals, ibis) hold that backend's
  inherent expr-argument facts (LITERAL_ONLY etc.).
- Family/dialect discipline: ibis declares family-default (dialect=None)
  AND concrete-dialect facts (except family-supported ops with dialect-only
  gaps, per the strptime precedent); narwhals declares per-dialect only.
- Retirement: a fixed limitation MOVES to core/capabilities/retired.py.
"""
from __future__ import annotations
```

`src/mountainash/relations/backends/capabilities/__init__.py`: same docstring with "relation backends" in the first line and the placement bullet replaced by: `- All relation facts (RKEY_*) live in the per-backend module for the restricted backend.`

- [ ] **Step 2: Create `string.py` by moving content**

```bash
cp src/mountainash/expressions/backends/expression_systems/string_option_capabilities.py src/mountainash/expressions/backends/capabilities/string.py
```

Then edit `capabilities/string.py`:
1. Apply the Global-Constraints conversion contract (docstring note, no reformatting).
2. Rename `_BROKEN_STRING_OPS_BY_BACKEND` → `BROKEN_STRING_OPS_BY_BACKEND` and `_OP_LEVEL_FKEYS` → `OP_LEVEL_FKEYS` (module-internal references too — `grep -n "_BROKEN_STRING_OPS_BY_BACKEND\|_OP_LEVEL_FKEYS" src/mountainash/expressions/backends/capabilities/string.py` must return only the new names afterward).
3. Delete the three trailing `CapabilityRegistry.register_backend(...)` calls and the `CapabilityRegistry` import; append instead:

```python
from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)

_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,          # 2026-07-23
    library_versions=(),        # not recorded in the original docstring
    fixtures=(
        "polars", "ibis-duckdb", "narwhals-polars", "narwhals-pandas",
    ),
)

DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.POLARS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT, facts=_POLARS_FACTS,
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=tuple(_IBIS_FAMILY_DEFAULTS) + tuple(_IBIS_DUCKDB_FACTS)
        + _op_level_facts(CONST_BACKEND.IBIS),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=tuple(_NARWHALS_FACTS) + _op_level_facts(CONST_BACKEND.NARWHALS),
        evidence=_EVIDENCE,
    ),
)
```

The fact expressions MUST reproduce the old file's three `register_backend` argument expressions exactly (read the old file's bottom; the polars call passes `_POLARS_FACTS`, the ibis call `_IBIS_FAMILY_DEFAULTS + _IBIS_DUCKDB_FACTS + _op_level_facts(IBIS)`, the narwhals call `_NARWHALS_FACTS + _op_level_facts(NARWHALS)`). If any name differs from the above, follow the FILE, not this plan, and note it.

- [ ] **Step 3: Write the equivalence test**

```python
# tests/core/test_capability_migration_equivalence.py
"""Each migrated declaration module registers EXACTLY the facts its
predecessor registered (spec: fact identity is the drift detector).

These tests import BOTH old and new modules; they are deleted in Task 11
together with the old files.
"""
from __future__ import annotations


def _multiset_equal(new_facts, old_facts):
    old = list(old_facts)
    assert len(new_facts) == len(old)
    for f in new_facts:
        assert f in old, f"fact not in legacy set: {f}"
        old.remove(f)
    assert old == [], f"legacy facts missing from new module: {old}"


def test_string_module_equivalence():
    from mountainash.expressions.backends.capabilities import string as new
    from mountainash.expressions.backends.expression_systems import (
        string_option_capabilities as old,
    )
    from mountainash.core.constants import CONST_BACKEND

    legacy = (
        list(old._POLARS_FACTS)
        + list(old._IBIS_FAMILY_DEFAULTS) + list(old._IBIS_DUCKDB_FACTS)
        + list(old._op_level_facts(CONST_BACKEND.IBIS))
        + list(old._NARWHALS_FACTS)
        + list(old._op_level_facts(CONST_BACKEND.NARWHALS))
    )
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)
    assert new.BROKEN_STRING_OPS_BY_BACKEND == old._BROKEN_STRING_OPS_BY_BACKEND
    assert new.OP_LEVEL_FKEYS == old._OP_LEVEL_FKEYS
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/core/test_capability_migration_equivalence.py -x -q`
Expected: PASS. A `CapabilityDeclaration` construction error here means a source/domain misclassification — check whether the module contains an FKEY enum the classifier table misses; extend `_DOMAIN_SUFFIXES` ONLY per spec Domain members, otherwise flag.

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/backends/capabilities src/mountainash/relations/backends/capabilities tests/core/test_capability_migration_equivalence.py
git commit -m "refactor(capabilities): capabilities packages + string declarations module"
```

---

### Task 6: `arithmetic.py`

**Files:**
- Create: `src/mountainash/expressions/backends/capabilities/arithmetic.py` (from `arithmetic_option_capabilities.py`)
- Test: extend `tests/core/test_capability_migration_equivalence.py`

**Interfaces:**
- Consumes: Task 1 protocol; old module (still present).
- Produces: `capabilities.arithmetic.DECLARATIONS`.

- [ ] **Step 1: Copy and convert** (Global-Constraints contract). Read the old file's bottom `register_backend` calls first (`src/mountainash/expressions/backends/expression_systems/arithmetic_option_capabilities.py:360-382`) — they combine `POLARS_ARITHMETIC_OPTION_CAPABILITIES + _SEMANTIC_FACTS[...] + _ROUNDING_FACTS[...]` etc. Reproduce each call's argument expression as one `CapabilityDeclaration.facts` (three declarations: POLARS, IBIS, NARWHALS; all `domain=Domain.ARITHMETIC`, `source=FactSource.SUBSTRAIT`), with

```python
_EVIDENCE = ProbeEvidence(
    probe_date=_SINCE,   # 2026-07-21
    library_versions=(),
    fixtures=("polars", "ibis-duckdb", "narwhals-polars", "narwhals-pandas"),
)
```

If any fact in those tuples is keyed by a non-ARITHMETIC enum, the declaration constructor will raise — split that fact into its own correctly-domained declaration and note it in the report.

- [ ] **Step 2: Extend the equivalence test**

```python
def test_arithmetic_module_equivalence():
    from mountainash.expressions.backends.capabilities import arithmetic as new
    from mountainash.expressions.backends.expression_systems import (
        arithmetic_option_capabilities as old,
    )
    legacy = (
        list(old.POLARS_ARITHMETIC_OPTION_CAPABILITIES)
        + list(old._SEMANTIC_FACTS["polars"]) + list(old._ROUNDING_FACTS["polars"])
        + list(old.IBIS_ARITHMETIC_OPTION_CAPABILITIES)
        + list(old.IBIS_DUCKDB_OVERFLOW_REFINEMENTS)
        + list(old._IBIS_SEMANTIC_FAMILY_DEFAULTS) + list(old._IBIS_ROUNDING_FAMILY_DEFAULTS)
        + list(old._SEMANTIC_FACTS["ibis-duckdb"]) + list(old._ROUNDING_FACTS["ibis-duckdb"])
        + list(old.NARWHALS_ARITHMETIC_OPTION_CAPABILITIES)
        + list(old._SEMANTIC_FACTS["narwhals-polars"]) + list(old._SEMANTIC_FACTS["narwhals-pandas"])
        + list(old._ROUNDING_FACTS["narwhals-polars"]) + list(old._ROUNDING_FACTS["narwhals-pandas"])
    )
    new_facts = [f for d in new.DECLARATIONS for f in d.facts]
    _multiset_equal(new_facts, legacy)
```

FIRST verify the legacy expression against the old file's actual `register_backend` bottom calls (`read` lines 360-382 and the `_SEMANTIC_FACTS`/`_ROUNDING_FACTS` dict keys at 285-357) — the dict keys above are the plan's best reading; the FILE is authoritative. Adjust the test to mirror the file exactly.

- [ ] **Step 3: Run** `uv run pytest tests/core/test_capability_migration_equivalence.py -x -q` — Expected: PASS.

- [ ] **Step 4: Commit** — `git add -A && git commit -m "refactor(capabilities): arithmetic declarations module"`

---

### Task 7: `datetime/` subpackage (4 modules)

**Files:**
- Create: `src/mountainash/expressions/backends/capabilities/datetime/__init__.py` (docstring only: `"""Datetime capability declarations. MA/Substrait physical separation preserved: value_classes_ma.py vs value_classes_substrait.py — never one mixed module."""` + `from __future__ import annotations`)
- Create: `datetime/options.py` ← `datetime_option_capabilities.py`; `datetime/value_classes_ma.py` ← `datetime_value_class_capabilities_ma.py`; `datetime/value_classes_substrait.py` ← `datetime_value_class_capabilities_substrait.py`; `datetime/strptime.py` ← `strptime_format_capabilities.py`
- Test: extend `tests/core/test_capability_migration_equivalence.py`

**Interfaces:**
- Produces: four `DECLARATIONS` tuples. Declarations table (domain always `Domain.DATETIME`):

| module | declarations (backend, source, facts-expression from old bottom calls) | evidence |
|---|---|---|
| `options.py` | (IBIS, MOUNTAINASH, `_IBIS_FAMILY_DEFAULTS + _IBIS_DUCKDB_FACTS`); (NARWHALS, MOUNTAINASH, `_NARWHALS_POLARS_FACTS + _NARWHALS_PANDAS_FACTS`) | probe_date `_SINCE` (2026-07-24), versions `()`, fixtures `("polars","ibis-duckdb","narwhals-polars","narwhals-pandas")` |
| `value_classes_ma.py` | (IBIS, MOUNTAINASH, `_IBIS_FACTS`); (NARWHALS, MOUNTAINASH, `_NARWHALS_FACTS`) | probe_date `_SINCE` (2026-07-25), versions `()`, fixtures per its docstring matrix |
| `value_classes_substrait.py` | (IBIS, SUBSTRAIT, `_IBIS_FACTS`); (NARWHALS, SUBSTRAIT, `_NARWHALS_FACTS`) | probe_date `_SINCE` (2026-07-25), versions `()`, fixtures per its docstring matrix |
| `strptime.py` | (IBIS, SUBSTRAIT, `_IBIS_SQLITE_FACTS`); (NARWHALS, SUBSTRAIT, `_NARWHALS_FACTS`) | probe_date `"2026-07-30"`, versions `(("ibis","12.0.0"),("narwhals","2.23.0"))`, fixtures `("polars","ibis-duckdb","ibis-polars","ibis-sqlite","narwhals-polars","narwhals-pandas")` |

(strptime facts are all `probe_exempt` — evidence is still ATTACHED because the docstring records a real probe; `evidence=None` is a permission, not a requirement.)

- [ ] **Step 1: Copy + convert all four** per the Global-Constraints contract and the table above.
- [ ] **Step 2: Extend the equivalence test** — one function per module, same `_multiset_equal` pattern as Task 5 Step 3, legacy side = the old module's exact `register_backend` argument expressions (read each old file's bottom lines first; e.g. for options: `old._IBIS_FAMILY_DEFAULTS + old._IBIS_DUCKDB_FACTS` and `old._NARWHALS_POLARS_FACTS + old._NARWHALS_PANDAS_FACTS`).
- [ ] **Step 3: Run** `uv run pytest tests/core/test_capability_migration_equivalence.py -x -q` — Expected: PASS.
- [ ] **Step 4: Commit** — `git add -A && git commit -m "refactor(capabilities): datetime declarations subpackage"`

---

### Task 8: `polymorphic.py` (from `core_facts.py`)

**Files:**
- Create: `src/mountainash/expressions/backends/capabilities/polymorphic.py`
- Test: extend `tests/core/test_capability_migration_equivalence.py`

**Interfaces:**
- Consumes: `core_facts.py` (still present; deleted in Task 11).
- Produces: `polymorphic.DECLARATIONS` — 6 declarations: (family × domain) for families POLARS/IBIS/NARWHALS × domains SET/TERNARY.

- [ ] **Step 1: Implement as pure data**

```python
# src/mountainash/expressions/backends/capabilities/polymorphic.py
"""Core polymorphic declarations — LIST-wrapper literal marker semantics
shared by every family (arguments-vs-options.md §Polymorphic Parameters).
Migrated from mountainash.core.capabilities.core_facts (2026-08 capability-architecture PR).
"""
from __future__ import annotations

from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration,
    Domain,
    FactSource,
)
from mountainash.core.capabilities.schema import CapabilityFact, CapabilityLevel
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_SET as FK_SET,
    FKEY_MOUNTAINASH_SCALAR_TERNARY as FK_TERN,
)

_MSG = (
    "literal collections unwrap to raw values; "
    "expressions compile through (LIST-wrapper marker)"
)


def _fact(op, param, family):
    return CapabilityFact(
        operation_key=op, param=param,
        level=CapabilityLevel.POLYMORPHIC, backend=family,
        message=_MSG, since="2026-07-05",
        probe_exempt="polymorphic — both paths supported by design",
    )


_FAMILIES = (CONST_BACKEND.POLARS, CONST_BACKEND.IBIS, CONST_BACKEND.NARWHALS)

DECLARATIONS = tuple(
    CapabilityDeclaration(
        backend=family, domain=Domain.SET, source=FactSource.MOUNTAINASH,
        facts=(
            _fact(FK_SET.IS_IN, "haystack", family),
            _fact(FK_SET.IS_NOT_IN, "haystack", family),
        ),
    )
    for family in _FAMILIES
) + tuple(
    CapabilityDeclaration(
        backend=family, domain=Domain.TERNARY, source=FactSource.MOUNTAINASH,
        facts=(_fact(FK_TERN.COLLECT_VALUES, "*", family),),
    )
    for family in _FAMILIES
)
```

(Message, since, and probe_exempt strings MUST match `core_facts.py` byte-for-byte — open it and verify.)

- [ ] **Step 2: Equivalence test** — register `core_facts.register_core_polymorphic_facts()` into an isolated registry (snapshot/reset/restore around it, and reset the module's `_REGISTERED` flag via `monkeypatch.setattr(core_facts, "_REGISTERED", False)` first), collect `CapabilityRegistry.facts()`, and `_multiset_equal` against `[f for d in polymorphic.DECLARATIONS for f in d.facts]`.
- [ ] **Step 3: Run** `uv run pytest tests/core/test_capability_migration_equivalence.py -x -q` — Expected: PASS.
- [ ] **Step 4: Commit** — `git add -A && git commit -m "refactor(capabilities): polymorphic declarations module"`

---

### Task 9: Backend modules — `ibis.py`, `polars.py`, `narwhals.py`

**Files:**
- Create: `capabilities/ibis.py` (from `ibis_capabilities.py`), `capabilities/polars.py` (extract `PolarsBaseExpressionSystem.CAPABILITIES`), `capabilities/narwhals.py` (extract `NarwhalsBaseExpressionSystem.CAPABILITIES` + its `_STRING_LITERAL_ONLY`/`_DT_LITERAL_ONLY`/`_POLARS_BACKED_FIXED` tables and message constants)
- Test: extend `tests/core/test_capability_migration_equivalence.py`

**Interfaces:**
- Consumes: old files (untouched in this task — base classes still self-register; the rewire happens in Task 11).
- Produces:
  - `capabilities.ibis.IBIS_EXPR_CAPABILITIES` (same name as today) + `DECLARATIONS` = (IBIS, DATETIME, MOUNTAINASH — the `FK_DT.ADD_*` LITERAL_ONLY block) and (IBIS, STRING, SUBSTRAIT — the `FK_STR` blocks incl. trim probe-exempt facts); evidence `ProbeEvidence("2026-07-05", (), ())` on both.
  - `capabilities.polars.POLARS_EXPR_CAPABILITIES: tuple[CapabilityFact, ...]` + `DECLARATIONS` = (POLARS, STRING, SUBSTRAIT) — the current class tuple verbatim; evidence `ProbeEvidence("2026-07-05", (), ("polars",))` (use the actual `since` values found in the class body; if they differ per fact, evidence probe_date = the earliest).
  - `capabilities.narwhals.NARWHALS_EXPR_CAPABILITIES` + `DECLARATIONS` split per (domain × wave): (NARWHALS, STRING, SUBSTRAIT, family-LITERAL_ONLY wave), (NARWHALS, STRING, SUBSTRAIT, polars-backed-fixed wave — the `_POLARS_BACKED_FIXED` EXPR_CAPABLE refinements, own `ProbeEvidence` with `library_versions=(("narwhals","2.19.0"),)` per the class comment), (NARWHALS, DATETIME, MOUNTAINASH), and (NARWHALS, LIST, MOUNTAINASH) if the class tuple contains `FK_LIST` facts — read `narwhals/base.py:47-242` first and derive the exact split from the enums actually present.

- [ ] **Step 1: Read the sources fully** — `expression_systems/ibis_capabilities.py` (78 lines), `polars/base.py:29-100`, `narwhals/base.py:29-242`. List every fact block and its enum family before writing anything.
- [ ] **Step 2: Create the three modules** per the contract. For polars/narwhals this is an EXTRACTION: move the fact-tuple expressions and their supporting constants out of the class body into the new module as module-level `*_EXPR_CAPABILITIES`; do NOT edit the base classes yet.
- [ ] **Step 3: Equivalence tests** — `_multiset_equal` of each new module's declaration-union against, respectively: `old ibis_capabilities.IBIS_EXPR_CAPABILITIES`, `PolarsBaseExpressionSystem.CAPABILITIES`, `NarwhalsBaseExpressionSystem.CAPABILITIES`. Also `assert new.IBIS_EXPR_CAPABILITIES == old.IBIS_EXPR_CAPABILITIES`.
- [ ] **Step 4: Run** `uv run pytest tests/core/test_capability_migration_equivalence.py -x -q` — Expected: PASS.
- [ ] **Step 5: Commit** — `git add -A && git commit -m "refactor(capabilities): backend expr-capability declaration modules"`

---

### Task 10: Relations capability modules

**Files:**
- Create: `src/mountainash/relations/backends/capabilities/ibis.py` (from `ibis_relation_capabilities.py`), `.../polars.py` (extract `PolarsBaseRelationSystem.CAPABILITIES`), `.../narwhals.py` (extract `NarwhalsBaseRelationSystem.CAPABILITIES`)
- Test: extend `tests/core/test_capability_migration_equivalence.py`

**Interfaces:**
- Produces: `IBIS_REL_CAPABILITIES` / `POLARS_REL_CAPABILITIES` / `NARWHALS_REL_CAPABILITIES` tuples + one `DECLARATIONS` per module: `(backend, Domain.RELATION, FactSource.MOUNTAINASH, <tuple>)`, evidence `ProbeEvidence(<earliest since in the tuple>, (), ())`. Base relation classes untouched until Task 11.

- [ ] **Step 1: Read** `relations/backends/relation_systems/{ibis_relation_capabilities.py,polars/base.py,narwhals/base.py}` fully (all small).
- [ ] **Step 2: Create the three modules** per the contract (extraction, as Task 9 Step 2).
- [ ] **Step 3: Equivalence tests** against `IBIS_REL_CAPABILITIES` / `PolarsBaseRelationSystem.CAPABILITIES` / `NarwhalsBaseRelationSystem.CAPABILITIES`.
- [ ] **Step 4: Run** `uv run pytest tests/core/test_capability_migration_equivalence.py -x -q` — Expected: PASS.
- [ ] **Step 5: Commit** — `git add -A && git commit -m "refactor(capabilities): relation declaration modules"`

---

### Task 11: Cutover — rewire consumers, discovery bootstrap, delete old files

**Files:**
- Modify: `expressions/backends/expression_systems/{base.py,ibis/base.py,polars/base.py,narwhals/base.py}`, `relations/backends/relation_systems/{polars/base.py,narwhals/base.py}` (and its `base.py` if it self-registers — grep), `core/capabilities/bootstrap.py`
- Delete: the seven `expression_systems/*_capabilities.py` root files, `relation_systems/ibis_relation_capabilities.py`, `core/capabilities/core_facts.py`, `tests/core/test_capability_migration_equivalence.py`
- Modify: `tests/expressions/argument_types/test_arg_types_string.py`, `tests/expressions/argument_types/test_op_level_gate_probes.py`, `tests/fixtures/capability_census.py` (imports + `node_id` strings)

**Interfaces:**
- Consumes: Tasks 5–10 modules; Task 4 `register_declaration`/state machine.
- Produces: production wiring — discovery bootstrap; base classes importing `CAPABILITIES` from `capabilities/*`; zero import-side-effect registration anywhere.

- [ ] **Step 1: Rewire the six base classes.** In each: delete the class-body fact tables and the trailing `CapabilityRegistry.register_backend(...)` line; import the tuple instead, e.g. in `expression_systems/polars/base.py`:

```python
from mountainash.expressions.backends.capabilities.polars import (
    POLARS_EXPR_CAPABILITIES,
)

class PolarsBaseExpressionSystem(BaseExpressionSystem):
    ...
    CAPABILITIES: tuple[CapabilityFact, ...] = POLARS_EXPR_CAPABILITIES
```

Mirror for narwhals (also delete the now-moved `_STRING_LITERAL_ONLY` etc. tables), ibis (`ibis/base.py` re-points its existing import to `mountainash.expressions.backends.capabilities.ibis`), and the two relation base classes. Keep the `CAPABILITIES` class attribute — subclass/introspection consumers may read it (`grep -rn "\.CAPABILITIES" src/ tests/` and fix any importer of the old module paths).

- [ ] **Step 2: Delete the `expression_systems/base.py` tail** — remove the bottom `from mountainash.core.capabilities.core_facts import ...` / `register_core_polymorphic_facts()` lines (base.py:84-88).

- [ ] **Step 3: Discovery bootstrap.** Replace `bootstrap.py`'s module list and `_load_into_registry`:

```python
"""Load every capability declaration (spec rev 3, §2).

Declaration modules are DISCOVERED under the two capability package roots —
there is no manifest to forget. Exempt from the DECLARATIONS requirement:
__init__.py and ``_``-prefixed helper modules.
"""
from __future__ import annotations

import importlib
import pkgutil

_ROOTS = (
    "mountainash.expressions.backends.capabilities",
    "mountainash.relations.backends.capabilities",
)


def discover_declaration_modules() -> tuple[str, ...]:
    names: list[str] = []
    for root in _ROOTS:
        pkg = importlib.import_module(root)
        for info in pkgutil.walk_packages(pkg.__path__, prefix=root + "."):
            leaf = info.name.rsplit(".", 1)[1]
            if leaf.startswith("_"):
                continue
            if not info.ispkg:
                names.append(info.name)
    return tuple(sorted(names))


def _load_into_registry() -> None:
    """Registry-internal hook; called ONLY under the registry load lock."""
    from mountainash.core.capabilities.registry import CapabilityRegistry

    for name in discover_declaration_modules():
        module = importlib.import_module(name)
        declarations = getattr(module, "DECLARATIONS", None)
        if declarations is None:
            raise TypeError(
                f"capability declaration module {name!r} exposes no "
                "DECLARATIONS tuple (spec 2026-08-07 §1); helper modules "
                "must be _-prefixed"
            )
        for declaration in declarations:
            CapabilityRegistry.register_declaration(declaration)
```

(`load_all_capability_declarations` from Task 4 Step 4 is unchanged.) Note: subpackages (`datetime/`) are recursed by `walk_packages`; their `__init__` is `ispkg=True` and skipped.

- [ ] **Step 4: Delete the old files and the equivalence tests**

```bash
git rm src/mountainash/expressions/backends/expression_systems/{arithmetic_option_capabilities,string_option_capabilities,datetime_option_capabilities,datetime_value_class_capabilities_ma,datetime_value_class_capabilities_substrait,strptime_format_capabilities,ibis_capabilities}.py
git rm src/mountainash/relations/backends/relation_systems/ibis_relation_capabilities.py
git rm src/mountainash/core/capabilities/core_facts.py
git rm tests/core/test_capability_migration_equivalence.py
```

Then `grep -rn "core_facts\|_option_capabilities\|value_class_capabilities\|strptime_format_capabilities\|ibis_capabilities\|ibis_relation_capabilities" src/ tests/ scripts/` — every remaining hit is either (a) an importer to update to the new path, or (b) a prose/docstring reference to update (e.g. `expsys_ib_ext_ma_scalar_datetime.py:29,598` and `expsys_ib_scalar_datetime.py:28,298` reference `datetime_value_class_capabilities_*.py` → point them at `capabilities/datetime/value_classes_*.py`). Zero hits may remain except in `docs/superpowers/`.

- [ ] **Step 5: Update the three test importers + census node_ids.** Point the imports at `mountainash.expressions.backends.capabilities.string` with the PUBLIC names (`BROKEN_STRING_OPS_BY_BACKEND`, `OP_LEVEL_FKEYS`). In `tests/fixtures/capability_census.py`, `grep -n "_BROKEN_STRING_OPS_BY_BACKEND\|_OP_LEVEL_FKEYS"` and update BOTH the imports AND any `node_id` f-strings embedding the old names; then `grep -rn "_BROKEN_STRING_OPS_BY_BACKEND" tests/` to catch consumers matching on those node_id strings (closure tests, committed census `.md`) and update them in this same commit.

- [ ] **Step 6: Smoke the wiring**

```bash
uv run python -c "
import mountainash as ma
from mountainash.core.capabilities import CapabilityRegistry
n = len(CapabilityRegistry.facts())
assert n > 100, n
print('facts:', n, 'declarations:', len(CapabilityRegistry.declarations()))
"
uv run pytest tests/core -k "capabilit or divergence" -q
```

Expected: fact count ≥ the Task 0 baseline count; capability suite PASS.

- [ ] **Step 7: Regenerate the spine expectation census** (if the generator exists on develop — check `scripts/` and `tests/_spine_expectation_census.md`; the file header names its generator). Run it and commit the diff; source paths/line numbers changing is EXPECTED, fact rows changing is NOT — a fact-row diff is a Task 5–10 migration bug: stop and fix there.

- [ ] **Step 8: Commit** — `git add -A && git commit -m "refactor(capabilities): discovery bootstrap cutover; delete legacy declaration modules"`

---

### Task 12: Protocol guard suite + full verification

**Files:**
- Create: `tests/core/test_capability_protocol_guard.py`
- Test: full capability selection + per-backend smoke.

**Interfaces:**
- Consumes: everything above.
- Produces: the closed-by-default guards from spec §7.

- [ ] **Step 1: Write the guard suite**

```python
# tests/core/test_capability_protocol_guard.py
"""Closed-by-default guards for the declaration protocol (spec rev 3, §7)."""
from __future__ import annotations

import importlib
import subprocess
import sys
import textwrap

import pytest

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    CapabilityRegistry,
    Domain,
    load_all_capability_declarations,
)
from mountainash.core.capabilities.bootstrap import discover_declaration_modules
from mountainash.core.capabilities.declarations import (
    classify_domain,
    classify_source,
)
from mountainash.core.capabilities.retired import assert_no_active_retired_overlap
from mountainash.core.capabilities.schema import WILDCARD_PARAM


def test_every_discovered_module_is_well_formed():
    names = discover_declaration_modules()
    assert len(names) >= 12  # string, arithmetic, 4x datetime, polymorphic,
                             # 3x expr-backend, 3x relation-backend
    for name in names:
        module = importlib.import_module(name)
        decls = module.DECLARATIONS
        assert isinstance(decls, tuple) and decls, name
        for d in decls:
            assert isinstance(d, CapabilityDeclaration), (name, d)


def test_same_key_declarations_have_distinct_evidence():
    for name in discover_declaration_modules():
        module = importlib.import_module(name)
        seen: dict[tuple, list] = {}
        for d in module.DECLARATIONS:
            seen.setdefault((d.backend, d.source, d.domain), []).append(d.evidence)
        for key, evidences in seen.items():
            assert len(evidences) == len(set(evidences)), (
                f"{name}: same-key declarations {key} share evidence — "
                "one declaration per probe wave"
            )


# Placement decision table (spec §3) — THE guard config, nothing else.
# module-leaf -> predicate(fact) that every fact in the module must satisfy.
def _is_domain_module_fact(module_leaf: str):
    domains = {
        "string": Domain.STRING, "arithmetic": Domain.ARITHMETIC,
        "options": Domain.DATETIME, "value_classes_ma": Domain.DATETIME,
        "value_classes_substrait": Domain.DATETIME, "strptime": Domain.DATETIME,
    }
    want = domains[module_leaf]
    return lambda f: classify_domain(f.operation_key) is want


_BACKEND_MODULES = {"polars", "narwhals", "ibis"}


def test_placement_decision_table():
    for name in discover_declaration_modules():
        leaf = name.rsplit(".", 1)[1]
        module = importlib.import_module(name)
        facts = [f for d in module.DECLARATIONS for f in d.facts]
        if ".relations." in name:
            assert all(
                classify_domain(f.operation_key) is Domain.RELATION for f in facts
            ), name
        elif leaf in _BACKEND_MODULES:
            # backend modules: the backend is the module's namesake
            assert all(f.backend.value == leaf for f in facts), name
        elif leaf == "polymorphic":
            assert all(
                classify_domain(f.operation_key) in (Domain.SET, Domain.TERNARY)
                for f in facts
            ), name
        else:
            pred = _is_domain_module_fact(leaf)
            assert all(pred(f) for f in facts), name


_SUBPROCESS_PRELUDE = """
import sys

class _Block:
    def __init__(self, names): self.names = names
    def find_module(self, fullname, path=None):
        return self if fullname.split(".")[0] in self.names else None
    def load_module(self, fullname):
        raise ImportError(f"blocked optional backend: {fullname}")

sys.meta_path.insert(0, _Block({"ibis", "narwhals"}))
"""


def test_import_safety_without_optional_backends():
    code = _SUBPROCESS_PRELUDE + textwrap.dedent("""
        from mountainash.core.capabilities.bootstrap import (
            discover_declaration_modules,
        )
        import importlib
        total = 0
        for name in discover_declaration_modules():
            module = importlib.import_module(name)
            total += len(module.DECLARATIONS)
        print("OK", total)
    """)
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=180
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.startswith("OK "), out.stdout


def test_no_registration_side_effects_on_import():
    code = textwrap.dedent("""
        import importlib
        from mountainash.core.capabilities.bootstrap import (
            discover_declaration_modules,
        )
        from mountainash.core.capabilities.registry import CapabilityRegistry
        for name in discover_declaration_modules():
            importlib.import_module(name)
        assert CapabilityRegistry._facts == {}, "import side-effect registration"
        assert CapabilityRegistry._value_class_facts == {}
        print("OK")
    """)
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=180
    )
    assert out.returncode == 0, out.stderr


def test_no_fact_simultaneously_active_and_retired():
    load_all_capability_declarations()
    assert_no_active_retired_overlap(CapabilityRegistry)
```

- [ ] **Step 2: Run the guard suite** — `uv run pytest tests/core/test_capability_protocol_guard.py -x -q` — Expected: PASS. (The import-safety subprocess inherits the parent chain importing polars — that's the spec's exemption. If it fails on `ibis`/`narwhals` leaking in via `expressions/backends/__init__`, the try/except probes there already tolerate ImportError — investigate the actual traceback before touching anything.)

- [ ] **Step 3: Full verification**

```bash
uv run pytest tests/core tests/fixtures -q
uv run pytest tests/expressions/argument_types -q
uv run pytest tests/core -k "capabilit or divergence" -q
```

Expected: all PASS with counts ≥ the Task 0 baseline. Per-backend end-to-end smoke:

```bash
uv run python -c "
import polars as pl
import mountainash as ma
df = pl.DataFrame({'x': ['abc', 'b']})
expr = ma.col('x').str_pad_start(5, '_') if hasattr(ma.col('x'), 'str_pad_start') else ma.col('x')
print(df.select(ma.col('x').compile('polars') if hasattr(ma.col('x'), 'compile') else pl.col('x')))
"
```

If the public compile entrypoint differs, use the pattern the existing tests in `tests/expressions/` use (grep `ma.col` there) — the requirement is: one expression per available backend (polars mandatory; ibis/narwhals if installed) exercises a CAPABILITY-GATED path end-to-end and (for a gated input) raises `BackendCapabilityError`, proving autoload fired.

- [ ] **Step 4: Commit** — `git add -A && git commit -m "test(capabilities): protocol guard suite"`

---

### Task 13: Final review gate + PR

- [ ] **Step 1:** Re-run the whole targeted selection one final time: `uv run pytest tests/core tests/fixtures tests/expressions/argument_types -q` — PASS required.
- [ ] **Step 2:** Whole-branch adversarial review per the repo's SDD flow (most-capable tier), then fix findings.
- [ ] **Step 3:** `gh pr create --base develop --title "refactor(capabilities): declaration architecture (spec 2026-08-07)"` with a body summarizing spec §§1–7 and the migration map. Do NOT merge without user confirmation.
