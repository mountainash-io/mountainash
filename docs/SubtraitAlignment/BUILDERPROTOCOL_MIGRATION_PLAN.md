# BuilderProtocol Migration Plan: Substrait Alignment

**Status**: ACTIVE
**Date**: 2025-12-20
**Related ADR**: ADR-002-substrait-builder-protocols

## Overview

Complete the three-layer protocol architecture for Substrait-aligned protocols. The ExpressionProtocols have been auto-generated from Substrait YAMLs; now we need to add corresponding BuilderProtocols that define the user-facing fluent API.

## Background

### Current State

The `expression_protocols/` directory contains three subdirectories:

| Directory | ExpressionProtocol | BuilderProtocol | VisitorProtocol |
|-----------|-------------------|-----------------|-----------------|
| `deprecated/` | Yes | Yes | Yes |
| `substrait/` | Yes | **NO** | NO |
| `extensions/` | Yes | **NO** | NO |

The deprecated/ folder has the complete three-layer pattern. The substrait/ and extensions/ folders only have ExpressionProtocols (auto-generated from Substrait YAML specifications).

### Target State

Add BuilderProtocols to `substrait/` directory that mirror the ExpressionProtocols. This completes the protocol layer for the new architecture.

**Note:** We are NOT migrating VisitorProtocols - the unified visitor pattern replaces them.

## Scope

### In Scope

- Add BuilderProtocols to all 13 files in `substrait/`
- Same file placement (BuilderProtocol in same file as ExpressionProtocol)
- Substrait naming convention (ScalarComparisonBuilderProtocol, etc.)
- Update `substrait/__init__.py` exports

### Out of Scope (Phase 2)

- BuilderProtocols for `extensions/` directory
- Namespace implementations using new protocols
- Visitor migrations

## Files to Modify

### 1. prtcl_scalar_comparison.py

**Add:** `ScalarComparisonBuilderProtocol`

Methods (24 total):
- `not_equal(other)`, `equal(other)`, `lt(other)`, `gt(other)`, `lte(other)`, `gte(other)`
- `between(low, high)`
- `is_true()`, `is_not_true()`, `is_false()`, `is_not_false()`
- `is_null()`, `is_not_null()`
- `is_nan()`, `is_finite()`, `is_infinite()`
- `nullif(other)`
- `coalesce(*others)`, `least(*others)`, `least_skip_null(*others)`, `greatest(*others)`, `greatest_skip_null(*others)`

### 2. prtcl_scalar_boolean.py

**Add:** `ScalarBooleanBuilderProtocol`

Methods (5 total):
- `or_(*others)`, `and_(*others)`, `and_not(other)`, `xor(other)`, `not_()`

### 3. prtcl_scalar_arithmetic.py

**Add:** `ScalarArithmeticBuilderProtocol`

Methods (7 total):
- `add(other)`, `subtract(other)`, `multiply(other)`, `divide(other)`
- `negate()`, `modulus(other)`, `power(other)`

### 4. prtcl_scalar_string.py

**Add:** `ScalarStringBuilderProtocol`

Methods (30+ total):
- Concatenation: `concat(*others)`, `concat_ws(separator, *strings)`
- Pattern: `like(match)`, `starts_with(prefix)`, `ends_with(suffix)`, `contains(substring)`
- Extraction: `substring(start, length)`, `left(count)`, `right(count)`
- Case: `lower()`, `upper()`, `swapcase()`, `capitalize()`, `title()`, `initcap()`
- Trim: `trim(chars)`, `ltrim(chars)`, `rtrim(chars)`
- Pad: `lpad(length, chars)`, `rpad(length, chars)`, `center(length, char)`
- Length: `char_length()`, `bit_length()`, `octet_length()`
- Other: `replace(substr, repl)`, `reverse()`, `repeat(count)`, `strpos(substr)`
- Split: `string_split(separator)`
- Regex: `regexp_match_substring(...)`, `regexp_replace(...)`, `regexp_strpos(...)`, `regexp_count_substring(...)`, `regexp_string_split(...)`

### 5. prtcl_scalar_datetime.py

**Add:** `ScalarDatetimeBuilderProtocol`

Methods (2 active, more commented out):
- `extract(component, timezone)`, `extract_boolean(component)`

### 6. prtcl_literal.py

**Add:** `LiteralBuilderProtocol`

Methods:
- Static factory pattern for creating literals

### 7. prtcl_field_reference.py

**Add:** `FieldReferenceBuilderProtocol`

Methods:
- Static factory pattern for column references

### 8. prtcl_cast.py

**Add:** `CastBuilderProtocol`

Methods:
- `cast(target_type)`

### 9. prtcl_conditional.py

**Add:** `ConditionalBuilderProtocol`

Methods:
- when/then/otherwise builder pattern

### 10. prtcl_scalar_set.py

**Add:** `ScalarSetBuilderProtocol`

Methods:
- Set membership operations

### 11. prtcl_scalar_rounding.py

**Add:** `ScalarRoundingBuilderProtocol`

Methods:
- Rounding operations (floor, ceil, round, etc.)

### 12. prtcl_scalar_logarithmic.py

**Add:** `ScalarLogarithmicBuilderProtocol`

Methods:
- Logarithmic operations (log, ln, exp, etc.)

### 13. prtcl_scalar_aggregate.py

**Add:** `ScalarAggregateBuilderProtocol`

Methods:
- Aggregate function patterns

### 14. substrait/__init__.py

**Update:** Export all new BuilderProtocols

## Implementation Pattern

Each BuilderProtocol follows the established pattern from deprecated protocols:

```python
from typing import Any, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace


class ScalarComparisonBuilderProtocol(Protocol):
    """Builder protocol for comparison operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseNamespace for chaining.
    """

    def equal(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Equal comparison (==).

        Substrait: equal
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def not_equal(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Not equal comparison (!=).

        Substrait: not_equal
        """
        ...

    # Unary operations take no parameters
    def is_null(self) -> "BaseNamespace":
        """Check if value is null.

        Substrait: is_null
        """
        ...

    # Variadic operations use *args
    def coalesce(self, *others: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Return first non-null value.

        Substrait: coalesce
        """
        ...
```

### Key Patterns

1. **Return Type**: Always `BaseNamespace` for fluent chaining
2. **Input Type**: `Union[BaseNamespace, ExpressionNode, Any]` for flexibility
3. **Variadic**: Use `*args` for operations like `and_()`, `coalesce()`
4. **Unary**: No parameters for operations like `is_null()`, `not_()`
5. **Docstrings**: Include Substrait function name and URI reference

## Execution Order

1. Add `TYPE_CHECKING` imports block to each file
2. Add BuilderProtocol class after ExpressionProtocol class
3. Update `substrait/__init__.py` with new exports
4. Verify no import errors

## Success Criteria

- [ ] All 13 BuilderProtocols created
- [ ] All methods match corresponding ExpressionProtocol signatures
- [ ] Substrait naming convention used consistently
- [ ] `__init__.py` exports all new protocols
- [ ] No import errors when importing from substrait module

## Related Documents

- ADR-002: Substrait BuilderProtocol Migration
- SUBSTRAIT_ALIGNMENT_PLAN.md: Overall alignment strategy
- deprecated/boolean_protocols.py: Reference implementation pattern
