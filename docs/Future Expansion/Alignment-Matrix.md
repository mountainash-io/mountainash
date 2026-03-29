# Complete Alignment Matrix: Public API → Nodes → Visitors → Backends

**Date:** 2025-01-09
**Purpose:** Document complete alignment across all layers of the expression system

---

## Overview

This document provides a comprehensive mapping of how operations flow through all layers of the mountainash-expressions architecture:

1. **Public API** (ExpressionBuilder methods) - What users call
2. **Expression Nodes** (AST) - What gets created
3. **Visitor Mixins** (Processing) - How nodes are visited
4. **Backend Methods** (Execution) - How operations execute

---

## Layer 1: Core Operations

### Column Reference

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `col(name)` | Function | api/__init__.py | |
| | `ExpressionBuilder` | - | - | - |
| **Node** | `SourceExpressionNode` | CONST_EXPRESSION_TYPES.SOURCE | expression_nodes.py | |
| **Visitor Mixin** | `SourceExpressionVisitor` | visit_source_expression() | source_visitor_mixin.py | |
| **Abstract Method** | `_source_col()` | Abstract | source_visitor_mixin.py | |
| **Backend** | `col(name)` | Concrete | */expression_system.py | |

### Literal Value

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `lit(value)` | Function | api/__init__.py | |
| | `ExpressionBuilder(LiteralNode)` | - | - | - |
| **Node** | `LiteralExpressionNode` | CONST_EXPRESSION_TYPES.LITERAL | expression_nodes.py | |
| **Visitor Mixin** | `LiteralExpressionVisitor` | visit_literal_expression() | literal_visitor_mixin.py | |
| **Abstract Method** | `_lit()` | Abstract | literal_visitor_mixin.py | |
| **Backend** | `lit(value)` | Concrete | */expression_system.py | |

---

## Layer 2: Comparison Operations

### Equality (==)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.eq(other)` | Method | expression_builder.py | |
| **Node** | `BooleanComparisonExpressionNode` | Operator: EQ | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanComparisonExpressionVisitor` | visit_comparison_expression() | boolean_comparison_visitor_mixin.py | |
| **Abstract Method** | `_B_eq(left, right)` | Abstract | boolean_comparison_visitor_mixin.py | |
| **Backend** | `eq(left, right)` | Concrete | */expression_system.py | |

### Inequality (!=)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.ne(other)` | Method | expression_builder.py | |
| **Node** | `BooleanComparisonExpressionNode` | Operator: NE | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanComparisonExpressionVisitor` | visit_comparison_expression() | boolean_comparison_visitor_mixin.py | |
| **Abstract Method** | `_B_ne(left, right)` | Abstract | boolean_comparison_visitor_mixin.py | |
| **Backend** | `ne(left, right)` | Concrete | */expression_system.py | |

### Greater Than (>)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.gt(other)` | Method | expression_builder.py | |
| **Node** | `BooleanComparisonExpressionNode` | Operator: GT | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanComparisonExpressionVisitor` | visit_comparison_expression() | boolean_comparison_visitor_mixin.py | |
| **Abstract Method** | `_B_gt(left, right)` | Abstract | boolean_comparison_visitor_mixin.py | |
| **Backend** | `gt(left, right)` | Concrete | */expression_system.py | |

### Less Than (<)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.lt(other)` | Method | expression_builder.py | |
| **Node** | `BooleanComparisonExpressionNode` | Operator: LT | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanComparisonExpressionVisitor` | visit_comparison_expression() | boolean_comparison_visitor_mixin.py | |
| **Abstract Method** | `_B_lt(left, right)` | Abstract | boolean_comparison_visitor_mixin.py | |
| **Backend** | `lt(left, right)` | Concrete | */expression_system.py | |

### Greater or Equal (>=)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.ge(other)` | Method | expression_builder.py | |
| **Node** | `BooleanComparisonExpressionNode` | Operator: GE | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanComparisonExpressionVisitor` | visit_comparison_expression() | boolean_comparison_visitor_mixin.py | |
| **Abstract Method** | `_B_ge(left, right)` | Abstract | boolean_comparison_visitor_mixin.py | |
| **Backend** | `ge(left, right)` | Concrete | */expression_system.py | |

### Less or Equal (<=)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.le(other)` | Method | expression_builder.py | |
| **Node** | `BooleanComparisonExpressionNode` | Operator: LE | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanComparisonExpressionVisitor` | visit_comparison_expression() | boolean_comparison_visitor_mixin.py | |
| **Abstract Method** | `_B_le(left, right)` | Abstract | boolean_comparison_visitor_mixin.py | |
| **Backend** | `le(left, right)` | Concrete | */expression_system.py | |

---

## Layer 3: Logical Operations

### Logical AND

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.and_(other)` | Method | expression_builder.py | |
| | `and_(*exprs)` | Function | api/__init__.py | |
| **Node** | `BooleanLogicalExpressionNode` | Operator: AND | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanOperatorsExpressionVisitor` | visit_logical_expression() | boolean_operators_visitor_mixin.py | |
| **Abstract Method** | `_B_and(left, right)` | Abstract | boolean_operators_visitor_mixin.py | |
| **Backend** | `and_(left, right)` | Concrete | */expression_system.py | |

### Logical OR

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.or_(other)` | Method | expression_builder.py | |
| | `or_(*exprs)` | Function | api/__init__.py | |
| **Node** | `BooleanLogicalExpressionNode` | Operator: OR | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanOperatorsExpressionVisitor` | visit_logical_expression() | boolean_operators_visitor_mixin.py | |
| **Abstract Method** | `_B_or(left, right)` | Abstract | boolean_operators_visitor_mixin.py | |
| **Backend** | `or_(left, right)` | Concrete | */expression_system.py | |

### Logical NOT

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.not_()` | Method | expression_builder.py | |
| | `not_(expr)` | Function | api/__init__.py | |
| **Node** | `BooleanUnaryExpressionNode` | Operator: NOT | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanUnaryExpressionVisitor` | visit_unary_expression() | boolean_unary_visitor_mixin.py | |
| **Abstract Method** | `_B_not(operand)` | Abstract | boolean_unary_visitor_mixin.py | |
| **Backend** | `not_(operand)` | Concrete | */expression_system.py | |

---

## Layer 4: Arithmetic Operations

### Addition (+)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.add(other)` | Method | expression_builder.py | |
| **Node** | `ArithmeticExpressionNode` | Operator: ADD | expression_nodes.py | |
| **Visitor Mixin** | `ArithmeticOperatorsExpressionVisitor` | visit_arithmetic_expression() | arithmetic_operators_visitor_mixin.py | |
| **Abstract Method** | `_add(left, right)` | Abstract | arithmetic_operators_visitor_mixin.py | |
| **Backend** | `add(left, right)` | Concrete | */expression_system.py | |

### Subtraction (-)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.sub(other)` | Method | expression_builder.py | |
| **Node** | `ArithmeticExpressionNode` | Operator: SUB | expression_nodes.py | |
| **Visitor Mixin** | `ArithmeticOperatorsExpressionVisitor` | visit_arithmetic_expression() | arithmetic_operators_visitor_mixin.py | |
| **Abstract Method** | `_subtract(left, right)` | Abstract | arithmetic_operators_visitor_mixin.py | |
| **Backend** | `subtract(left, right)` | Concrete | */expression_system.py | |

### Multiplication (*)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.mul(other)` | Method | expression_builder.py | |
| **Node** | `ArithmeticExpressionNode` | Operator: MUL | expression_nodes.py | |
| **Visitor Mixin** | `ArithmeticOperatorsExpressionVisitor` | visit_arithmetic_expression() | arithmetic_operators_visitor_mixin.py | |
| **Abstract Method** | `_multiply(left, right)` | Abstract | arithmetic_operators_visitor_mixin.py | |
| **Backend** | `multiply(left, right)` | Concrete | */expression_system.py | |

### Division (/)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.div(other)` | Method | expression_builder.py | |
| **Node** | `ArithmeticExpressionNode` | Operator: DIV | expression_nodes.py | |
| **Visitor Mixin** | `ArithmeticOperatorsExpressionVisitor` | visit_arithmetic_expression() | arithmetic_operators_visitor_mixin.py | |
| **Abstract Method** | `_divide(left, right)` | Abstract | arithmetic_operators_visitor_mixin.py | |
| **Backend** | `divide(left, right)` | Concrete | */expression_system.py | |

### Modulo (%)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.mod(other)` | Method | expression_builder.py | |
| **Node** | `ArithmeticExpressionNode` | Operator: MOD | expression_nodes.py | |
| **Visitor Mixin** | `ArithmeticOperatorsExpressionVisitor` | visit_arithmetic_expression() | arithmetic_operators_visitor_mixin.py | |
| **Abstract Method** | `_modulo(left, right)` | Abstract | arithmetic_operators_visitor_mixin.py | |
| **Backend** | `modulo(left, right)` | Concrete | */expression_system.py | |

### Exponentiation (**)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.pow(other)` | Method | expression_builder.py | |
| **Node** | `ArithmeticExpressionNode` | Operator: POW | expression_nodes.py | |
| **Visitor Mixin** | `ArithmeticOperatorsExpressionVisitor` | visit_arithmetic_expression() | arithmetic_operators_visitor_mixin.py | |
| **Abstract Method** | `_power(left, right)` | Abstract | arithmetic_operators_visitor_mixin.py | |
| **Backend** | `power(left, right)` | Concrete | */expression_system.py | |

### Floor Division (//)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.floor_div(other)` | Method | expression_builder.py | |
| **Node** | `ArithmeticExpressionNode` | Operator: FLOOR_DIV | expression_nodes.py | |
| **Visitor Mixin** | `ArithmeticOperatorsExpressionVisitor` | visit_arithmetic_expression() | arithmetic_operators_visitor_mixin.py | |
| **Abstract Method** | `_floor_divide(left, right)` | Abstract | arithmetic_operators_visitor_mixin.py | |
| **Backend** | `floor_divide(left, right)` | Concrete | */expression_system.py | |

---

## Layer 5: String Operations

### Uppercase

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.upper()` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: UPPER | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_upper(operand)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_upper(operand)` | Concrete | */expression_system.py | |

### Lowercase

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.lower()` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: LOWER | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_lower(operand)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_lower(operand)` | Concrete | */expression_system.py | |

### Trim (Both)

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.trim()` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: TRIM | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_trim(operand)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_trim(operand)` | Concrete | */expression_system.py | |

### Left Trim

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.ltrim()` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: LTRIM | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_ltrim(operand)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_ltrim(operand)` | Concrete | */expression_system.py | |

### Right Trim

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.rtrim()` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: RTRIM | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_rtrim(operand)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_rtrim(operand)` | Concrete | */expression_system.py | |

### Substring

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.substring(start, end)` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: SUBSTRING | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_substring(operand, start, end)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_substring(operand, start, end)` | Concrete | */expression_system.py | |

### Concatenate

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.concat(*others)` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: CONCAT | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_concat(*operands)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_concat(*operands)` | Concrete | */expression_system.py | |

### Length

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.len()` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: LENGTH | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_length(operand)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_length(operand)` | Concrete | */expression_system.py | |

### Replace

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.replace(pattern, replacement)` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: REPLACE | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_replace(operand, pattern, replacement)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_replace(operand, pattern, replacement)` | Concrete | */expression_system.py | |

### Contains

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.contains(substring)` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: CONTAINS | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_contains(operand, substring)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_contains(operand, substring)` | Concrete | */expression_system.py | |

### Starts With

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.startswith(prefix)` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: STARTS_WITH | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_starts_with(operand, prefix)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_starts_with(operand, prefix)` | Concrete | */expression_system.py | |

### Ends With

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.endswith(suffix)` | Method | expression_builder.py | |
| **Node** | `StringExpressionNode` | Operator: ENDS_WITH | expression_nodes.py | |
| **Visitor Mixin** | `StringOperatorsExpressionVisitor` | visit_string_expression() | string_operators_visitor_mixin.py | |
| **Abstract Method** | `_str_ends_with(operand, suffix)` | Abstract | string_operators_visitor_mixin.py | |
| **Backend** | `str_ends_with(operand, suffix)` | Concrete | */expression_system.py | |

---

## Layer 6: Pattern Operations

### LIKE Pattern

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.like(pattern)` | Method | expression_builder.py | |
| **Node** | `PatternExpressionNode` | Operator: LIKE | expression_nodes.py | |
| **Visitor Mixin** | `PatternOperatorsExpressionVisitor` | visit_pattern_expression() | pattern_operators_visitor_mixin.py | |
| **Abstract Method** | `_pattern_like(operand, pattern)` | Abstract | pattern_operators_visitor_mixin.py | |
| **Backend** | `pattern_like(operand, pattern)` | Concrete | */expression_system.py | |

### Regex Match

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.regex_match(pattern)` | Method | expression_builder.py | |
| **Node** | `PatternExpressionNode` | Operator: REGEX_MATCH | expression_nodes.py | |
| **Visitor Mixin** | `PatternOperatorsExpressionVisitor` | visit_pattern_expression() | pattern_operators_visitor_mixin.py | |
| **Abstract Method** | `_pattern_regex_match(operand, pattern)` | Abstract | pattern_operators_visitor_mixin.py | |
| **Backend** | `pattern_regex_match(operand, pattern)` | Concrete | */expression_system.py | |

### Regex Contains

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.regex_contains(pattern)` | Method | expression_builder.py | |
| **Node** | `PatternExpressionNode` | Operator: REGEX_CONTAINS | expression_nodes.py | |
| **Visitor Mixin** | `PatternOperatorsExpressionVisitor` | visit_pattern_expression() | pattern_operators_visitor_mixin.py | |
| **Abstract Method** | `_pattern_regex_contains(operand, pattern)` | Abstract | pattern_operators_visitor_mixin.py | |
| **Backend** | `pattern_regex_contains(operand, pattern)` | Concrete | */expression_system.py | |

### Regex Replace

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.regex_replace(pattern, replacement)` | Method | expression_builder.py | |
| **Node** | `PatternExpressionNode` | Operator: REGEX_REPLACE | expression_nodes.py | |
| **Visitor Mixin** | `PatternOperatorsExpressionVisitor` | visit_pattern_expression() | pattern_operators_visitor_mixin.py | |
| **Abstract Method** | `_pattern_regex_replace(operand, pattern, replacement)` | Abstract | pattern_operators_visitor_mixin.py | |
| **Backend** | `pattern_regex_replace(operand, pattern, replacement)` | Concrete | */expression_system.py | |

---

## Layer 7: Conditional Operations

### When-Then-Otherwise

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.when(cond).then(val).otherwise(alt)` | Method | expression_builder.py | |
| | `when(cond).then(val).otherwise(alt)` | Function | api/__init__.py | |
| **Node** | `BooleanConditionalIfElseExpressionNode` | - | boolean_expression_nodes.py | |
| **Visitor Mixin** | `ConditionalOperatorsExpressionVisitor` | visit_conditional_expression() | conditional_operators_visitor_mixin.py | |
| **Abstract Method** | `_conditional_when(condition, then_value, else_value)` | Abstract | conditional_operators_visitor_mixin.py | |
| **Backend** | `conditional_when(condition, then_value, else_value)` | Concrete | */expression_system.py | |

### Coalesce

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.coalesce(other)` | Method | expression_builder.py | |
| | `coalesce(*values)` | Function | api/__init__.py | |
| **Node** | `ConditionalExpressionNode` (?) | Operator: COALESCE | expression_nodes.py | |
| **Visitor Mixin** | `ConditionalOperatorsExpressionVisitor` | visit_conditional_expression() | conditional_operators_visitor_mixin.py | |
| **Abstract Method** | `_conditional_coalesce(*operands)` | Abstract | conditional_operators_visitor_mixin.py | |
| **Backend** | `conditional_coalesce(*operands)` | Concrete | */expression_system.py | |

### Fill Null

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.fill_null(value)` | Method | expression_builder.py | |
| **Node** | `ConditionalExpressionNode` (?) | Operator: FILL_NULL | expression_nodes.py | |
| **Visitor Mixin** | `ConditionalOperatorsExpressionVisitor` | visit_conditional_expression() | conditional_operators_visitor_mixin.py | |
| **Abstract Method** | `_conditional_fill_null(operand, fill_value)` | Abstract | conditional_operators_visitor_mixin.py | |
| **Backend** | `conditional_fill_null(operand, fill_value)` | Concrete | */expression_system.py | |

---

## Layer 8: Temporal Operations

### Extract Year

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.year()` | Method | expression_builder.py | |
| **Node** | `TemporalExpressionNode` | Operator: YEAR | expression_nodes.py | |
| **Visitor Mixin** | `TemporalOperatorsExpressionVisitor` | visit_temporal_expression() | temporal_operators_visitor_mixin.py | |
| **Abstract Method** | `_temporal_year(operand)` | Abstract | temporal_operators_visitor_mixin.py | |
| **Backend** | `temporal_year(operand)` | Concrete | */expression_system.py | |

### Extract Month

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.month()` | Method | expression_builder.py | |
| **Node** | `TemporalExpressionNode` | Operator: MONTH | expression_nodes.py | |
| **Visitor Mixin** | `TemporalOperatorsExpressionVisitor` | visit_temporal_expression() | temporal_operators_visitor_mixin.py | |
| **Abstract Method** | `_temporal_month(operand)` | Abstract | temporal_operators_visitor_mixin.py | |
| **Backend** | `temporal_month(operand)` | Concrete | */expression_system.py | |

### Extract Day

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.day()` | Method | expression_builder.py | |
| **Node** | `TemporalExpressionNode` | Operator: DAY | expression_nodes.py | |
| **Visitor Mixin** | `TemporalOperatorsExpressionVisitor` | visit_temporal_expression() | temporal_operators_visitor_mixin.py | |
| **Abstract Method** | `_temporal_day(operand)` | Abstract | temporal_operators_visitor_mixin.py | |
| **Backend** | `temporal_day(operand)` | Concrete | */expression_system.py | |

### Extract Hour

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.hour()` | Method | expression_builder.py | |
| **Node** | `TemporalExpressionNode` | Operator: HOUR | expression_nodes.py | |
| **Visitor Mixin** | `TemporalOperatorsExpressionVisitor` | visit_temporal_expression() | temporal_operators_visitor_mixin.py | |
| **Abstract Method** | `_temporal_hour(operand)` | Abstract | temporal_operators_visitor_mixin.py | |
| **Backend** | `temporal_hour(operand)` | Concrete | */expression_system.py | |

### Extract Minute

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.minute()` | Method | expression_builder.py | |
| **Node** | `TemporalExpressionNode` | Operator: MINUTE | expression_nodes.py | |
| **Visitor Mixin** | `TemporalOperatorsExpressionVisitor` | visit_temporal_expression() | temporal_operators_visitor_mixin.py | |
| **Abstract Method** | `_temporal_minute(operand)` | Abstract | temporal_operators_visitor_mixin.py | |
| **Backend** | `temporal_minute(operand)` | Concrete | */expression_system.py | |

### Extract Second

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.second()` | Method | expression_builder.py | |
| **Node** | `TemporalExpressionNode` | Operator: SECOND | expression_nodes.py | |
| **Visitor Mixin** | `TemporalOperatorsExpressionVisitor` | visit_temporal_expression() | temporal_operators_visitor_mixin.py | |
| **Abstract Method** | `_temporal_second(operand)` | Abstract | temporal_operators_visitor_mixin.py | |
| **Backend** | `temporal_second(operand)` | Concrete | */expression_system.py | |

### Extract Weekday

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.weekday()` | Method | expression_builder.py | |
| **Node** | `TemporalExpressionNode` | Operator: WEEKDAY | expression_nodes.py | |
| **Visitor Mixin** | `TemporalOperatorsExpressionVisitor` | visit_temporal_expression() | temporal_operators_visitor_mixin.py | |
| **Abstract Method** | `_temporal_weekday(operand)` | Abstract | temporal_operators_visitor_mixin.py | |
| **Backend** | `temporal_weekday(operand)` | Concrete | */expression_system.py | |

### Add Days

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.add_days(days)` | Method | expression_builder.py | |
| **Node** | `TemporalExpressionNode` | Operator: ADD_DAYS | expression_nodes.py | |
| **Visitor Mixin** | `TemporalOperatorsExpressionVisitor` | visit_temporal_expression() | temporal_operators_visitor_mixin.py | |
| **Abstract Method** | `_temporal_add_days(operand, days)` | Abstract | temporal_operators_visitor_mixin.py | |
| **Backend** | `temporal_add_days(operand, days)` | Concrete | */expression_system.py | |

*(Additional temporal operations follow same pattern: add_months, add_years, add_hours, add_minutes, add_seconds, diff_days, diff_months, diff_years, diff_hours, diff_minutes, diff_seconds, truncate, offset_by)*

---

## Layer 9: Collection Operations

### Is In

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.is_in(values)` | Method | expression_builder.py | |
| **Node** | `BooleanCollectionExpressionNode` | Operator: IS_IN | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanCollectionExpressionVisitor` | visit_collection_expression() | boolean_collection_visitor_mixin.py | |
| **Abstract Method** | `_B_is_in(operand, values)` | Abstract | boolean_collection_visitor_mixin.py | |
| **Backend** | `is_in(operand, values)` | Concrete | */expression_system.py | |

### Is Not In

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.is_not_in(values)` | Method | expression_builder.py | |
| **Node** | `BooleanCollectionExpressionNode` | Operator: IS_NOT_IN | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanCollectionExpressionVisitor` | visit_collection_expression() | boolean_collection_visitor_mixin.py | |
| **Abstract Method** | `_B_is_not_in(operand, values)` | Abstract | boolean_collection_visitor_mixin.py | |
| **Backend** | `not_(is_in(operand, values))` | Composed | */expression_system.py | |

---

## Layer 10: Type Operations

### Cast

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.cast(dtype)` | Method | expression_builder.py | |
| **Node** | `CastExpressionNode` | - | expression_nodes.py | |
| **Visitor Mixin** | `CastExpressionVisitor` | visit_cast_expression() | cast_visitor_mixin.py | |
| **Abstract Method** | `_cast(operand, dtype)` | Abstract | cast_visitor_mixin.py | |
| **Backend** | `cast(operand, dtype)` | Concrete | */expression_system.py | |

---

## Layer 11: Null Operations

### Is Null

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.is_null()` | Method | expression_builder.py | |
| **Node** | `BooleanUnaryExpressionNode` | Operator: IS_NULL | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanUnaryExpressionVisitor` | visit_unary_expression() | boolean_unary_visitor_mixin.py | |
| **Abstract Method** | `_B_is_null(operand)` | Abstract | boolean_unary_visitor_mixin.py | |
| **Backend** | `is_null(operand)` | Concrete | */expression_system.py | |

### Is Not Null

| Layer | Component | Method/Class | File | Line |
|-------|-----------|--------------|------|------|
| **Public API** | `.is_not_null()` | Method | expression_builder.py | |
| **Node** | `BooleanUnaryExpressionNode` | Operator: IS_NOT_NULL | boolean_expression_nodes.py | |
| **Visitor Mixin** | `BooleanUnaryExpressionVisitor` | visit_unary_expression() | boolean_unary_visitor_mixin.py | |
| **Abstract Method** | `_B_is_not_null(operand)` | Abstract | boolean_unary_visitor_mixin.py | |
| **Backend** | `not_(is_null(operand))` | Composed | */expression_system.py | |

---

## Summary Statistics

### Operation Categories

| Category | Public API Methods | Node Types | Visitor Mixins | Abstract Methods | Backend Methods |
|----------|-------------------|------------|----------------|------------------|-----------------|
| Core | 2 (col, lit) | 2 | 2 | 2 | 2 |
| Comparison | 6 | 1 | 1 | 6 | 6 |
| Logical | 3 | 2 | 2 | 7 | 3 |
| Arithmetic | 7 | 1 | 1 | 7 | 7 |
| String | 12 | 1 | 1 | 12 | 12 |
| Pattern | 4 | 1 | 1 | 4 | 4 |
| Conditional | 3 | 2 | 1 | 3 | 3 |
| Temporal | 20+ | 1 | 1 | 23 | 20+ |
| Collection | 2 | 1 | 1 | 2 | 1 |
| Type | 1 | 1 | 1 | 1 | 1 |
| Null | 2 | - | 1 | 2 | 1 |

### Alignment Verification

- ✅ **Public API → Nodes:** 100% aligned (every API method creates corresponding node)
- ✅ **Nodes → Visitors:** 100% aligned (every node has visitor method)
- ✅ **Visitors → Backends:** 100% aligned (every visitor calls backend method)
- ⚠️ **Base Class → Implementations:** Interface drift (19 declared, 60+ implemented)

---

## Proposed Protocol Alignment

After refactoring to protocol-based mixins, the alignment will be:

| Protocol | Visitor Mixin Equivalent | Methods | Backends |
|----------|-------------------------|---------|----------|
| `CoreBackend` | SourceExpressionVisitor + LiteralExpressionVisitor | 2 | Polars/Narwhals/Ibis |
| `ComparisonBackend` | BooleanComparisonExpressionVisitor | 6 | Polars/Narwhals/Ibis |
| `LogicalBackend` | BooleanOperatorsExpressionVisitor (partial) | 3 | Polars/Narwhals/Ibis |
| `ArithmeticBackend` | ArithmeticOperatorsExpressionVisitor | 7 | Polars/Narwhals/Ibis |
| `StringBackend` | StringOperatorsExpressionVisitor | 12 | Polars/Narwhals/Ibis |
| `PatternBackend` | PatternOperatorsExpressionVisitor | 4 | Polars/Narwhals/Ibis |
| `ConditionalBackend` | ConditionalOperatorsExpressionVisitor | 3 | Polars/Narwhals/Ibis |
| `TemporalBackend` | TemporalOperatorsExpressionVisitor | 20+ | Polars/Narwhals/Ibis |

**Result:** Perfect 8:8:8 alignment (8 protocols, 8 visitor categories, 8 backend mixin sets)

---

**Next Steps:** See `Refactoring-Roadmap.md` for implementation plan.
