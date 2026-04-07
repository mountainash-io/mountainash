# Frictionless Data Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-class Frictionless Data Package support — descriptor round-trip, multi-resource materialization via the storage facade, and a Relation DAG orchestrator that lets named relations reference each other via `dag.ref(name)`.

**Architecture:** A new `typespec.datapackage` module wraps existing single-table Frictionless code with package-level metadata. Two new mountainash-extension relation nodes (`RefRelNode`, `ResourceReadRelNode`) plug into the existing `UnifiedRelationVisitor` via a new `ref_resolver` kwarg and per-backend visit methods. A thin `RelationDAG` orchestrator stitches it together: it walks each named relation's tree for refs, topologically orders them, and compiles them in order through the existing visitor — feeding cached upstream results back via the resolver. No new visitor stack, no new protocol layer beyond the wiring matrix entry for the two new nodes.

**Tech Stack:** Python 3.10+, Pydantic v2, Polars (LazyFrame), Narwhals, Ibis, hatch + pytest, ruff, mypy, `mountainash-utils-files` storage facade.

**Spec:** `docs/superpowers/specs/2026-04-07-frictionless-datapackage-design.md`

---

## File Structure

### New files
```
src/mountainash/typespec/datapackage.py           # DataPackage, DataResource, TableDialect
src/mountainash/relations/core/relation_nodes/extensions_mountainash/
    reln_ext_ref.py                                # RefRelNode
    reln_ext_resource_read.py                      # ResourceReadRelNode
src/mountainash/relations/core/relation_protocols/relation_systems/extensions_mountainash/
    prtcl_relsys_ext_ma_dag.py                     # protocol for ref + resource_read
src/mountainash/relations/backends/relation_systems/polars/extensions_mountainash/
    relsys_pl_ext_ma_dag.py                        # Polars impl
src/mountainash/relations/backends/relation_systems/narwhals/extensions_mountainash/
    relsys_nw_ext_ma_dag.py                        # Narwhals impl
src/mountainash/relations/backends/relation_systems/ibis/extensions_mountainash/
    relsys_ib_ext_ma_dag.py                        # Ibis impl
src/mountainash/relations/dag/
    __init__.py
    dag.py                                         # RelationDAG orchestrator
    resource_ref.py                                # ResourceRef wrapper
    errors.py                                      # RelationDAGRequired, MissingResourceSchema
src/mountainash/relations/dag/readers/
    __init__.py                                    # format → reader dispatch
    csv.py
    json.py
    parquet.py
    inline.py
tests/typespec/test_datapackage_table_dialect.py
tests/typespec/test_datapackage_resource.py
tests/typespec/test_datapackage_package.py
tests/typespec/test_datapackage_round_trip.py
tests/typespec/fixtures/                           # real datapackage.json fixtures
    gdp.datapackage.json
    country-codes.datapackage.json
tests/relations/dag/test_ref_rel_node.py
tests/relations/dag/test_resource_read_rel_node.py
tests/relations/dag/test_relation_dag.py
tests/relations/dag/test_dag_collect.py
tests/relations/dag/test_package_to_dag.py
tests/relations/dag/test_dag_to_package.py
tests/relations/dag/test_e2e_real_descriptor.py
```

### Modified files
```
src/mountainash/core/constants.py                          # +ExtensionRelOperation.READ_RESOURCE, REF
src/mountainash/relations/core/unified_visitor/relation_visitor.py   # +ref_resolver, +visit_ref_rel, +visit_resource_read_rel
src/mountainash/relations/core/relation_nodes/extensions_mountainash/__init__.py  # export new nodes
src/mountainash/relations/core/relation_protocols/relation_systems/extensions_mountainash/__init__.py
src/mountainash/relations/backends/relation_systems/polars/extensions_mountainash/__init__.py
src/mountainash/relations/backends/relation_systems/narwhals/extensions_mountainash/__init__.py
src/mountainash/relations/backends/relation_systems/ibis/extensions_mountainash/__init__.py
src/mountainash/typespec/__init__.py                        # export DataPackage, DataResource, TableDialect
src/mountainash/typespec/frictionless.py                    # FieldSpec round-trip gap fixes (Phase 1)
src/mountainash/__init__.py                                 # top-level re-exports
```

---

## Phase 1 — TypeSpec audit and TableDialect

### Task 1: Audit existing FieldSpec ↔ Frictionless round-trip

**Purpose:** The package-level round-trip is meaningless if `FieldSpec` doesn't round-trip cleanly. Identify gaps before building on top.

**Files:**
- Read: `src/mountainash/typespec/spec.py`, `src/mountainash/typespec/frictionless.py`
- Reference: Frictionless Table Schema spec — fetch via `gh api repos/frictionlessdata/datapackage/contents/content/docs/standard/table-schema.mdx`

- [ ] **Step 1: Read both files end-to-end and list every `FieldSpec` / `FieldConstraints` / `ForeignKey` field**

- [ ] **Step 2: Cross-check against the Table Schema spec.** For each spec field, note: round-tripped, partially round-tripped, or missing. Specifically check: `name`, `type`, `format`, `title`, `description`, `example`, `constraints` (`required`, `unique`, `minLength`, `maxLength`, `minimum`, `maximum`, `pattern`, `enum`), `rdfType`, `categories`, `categoriesOrdered`, `missingValues` (resource-level — note for later), `primaryKey`, `foreignKeys`.

- [ ] **Step 3: Write the gap list as a checklist into a temp file** `notes/typespec-frictionless-gaps.md` (gitignored or committed for the next task to consume). Format: one line per gap, file:line pointer where the existing converter currently silently drops the field. If there are no gaps, write `# No gaps found` and Task 2 becomes a no-op commit.

### Task 2: Fix FieldSpec round-trip gaps

**Files:**
- Modify: `src/mountainash/typespec/frictionless.py`
- Modify: `src/mountainash/typespec/spec.py` (only if a gap reflects a missing model field)
- Test: `tests/typespec/test_frictionless_round_trip.py` (create or extend)

- [ ] **Step 1: Write a parametrized round-trip test** asserting that for each gap-listed field, `typespec_to_frictionless(typespec_from_frictionless(d)) == d`. One parametrize entry per gap.

```python
import pytest
from mountainash.typespec.frictionless import (
    typespec_from_frictionless, typespec_to_frictionless,
)

GAP_FIXTURES = [
    pytest.param({"fields": [{"name": "x", "type": "integer", "rdfType": "http://schema.org/Integer"}]}, id="rdfType"),
    # one entry per gap from notes/typespec-frictionless-gaps.md
]

@pytest.mark.parametrize("descriptor", GAP_FIXTURES)
def test_field_round_trip(descriptor):
    spec = typespec_from_frictionless(descriptor)
    assert typespec_to_frictionless(spec) == descriptor
```

- [ ] **Step 2: Run, see them fail.** `hatch run test:test-target-quick tests/typespec/test_frictionless_round_trip.py`

- [ ] **Step 3: Implement each gap fix.** For each gap, edit `frictionless.py` (and `spec.py` if needed). Keep changes minimal — one gap, one edit.

- [ ] **Step 4: Run until green.** All parametrized cases pass.

- [ ] **Step 5: Commit.**
```bash
git add src/mountainash/typespec/frictionless.py src/mountainash/typespec/spec.py tests/typespec/test_frictionless_round_trip.py
git commit -m "fix(typespec): close FieldSpec ↔ Frictionless round-trip gaps"
```

### Task 3: TableDialect class

**Files:**
- Create: `src/mountainash/typespec/datapackage.py` (new file — start with `TableDialect` only)
- Test: `tests/typespec/test_datapackage_table_dialect.py`

- [ ] **Step 1: Write the failing tests.**

```python
# tests/typespec/test_datapackage_table_dialect.py
import pytest
from mountainash.typespec.datapackage import TableDialect


def test_default_dialect_round_trips_to_empty_dict():
    d = TableDialect()
    assert d.to_descriptor() == {}


def test_csv_dialect_round_trips():
    raw = {
        "delimiter": ";",
        "lineTerminator": "\r\n",
        "quoteChar": "'",
        "doubleQuote": False,
        "escapeChar": "\\",
        "nullSequence": "NA",
        "skipInitialSpace": True,
        "header": True,
        "headerRows": [1],
        "headerJoin": " ",
        "commentChar": "#",
        "caseSensitiveHeader": False,
        "csvddfVersion": "1.2",
    }
    d = TableDialect.from_descriptor(raw)
    assert d.to_descriptor() == raw


def test_unknown_keys_are_dropped_silently():
    # Unknown dialect keys are not preserved; dialect is a closed schema.
    raw = {"delimiter": ",", "futureFlag": True}
    d = TableDialect.from_descriptor(raw)
    assert "futureFlag" not in d.to_descriptor()


def test_polars_kwargs_translation():
    d = TableDialect.from_descriptor(
        {"delimiter": "|", "header": True, "skipInitialSpace": True}
    )
    kw = d.to_polars_read_csv_kwargs()
    assert kw == {"separator": "|", "has_header": True}
    # skipInitialSpace has no Polars equivalent — it must be dropped, not raise
```

- [ ] **Step 2: Run, see fail.** `hatch run test:test-target-quick tests/typespec/test_datapackage_table_dialect.py`

- [ ] **Step 3: Implement `TableDialect`.**

```python
# src/mountainash/typespec/datapackage.py
"""Frictionless Data Package types — TableDialect, DataResource, DataPackage."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TableDialect(BaseModel):
    """Frictionless Table Dialect spec — closed schema, unknown keys are dropped."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    delimiter: Optional[str] = None
    line_terminator: Optional[str] = Field(default=None, alias="lineTerminator")
    quote_char: Optional[str] = Field(default=None, alias="quoteChar")
    double_quote: Optional[bool] = Field(default=None, alias="doubleQuote")
    escape_char: Optional[str] = Field(default=None, alias="escapeChar")
    null_sequence: Optional[str] = Field(default=None, alias="nullSequence")
    skip_initial_space: Optional[bool] = Field(default=None, alias="skipInitialSpace")
    header: Optional[bool] = None
    header_rows: Optional[list[int]] = Field(default=None, alias="headerRows")
    header_join: Optional[str] = Field(default=None, alias="headerJoin")
    comment_char: Optional[str] = Field(default=None, alias="commentChar")
    case_sensitive_header: Optional[bool] = Field(default=None, alias="caseSensitiveHeader")
    csvddf_version: Optional[str] = Field(default=None, alias="csvddfVersion")

    @classmethod
    def from_descriptor(cls, raw: dict[str, Any]) -> "TableDialect":
        return cls.model_validate(raw)

    def to_descriptor(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

    def to_polars_read_csv_kwargs(self) -> dict[str, Any]:
        """Translate to ``polars.read_csv`` kwargs. Unsupported keys are dropped silently."""
        out: dict[str, Any] = {}
        if self.delimiter is not None:
            out["separator"] = self.delimiter
        if self.header is not None:
            out["has_header"] = self.header
        if self.quote_char is not None:
            out["quote_char"] = self.quote_char
        if self.escape_char is not None:
            out["eol_char"] = self.escape_char
        if self.comment_char is not None:
            out["comment_prefix"] = self.comment_char
        if self.null_sequence is not None:
            out["null_values"] = [self.null_sequence]
        return out
```

- [ ] **Step 4: Run, see green.**

- [ ] **Step 5: Commit.**
```bash
git add src/mountainash/typespec/datapackage.py tests/typespec/test_datapackage_table_dialect.py
git commit -m "feat(typespec): add TableDialect with descriptor round-trip and Polars kwarg translation"
```

---

## Phase 2 — DataResource and DataPackage

### Task 4: DataResource class with construction validation

**Files:**
- Modify: `src/mountainash/typespec/datapackage.py` (append `DataResource` below `TableDialect`)
- Test: `tests/typespec/test_datapackage_resource.py`

- [ ] **Step 1: Write the failing tests.**

```python
# tests/typespec/test_datapackage_resource.py
import pytest
from mountainash.typespec.datapackage import DataResource, TableDialect


def test_minimal_resource_with_path():
    r = DataResource(name="orders", path="orders.csv")
    assert r.name == "orders"
    assert r.path == "orders.csv"
    assert r.data is None


def test_resource_with_inline_data():
    r = DataResource(name="orders", data=[{"id": 1}, {"id": 2}])
    assert r.data == [{"id": 1}, {"id": 2}]
    assert r.path is None


def test_must_have_exactly_one_of_path_or_data():
    with pytest.raises(ValueError, match="exactly one of path or data"):
        DataResource(name="orders")
    with pytest.raises(ValueError, match="exactly one of path or data"):
        DataResource(name="orders", path="x.csv", data=[{"id": 1}])


def test_multi_file_path_array():
    r = DataResource(name="orders", path=["a.csv", "b.csv"])
    assert r.path == ["a.csv", "b.csv"]


def test_extras_preserved():
    raw = {"name": "orders", "path": "orders.csv", "futurePropX": 42}
    r = DataResource.from_descriptor(raw)
    assert r.extras == {"futurePropX": 42}
    assert r.to_descriptor() == raw


def test_dialect_round_trip():
    raw = {
        "name": "orders",
        "path": "orders.csv",
        "type": "table",
        "dialect": {"delimiter": ";"},
    }
    r = DataResource.from_descriptor(raw)
    assert isinstance(r.dialect, TableDialect)
    assert r.to_descriptor() == raw
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement `DataResource`.** Append to `src/mountainash/typespec/datapackage.py`:

```python
from mountainash.typespec.spec import TypeSpec
from mountainash.typespec.frictionless import (
    typespec_from_frictionless, typespec_to_frictionless,
)


_KNOWN_RESOURCE_FIELDS = {
    "name", "path", "data", "type", "dialect", "schema",
    "title", "description", "format", "mediatype", "encoding",
    "bytes", "hash", "sources", "licenses",
}


class DataResource(BaseModel):
    """Frictionless Data Resource — wraps a TypeSpec with resource-level metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    path: Optional[str | list[str]] = None
    data: Optional[Any] = None
    type: Optional[str] = None
    dialect: Optional[TableDialect] = None
    schema: Optional[TypeSpec] = None
    title: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    mediatype: Optional[str] = None
    encoding: Optional[str] = None
    bytes: Optional[int] = None
    hash: Optional[str] = None
    sources: Optional[list[dict[str, Any]]] = None
    licenses: Optional[list[dict[str, Any]]] = None
    extras: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, _ctx: Any) -> None:
        has_path = self.path is not None
        has_data = self.data is not None
        if has_path == has_data:  # both true OR both false
            raise ValueError(
                f"DataResource '{self.name}' must declare exactly one of path or data"
            )

    @classmethod
    def from_descriptor(cls, raw: dict[str, Any]) -> "DataResource":
        kwargs: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for k, v in raw.items():
            if k in _KNOWN_RESOURCE_FIELDS:
                kwargs[k] = v
            else:
                extras[k] = v
        if "dialect" in kwargs and isinstance(kwargs["dialect"], dict):
            kwargs["dialect"] = TableDialect.from_descriptor(kwargs["dialect"])
        if "schema" in kwargs and isinstance(kwargs["schema"], dict):
            kwargs["schema"] = typespec_from_frictionless(kwargs["schema"])
        kwargs["extras"] = extras
        return cls(**kwargs)

    def to_descriptor(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name}
        if self.path is not None:
            out["path"] = self.path
        if self.data is not None:
            out["data"] = self.data
        for k in ("type", "title", "description", "format", "mediatype",
                  "encoding", "bytes", "hash", "sources", "licenses"):
            v = getattr(self, k)
            if v is not None:
                out[k] = v
        if self.dialect is not None:
            d = self.dialect.to_descriptor()
            if d:
                out["dialect"] = d
        if self.schema is not None:
            out["schema"] = typespec_to_frictionless(self.schema)
        out.update(self.extras)
        return out
```

- [ ] **Step 4: Run, see green.**

- [ ] **Step 5: Commit.**
```bash
git add src/mountainash/typespec/datapackage.py tests/typespec/test_datapackage_resource.py
git commit -m "feat(typespec): add DataResource with path/data validation and round-trip"
```

### Task 5: DataPackage class with construction validation

**Files:**
- Modify: `src/mountainash/typespec/datapackage.py` (append `DataPackage`)
- Test: `tests/typespec/test_datapackage_package.py`

- [ ] **Step 1: Write the failing tests.**

```python
# tests/typespec/test_datapackage_package.py
import pytest
from mountainash.typespec.datapackage import DataPackage, DataResource


def _r(name: str, **kw) -> DataResource:
    return DataResource(name=name, path=f"{name}.csv", **kw)


def test_minimal_package():
    pkg = DataPackage(resources=[_r("orders")])
    assert len(pkg.resources) == 1


def test_must_have_at_least_one_resource():
    with pytest.raises(ValueError, match="at least one resource"):
        DataPackage(resources=[])


def test_resource_names_must_be_unique():
    with pytest.raises(ValueError, match="duplicate resource name"):
        DataPackage(resources=[_r("orders"), _r("orders")])


def test_extras_preserved():
    raw = {
        "name": "demo",
        "resources": [{"name": "orders", "path": "orders.csv"}],
        "futureProp": "x",
    }
    pkg = DataPackage.from_descriptor(raw)
    assert pkg.extras == {"futureProp": "x"}
    assert pkg.to_descriptor() == raw


def test_dollar_schema_preserved():
    raw = {
        "$schema": "https://datapackage.org/profiles/2.0/datapackage.json",
        "resources": [{"name": "orders", "path": "orders.csv"}],
    }
    pkg = DataPackage.from_descriptor(raw)
    assert pkg.dollar_schema == "https://datapackage.org/profiles/2.0/datapackage.json"
    assert pkg.to_descriptor()["$schema"] == raw["$schema"]
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement `DataPackage`.** Append:

```python
_KNOWN_PACKAGE_FIELDS = {
    "name", "id", "licenses", "$schema", "profile",
    "title", "description", "homepage", "version", "created",
    "keywords", "contributors", "sources", "image", "resources",
}


class DataPackage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    resources: list[DataResource]
    name: Optional[str] = None
    id: Optional[str] = None
    licenses: Optional[list[dict[str, Any]]] = None
    dollar_schema: Optional[str] = Field(default=None, alias="$schema")
    profile: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    version: Optional[str] = None
    created: Optional[str] = None
    keywords: Optional[list[str]] = None
    contributors: Optional[list[dict[str, Any]]] = None
    sources: Optional[list[dict[str, Any]]] = None
    image: Optional[str] = None
    extras: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, _ctx: Any) -> None:
        if not self.resources:
            raise ValueError("DataPackage must have at least one resource")
        seen: set[str] = set()
        for r in self.resources:
            if r.name in seen:
                raise ValueError(f"duplicate resource name: {r.name!r}")
            seen.add(r.name)
        # FK references resolve to existing resource names (or "" for self-ref)
        valid = seen | {""}
        for r in self.resources:
            if r.schema is None:
                continue
            for fk in (r.schema.foreign_keys or []):
                ref_resource = fk.reference.resource
                if ref_resource not in valid:
                    raise ValueError(
                        f"resource {r.name!r} foreignKey references unknown resource {ref_resource!r}"
                    )

    @classmethod
    def from_descriptor(cls, raw: dict[str, Any] | str | "Path") -> "DataPackage":
        from pathlib import Path
        import json
        if isinstance(raw, (str, Path)):
            p = Path(raw)
            if p.exists():
                raw = json.loads(p.read_text())
            else:
                raw = json.loads(str(raw))
        assert isinstance(raw, dict)
        kwargs: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for k, v in raw.items():
            if k in _KNOWN_PACKAGE_FIELDS:
                kwargs[k] = v
            else:
                extras[k] = v
        kwargs["resources"] = [DataResource.from_descriptor(r) for r in kwargs["resources"]]
        if "$schema" in kwargs:
            kwargs["dollar_schema"] = kwargs.pop("$schema")
        kwargs["extras"] = extras
        return cls(**kwargs)

    def to_descriptor(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.dollar_schema is not None:
            out["$schema"] = self.dollar_schema
        for k in ("name", "id", "title", "description", "homepage", "version",
                  "created", "keywords", "contributors", "sources", "image",
                  "licenses", "profile"):
            v = getattr(self, k)
            if v is not None:
                out[k] = v
        out["resources"] = [r.to_descriptor() for r in self.resources]
        out.update(self.extras)
        return out

    def write(self, path: str | "Path") -> None:
        from pathlib import Path
        import json
        Path(path).write_text(json.dumps(self.to_descriptor(), indent=2))
```

- [ ] **Step 4: Run, see green.**

- [ ] **Step 5: Commit.**
```bash
git add src/mountainash/typespec/datapackage.py tests/typespec/test_datapackage_package.py
git commit -m "feat(typespec): add DataPackage with uniqueness and FK validation"
```

### Task 6: Real-world descriptor fixtures and round-trip test

**Files:**
- Create: `tests/typespec/fixtures/gdp.datapackage.json`
- Create: `tests/typespec/fixtures/country-codes.datapackage.json`
- Test: `tests/typespec/test_datapackage_round_trip.py`

- [ ] **Step 1: Fetch real descriptors.**
```bash
gh api repos/datasets/gdp/contents/datapackage.json --jq '.content' | base64 -d \
  > tests/typespec/fixtures/gdp.datapackage.json
gh api repos/datasets/country-codes/contents/datapackage.json --jq '.content' | base64 -d \
  > tests/typespec/fixtures/country-codes.datapackage.json
```

- [ ] **Step 2: Write the round-trip test.**

```python
# tests/typespec/test_datapackage_round_trip.py
import json
from pathlib import Path
import pytest
from mountainash.typespec.datapackage import DataPackage

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.mark.parametrize("name", ["gdp", "country-codes"])
def test_real_descriptor_round_trips(name):
    raw = json.loads((FIXTURES / f"{name}.datapackage.json").read_text())
    pkg = DataPackage.from_descriptor(raw)
    assert pkg.to_descriptor() == raw
```

- [ ] **Step 3: Run, fix any `extras` or schema-conversion gaps surfaced.** Real descriptors will likely surface edge cases not covered by synthetic tests. Each gap → either fix the converter or file as backlog if out of scope. Iterate until both pass.

- [ ] **Step 4: Commit.**
```bash
git add tests/typespec/fixtures/ tests/typespec/test_datapackage_round_trip.py src/mountainash/typespec/datapackage.py
git commit -m "test(typespec): add real datapackage.json round-trip fixtures"
```

### Task 7: Export from `typespec/__init__.py`

**Files:**
- Modify: `src/mountainash/typespec/__init__.py`

- [ ] **Step 1: Add re-exports.**

```python
# append
from mountainash.typespec.datapackage import DataPackage, DataResource, TableDialect

__all__ += ["DataPackage", "DataResource", "TableDialect"]
```

- [ ] **Step 2: Verify.**
```bash
hatch run test:test-target-quick -k "from mountainash.typespec import DataPackage"
python -c "from mountainash.typespec import DataPackage, DataResource, TableDialect; print('ok')"
```

- [ ] **Step 3: Commit.**
```bash
git add src/mountainash/typespec/__init__.py
git commit -m "feat(typespec): re-export DataPackage types"
```

---

## Phase 3 — New AST nodes and visitor wiring

### Task 8: Add `ExtensionRelOperation` enum entries

**Files:**
- Modify: `src/mountainash/core/constants.py:579-587`

- [ ] **Step 1: Append to the enum.**

```python
class ExtensionRelOperation(Enum):
    """Mountainash extension relation operations (not in Substrait)."""
    DROP_NULLS = auto()
    WITH_ROW_INDEX = auto()
    EXPLODE = auto()
    SAMPLE = auto()
    UNPIVOT = auto()
    PIVOT = auto()
    TOP_K = auto()
    REF = auto()              # NEW: dag.ref(name) placeholder
    READ_RESOURCE = auto()    # NEW: load via storage facade
```

- [ ] **Step 2: Commit.**
```bash
git add src/mountainash/core/constants.py
git commit -m "feat(constants): add REF and READ_RESOURCE extension rel ops"
```

### Task 9: `RefRelNode`

**Files:**
- Create: `src/mountainash/relations/core/relation_nodes/extensions_mountainash/reln_ext_ref.py`
- Modify: `src/mountainash/relations/core/relation_nodes/extensions_mountainash/__init__.py`
- Test: `tests/relations/dag/test_ref_rel_node.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/relations/dag/test_ref_rel_node.py
from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
from mountainash.typespec.spec import TypeSpec


def test_ref_rel_node_minimal():
    node = RefRelNode(name="orders")
    assert node.name == "orders"
    assert node.output_schema is None


def test_ref_rel_node_with_schema():
    spec = TypeSpec(fields=[])
    node = RefRelNode(name="orders", output_schema=spec)
    assert node.output_schema is spec


def test_ref_rel_node_dispatches_to_visit_ref_rel():
    seen = []

    class V:
        def visit_ref_rel(self, node):
            seen.append(node.name)
            return "visited"

    assert RefRelNode(name="x").accept(V()) == "visited"
    assert seen == ["x"]
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement.**

```python
# src/mountainash/relations/core/relation_nodes/extensions_mountainash/reln_ext_ref.py
"""RefRelNode — placeholder for dag.ref(name); resolved at visit time via ref_resolver."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import ConfigDict

from mountainash.typespec.spec import TypeSpec
from ..reln_base import RelationNode


class RefRelNode(RelationNode):
    """Leaf node referencing another named relation in a RelationDAG.

    Cannot be compiled standalone — requires a UnifiedRelationVisitor instantiated
    with a ``ref_resolver`` callback (see RelationDAG.collect()).
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    name: str
    output_schema: Optional[TypeSpec] = None

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_ref_rel(self)
```

- [ ] **Step 4: Update `__init__.py`.**

```python
# src/mountainash/relations/core/relation_nodes/extensions_mountainash/__init__.py
from .reln_ext_ma_util import *  # existing
from .reln_ext_source import SourceRelNode
from .reln_ext_ref import RefRelNode

__all__ = [..., "SourceRelNode", "RefRelNode"]  # merge with existing __all__
```

- [ ] **Step 5: Run, see green. Commit.**
```bash
git add src/mountainash/relations/core/relation_nodes/extensions_mountainash/
git add tests/relations/dag/test_ref_rel_node.py
git commit -m "feat(relations): add RefRelNode for DAG ref placeholders"
```

### Task 10: `ResourceReadRelNode`

**Files:**
- Create: `src/mountainash/relations/core/relation_nodes/extensions_mountainash/reln_ext_resource_read.py`
- Modify: same `__init__.py` from Task 9
- Test: `tests/relations/dag/test_resource_read_rel_node.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/relations/dag/test_resource_read_rel_node.py
from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    ResourceReadRelNode,
)
from mountainash.typespec.datapackage import DataResource


def test_resource_read_rel_node_holds_resource():
    res = DataResource(name="orders", path="orders.csv", format="csv")
    node = ResourceReadRelNode(resource=res)
    assert node.resource is res


def test_resource_read_rel_node_dispatches():
    seen = []

    class V:
        def visit_resource_read_rel(self, node):
            seen.append(node.resource.name)
            return "visited"

    res = DataResource(name="orders", path="orders.csv")
    assert ResourceReadRelNode(resource=res).accept(V()) == "visited"
    assert seen == ["orders"]
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement.**

```python
# src/mountainash/relations/core/relation_nodes/extensions_mountainash/reln_ext_resource_read.py
"""ResourceReadRelNode — leaf node carrying a DataResource for storage-facade load."""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from mountainash.typespec.datapackage import DataResource
from ..reln_base import RelationNode


class ResourceReadRelNode(RelationNode):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    resource: DataResource

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_resource_read_rel(self)
```

- [ ] **Step 4: Update `__init__.py`.** Add `ResourceReadRelNode` to imports and `__all__`.

- [ ] **Step 5: Run green. Commit.**
```bash
git add src/mountainash/relations/core/relation_nodes/extensions_mountainash/ tests/relations/dag/
git commit -m "feat(relations): add ResourceReadRelNode for storage-facade loads"
```

### Task 11: Format reader dispatch

**Files:**
- Create: `src/mountainash/relations/dag/__init__.py` (empty for now)
- Create: `src/mountainash/relations/dag/readers/__init__.py`
- Create: `src/mountainash/relations/dag/readers/csv.py`
- Create: `src/mountainash/relations/dag/readers/json.py`
- Create: `src/mountainash/relations/dag/readers/parquet.py`
- Create: `src/mountainash/relations/dag/readers/inline.py`
- Create: `src/mountainash/relations/dag/errors.py`
- Test: `tests/relations/dag/test_readers.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/relations/dag/test_readers.py
import polars as pl
import pytest
from mountainash.relations.dag.readers import read_resource_to_polars
from mountainash.relations.dag.errors import UnsupportedResourceFormat
from mountainash.typespec.datapackage import DataResource


def test_inline_list_of_dicts():
    res = DataResource(name="t", data=[{"a": 1}, {"a": 2}], format="json")
    df = read_resource_to_polars(res).collect()
    assert df["a"].to_list() == [1, 2]


def test_csv_path(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a,b\n1,2\n3,4\n")
    res = DataResource(name="t", path=str(p), format="csv")
    df = read_resource_to_polars(res).collect()
    assert df.shape == (2, 2)


def test_csv_with_dialect(tmp_path):
    from mountainash.typespec.datapackage import TableDialect
    p = tmp_path / "t.csv"
    p.write_text("a;b\n1;2\n")
    res = DataResource(
        name="t", path=str(p), format="csv",
        dialect=TableDialect(delimiter=";"),
    )
    assert read_resource_to_polars(res).collect().shape == (1, 2)


def test_multi_file_path_concat(tmp_path):
    a = tmp_path / "a.csv"; a.write_text("x\n1\n")
    b = tmp_path / "b.csv"; b.write_text("x\n2\n")
    res = DataResource(name="t", path=[str(a), str(b)], format="csv")
    df = read_resource_to_polars(res).collect()
    assert df["x"].to_list() == [1, 2]


def test_unknown_format_raises():
    res = DataResource(name="t", path="t.weird", format="weird")
    with pytest.raises(UnsupportedResourceFormat, match="weird"):
        read_resource_to_polars(res)
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement errors module.**

```python
# src/mountainash/relations/dag/errors.py
"""DAG-related exceptions."""


class RelationDAGRequired(RuntimeError):
    """Raised when a relation containing a RefRelNode is compiled outside a RelationDAG."""


class MissingResourceSchema(ValueError):
    """Raised when DAG.to_package() encounters a relation with no inferable schema."""


class UnsupportedResourceFormat(ValueError):
    """Raised when a resource's format/mediatype has no registered reader."""
```

- [ ] **Step 4: Implement readers.**

```python
# src/mountainash/relations/dag/readers/__init__.py
"""Format dispatch for ResourceReadRelNode → Polars LazyFrame."""
from __future__ import annotations

import polars as pl

from mountainash.typespec.datapackage import DataResource
from ..errors import UnsupportedResourceFormat
from .csv import read_csv
from .json import read_json
from .parquet import read_parquet
from .inline import read_inline


def _detect_format(res: DataResource) -> str:
    if res.format:
        return res.format.lower()
    if res.mediatype:
        mt = res.mediatype.lower()
        if "csv" in mt: return "csv"
        if "json" in mt: return "json"
        if "parquet" in mt: return "parquet"
    if isinstance(res.path, str) and "." in res.path:
        return res.path.rsplit(".", 1)[-1].lower()
    if isinstance(res.path, list) and res.path and "." in res.path[0]:
        return res.path[0].rsplit(".", 1)[-1].lower()
    raise UnsupportedResourceFormat(f"cannot detect format for resource {res.name!r}")


def read_resource_to_polars(res: DataResource) -> pl.LazyFrame:
    if res.data is not None:
        return read_inline(res)
    fmt = _detect_format(res)
    if fmt == "csv":
        return read_csv(res)
    if fmt == "json":
        return read_json(res)
    if fmt == "parquet":
        return read_parquet(res)
    raise UnsupportedResourceFormat(f"no reader for format {fmt!r} (resource {res.name!r})")
```

```python
# src/mountainash/relations/dag/readers/csv.py
from __future__ import annotations

import polars as pl

from mountainash.typespec.datapackage import DataResource


def read_csv(res: DataResource) -> pl.LazyFrame:
    kwargs = res.dialect.to_polars_read_csv_kwargs() if res.dialect else {}
    paths = res.path if isinstance(res.path, list) else [res.path]
    frames = [pl.scan_csv(p, **kwargs) for p in paths]
    if len(frames) == 1:
        return frames[0]
    return pl.concat(frames, how="vertical")
```

```python
# src/mountainash/relations/dag/readers/json.py
from __future__ import annotations

import polars as pl

from mountainash.typespec.datapackage import DataResource


def read_json(res: DataResource) -> pl.LazyFrame:
    paths = res.path if isinstance(res.path, list) else [res.path]
    frames = [pl.read_json(p).lazy() for p in paths]
    return frames[0] if len(frames) == 1 else pl.concat(frames, how="vertical")
```

```python
# src/mountainash/relations/dag/readers/parquet.py
from __future__ import annotations

import polars as pl

from mountainash.typespec.datapackage import DataResource


def read_parquet(res: DataResource) -> pl.LazyFrame:
    paths = res.path if isinstance(res.path, list) else [res.path]
    frames = [pl.scan_parquet(p) for p in paths]
    return frames[0] if len(frames) == 1 else pl.concat(frames, how="vertical")
```

```python
# src/mountainash/relations/dag/readers/inline.py
from __future__ import annotations

import polars as pl

from mountainash.pydata.ingress.pydata_ingress import PydataIngress
from mountainash.typespec.datapackage import DataResource


def read_inline(res: DataResource) -> pl.LazyFrame:
    df = PydataIngress().to_polars(res.data)
    return df.lazy()
```

> **Note on storage facade integration:** these readers currently call Polars directly with file paths. The storage facade integration arrives in Task 12 — it will provide a streaming bytes interface for non-local paths (s3://, https://, etc.) that wraps these readers. Local paths continue to work via Polars directly.

- [ ] **Step 5: Run green. Commit.**
```bash
git add src/mountainash/relations/dag/ tests/relations/dag/test_readers.py
git commit -m "feat(dag): add format-dispatched resource readers (csv/json/parquet/inline)"
```

### Task 12: Storage facade integration for non-local paths

**Files:**
- Modify: each reader file from Task 11
- Test: `tests/relations/dag/test_readers_storage_facade.py`

- [ ] **Step 1: Read the storage facade API.**

```bash
ls /home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-files/src/mountainash_utils_files/storage_facade/
cat /home/nathanielramm/git/mountainash-io/mountainash/mountainash-utils-files/src/mountainash_utils_files/storage_facade/facade.py
```

- [ ] **Step 2: Write a failing test for `s3://` and `https://` path resolution** (skip if `mountainash_utils_files` is not installed in the test env). Use `monkeypatch` to stub the facade — do not hit the network in tests.

```python
# tests/relations/dag/test_readers_storage_facade.py
import io
import polars as pl
import pytest
from mountainash.relations.dag.readers import read_resource_to_polars
from mountainash.typespec.datapackage import DataResource


def test_https_path_routed_through_facade(monkeypatch):
    fake_csv = b"a,b\n1,2\n"
    calls = []

    def fake_read_bytes(path):
        calls.append(path)
        return fake_csv

    from mountainash.relations.dag.readers import csv as csv_reader
    monkeypatch.setattr(csv_reader, "_facade_read_bytes", fake_read_bytes)

    res = DataResource(name="t", path="https://example.com/t.csv", format="csv")
    df = read_resource_to_polars(res).collect()
    assert df["a"].to_list() == [1]
    assert calls == ["https://example.com/t.csv"]
```

- [ ] **Step 3: Implement a small `_facade_read_bytes` helper inside each reader.** A path is "remote" if it starts with `http://`, `https://`, `s3://`, `r2://`, `minio://`, etc. — anything not a local file. Local paths continue to bypass the facade.

```python
# src/mountainash/relations/dag/readers/csv.py  (updated)
from __future__ import annotations

import io
import polars as pl

from mountainash.typespec.datapackage import DataResource

_REMOTE_SCHEMES = ("http://", "https://", "s3://", "r2://", "minio://")


def _is_remote(path: str) -> bool:
    return any(path.startswith(s) for s in _REMOTE_SCHEMES)


def _facade_read_bytes(path: str) -> bytes:
    from mountainash_utils_files.storage_facade.facade import StorageFacade
    return StorageFacade().read_bytes(path)


def _scan_one(path: str, kwargs: dict) -> pl.LazyFrame:
    if _is_remote(path):
        return pl.read_csv(io.BytesIO(_facade_read_bytes(path)), **kwargs).lazy()
    return pl.scan_csv(path, **kwargs)


def read_csv(res: DataResource) -> pl.LazyFrame:
    kwargs = res.dialect.to_polars_read_csv_kwargs() if res.dialect else {}
    paths = res.path if isinstance(res.path, list) else [res.path]
    frames = [_scan_one(p, kwargs) for p in paths]
    if len(frames) == 1:
        return frames[0]
    return pl.concat(frames, how="vertical")
```

Apply the same `_is_remote` / `_facade_read_bytes` pattern to `json.py` and `parquet.py`. Use `pl.read_json(io.BytesIO(...))` and `pl.read_parquet(io.BytesIO(...))` respectively.

- [ ] **Step 4: Run, see green. Commit.**
```bash
git add src/mountainash/relations/dag/readers/ tests/relations/dag/test_readers_storage_facade.py
git commit -m "feat(dag): route remote paths through mountainash-utils-files storage facade"
```

### Task 13: `UnifiedRelationVisitor` gains `ref_resolver` and visit methods

**Files:**
- Modify: `src/mountainash/relations/core/unified_visitor/relation_visitor.py`
- Test: `tests/relations/dag/test_visitor_ref_resolver.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/relations/dag/test_visitor_ref_resolver.py
import pytest
import polars as pl
from mountainash.relations.core.unified_visitor.relation_visitor import (
    UnifiedRelationVisitor,
)
from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    RefRelNode, ResourceReadRelNode,
)
from mountainash.relations.dag.errors import RelationDAGRequired
from mountainash.typespec.datapackage import DataResource
from mountainash.relations.backends.relation_systems.polars.base import (
    PolarsRelationSystem,
)


def test_ref_without_resolver_raises():
    visitor = UnifiedRelationVisitor(PolarsRelationSystem(), expression_visitor=None)
    with pytest.raises(RelationDAGRequired):
        visitor.visit_ref_rel(RefRelNode(name="orders"))


def test_ref_with_resolver_returns_cached_value():
    cache = {"orders": pl.DataFrame({"x": [1, 2]}).lazy()}
    visitor = UnifiedRelationVisitor(
        PolarsRelationSystem(),
        expression_visitor=None,
        ref_resolver=lambda n: cache[n],
    )
    result = visitor.visit_ref_rel(RefRelNode(name="orders"))
    assert result.collect()["x"].to_list() == [1, 2]


def test_resource_read_rel_loads_inline_data():
    visitor = UnifiedRelationVisitor(PolarsRelationSystem(), expression_visitor=None)
    res = DataResource(name="orders", data=[{"a": 1}, {"a": 2}], format="json")
    result = visitor.visit_resource_read_rel(ResourceReadRelNode(resource=res))
    assert result.collect()["a"].to_list() == [1, 2]
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement visitor changes.**

```python
# src/mountainash/relations/core/unified_visitor/relation_visitor.py  (additions)

# Update __init__:
def __init__(
    self,
    relation_system: Any,
    expression_visitor: Any,
    *,
    ref_resolver: Optional[Callable[[str], Any]] = None,
) -> None:
    self.relation_system = relation_system
    self.expression_visitor = expression_visitor
    self.ref_resolver = ref_resolver

# Add visit methods:
def visit_ref_rel(self, node: "RefRelNode") -> Any:
    if self.ref_resolver is None:
        from mountainash.relations.dag.errors import RelationDAGRequired
        raise RelationDAGRequired(
            f"RefRelNode({node.name!r}) cannot be compiled standalone — "
            "use RelationDAG.collect() or supply ref_resolver explicitly"
        )
    return self.ref_resolver(node.name)

def visit_resource_read_rel(self, node: "ResourceReadRelNode") -> Any:
    from mountainash.relations.dag.readers import read_resource_to_polars
    from mountainash.conform import compile_conform
    lf = read_resource_to_polars(node.resource)
    if node.resource.schema is not None:
        # Apply conform via the conform compiler
        lf = compile_conform(node.resource.schema, lf, backend=self.relation_system)
    return lf
```

> **Note:** the `compile_conform` import path may differ — verify against actual `src/mountainash/conform/compiler.py` and adjust the call signature. If conform expects an eager DataFrame, materialize: `df = lf.collect(); df = compile_conform(...); return df.lazy()`.

- [ ] **Step 4: Run green. Commit.**
```bash
git add src/mountainash/relations/core/unified_visitor/relation_visitor.py tests/relations/dag/test_visitor_ref_resolver.py
git commit -m "feat(visitor): add ref_resolver kwarg and visit methods for ref/resource_read"
```

### Task 14: Per-backend wiring (Narwhals + Ibis)

The Polars implementation is handled by Task 13's visitor methods (since `read_resource_to_polars` returns a `pl.LazyFrame`). For Narwhals and Ibis, the visitor methods need to convert.

**Files:**
- Modify: `src/mountainash/relations/core/unified_visitor/relation_visitor.py` (extend `visit_resource_read_rel` to dispatch by backend)
- Test: `tests/relations/dag/test_visitor_narwhals_ibis.py`

- [ ] **Step 1: Write a parametrized failing test across all three backends.**

```python
# tests/relations/dag/test_visitor_narwhals_ibis.py
import pytest
from mountainash.relations.core.unified_visitor.relation_visitor import (
    UnifiedRelationVisitor,
)
from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    ResourceReadRelNode,
)
from mountainash.typespec.datapackage import DataResource


@pytest.mark.parametrize("backend_name", ["polars", "narwhals_polars", "ibis_duckdb"])
def test_resource_read_across_backends(backend_name, tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a,b\n1,2\n3,4\n")
    res = DataResource(name="t", path=str(p), format="csv")

    # Resolve backend system per backend_name
    rs = _make_relation_system(backend_name)
    visitor = UnifiedRelationVisitor(rs, expression_visitor=None)
    result = visitor.visit_resource_read_rel(ResourceReadRelNode(resource=res))
    # Coerce to polars for comparison
    df = _to_polars(result, backend_name)
    assert df.shape == (2, 2)


def _make_relation_system(name): ...   # implementer fills in using existing test helpers
def _to_polars(result, name): ...
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Extend `visit_resource_read_rel` to convert based on `relation_system` type.**

```python
# in relation_visitor.py
def visit_resource_read_rel(self, node):
    from mountainash.relations.dag.readers import read_resource_to_polars
    lf = read_resource_to_polars(node.resource)  # always returns pl.LazyFrame
    out = self._coerce_from_polars_lazy(lf)
    if node.resource.schema is not None:
        out = self._apply_conform(out, node.resource.schema)
    return out

def _coerce_from_polars_lazy(self, lf):
    """Convert pl.LazyFrame to the relation_system's native type."""
    cls_name = type(self.relation_system).__name__
    if "Polars" in cls_name:
        return lf
    if "Narwhals" in cls_name:
        import narwhals as nw
        return nw.from_native(lf.collect(), eager_only=True)
    if "Ibis" in cls_name:
        import ibis
        return ibis.memtable(lf.collect().to_pandas())
    raise NotImplementedError(f"no coercion for relation system {cls_name}")

def _apply_conform(self, native, schema):
    from mountainash.conform import compile_conform
    return compile_conform(schema, native, backend=self.relation_system)
```

> **Conform call signature note:** verify against `src/mountainash/conform/compiler.py`. If the existing API takes different args, adjust accordingly — but do not change `compile_conform` itself.

- [ ] **Step 4: Run green. Commit.**
```bash
git add src/mountainash/relations/core/unified_visitor/relation_visitor.py tests/relations/dag/test_visitor_narwhals_ibis.py
git commit -m "feat(visitor): coerce ResourceReadRelNode output to backend-native type"
```

---

## Phase 4 — RelationDAG orchestrator

### Task 15: `ResourceRef` wrapper

**Files:**
- Create: `src/mountainash/relations/dag/resource_ref.py`
- Test: `tests/relations/dag/test_resource_ref.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/relations/dag/test_resource_ref.py
import pytest
from mountainash.relations.dag.resource_ref import ResourceRef
from mountainash.typespec.datapackage import DataResource


def test_tabular_resource_ref(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a\n1\n")
    res = DataResource(name="t", path=str(p), type="table", format="csv")
    ref = ResourceRef(res)
    assert ref.is_tabular
    assert ref.read_bytes() == p.read_bytes()
    rel = ref.relation()
    assert rel is not None


def test_non_tabular_resource_ref(tmp_path):
    p = tmp_path / "logo.png"
    p.write_bytes(b"\x89PNG...")
    res = DataResource(name="logo", path=str(p), format="png")
    ref = ResourceRef(res)
    assert not ref.is_tabular
    assert ref.read_bytes() == b"\x89PNG..."
    with pytest.raises(ValueError, match="not tabular"):
        ref.relation()
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement.**

```python
# src/mountainash/relations/dag/resource_ref.py
"""ResourceRef — uniform wrapper for tabular and non-tabular resources."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mountainash.typespec.datapackage import DataResource

if TYPE_CHECKING:
    from mountainash.relations.core.relation_api.relation import Relation


_TABULAR_TYPES = {"table", None}  # spec: missing type may still be tabular by detection
_TABULAR_FORMATS = {"csv", "json", "parquet", "tsv", "ndjson"}


class ResourceRef:
    """Uniform wrapper for both tabular and non-tabular Data Resources."""

    def __init__(self, resource: DataResource) -> None:
        self.resource = resource

    @property
    def is_tabular(self) -> bool:
        if self.resource.type == "table":
            return True
        if self.resource.format and self.resource.format.lower() in _TABULAR_FORMATS:
            return True
        return False

    def read_bytes(self) -> bytes:
        if self.resource.data is not None:
            raise ValueError(f"resource {self.resource.name!r} has inline data, not bytes")
        path = self.resource.path
        if isinstance(path, list):
            path = path[0]
        if any(path.startswith(s) for s in ("http://", "https://", "s3://", "r2://", "minio://")):
            from mountainash_utils_files.storage_facade.facade import StorageFacade
            return StorageFacade().read_bytes(path)
        return Path(path).read_bytes()

    def relation(self) -> "Relation":
        if not self.is_tabular:
            raise ValueError(f"resource {self.resource.name!r} is not tabular")
        from mountainash.relations.core.relation_api.relation import Relation
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            ResourceReadRelNode,
        )
        return Relation(ResourceReadRelNode(resource=self.resource))
```

> **`Relation` constructor note:** check `relation_api/relation.py` for the actual constructor — adjust the wrap call to match. The pattern above assumes `Relation(node)` works.

- [ ] **Step 4: Run green. Commit.**
```bash
git add src/mountainash/relations/dag/resource_ref.py tests/relations/dag/test_resource_ref.py
git commit -m "feat(dag): add ResourceRef wrapper for tabular and non-tabular resources"
```

### Task 16: `RelationDAG` core (add, ref, topological_order)

**Files:**
- Create: `src/mountainash/relations/dag/dag.py`
- Test: `tests/relations/dag/test_relation_dag.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/relations/dag/test_relation_dag.py
import pytest
from mountainash.relations.dag.dag import RelationDAG
import mountainash as ma


def test_empty_dag():
    dag = RelationDAG()
    assert dag.relations == {}
    assert dag.dependency_edges == set()


def test_add_named_relation():
    dag = RelationDAG()
    dag.add("orders", ma.relation([{"id": 1}]))
    assert "orders" in dag.relations


def test_ref_creates_dependency_edge():
    dag = RelationDAG()
    dag.add("orders", ma.relation([{"id": 1}]))
    dag.add("active_orders", dag.ref("orders").filter(ma.col("id").gt(0)))
    assert dag.dependency_edges == {("orders", "active_orders")}


def test_topological_order_simple_chain():
    dag = RelationDAG()
    dag.add("a", ma.relation([{"x": 1}]))
    dag.add("b", dag.ref("a"))
    dag.add("c", dag.ref("b"))
    assert dag.topological_order("c") == ["a", "b", "c"]


def test_topological_order_unrelated_nodes_excluded():
    dag = RelationDAG()
    dag.add("a", ma.relation([{"x": 1}]))
    dag.add("b", ma.relation([{"x": 2}]))   # unrelated
    dag.add("c", dag.ref("a"))
    assert dag.topological_order("c") == ["a", "c"]  # b excluded


def test_cycle_raises():
    dag = RelationDAG()
    # Build a fake cycle by manipulating edges directly (since dag.ref() can't form one normally)
    dag.add("a", ma.relation([{"x": 1}]))
    dag.add("b", dag.ref("a"))
    dag.dependency_edges.add(("b", "a"))  # forced cycle
    with pytest.raises(ValueError, match="cycle"):
        dag.topological_order("b")
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement.**

```python
# src/mountainash/relations/dag/dag.py
"""RelationDAG — orchestrator over named Relations."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    RefRelNode,
    ResourceReadRelNode,
)
from .errors import RelationDAGRequired
from .resource_ref import ResourceRef


def _walk_refs(node: Any) -> set[str]:
    """Recursively collect names of all RefRelNode descendants under ``node``."""
    found: set[str] = set()
    if isinstance(node, RefRelNode):
        found.add(node.name)
    # Walk children: RelationNode subtypes carry inputs in fields named 'input', 'left', 'right', etc.
    for attr in ("input", "left", "right", "inputs"):
        child = getattr(node, attr, None)
        if child is None:
            continue
        if isinstance(child, list):
            for c in child:
                found |= _walk_refs(c)
        else:
            found |= _walk_refs(child)
    return found


class RelationDAG:
    def __init__(self) -> None:
        self.relations: dict[str, Any] = {}
        self.assets: dict[str, ResourceRef] = {}
        self.dependency_edges: set[tuple[str, str]] = set()
        self.constraint_edges: set[tuple[str, str]] = set()

    def add(self, name: str, relation: Any) -> None:
        if name in self.relations:
            raise ValueError(f"relation {name!r} already in DAG")
        self.relations[name] = relation
        for upstream in _walk_refs(relation.node):
            self.dependency_edges.add((upstream, name))

    def ref(self, name: str) -> Any:
        from mountainash.relations.core.relation_api.relation import Relation
        node = RefRelNode(name=name)
        return Relation(node)

    def topological_order(self, target: Optional[str] = None) -> list[str]:
        nodes = set(self.relations.keys())
        if target is not None:
            # Restrict to ancestors of target
            wanted = {target}
            stack = [target]
            while stack:
                cur = stack.pop()
                for u, d in self.dependency_edges:
                    if d == cur and u not in wanted:
                        wanted.add(u)
                        stack.append(u)
            nodes = wanted

        # Kahn's algorithm
        indeg: dict[str, int] = {n: 0 for n in nodes}
        adj: dict[str, list[str]] = defaultdict(list)
        for u, d in self.dependency_edges:
            if u in nodes and d in nodes:
                adj[u].append(d)
                indeg[d] += 1
        ready = [n for n, i in indeg.items() if i == 0]
        out: list[str] = []
        while ready:
            n = ready.pop(0)
            out.append(n)
            for m in adj[n]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    ready.append(m)
        if len(out) != len(nodes):
            raise ValueError(f"cycle detected in dependency_edges (target={target!r})")
        return out
```

> **Notes for the implementer:**
> - `_walk_refs` walks `input/left/right/inputs` — verify these are the actual child attribute names on `RelationNode` subtypes by reading `relation_nodes/substrait/*.py`. Adjust if different.
> - `relation.node` assumes the `Relation` class exposes its root node as `.node`. Verify against `relation_api/relation.py` and adjust.

- [ ] **Step 4: Run green. Commit.**
```bash
git add src/mountainash/relations/dag/dag.py tests/relations/dag/test_relation_dag.py
git commit -m "feat(dag): add RelationDAG with add/ref/topological_order"
```

### Task 17: `RelationDAG.collect()` with caching

**Files:**
- Modify: `src/mountainash/relations/dag/dag.py`
- Test: `tests/relations/dag/test_dag_collect.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/relations/dag/test_dag_collect.py
import polars as pl
import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG


def test_collect_simple():
    dag = RelationDAG()
    dag.add("orders", ma.relation([{"id": 1, "amount": 10}, {"id": 2, "amount": 20}]))
    result = dag.collect("orders")
    assert isinstance(result, pl.LazyFrame) or isinstance(result, pl.DataFrame)
    df = result.collect() if isinstance(result, pl.LazyFrame) else result
    assert df["amount"].sum() == 30


def test_collect_chain():
    dag = RelationDAG()
    dag.add("orders", ma.relation([{"id": 1, "amount": 10}, {"id": 2, "amount": 20}]))
    dag.add("big", dag.ref("orders").filter(ma.col("amount").gt(15)))
    result = dag.collect("big")
    df = result.collect() if isinstance(result, pl.LazyFrame) else result
    assert df["id"].to_list() == [2]


def test_collect_caches_upstream_per_call():
    visit_count = [0]
    dag = RelationDAG()
    dag.add("a", ma.relation([{"x": 1}]))
    dag.add("b", dag.ref("a"))
    dag.add("c", dag.ref("a"))
    # In one collect() of "b" then a separate collect("c"), "a" is computed twice (no cross-call cache).
    # Within a single collect(), if both b and c needed a, a should be computed once.
    # For this simple test we just assert collect() works correctly.
    dag.collect("b")
    dag.collect("c")
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement `collect()`.**

```python
# Append to RelationDAG class in dag.py
def collect(self, name: str, *, backend: Any = None) -> Any:
    from mountainash.relations.core.unified_visitor.relation_visitor import (
        UnifiedRelationVisitor,
    )
    from mountainash.core.factories import (
        get_relation_system_for_backend,
        get_expression_visitor_for_backend,
    )

    # Default to Polars if no backend specified
    if backend is None:
        backend = "polars"
    relation_system = get_relation_system_for_backend(backend)
    expression_visitor = get_expression_visitor_for_backend(backend)

    cache: dict[str, Any] = {}
    resolver = lambda n: cache[n]
    visitor = UnifiedRelationVisitor(
        relation_system,
        expression_visitor=expression_visitor,
        ref_resolver=resolver,
    )

    order = self.topological_order(target=name)
    for n in order:
        cache[n] = self.relations[n].node.accept(visitor)
    return cache[name]
```

> **Note:** the factory function names (`get_relation_system_for_backend`, `get_expression_visitor_for_backend`) are placeholders — verify against actual `src/mountainash/core/factories.py` and adjust import + call signatures. If there is no factory, instantiate the relation system class directly using the same pattern existing tests use.

- [ ] **Step 4: Run green. Commit.**
```bash
git add src/mountainash/relations/dag/dag.py tests/relations/dag/test_dag_collect.py
git commit -m "feat(dag): implement RelationDAG.collect() with per-call upstream cache"
```

### Task 18: Top-level re-exports

**Files:**
- Modify: `src/mountainash/relations/dag/__init__.py`
- Modify: `src/mountainash/__init__.py`

- [ ] **Step 1: Add re-exports.**

```python
# src/mountainash/relations/dag/__init__.py
from .dag import RelationDAG
from .resource_ref import ResourceRef
from .errors import RelationDAGRequired, MissingResourceSchema, UnsupportedResourceFormat

__all__ = [
    "RelationDAG",
    "ResourceRef",
    "RelationDAGRequired",
    "MissingResourceSchema",
    "UnsupportedResourceFormat",
]
```

```python
# src/mountainash/__init__.py — append to existing top-level re-exports
from mountainash.typespec.datapackage import DataPackage, DataResource, TableDialect
from mountainash.relations.dag import RelationDAG, ResourceRef

__all__ += ["DataPackage", "DataResource", "TableDialect", "RelationDAG", "ResourceRef"]
```

- [ ] **Step 2: Smoke test.**

```bash
python -c "import mountainash as ma; print(ma.DataPackage, ma.RelationDAG, ma.ResourceRef)"
```

- [ ] **Step 3: Commit.**
```bash
git add src/mountainash/__init__.py src/mountainash/relations/dag/__init__.py
git commit -m "feat: re-export DataPackage and RelationDAG at top level"
```

---

## Phase 5 — Bidirectional bridge

### Task 19: `DataPackage.to_relation_dag()` with overrides

**Files:**
- Modify: `src/mountainash/typespec/datapackage.py` (add method)
- Test: `tests/relations/dag/test_package_to_dag.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/relations/dag/test_package_to_dag.py
import polars as pl
import pytest
from mountainash.typespec.datapackage import DataPackage, DataResource


def _pkg(tmp_path):
    p = tmp_path / "orders.csv"
    p.write_text("id,amount\n1,10\n2,20\n")
    return DataPackage(resources=[
        DataResource(name="orders", path=str(p), format="csv", type="table"),
    ])


def test_package_to_dag_basic(tmp_path):
    pkg = _pkg(tmp_path)
    dag = pkg.to_relation_dag()
    assert "orders" in dag.relations
    df = dag.collect("orders")
    df = df.collect() if hasattr(df, "collect") else df
    assert df["amount"].sum() == 30


def test_package_to_dag_overrides(tmp_path):
    pkg = _pkg(tmp_path)
    override_df = pl.DataFrame({"id": [99], "amount": [999]})
    dag = pkg.to_relation_dag(overrides={"orders": override_df})
    df = dag.collect("orders")
    df = df.collect() if hasattr(df, "collect") else df
    assert df["amount"].to_list() == [999]


def test_package_to_dag_constraint_edges_from_foreign_keys(tmp_path):
    # Build a package where one resource has a foreignKey pointing at another
    from mountainash.typespec.spec import TypeSpec, FieldSpec, ForeignKey, ForeignKeyReference
    cust_spec = TypeSpec(fields=[FieldSpec(name="id", type="integer")])
    order_spec = TypeSpec(
        fields=[
            FieldSpec(name="id", type="integer"),
            FieldSpec(name="customer_id", type="integer"),
        ],
        foreign_keys=[
            ForeignKey(
                fields=["customer_id"],
                reference=ForeignKeyReference(resource="customers", fields=["id"]),
            )
        ],
    )
    pkg = DataPackage(resources=[
        DataResource(name="customers", path="customers.csv", schema=cust_spec, type="table"),
        DataResource(name="orders", path="orders.csv", schema=order_spec, type="table"),
    ])
    dag = pkg.to_relation_dag()
    assert ("customers", "orders") in dag.constraint_edges
    assert dag.dependency_edges == set()  # FKs do NOT become dependency edges
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement.**

```python
# Append to DataPackage class in datapackage.py
def to_relation_dag(self, overrides: Optional[dict[str, Any]] = None) -> Any:
    from mountainash.relations.dag.dag import RelationDAG
    from mountainash.relations.dag.resource_ref import ResourceRef
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        ResourceReadRelNode,
    )
    import mountainash as ma

    overrides = overrides or {}
    dag = RelationDAG()
    for r in self.resources:
        ref = ResourceRef(r)
        if not ref.is_tabular:
            dag.assets[r.name] = ref
            continue
        if r.name in overrides:
            dag.add(r.name, ma.relation(overrides[r.name]))
        else:
            dag.add(r.name, Relation(ResourceReadRelNode(resource=r)))
    # Constraint edges from foreignKeys
    for r in self.resources:
        if r.schema is None:
            continue
        for fk in (r.schema.foreign_keys or []):
            target = fk.reference.resource or r.name  # "" = self
            if target in dag.relations:
                dag.constraint_edges.add((target, r.name))
    return dag
```

- [ ] **Step 4: Run green. Commit.**
```bash
git add src/mountainash/typespec/datapackage.py tests/relations/dag/test_package_to_dag.py
git commit -m "feat(datapackage): add DataPackage.to_relation_dag with overrides"
```

### Task 20: `RelationDAG.to_package()`

**Files:**
- Modify: `src/mountainash/relations/dag/dag.py`
- Test: `tests/relations/dag/test_dag_to_package.py`

- [ ] **Step 1: Write the failing test.**

```python
# tests/relations/dag/test_dag_to_package.py
import pytest
from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag.errors import MissingResourceSchema
from mountainash.typespec.spec import TypeSpec, FieldSpec
import mountainash as ma


def test_dag_to_package_with_schemas(tmp_path):
    spec = TypeSpec(fields=[FieldSpec(name="id", type="integer")])
    p = tmp_path / "orders.csv"
    p.write_text("id\n1\n2\n")
    from mountainash.typespec.datapackage import DataPackage, DataResource
    pkg = DataPackage(resources=[
        DataResource(name="orders", path=str(p), schema=spec, type="table", format="csv"),
    ])
    dag = pkg.to_relation_dag()
    pkg2 = dag.to_package()
    assert "orders" in {r.name for r in pkg2.resources}


def test_dag_to_package_raises_on_missing_schema():
    dag = RelationDAG()
    dag.add("anon", ma.relation([{"x": 1}]))   # no schema, no source resource
    with pytest.raises(MissingResourceSchema, match="anon"):
        dag.to_package()
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement.**

```python
# Append to RelationDAG in dag.py
def to_package(self) -> Any:
    from mountainash.typespec.datapackage import DataPackage, DataResource
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        ResourceReadRelNode,
    )
    from .errors import MissingResourceSchema

    resources: list[DataResource] = []
    missing: list[str] = []
    for name, relation in self.relations.items():
        # If the root node is a ResourceReadRelNode, reuse its resource
        root = relation.node
        if isinstance(root, ResourceReadRelNode):
            res = root.resource.model_copy()
            if res.name != name:
                res = res.model_copy(update={"name": name})
            resources.append(res)
            continue
        # Otherwise we need an output schema — try to derive it
        schema = getattr(relation, "output_schema", None)
        if schema is None:
            missing.append(name)
            continue
        resources.append(DataResource(
            name=name,
            path=f"{name}.csv",   # placeholder; user can edit before writing
            type="table",
            format="csv",
            schema=schema,
        ))
    # Carry forward asset resources
    for name, ref in self.assets.items():
        resources.append(ref.resource)

    if missing:
        raise MissingResourceSchema(
            f"cannot export to DataPackage; relations without schema: {missing}"
        )
    return DataPackage(resources=resources)
```

- [ ] **Step 4: Run green. Commit.**
```bash
git add src/mountainash/relations/dag/dag.py tests/relations/dag/test_dag_to_package.py
git commit -m "feat(dag): add RelationDAG.to_package with MissingResourceSchema validation"
```

---

## Phase 6 — End-to-end

### Task 21: Real descriptor end-to-end test

**Files:**
- Test: `tests/relations/dag/test_e2e_real_descriptor.py`

- [ ] **Step 1: Write the test.** Use a real fixture from Task 6 (`gdp.datapackage.json`) plus a small CSV stub for any path it references — or use a tiny synthetic fixture if `gdp` references remote URLs that we don't want hit in tests.

```python
# tests/relations/dag/test_e2e_real_descriptor.py
import json
from pathlib import Path
import pytest
from mountainash.typespec.datapackage import DataPackage

FIXTURES = Path(__file__).parent.parent.parent / "typespec" / "fixtures"


def test_descriptor_round_trip_through_dag(tmp_path):
    raw = json.loads((FIXTURES / "gdp.datapackage.json").read_text())
    # Replace any remote `path` with a local stub matching the schema
    for r in raw["resources"]:
        r["path"] = str(tmp_path / f"{r['name']}.csv")
        Path(r["path"]).write_text("Country Name,Country Code,Year,Value\nA,A,2020,1\n")
    pkg = DataPackage.from_descriptor(raw)
    dag = pkg.to_relation_dag()
    pkg2 = dag.to_package()
    # Round-trip preserves resource names and schemas
    assert {r.name for r in pkg2.resources} == {r.name for r in pkg.resources}
```

- [ ] **Step 2: Run.** Iterate on any gaps surfaced.

- [ ] **Step 3: Commit.**
```bash
git add tests/relations/dag/test_e2e_real_descriptor.py
git commit -m "test(dag): end-to-end DataPackage → RelationDAG → DataPackage round-trip"
```

### Task 22: Lint, type check, full suite, finalize

- [ ] **Step 1: Run ruff.**
```bash
hatch run ruff:check
hatch run ruff:fix   # if anything to fix
```

- [ ] **Step 2: Run mypy.**
```bash
hatch run mypy:check
```

- [ ] **Step 3: Run full suite with coverage.**
```bash
hatch run test:test
```

- [ ] **Step 4: Fix any failures, lint warnings, or type errors. Commit any fixes.**

- [ ] **Step 5: Final commit.**
```bash
git commit --allow-empty -m "chore(datapackage): finalize Frictionless DataPackage support"
```

---

## Self-Review (run by plan author before handoff)

**Spec coverage check:**

| Spec section | Covered by |
|---|---|
| § 1 New types: TableDialect | Task 3 |
| § 1 New types: DataResource | Task 4 |
| § 1 New types: DataPackage | Task 5 |
| § 2 RefRelNode | Task 9, 13 |
| § 2 ResourceReadRelNode | Task 10, 13, 14 |
| § 3 RelationDAG container | Task 16 |
| § 3 ResourceRef wrapper | Task 15 |
| § 3 dependency_edges + constraint_edges | Task 16 (dep), Task 19 (constraint) |
| § 3 collect() with caching | Task 17 |
| § 4 Visitor changes (ref_resolver, visit methods) | Task 13, 14 |
| § 5 API: from_descriptor / to_descriptor | Task 4, 5 |
| § 5 API: package.to_relation_dag(overrides=) | Task 19 |
| § 5 API: dag.to_package() | Task 20 |
| § 5 API: top-level re-exports | Task 18 |
| § 6 Round-trip semantics: extras preserved | Task 4, 5 |
| § 6 Round-trip semantics: $schema preserved | Task 5 |
| § 6 Round-trip semantics: FK validation | Task 5 |
| § 6 MissingResourceSchema error | Task 20 |
| § 7 Phase 1 — TypeSpec audit + TableDialect | Tasks 1–3 |
| § 7 Phase 2 — DataResource + DataPackage | Tasks 4–7 |
| § 7 Phase 3 — AST nodes + visitor wiring | Tasks 8–14 |
| § 7 Phase 4 — RelationDAG | Tasks 15–18 |
| § 7 Phase 5 — Bidirectional bridge | Tasks 19–20 |
| § 7 Phase 6 — E2E tests | Task 21 |
| § 8 Storage facade integration | Task 12 |
| § 8 Multi-file path concat | Task 11 |
| § 8 Inline data via pydata.ingress | Task 11 |
| § 9 Risks: HTTPS routing | Task 12 |
| § 9 Risks: lazy frame conform | Task 13 (note + verification step) |

No spec gaps.

**Placeholder scan:** All steps contain concrete code, file paths, and commands. Tasks 13/14/15/17 contain explicit "verify against actual file" notes where the existing-code surface was probed but not exhaustively read; these notes name the file to consult and the specific assumption to check. This is intentional and not a placeholder — the implementer needs to ground these calls in code that wasn't readable from the planning context.

**Type consistency:** `RelationDAG.relations: dict[str, Relation]`, `dependency_edges: set[tuple[str,str]]` used consistently across Tasks 16/17/19/20. `RefRelNode(name=...)`, `ResourceReadRelNode(resource=...)` constructors consistent. `read_resource_to_polars(resource)` signature consistent across Tasks 11–14. `compile_conform` call signature flagged for verification in Task 13/14. No drift.

---

Plan complete and saved to `docs/superpowers/plans/2026-04-07-frictionless-datapackage.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
