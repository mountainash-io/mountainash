# Nested Data & Duration Expression Gaps — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `.struct` and `.list` accessor namespaces plus a `ma.duration()` constructor and `.dt.total_*()` extraction methods, closing gaps 5, 6, and 15 from the PromptBase pipeline backlog.

**Architecture:** All three gaps follow the established mountainash extension pattern — Polars-style public API, `ScalarFunctionNode` with mountainash extension function keys, wired through all 6 architecture layers. Duration constructor is a thin wrapper over `LiteralNode(timedelta(...))` with no new node types.

**Tech Stack:** Python, Polars, Narwhals, Ibis. Cross-backend parametrised tests.

---

## 1. Struct Field Access (Gap 5)

### Public API

```python
ma.col("reaction").struct.field("emoji")              # extract field
ma.col("reaction").struct.field("emoji").str.upper()   # chain into typed namespace
ma.col("reaction").struct.field("count").sum()         # aggregate extracted field
```

Single method: `field(name: str)`. Returns `BaseExpressionAPI` — full chaining supported.

### AST Representation

```python
ScalarFunctionNode(
    function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD,
    arguments=[self._node],              # the struct column
    options={"field_name": "emoji"},      # literal string, not visited
)
```

`field_name` is an **option** (raw literal string), not an argument. It is always a Python string, never a column reference or expression.

### Function Key Enum

```python
class FKEY_MOUNTAINASH_SCALAR_STRUCT(Enum):
    FIELD = auto()
```

Extension URI: `None` — these are pragmatic API operations, not formal Substrait extensions.

### Protocol

```python
class MountainAshScalarStructExpressionSystemProtocol(Protocol[ExpressionT]):
    def struct_field(self, x: ExpressionT, /, *, field_name: str) -> ExpressionT: ...
```

### API Builder

New file: `api_bldr_ext_ma_scalar_struct.py` in `expression_api/api_builders/extensions_mountainash/`.

```python
class MountainAshScalarStructAPIBuilder(BaseExpressionAPIBuilder):
    def field(self, name: str) -> BaseExpressionAPI:
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD,
            arguments=[self._node],
            options={"field_name": name},
        )
        return self._build(node)
```

### Descriptor Registration

In `boolean.py`:

```python
class StructAPIBuilder(MountainAshScalarStructAPIBuilder):
    pass

class BooleanExpressionAPI(BaseExpressionAPI):
    struct = NamespaceDescriptor(StructAPIBuilder)
    # ... existing str, dt, name descriptors
```

### Backend Implementations

| Backend | File | Implementation |
|---------|------|----------------|
| Polars | `expsys_pl_ext_ma_scalar_struct.py` | `x.struct.field(field_name)` |
| Narwhals | `expsys_nw_ext_ma_scalar_struct.py` | `x.struct.field(field_name)` |
| Ibis | `expsys_ib_ext_ma_scalar_struct.py` | `x[field_name]` |

Each backend class implements `MountainAshScalarStructExpressionSystemProtocol` and is composed into the backend's `ExpressionSystem` via multiple inheritance.

### Function Mapping Registration

```python
ExpressionFunctionDef(
    function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD,
    substrait_uri=None,
    substrait_name=None,
    is_extension=True,
    options=("field_name",),
    protocol_method=MountainAshScalarStructExpressionSystemProtocol.struct_field,
)
```

### Known Limitations

None for the basic `field()` operation — all three backends support it.

### Tests

- Cross-backend parametrised: extract field from struct, verify value
- Chaining: `struct.field("name").str.upper()`
- Aggregation: `struct.field("count").sum()`

---

## 2. List Operations (Gap 6 — subset)

### Public API

```python
# Aggregates
ma.col("scores").list.sum()
ma.col("scores").list.min()
ma.col("scores").list.max()
ma.col("scores").list.mean()

# Info
ma.col("tags").list.len()

# Search
ma.col("tags").list.contains("python")
ma.col("tags").list.contains(ma.col("search_term"))  # expression arg

# Manipulation
ma.col("scores").list.sort()
ma.col("scores").list.sort(descending=True)
ma.col("tags").list.unique()
```

8 operations. `eval`, `explode`, `join`, set ops, positional access — all deferred (see backlog D5–D10).

### Function Key Enum

```python
class FKEY_MOUNTAINASH_SCALAR_LIST(Enum):
    SUM = auto()
    MIN = auto()
    MAX = auto()
    MEAN = auto()
    LEN = auto()
    CONTAINS = auto()
    SORT = auto()
    UNIQUE = auto()
```

### Protocol

```python
class MountainAshScalarListExpressionSystemProtocol(Protocol[ExpressionT]):
    def list_sum(self, x: ExpressionT, /) -> ExpressionT: ...
    def list_min(self, x: ExpressionT, /) -> ExpressionT: ...
    def list_max(self, x: ExpressionT, /) -> ExpressionT: ...
    def list_mean(self, x: ExpressionT, /) -> ExpressionT: ...
    def list_len(self, x: ExpressionT, /) -> ExpressionT: ...
    def list_contains(self, x: ExpressionT, /, item: ExpressionT) -> ExpressionT: ...
    def list_sort(self, x: ExpressionT, /, *, descending: bool = False) -> ExpressionT: ...
    def list_unique(self, x: ExpressionT, /) -> ExpressionT: ...
```

### Arguments vs Options

| Method | Arguments (visited) | Options (literal) |
|--------|--------------------|--------------------|
| `list_sum/min/max/mean/len/unique` | `x` only | — |
| `list_contains` | `x`, `item` | — |
| `list_sort` | `x` only | `descending: bool` |

`item` in `list_contains` is an **argument** — it can be a literal value OR a column reference. `descending` is an **option** — always a raw bool.

### API Builder

New file: `api_bldr_ext_ma_scalar_list.py` in `expression_api/api_builders/extensions_mountainash/`.

```python
class MountainAshScalarListAPIBuilder(BaseExpressionAPIBuilder):
    def sum(self) -> BaseExpressionAPI:
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SUM,
            arguments=[self._node],
        )
        return self._build(node)

    def contains(self, item) -> BaseExpressionAPI:
        item_node = self._to_substrait_node(item)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS,
            arguments=[self._node, item_node],
        )
        return self._build(node)

    def sort(self, *, descending: bool = False) -> BaseExpressionAPI:
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SORT,
            arguments=[self._node],
            options={"descending": descending},
        )
        return self._build(node)

    # ... min, max, mean, len, unique follow the same pattern as sum
```

### Descriptor Registration

```python
class ListAPIBuilder(MountainAshScalarListAPIBuilder):
    pass

class BooleanExpressionAPI(BaseExpressionAPI):
    list = NamespaceDescriptor(ListAPIBuilder)
```

### Backend Implementations

| Method | Polars | Narwhals | Ibis |
|--------|--------|----------|------|
| `list_sum` | `x.list.sum()` | `x.list.sum()` | `x.sums()` |
| `list_min` | `x.list.min()` | `x.list.min()` | `x.mins()` |
| `list_max` | `x.list.max()` | `x.list.max()` | `x.maxs()` |
| `list_mean` | `x.list.mean()` | `x.list.mean()` | `x.means()` |
| `list_len` | `x.list.len()` | `x.list.len()` | `x.length()` |
| `list_contains` | `x.list.contains(item)` | `x.list.contains(item)` | `x.contains(item)` |
| `list_sort` | `x.list.sort(descending=d)` | `x.list.sort(descending=d)` | `x.sort()` (ascending only — see below) |
| `list_unique` | `x.list.unique()` | `x.list.unique()` | `x.unique()` |

### Known Limitations

| Backend | Operation | Limitation | Workaround |
|---------|-----------|------------|------------|
| Narwhals (Arrow/pandas) | `list_contains` | Not supported on Arrow or pandas-backed frames | Use Polars or Ibis backend |
| Narwhals (Arrow/pandas) | `list_unique` | Not supported on Arrow or pandas-backed frames | Use Polars or Ibis backend |
| Narwhals | `list_contains(Expr)` | Rejects expression arguments (existing divergence #9) | Use literal value |
| Ibis | `list_sort(descending=True)` | `ArrayValue.sort()` has no `descending` parameter and no `reverse()` method. **Must raise `BackendCapabilityError`** when `descending=True` — silent ascending return is not acceptable. | Use ascending sort, or use Polars/Narwhals backend |

All registered via `KNOWN_EXPR_LIMITATIONS` in each backend's `base.py`.

**Critical: Ibis `list_sort` with `descending=True` must fail loudly.** The Ibis backend's `list_sort` implementation must check `descending` and raise `BackendCapabilityError` before calling `x.sort()`, since `x.sort()` silently ignores the parameter and returns ascending order. This is not a limitation that can be caught by `_call_with_expr_support` — there is no native error to enrich. The check must be explicit in the backend method.

### Tests

- Cross-backend parametrised: each of the 8 operations on a list column
- `list.contains` with literal value
- `list.contains` with expression argument (xfail Narwhals)
- `list.sort(descending=True)` — **must raise `BackendCapabilityError` on Ibis, not silently return ascending**
- Chaining: `list.sum().gt(10)`

---

## 3. Duration Constructor & Extraction (Gap 15)

### Public API — Constructor

```python
# Free function — creates duration literal
ma.duration(days=1, hours=2, minutes=30)

# Datetime arithmetic
ma.col("timestamp") + ma.duration(days=7)
ma.col("timestamp") - ma.duration(hours=1)

# Duration comparison (KNOWN_EXPR_LIMITATIONS on Ibis)
ma.col("gap") > ma.duration(hours=4)
```

### Constructor Implementation

`ma.duration()` is a thin wrapper that creates a `LiteralNode` from a Python `timedelta`. **No new node type, no new function key.**

```python
# In src/mountainash/__init__.py or entrypoints.py
from datetime import timedelta

def duration(
    *,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    milliseconds: int = 0,
    microseconds: int = 0,
) -> BaseExpressionAPI:
    td = timedelta(
        weeks=weeks, days=days, hours=hours, minutes=minutes,
        seconds=seconds, milliseconds=milliseconds, microseconds=microseconds,
    )
    return lit(td)
```

All parameters are keyword-only and literal-only (int, not Expr). Expression arguments are deferred (backlog D11).

### Backend Literal Handling

Each backend's literal visitor must handle `timedelta` values:

| Backend | `visit_literal(timedelta)` → | Sub-second precision? |
|---------|------|------|
| Polars | `pl.lit(td)` (Polars infers `Duration` dtype) | Yes |
| Narwhals | `nw.lit(td, dtype=nw.Duration())` | Yes |
| Ibis | `ibis.literal(td)` | Yes — converts to microseconds internally |

**Critical: Ibis must use `ibis.literal(td)`, NOT `ibis.interval(seconds=int(td.total_seconds()))`.** The `int()` truncation drops all sub-second precision, making `ma.duration(milliseconds=500)` a zero-length interval. Verified: `ibis.literal(timedelta(milliseconds=500))` correctly produces `500000 us` and executes correctly on DuckDB.

If any backend's literal handler doesn't cover `timedelta` yet, add a branch. This is the only backend-side work for the constructor.

### Extraction Methods

4 new methods added to the **existing `.dt` namespace**:

```python
ma.col("gap").dt.total_seconds()
ma.col("gap").dt.total_minutes()
ma.col("gap").dt.total_milliseconds()
ma.col("gap").dt.total_microseconds()
```

### Function Key Additions

Add to **existing** `FKEY_MOUNTAINASH_SCALAR_DATETIME` enum:

```python
TOTAL_SECONDS = auto()
TOTAL_MINUTES = auto()
TOTAL_MILLISECONDS = auto()
TOTAL_MICROSECONDS = auto()
```

### Protocol Additions

Add to **existing** `MountainAshScalarDatetimeExpressionSystemProtocol`:

```python
def total_seconds(self, x: ExpressionT, /) -> ExpressionT: ...
def total_minutes(self, x: ExpressionT, /) -> ExpressionT: ...
def total_milliseconds(self, x: ExpressionT, /) -> ExpressionT: ...
def total_microseconds(self, x: ExpressionT, /) -> ExpressionT: ...
```

### API Builder Additions

Add to **existing** `MountainAshScalarDatetimeAPIBuilder`:

```python
def total_seconds(self) -> BaseExpressionAPI:
    node = ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_SECONDS,
        arguments=[self._node],
    )
    return self._build(node)
# ... total_minutes, total_milliseconds, total_microseconds identical pattern
```

### Backend Implementations

| Method | Polars | Narwhals | Ibis |
|--------|--------|----------|------|
| `total_seconds` | `x.dt.total_seconds()` | `x.dt.total_seconds()` | `KNOWN_EXPR_LIMITATIONS` |
| `total_minutes` | `x.dt.total_minutes()` | `x.dt.total_minutes()` | `KNOWN_EXPR_LIMITATIONS` |
| `total_milliseconds` | `x.dt.total_milliseconds()` | `x.dt.total_milliseconds()` | `KNOWN_EXPR_LIMITATIONS` |
| `total_microseconds` | `x.dt.total_microseconds()` | `x.dt.total_microseconds()` | `KNOWN_EXPR_LIMITATIONS` |

### Known Limitations

| Backend | Operation | Limitation | Workaround |
|---------|-----------|------------|------------|
| Ibis | `total_seconds/minutes/milliseconds/microseconds` | Ibis `IntervalValue` has no `total_*()` methods | Use `dt.diff_minutes()` which returns integer directly |
| Ibis | Duration comparison (`gt`, `lt`, etc.) | Ibis `IntervalValue` does not support comparison operators | Use `dt.diff_minutes()` → integer comparison |

### Re-export

Add `duration` to `src/mountainash/__init__.py`:

```python
from mountainash.expressions.core.expression_api.entrypoints import duration
```

### Tests

- Constructor: `ma.duration(hours=4)` produces correct `timedelta`
- Datetime arithmetic: `col + ma.duration(days=1)` (cross-backend)
- Duration comparison: `col > ma.duration(hours=4)` (xfail Ibis)
- Extraction: `total_seconds()`, `total_minutes()` on a duration column (xfail Ibis)
- **Sub-second precision**: `col + ma.duration(milliseconds=500)` must produce a timestamp offset by exactly 500ms (cross-backend, including Ibis)
- **Microsecond precision**: `col + ma.duration(microseconds=1500)` must produce a timestamp offset by exactly 1.5ms (cross-backend)

---

## Wiring Matrix Summary

Each gap follows the 6-layer wiring from `adding-operations.md`:

| Layer | Struct | List | Duration Constructor | Duration Extraction |
|-------|--------|------|---------------------|-------------------|
| 1. Function key enum | `FKEY_MOUNTAINASH_SCALAR_STRUCT` (1 key) | `FKEY_MOUNTAINASH_SCALAR_LIST` (8 keys) | N/A (uses `LiteralNode`) | Add 4 keys to existing `FKEY_MOUNTAINASH_SCALAR_DATETIME` |
| 2. Protocol | New `MountainAshScalarStructExpressionSystemProtocol` | New `MountainAshScalarListExpressionSystemProtocol` | N/A | Add 4 methods to existing datetime protocol |
| 3. API builder | New `MountainAshScalarStructAPIBuilder` | New `MountainAshScalarListAPIBuilder` | New `duration()` free function | Add 4 methods to existing datetime builder |
| 4. Function mapping | 1 registration | 8 registrations | N/A | 4 registrations |
| 5. Backend (×3) | 3 new files (1 method each) | 3 new files (8 methods each) | Verify/add `timedelta` literal handling | Add 4 methods to existing datetime backends |
| 6. Descriptor | `struct = NamespaceDescriptor(...)` | `list = NamespaceDescriptor(...)` | Re-export in `__init__.py` | N/A (already in `.dt`) |

**New files:** ~12 (4 per namespace × 2 namespaces + 3 backend literal tweaks + 1 entrypoint)
**Modified files:** ~15 (enums, definitions, boolean.py, 3× backend __init__.py, 3× existing datetime backends, protocol __init__.py, known-divergences, backlog)

---

## Deferred Items

See backlog items D1–D15 in `expression-api-gaps-promptbase-pipeline.md` for full list. Key deferrals:

- **D5: `list.eval(expr)`** (Low) — the key composability primitive for arbitrary expressions inside lists
- **D6: `list.explode()`** (Low) — expand list to rows
- **D11: Expression args in `ma.duration()`** (Very Low) — `ma.duration(hours=col("x"))`
- **D15: `ma.date_range()`** (Very Low) — data generation, not transformation
