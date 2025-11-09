# Protocol-Based Architecture Proposal

**Date:** 2025-01-09
**Status:** Planning - Architectural Design
**Goal:** Define protocol-based mixin architecture for ExpressionSystem backends

---

## Overview

This document specifies the proposed protocol-based architecture that will replace the current monolithic ExpressionSystem god classes with focused, composable protocol mixins.

---

## Proposed Directory Structure

```
src/mountainash_expressions/
├── backends/
│   │
│   ├── protocols/                      # NEW: Protocol interface definitions
│   │   ├── __init__.py                # Export all protocols
│   │   ├── core_protocol.py           # col(), lit() - 2 methods
│   │   ├── comparison_protocol.py     # eq(), ne(), gt(), lt(), ge(), le() - 6 methods
│   │   ├── logical_protocol.py        # and_(), or_(), not_() - 3 methods
│   │   ├── arithmetic_protocol.py     # add(), sub(), mul(), div(), mod(), pow(), // - 7 methods
│   │   ├── string_protocol.py         # upper(), lower(), trim(), etc. - 12 methods
│   │   ├── pattern_protocol.py        # like(), regex_* - 4 methods
│   │   ├── conditional_protocol.py    # when(), coalesce(), fill_null() - 3 methods
│   │   └── temporal_protocol.py       # year(), month(), add_*, diff_*, etc. - 20+ methods
│   │
│   ├── common/                         # NEW: Shared base mixins
│   │   ├── __init__.py
│   │   └── mixins/
│   │       ├── __init__.py
│   │       ├── operator_overloading_comparison_mixin.py    # For backends with == support
│   │       ├── operator_overloading_arithmetic_mixin.py    # For backends with +, -, * support
│   │       └── null_handling_mixin.py                      # Common null operations
│   │
│   ├── polars/
│   │   ├── mixins/                     # NEW: Polars-specific mixins
│   │   │   ├── __init__.py
│   │   │   ├── polars_core_mixin.py              # ~50 lines
│   │   │   ├── polars_comparison_mixin.py        # ~80 lines
│   │   │   ├── polars_logical_mixin.py           # ~40 lines
│   │   │   ├── polars_arithmetic_mixin.py        # ~100 lines
│   │   │   ├── polars_string_mixin.py            # ~150 lines
│   │   │   ├── polars_pattern_mixin.py           # ~60 lines
│   │   │   ├── polars_conditional_mixin.py       # ~50 lines
│   │   │   └── polars_temporal_mixin.py          # ~200 lines
│   │   │
│   │   └── expression_system/
│   │       └── polars_expression_system.py      # REFACTORED: ~100 lines (composition only)
│   │
│   ├── narwhals/
│   │   ├── mixins/                     # NEW: Narwhals-specific mixins
│   │   │   ├── __init__.py
│   │   │   ├── narwhals_core_mixin.py
│   │   │   ├── narwhals_comparison_mixin.py
│   │   │   ├── narwhals_logical_mixin.py
│   │   │   ├── narwhals_arithmetic_mixin.py
│   │   │   ├── narwhals_string_mixin.py
│   │   │   ├── narwhals_pattern_mixin.py
│   │   │   ├── narwhals_conditional_mixin.py
│   │   │   └── narwhals_temporal_mixin.py
│   │   │
│   │   └── expression_system/
│   │       └── narwhals_expression_system.py    # REFACTORED: ~100 lines (composition only)
│   │
│   └── ibis/
│       ├── mixins/                     # NEW: Ibis-specific mixins
│       │   ├── __init__.py
│       │   ├── ibis_core_mixin.py
│       │   ├── ibis_comparison_mixin.py
│       │   ├── ibis_logical_mixin.py
│       │   ├── ibis_arithmetic_mixin.py
│       │   ├── ibis_string_mixin.py
│       │   ├── ibis_pattern_mixin.py
│       │   ├── ibis_conditional_mixin.py
│       │   └── ibis_temporal_mixin.py
│       │
│       └── expression_system/
│           └── ibis_expression_system.py        # REFACTORED: ~100 lines (composition only)
│
└── core/
    └── expression_system/
        └── base.py                               # UPDATED: Protocol composition or complete ABC
```

---

## Protocol Definitions

### 1. CoreBackend Protocol

**File:** `backends/protocols/core_protocol.py`

```python
"""Core backend operations for column references and literals."""

from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class CoreBackend(Protocol):
    """
    Protocol for core backend operations.

    All backends must implement column references and literal values.
    """

    def col(self, name: str, **kwargs) -> Any:
        """
        Create a column reference.

        Args:
            name: Column name
            **kwargs: Backend-specific options

        Returns:
            Backend-specific expression representing the column

        Examples:
            Polars: pl.col("age")
            Narwhals: nw.col("age")
            Ibis: table["age"] or ibis._["age"]
        """
        ...

    def lit(self, value: Any, **kwargs) -> Any:
        """
        Create a literal value expression.

        Args:
            value: Python value to convert to literal
            **kwargs: Backend-specific options (e.g., dtype)

        Returns:
            Backend-specific expression representing the literal

        Examples:
            Polars: pl.lit(42)
            Narwhals: nw.lit(42)
            Ibis: ibis.literal(42)
        """
        ...
```

### 2. ComparisonBackend Protocol

**File:** `backends/protocols/comparison_protocol.py`

```python
"""Comparison operations protocol."""

from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class ComparisonBackend(Protocol):
    """
    Protocol for comparison operations.

    All backends must support: ==, !=, >, <, >=, <=
    """

    def eq(self, left: Any, right: Any) -> Any:
        """Equality: left == right"""
        ...

    def ne(self, left: Any, right: Any) -> Any:
        """Inequality: left != right"""
        ...

    def gt(self, left: Any, right: Any) -> Any:
        """Greater than: left > right"""
        ...

    def lt(self, left: Any, right: Any) -> Any:
        """Less than: left < right"""
        ...

    def ge(self, left: Any, right: Any) -> Any:
        """Greater or equal: left >= right"""
        ...

    def le(self, left: Any, right: Any) -> Any:
        """Less or equal: left <= right"""
        ...
```

### 3. LogicalBackend Protocol

**File:** `backends/protocols/logical_protocol.py`

```python
"""Logical operations protocol."""

from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class LogicalBackend(Protocol):
    """
    Protocol for logical operations.

    All backends must support: AND, OR, NOT
    """

    def and_(self, left: Any, right: Any) -> Any:
        """Logical AND: left & right"""
        ...

    def or_(self, left: Any, right: Any) -> Any:
        """Logical OR: left | right"""
        ...

    def not_(self, operand: Any) -> Any:
        """Logical NOT: ~operand"""
        ...
```

### 4. ArithmeticBackend Protocol

**File:** `backends/protocols/arithmetic_protocol.py`

```python
"""Arithmetic operations protocol."""

from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class ArithmeticBackend(Protocol):
    """
    Protocol for arithmetic operations.

    All backends must support: +, -, *, /, %, **, //
    """

    def add(self, left: Any, right: Any) -> Any:
        """Addition: left + right"""
        ...

    def subtract(self, left: Any, right: Any) -> Any:
        """Subtraction: left - right"""
        ...

    def multiply(self, left: Any, right: Any) -> Any:
        """Multiplication: left * right"""
        ...

    def divide(self, left: Any, right: Any) -> Any:
        """Division: left / right (float division)"""
        ...

    def modulo(self, left: Any, right: Any) -> Any:
        """
        Modulo: left % right

        Note: Backends may differ in semantics for negative numbers.
        Python/Polars use modulo (sign of divisor).
        SQL/DuckDB use remainder (sign of dividend).
        """
        ...

    def power(self, left: Any, right: Any) -> Any:
        """Exponentiation: left ** right"""
        ...

    def floor_divide(self, left: Any, right: Any) -> Any:
        """Floor division: left // right"""
        ...
```

### 5. StringBackend Protocol

**File:** `backends/protocols/string_protocol.py`

```python
"""String operations protocol."""

from typing import Protocol, Any, Optional, runtime_checkable


@runtime_checkable
class StringBackend(Protocol):
    """
    Protocol for string operations.

    All backends must support common string manipulations.
    """

    def str_upper(self, operand: Any) -> Any:
        """Convert string to uppercase"""
        ...

    def str_lower(self, operand: Any) -> Any:
        """Convert string to lowercase"""
        ...

    def str_trim(self, operand: Any) -> Any:
        """Remove leading and trailing whitespace"""
        ...

    def str_ltrim(self, operand: Any) -> Any:
        """Remove leading whitespace"""
        ...

    def str_rtrim(self, operand: Any) -> Any:
        """Remove trailing whitespace"""
        ...

    def str_substring(
        self,
        operand: Any,
        start: int,
        end: Optional[int] = None
    ) -> Any:
        """
        Extract substring.

        Args:
            operand: String expression
            start: Start index (0-based)
            end: End index (exclusive), None for end of string
        """
        ...

    def str_concat(self, *operands: Any) -> Any:
        """Concatenate multiple strings"""
        ...

    def str_length(self, operand: Any) -> Any:
        """Get string length"""
        ...

    def str_replace(
        self,
        operand: Any,
        pattern: str,
        replacement: str
    ) -> Any:
        """Replace substring with replacement"""
        ...

    def str_contains(self, operand: Any, substring: str) -> Any:
        """Check if string contains substring"""
        ...

    def str_starts_with(self, operand: Any, prefix: str) -> Any:
        """Check if string starts with prefix"""
        ...

    def str_ends_with(self, operand: Any, suffix: str) -> Any:
        """Check if string ends with suffix"""
        ...
```

### 6. PatternBackend Protocol

**File:** `backends/protocols/pattern_protocol.py`

```python
"""Pattern matching operations protocol."""

from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class PatternBackend(Protocol):
    """
    Protocol for pattern matching operations.

    All backends must support SQL LIKE and regex operations.
    """

    def pattern_like(self, operand: Any, pattern: str) -> Any:
        """
        SQL LIKE pattern matching.

        Args:
            operand: String expression
            pattern: SQL LIKE pattern (% = any chars, _ = single char)

        Example:
            pattern_like(col("name"), "John%")  # Names starting with "John"
        """
        ...

    def pattern_regex_match(self, operand: Any, pattern: str) -> Any:
        """
        Full regex match (entire string must match).

        Args:
            operand: String expression
            pattern: Regular expression pattern
        """
        ...

    def pattern_regex_contains(self, operand: Any, pattern: str) -> Any:
        """
        Regex contains (pattern found anywhere in string).

        Args:
            operand: String expression
            pattern: Regular expression pattern
        """
        ...

    def pattern_regex_replace(
        self,
        operand: Any,
        pattern: str,
        replacement: str
    ) -> Any:
        """
        Replace text matching regex pattern.

        Args:
            operand: String expression
            pattern: Regular expression pattern
            replacement: Replacement string
        """
        ...
```

### 7. ConditionalBackend Protocol

**File:** `backends/protocols/conditional_protocol.py`

```python
"""Conditional operations protocol."""

from typing import Protocol, Any, Optional, runtime_checkable


@runtime_checkable
class ConditionalBackend(Protocol):
    """
    Protocol for conditional operations.

    All backends must support if-then-else, coalesce, and null filling.
    """

    def conditional_when(
        self,
        condition: Any,
        then_value: Any,
        else_value: Optional[Any] = None
    ) -> Any:
        """
        Conditional if-then-else expression.

        Args:
            condition: Boolean expression
            then_value: Value if condition is true
            else_value: Value if condition is false (None = NULL)

        Returns:
            Expression that evaluates to then_value or else_value

        Examples:
            when(col("age") > 18, "adult", "minor")
        """
        ...

    def conditional_coalesce(self, *operands: Any) -> Any:
        """
        Return first non-null value.

        Args:
            *operands: Expressions to evaluate in order

        Returns:
            First non-null expression

        Examples:
            coalesce(col("nickname"), col("first_name"), lit("Unknown"))
        """
        ...

    def conditional_fill_null(self, operand: Any, fill_value: Any) -> Any:
        """
        Replace null values with fill value.

        Args:
            operand: Expression that may contain nulls
            fill_value: Value to use for nulls

        Returns:
            Expression with nulls replaced
        """
        ...
```

### 8. TemporalBackend Protocol

**File:** `backends/protocols/temporal_protocol.py`

```python
"""Temporal operations protocol."""

from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class TemporalBackend(Protocol):
    """
    Protocol for temporal/datetime operations.

    All backends must support datetime extraction, arithmetic, and differences.
    """

    # Extraction operations
    def temporal_year(self, operand: Any) -> Any:
        """Extract year from datetime"""
        ...

    def temporal_month(self, operand: Any) -> Any:
        """Extract month (1-12) from datetime"""
        ...

    def temporal_day(self, operand: Any) -> Any:
        """Extract day of month (1-31) from datetime"""
        ...

    def temporal_hour(self, operand: Any) -> Any:
        """Extract hour (0-23) from datetime"""
        ...

    def temporal_minute(self, operand: Any) -> Any:
        """Extract minute (0-59) from datetime"""
        ...

    def temporal_second(self, operand: Any) -> Any:
        """Extract second (0-59) from datetime"""
        ...

    def temporal_weekday(self, operand: Any) -> Any:
        """Extract weekday (0=Monday, 6=Sunday)"""
        ...

    def temporal_week(self, operand: Any) -> Any:
        """Extract ISO week number (1-53)"""
        ...

    def temporal_quarter(self, operand: Any) -> Any:
        """Extract quarter (1-4)"""
        ...

    # Addition operations
    def temporal_add_days(self, operand: Any, days: int) -> Any:
        """Add days to datetime"""
        ...

    def temporal_add_months(self, operand: Any, months: int) -> Any:
        """Add months to datetime (calendar-aware)"""
        ...

    def temporal_add_years(self, operand: Any, years: int) -> Any:
        """Add years to datetime (calendar-aware)"""
        ...

    def temporal_add_hours(self, operand: Any, hours: int) -> Any:
        """Add hours to datetime"""
        ...

    def temporal_add_minutes(self, operand: Any, minutes: int) -> Any:
        """Add minutes to datetime"""
        ...

    def temporal_add_seconds(self, operand: Any, seconds: int) -> Any:
        """Add seconds to datetime"""
        ...

    # Difference operations
    def temporal_diff_days(self, left: Any, right: Any) -> Any:
        """Calculate difference in days: left - right"""
        ...

    def temporal_diff_months(self, left: Any, right: Any) -> Any:
        """Calculate difference in months: left - right (calendar-aware)"""
        ...

    def temporal_diff_years(self, left: Any, right: Any) -> Any:
        """Calculate difference in years: left - right (calendar-aware)"""
        ...

    def temporal_diff_hours(self, left: Any, right: Any) -> Any:
        """Calculate difference in hours: left - right"""
        ...

    def temporal_diff_minutes(self, left: Any, right: Any) -> Any:
        """Calculate difference in minutes: left - right"""
        ...

    def temporal_diff_seconds(self, left: Any, right: Any) -> Any:
        """Calculate difference in seconds: left - right"""
        ...

    # Utility operations
    def temporal_truncate(self, operand: Any, unit: str) -> Any:
        """
        Truncate datetime to specified unit.

        Args:
            operand: Datetime expression
            unit: One of: 'year', 'month', 'day', 'hour', 'minute', 'second'

        Examples:
            truncate(datetime('2024-03-15 14:30:45'), 'day') → '2024-03-15 00:00:00'
        """
        ...

    def temporal_offset_by(self, operand: Any, offset: str) -> Any:
        """
        Offset datetime by duration string.

        Args:
            operand: Datetime expression
            offset: Duration string (e.g., '2h', '30m', '1d')

        Examples:
            offset_by(col("timestamp"), "2h")
        """
        ...
```

---

## Backend Mixin Implementations

### Example: PolarsComparisonMixin

**File:** `backends/polars/mixins/polars_comparison_mixin.py`

```python
"""Polars implementation of comparison operations."""

import polars as pl
from typing import Any


class PolarsComparisonMixin:
    """
    Polars implementation of ComparisonBackend protocol.

    Uses Polars operator overloading for comparisons.
    """

    def eq(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Equality: left == right"""
        return left == right

    def ne(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Inequality: left != right"""
        return left != right

    def gt(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Greater than: left > right"""
        return left > right

    def lt(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Less than: left < right"""
        return left < right

    def ge(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Greater or equal: left >= right"""
        return left >= right

    def le(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Less or equal: left <= right"""
        return left <= right
```

### Example: PolarsStringMixin

**File:** `backends/polars/mixins/polars_string_mixin.py`

```python
"""Polars implementation of string operations."""

import polars as pl
from typing import Any, Optional


class PolarsStringMixin:
    """
    Polars implementation of StringBackend protocol.

    Uses Polars .str namespace for string operations.
    """

    def str_upper(self, operand: pl.Expr) -> pl.Expr:
        """Convert string to uppercase"""
        return operand.str.to_uppercase()

    def str_lower(self, operand: pl.Expr) -> pl.Expr:
        """Convert string to lowercase"""
        return operand.str.to_lowercase()

    def str_trim(self, operand: pl.Expr) -> pl.Expr:
        """Remove leading and trailing whitespace"""
        return operand.str.strip_chars()

    def str_ltrim(self, operand: pl.Expr) -> pl.Expr:
        """Remove leading whitespace"""
        return operand.str.strip_chars_start()

    def str_rtrim(self, operand: pl.Expr) -> pl.Expr:
        """Remove trailing whitespace"""
        return operand.str.strip_chars_end()

    def str_substring(
        self,
        operand: pl.Expr,
        start: int,
        end: Optional[int] = None
    ) -> pl.Expr:
        """Extract substring"""
        if end is None:
            return operand.str.slice(start)
        else:
            length = end - start
            return operand.str.slice(start, length)

    def str_concat(self, *operands: pl.Expr) -> pl.Expr:
        """Concatenate multiple strings"""
        if len(operands) == 0:
            raise ValueError("At least one operand required for concatenation")

        result = operands[0]
        for operand in operands[1:]:
            result = result + operand
        return result

    def str_length(self, operand: pl.Expr) -> pl.Expr:
        """Get string length"""
        return operand.str.len_chars()

    def str_replace(
        self,
        operand: pl.Expr,
        pattern: str,
        replacement: str
    ) -> pl.Expr:
        """Replace substring with replacement"""
        return operand.str.replace(pattern, replacement, literal=True)

    def str_contains(self, operand: pl.Expr, substring: str) -> pl.Expr:
        """Check if string contains substring"""
        return operand.str.contains(substring, literal=True)

    def str_starts_with(self, operand: pl.Expr, prefix: str) -> pl.Expr:
        """Check if string starts with prefix"""
        return operand.str.starts_with(prefix)

    def str_ends_with(self, operand: pl.Expr, suffix: str) -> pl.Expr:
        """Check if string ends with suffix"""
        return operand.str.ends_with(suffix)
```

---

## Composed Backend ExpressionSystem

### Example: PolarsExpressionSystem (Refactored)

**File:** `backends/polars/expression_system/polars_expression_system.py`

```python
"""Polars ExpressionSystem - composed from focused mixins."""

import polars as pl
from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash_expressions.backends.polars.mixins import (
    PolarsCoreMixin,
    PolarsComparisonMixin,
    PolarsLogicalMixin,
    PolarsArithmeticMixin,
    PolarsStringMixin,
    PolarsPatternMixin,
    PolarsConditionalMixin,
    PolarsTemporalMixin,
)


class PolarsExpressionSystem(
    PolarsCoreMixin,
    PolarsComparisonMixin,
    PolarsLogicalMixin,
    PolarsArithmeticMixin,
    PolarsStringMixin,
    PolarsPatternMixin,
    PolarsConditionalMixin,
    PolarsTemporalMixin,
):
    """
    Polars backend implementation composed from category-specific mixins.

    This class provides no logic of its own - it simply composes the
    eight category mixins that implement the protocol interfaces.

    Returns: pl.Expr (Polars expressions)
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Identify this backend as Polars."""
        return CONST_VISITOR_BACKENDS.POLARS

    def __repr__(self) -> str:
        return f"PolarsExpressionSystem(backend={self.backend_type.value})"
```

**Size:** ~30-40 lines (down from 663 lines!)

---

## Shared Base Mixins

### Example: OperatorOverloadingComparisonMixin

**File:** `backends/common/mixins/operator_overloading_comparison_mixin.py`

```python
"""Shared mixin for backends that support operator overloading for comparisons."""

from typing import Any


class OperatorOverloadingComparisonMixin:
    """
    Comparison operations for backends that support Python operators.

    Works for: Polars, Narwhals (wraps Polars), Ibis (supports operators)
    """

    def eq(self, left: Any, right: Any) -> Any:
        """Equality: left == right"""
        return left == right

    def ne(self, left: Any, right: Any) -> Any:
        """Inequality: left != right"""
        return left != right

    def gt(self, left: Any, right: Any) -> Any:
        """Greater than: left > right"""
        return left > right

    def lt(self, left: Any, right: Any) -> Any:
        """Less than: left < right"""
        return left < right

    def ge(self, left: Any, right: Any) -> Any:
        """Greater or equal: left >= right"""
        return left >= right

    def le(self, left: Any, right: Any) -> Any:
        """Less or equal: left <= right"""
        return left <= right
```

**Usage:**

```python
# Polars, Narwhals can inherit from this instead of reimplementing
from mountainash_expressions.backends.common.mixins import (
    OperatorOverloadingComparisonMixin
)

class PolarsComparisonMixin(OperatorOverloadingComparisonMixin):
    """Polars comparison - uses shared operator overloading."""
    pass  # No implementation needed!
```

---

## Protocol Composition for Complete ExpressionSystem

### Option A: Protocol Intersection (Python 3.10+)

**File:** `core/expression_system/base.py`

```python
"""Complete ExpressionSystem protocol composed from category protocols."""

from typing import Protocol
from mountainash_expressions.backends.protocols import (
    CoreBackend,
    ComparisonBackend,
    LogicalBackend,
    ArithmeticBackend,
    StringBackend,
    PatternBackend,
    ConditionalBackend,
    TemporalBackend,
)
from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS


class ExpressionSystem(
    CoreBackend,
    ComparisonBackend,
    LogicalBackend,
    ArithmeticBackend,
    StringBackend,
    PatternBackend,
    ConditionalBackend,
    TemporalBackend,
    Protocol
):
    """
    Complete ExpressionSystem protocol.

    Composes all operation category protocols into a single interface.
    Any backend implementing all 8 category protocols automatically
    satisfies the ExpressionSystem protocol.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Identify which backend this is."""
        ...
```

### Option B: Keep ABC During Transition

**File:** `core/expression_system/base.py`

```python
"""ExpressionSystem base class with complete ABC interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS


class ExpressionSystem(ABC):
    """
    Abstract base class for backend expression systems.

    All backends must implement this complete interface.
    """

    @property
    @abstractmethod
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Identify which backend this is."""
        pass

    # Core operations (2 methods)
    @abstractmethod
    def col(self, name: str, **kwargs) -> Any:
        """Column reference"""
        pass

    @abstractmethod
    def lit(self, value: Any, **kwargs) -> Any:
        """Literal value"""
        pass

    # Comparison operations (6 methods)
    @abstractmethod
    def eq(self, left: Any, right: Any) -> Any:
        """Equality: left == right"""
        pass

    # ... all 60+ abstract methods declared here
```

**Note:** This approach completes the ABC during transition, then migrates to Protocol composition in final phase.

---

## Benefits Summary

### Before (Current)

| Backend | File Size | Methods | Maintainability |
|---------|-----------|---------|-----------------|
| Polars | 663 lines | 68 | ❌ God class |
| Narwhals | 734 lines | ~70 | ❌ God class |
| Ibis | 883 lines | ~70 | ❌ God class |

### After (Proposed)

| Backend | Composition File | Mixin Files | Total Lines | Maintainability |
|---------|------------------|-------------|-------------|-----------------|
| Polars | ~40 lines | 8 × 50-200 lines | ~730 lines | ✅ Focused mixins |
| Narwhals | ~40 lines | 8 × 50-200 lines | ~730 lines | ✅ Focused mixins |
| Ibis | ~40 lines | 8 × 50-200 lines | ~730 lines | ✅ Focused mixins |

**Key Improvements:**

1. **Reduced Cognitive Load:** 68 methods → 8 categories of 2-12 methods each
2. **Easier Testing:** Test each category independently
3. **Code Reuse:** Shared mixins for operator-overloading backends
4. **Clear Alignment:** Each protocol mirrors visitor mixin exactly
5. **Better Documentation:** Focused protocol interfaces
6. **Type Safety:** Protocol checking ensures completeness
7. **Easier Extension:** New backend = implement 8 small mixins

---

## Implementation Priority

1. **Phase 1:** Define all 8 protocols (foundation)
2. **Phase 2:** Extract Polars mixins (template for others)
3. **Phase 3:** Replicate for Narwhals and Ibis
4. **Phase 4:** Extract shared base mixins
5. **Phase 5:** Migrate to Protocol composition

---

**Next Steps:** See `Refactoring-Roadmap.md` for detailed implementation plan.
