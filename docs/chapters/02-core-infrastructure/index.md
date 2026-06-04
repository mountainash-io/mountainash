---
title: Core Infrastructure
description: Shared infrastructure underpinning all mountainash modules including constants, backend enums, detection, type guards, the dtype system, lazy imports, and factory patterns.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 2: Core Infrastructure

## Summary

Shared infrastructure underpinning all mountainash modules: constants, backend and operation enums, backend detection, DataFrame type guards, MountainashDtype, lazy imports, factory pattern, and BaseFactoryMixin.

## Concepts Covered

- Constants Module
- Backend Enum
- Backend System Enum
- Backend Detection
- DataFrame Type Guards
- MountainashDtype
- Lazy Import System
- Factory Pattern
- BaseFactoryMixin
- Operation Enums
- JoinType Enum
- SetType Enum

## Prerequisites

- [Chapter 1. Foundation Concepts](../01-foundations/)

---

## Introduction

Every module in mountainash shares a common layer of infrastructure that provides type definitions, backend identification, lazy loading, and factory patterns. This infrastructure lives primarily in `mountainash.core` and defines the vocabulary that all other layers speak. Understanding these shared components is essential before working with expressions, relations, or pipelines.

This chapter progresses from the simplest concepts (enum constants) through the detection and routing system, and concludes with the factory patterns that enable lazy-loaded, backend-agnostic code.

<!-- concept:13 -->
## Constants Module

The constants module (`mountainash.core.constants`) serves as the single source of truth for all enumeration values, operation identifiers, and shared data structures used across the library. By centralizing these definitions, mountainash avoids scattered string literals and ensures consistent naming throughout the codebase.

The module defines multiple categories of constants. Backend enums identify which library produced a given object. Operation enums categorize expression types (arithmetic, comparison, string, temporal). Relational enums describe join types, set operations, and projection variants.

```python
from mountainash.core.constants import (
    CONST_BACKEND,
    CONST_BACKEND_SYSTEM,
    JoinType,
    SetType,
    ExtensionRelOperation,
)
```

All constants follow a naming convention. Top-level enumeration classes use uppercase prefixed names (`CONST_BACKEND`, `CONST_EXPRESSION_NODE_TYPES`). Individual enum members use uppercase snake case (`POLARS`, `INNER`, `UNION_ALL`).

<!-- concept:14 -->
## Backend Enum

The `CONST_BACKEND` enumeration answers the question: "What library produced this object?" It uses `StrEnum` so that each member is simultaneously an enum value and a plain string, enabling both identity comparison and string-based registry lookups.

```python
class CONST_BACKEND(StrEnum):
    POLARS   = "polars"
    PANDAS   = "pandas"
    PYARROW  = "pyarrow"
    IBIS     = "ibis"
    NARWHALS = "narwhals"
```

The five backend values represent the concrete libraries mountainash can detect at the input layer. When a user passes a DataFrame to `relation()`, the system inspects it and assigns one of these backend values. This detection result then drives all downstream routing decisions.

| Backend | Typical Input Type | Notes |
|---------|-------------------|-------|
| `POLARS` | `pl.DataFrame`, `pl.LazyFrame` | Primary backend, native support |
| `PANDAS` | `pd.DataFrame` | Routed through Narwhals adapter |
| `PYARROW` | `pa.Table` | Routed through Narwhals adapter |
| `IBIS` | `ibis.Table` | SQL compilation backend |
| `NARWHALS` | `nw.DataFrame`, `nw.LazyFrame` | Direct Narwhals objects |

<!-- concept:15 -->
## Backend System Enum

While `CONST_BACKEND` identifies the source library (five values), `CONST_BACKEND_SYSTEM` identifies the compilation target (three values). This distinction separates detection from routing. Multiple detected backends can map to the same system implementation.

```python
class CONST_BACKEND_SYSTEM(StrEnum):
    POLARS   = "polars"
    NARWHALS = "narwhals"
    IBIS     = "ibis"
```

The mapping from backend to system is defined by the `backend_to_system()` function. Polars routes to its native system. Pandas and PyArrow both route through Narwhals. Ibis routes to its own SQL compilation system. This three-way split means mountainash maintains exactly three expression system implementations and three relation system implementations, regardless of how many input libraries it supports.

<!-- concept:16 -->
#### Diagram: Backend Detection and System Routing
<iframe src="../../sims/backend-routing/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Backend Detection and System Routing</summary>
Type: workflow
**sim-id:** backend-routing<br/>
**Library:** vis-network<br/>
**Status:** Specified

A flow diagram showing the two-stage routing process. Left column: five input types (Polars DataFrame, Polars LazyFrame, pandas DataFrame, PyArrow Table, Ibis Table). Middle column: the `CONST_BACKEND` detection stage with five enum values. Right column: the `CONST_BACKEND_SYSTEM` routing targets (three systems). Edges connect inputs to backends to systems, with color coding showing the many-to-one mapping (pandas and PyArrow both route to Narwhals). Hovering over any node highlights its full routing path. Learning objective: Trace how input data types map through two enum stages to reach the correct compilation system (Bloom: Apply).
</details>

## Backend Detection

Backend detection is the mechanism by which mountainash inspects an incoming object and determines which `CONST_BACKEND` value it corresponds to. This happens without importing any backend library. Instead, the system examines the object's class module path and class name as strings, then looks these up in a pre-configured type map.

The detection uses a two-layer strategy. The first layer checks an exact match dictionary mapping `(module, class_name)` tuples to backend enum values. If no exact match is found, the second layer applies regex pattern matching against the module path to handle library refactors and reorganizations.

```python
# Example exact matches from the type map:
("polars.dataframe.frame", "DataFrame") -> POLARS_DATAFRAME
("pandas.core.frame", "DataFrame")      -> PANDAS_DATAFRAME
("ibis.expr.types.relations", "Table")  -> IBIS_TABLE
```

This string-based approach means no backend library needs to be importable for detection to work. A user who has Polars installed but not Ibis can still pass Polars DataFrames without triggering an Ibis import error.

<!-- concept:17 -->
## DataFrame Type Guards

DataFrame type guards are specialized functions that check whether a given object is a DataFrame of a particular backend type. They return boolean values and are used at branch points where mountainash needs to make decisions based on the concrete type of input data.

The type guard system builds on the same string-inspection infrastructure as backend detection. The `CONST_DATAFRAME_TYPE` enum provides granular variant identification that distinguishes not just between libraries but between variants within a library (eager DataFrame vs LazyFrame in Polars).

```python
class CONST_DATAFRAME_TYPE(Enum):
    IBIS_TABLE           = auto()
    PANDAS_DATAFRAME     = auto()
    POLARS_DATAFRAME     = auto()
    POLARS_LAZYFRAME     = auto()
    PYARROW_TABLE        = auto()
    NARWHALS_DATAFRAME   = auto()
    NARWHALS_LAZYFRAME   = auto()
```

Type guards are essential at the boundary between mountainash's backend-agnostic core and the backend-specific compilation layer. They enable conditional logic that respects each backend's unique capabilities without polluting the core API.

<!-- concept:18 -->
## MountainashDtype

`MountainashDtype` is a string enum that defines the canonical data type identifiers used throughout the library. Rather than requiring users to work with backend-specific type objects (like `pl.Int64` or `pa.int64()`), mountainash normalizes all type references to short, memorable string identifiers.

```python
class MountainashDtype(str, Enum):
    BOOL = "bool"
    I8 = "i8"
    I16 = "i16"
    I32 = "i32"
    I64 = "i64"
    FP32 = "fp32"
    FP64 = "fp64"
    STRING = "string"
    DATE = "date"
    TIMESTAMP = "timestamp"
    # ... additional types
```

The `resolve_dtype()` function accepts any type specifier (enum member, Python builtin type, canonical string, alias string, or native backend type) and resolves it to the canonical string form. This means users can write `"Int64"`, `"i64"`, `int`, or `pl.Int64` and all resolve to the same canonical `"i64"` value.

- Substrait-aligned naming (i8, i16, i32, i64, fp32, fp64)
- Polars-style aliases (Int64, Float32, Utf8, Boolean)
- Python type mapping (int -> i64, float -> fp64, str -> string, bool -> bool)
- Backend types converted via `str()` before lookup

<!-- concept:19 -->
## Lazy Import System

The lazy import system (`mountainash.core.lazy_imports`) defers the loading of heavy backend libraries until they are actually needed. This keeps mountainash's own import time fast and avoids requiring all backends to be installed simultaneously.

Rather than `import polars` at module level (which loads the entire Polars library even if the user only needs Ibis), mountainash wraps backend imports in functions that execute only when called.

```python
def import_polars():
    """Import polars lazily. Returns None if not installed."""
    try:
        import polars as pl
        return pl
    except ImportError:
        return None
```

This pattern is critical for mountainash's "bring your own backend" philosophy. A user working exclusively with Ibis databases should not need Polars installed at all. The lazy import system ensures that missing optional dependencies produce clear error messages at the point of use rather than cryptic import failures at startup.

<!-- concept:20 -->
## Factory Pattern

The factory pattern in mountainash provides a mechanism for creating backend-specific strategy objects based on the type of input data. The `BaseStrategyFactory` class implements a lazy-loading strategy factory that detects backends using string inspection and loads strategy implementations only on first use.

The factory workflow proceeds in three steps. First, it detects the backend from the input object (using the string-based type inspection described earlier). Second, it checks a cache for a previously loaded strategy. Third, if uncached, it dynamically imports the strategy module and caches the result.

```python
# Conceptual usage:
strategy_cls = MyFactory.get_strategy(dataframe)
strategy = strategy_cls()
result = strategy.process(dataframe)
```

This lazy loading eliminates the "available backends" anti-pattern where factories eagerly check which libraries are installed at import time. Instead, discovery happens naturally at the point of use.

#### Diagram: Factory Pattern Lazy Loading Flow
<iframe src="../../sims/factory-lazy-loading/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Factory Pattern Lazy Loading Flow</summary>
Type: workflow
**sim-id:** factory-lazy-loading<br/>
**Library:** vis-network<br/>
**Status:** Specified

A sequential workflow diagram showing the three stages of factory resolution. Stage 1: "Detect Backend" shows string inspection of the input object's module path. Stage 2: "Cache Lookup" shows a decision diamond checking if the strategy is already cached. Stage 3: "Lazy Import" shows dynamic module loading via importlib. Arrows connect stages with success/failure paths. A separate "Error Path" shows the ValueError raised when no strategy matches. Interactive: clicking each stage expands details about what happens internally. Colors: DarkSlateBlue for infrastructure nodes. Learning objective: Explain the lazy-loading strategy factory mechanism and why it avoids premature backend imports (Bloom: Understand).
</details>

<!-- concept:21 -->
## BaseFactoryMixin

`BaseFactoryMixin` is the abstract base class that all mountainash factories inherit from. It defines the contract that every factory must implement: a `_type_map()` class method that returns a dictionary mapping type identification tuples to enum values.

The `DataFrameTypeFactoryMixin` extends this with DataFrame-specific detection capabilities, including both exact-match type maps and regex-based pattern matching for future-proofing against library reorganizations.

```python
class BaseFactoryMixin(ABC):
    @classmethod
    @abstractmethod
    def _type_map(cls) -> Dict[tuple, Enum]:
        """Return the mapping from (module, class_name) to backend enum."""
        pass
```

The mixin also supports runtime type registration. When the pattern matcher discovers a new type variant, it auto-registers the mapping for future fast-path lookups. This self-healing behavior means mountainash can adapt to library refactors without code changes.

<!-- concept:22 -->
## Operation Enums

Operation enums categorize the different types of operations that expressions can perform. Each category has its own enum class, enabling the type system to enforce that only valid operations are used in the correct context.

The main operation categories are:

- **Logical comparison**: `EQ`, `NE`, `GT`, `LT`, `GE`, `LE`
- **Arithmetic**: `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE`, `MODULO`, `POWER`, `FLOOR_DIVIDE`
- **String**: `UPPER`, `LOWER`, `TRIM`, `CONTAINS`, `STARTS_WITH`, `ENDS_WITH`
- **Temporal**: `YEAR`, `MONTH`, `DAY`, `HOUR`, `ADD_DAYS`, `DIFF_HOURS`, `TRUNCATE`
- **Logical connectives**: `NOT`, `AND`, `OR`, `XOR_EXCLUSIVE`
- **Conditional**: `WHEN`, `COALESCE`, `FILL_NULL`
- **Pattern**: `LIKE`, `REGEX_MATCH`, `REGEX_CONTAINS`, `REGEX_REPLACE`

```python
class CONST_EXPRESSION_ARITHMETIC_OPERATORS(Enum):
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    POWER = auto()
    FLOOR_DIVIDE = auto()
```

These enums serve as function keys in expression AST nodes. When a `ScalarFunctionNode` is created, its `function_key` field holds one of these enum values, telling the compiler exactly which operation to generate for the target backend.

<!-- concept:23 -->
## JoinType Enum

The `JoinType` enum defines the relational join variants that mountainash supports. It uses `StrEnum` for string compatibility with backend APIs that accept join type as a string parameter.

```python
class JoinType(StrEnum):
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    OUTER = "outer"
    SEMI = "semi"
    ANTI = "anti"
    CROSS = "cross"
    ASOF = "asof"
```

Each join type has distinct semantics that affect which rows appear in the result. The table below summarizes their behavior with respect to matching and non-matching rows.

| Join Type | Left Non-Match | Right Non-Match | Use Case |
|-----------|---------------|-----------------|----------|
| INNER | Excluded | Excluded | Only matching rows |
| LEFT | Included (nulls) | Excluded | Preserve all left rows |
| RIGHT | Excluded | Included (nulls) | Preserve all right rows |
| OUTER | Included (nulls) | Included (nulls) | Preserve all rows |
| SEMI | Included if match exists | N/A | Filter left by right existence |
| ANTI | Included if no match | N/A | Filter left by right absence |
| CROSS | All combinations | All combinations | Cartesian product |
| ASOF | Nearest match | N/A | Time-series alignment |

<!-- concept:24 -->
## SetType Enum

The `SetType` enum defines set-theoretic operations on relations. These operations combine rows from multiple relations vertically (as opposed to joins, which combine columns horizontally).

```python
class SetType(Enum):
    UNION_ALL = auto()
    UNION_DISTINCT = auto()
```

`UNION_ALL` concatenates all rows from all input relations, preserving duplicates. `UNION_DISTINCT` performs deduplication after concatenation. Both operations require that input relations share the same column schema (matching names and compatible types).

Set operations in mountainash align with the Substrait specification's `SetRel` node type. The `concat()` function at the top-level API typically produces a `UNION_ALL` set operation, while distinct unions require explicit specification.

## Key Takeaways

- The constants module centralizes all enum values, preventing scattered string literals and ensuring consistent naming across the entire library.
- Backend detection uses a two-stage architecture: `CONST_BACKEND` (five values) identifies the source library, while `CONST_BACKEND_SYSTEM` (three values) routes to the compilation target.
- String-based type inspection enables backend detection without importing heavy libraries, supporting mountainash's "bring your own backend" philosophy.
- `MountainashDtype` normalizes backend-specific type representations into short canonical identifiers (i64, fp32, string) with extensive alias support.
- The lazy import system defers backend library loading until first use, keeping mountainash's startup time fast and optional dependencies truly optional.
- `BaseStrategyFactory` implements a lazy-loading factory that auto-discovers backends at runtime and caches loaded strategies for subsequent use.
- Operation enums categorize all expression operations (arithmetic, comparison, string, temporal, logical) and serve as function keys in AST nodes.
- JoinType and SetType enums define the relational algebra operations available for combining data from multiple sources.
