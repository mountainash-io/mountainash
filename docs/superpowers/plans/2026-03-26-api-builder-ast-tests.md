# API Builder AST Construction Tests — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Systematically test that every API builder method constructs the correct AST node with the right function key and arguments — no backend, no DataFrame required.

**Architecture:** Each test calls a method through the public API (`ma.col("x").method(...)`) and asserts on the resulting `._node`. Pytest parametrize groups methods by signature pattern. Alias tests assert equivalence to canonical methods. Unimplemented protocol methods get `xfail` markers.

**Tech Stack:** pytest, mountainash_expressions public API, expression node types, function key enums

**Key imports used in every test file:**
```python
import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import (
    ScalarFunctionNode, FieldReferenceNode, LiteralNode, CastNode, IfThenNode,
)
```

**Key assertion pattern used throughout:**
```python
# For unary methods (no args beyond self):
expr = ma.col("x").method_name()
node = expr._node
assert isinstance(node, ScalarFunctionNode)
assert node.function_key == EXPECTED_FKEY
assert len(node.arguments) == 1
assert isinstance(node.arguments[0], FieldReferenceNode)

# For binary methods (one arg):
expr = ma.col("x").method_name(42)
node = expr._node
assert isinstance(node, ScalarFunctionNode)
assert node.function_key == EXPECTED_FKEY
assert len(node.arguments) == 2
assert isinstance(node.arguments[0], FieldReferenceNode)
assert isinstance(node.arguments[1], LiteralNode)
assert node.arguments[1].value == 42

# For alias equivalence:
canonical = ma.col("x").canonical_method(42)._node
alias = ma.col("x").alias_method(42)._node
assert canonical.function_key == alias.function_key
```

---

### Task 1: Scaffolding + Rounding tests

**Files:**
- Create: `tests/unit/api_builders/__init__.py`
- Create: `tests/unit/api_builders/test_ast_scalar_rounding.py`

- [ ] **Step 1: Create directory and __init__.py**

```python
# tests/unit/api_builders/__init__.py
# (empty file)
```

- [ ] **Step 2: Write test_ast_scalar_rounding.py**

```python
"""AST construction tests for scalar rounding API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ROUNDING


class TestRoundingMethods:
    """Test that rounding methods create correct ScalarFunctionNode."""

    def test_round(self):
        expr = ma.col("x").round(2)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 2

    def test_ceil(self):
        expr = ma.col("x").ceil()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ROUNDING.CEIL
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_floor(self):
        expr = ma.col("x").floor()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ROUNDING.FLOOR
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)
```

- [ ] **Step 3: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_scalar_rounding.py -v`
Expected: 3 PASSED

- [ ] **Step 4: Commit**

```bash
git add tests/unit/api_builders/__init__.py tests/unit/api_builders/test_ast_scalar_rounding.py
git commit -m "test: add AST construction tests for rounding API builders"
```

---

### Task 2: Logarithmic tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_scalar_logarithmic.py`

- [ ] **Step 1: Write test file**

```python
"""AST construction tests for scalar logarithmic API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC


class TestLogarithmicMethods:
    """Test that logarithmic methods create correct ScalarFunctionNode."""

    def test_ln(self):
        expr = ma.col("x").ln()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_log10(self):
        expr = ma.col("x").log10()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG10
        assert len(node.arguments) == 1

    def test_log2(self):
        expr = ma.col("x").log2()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOG2
        assert len(node.arguments) == 1

    def test_log_custom_base(self):
        expr = ma.col("x").log(10)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOGB
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 10
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_scalar_logarithmic.py -v`
Expected: 4 PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/unit/api_builders/test_ast_scalar_logarithmic.py
git commit -m "test: add AST construction tests for logarithmic API builders"
```

---

### Task 3: Cast, Null, and Native tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_cast.py`
- Create: `tests/unit/api_builders/test_ast_null.py`
- Create: `tests/unit/api_builders/test_ast_native.py`

- [ ] **Step 1: Write test_ast_cast.py**

```python
"""AST construction tests for cast API builder."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import CastNode, FieldReferenceNode


class TestCastMethod:
    """Test that cast creates correct CastNode."""

    def test_cast_string(self):
        expr = ma.col("x").cast("f64")
        node = expr._node
        assert isinstance(node, CastNode)
        assert node.target_type == "f64"
        assert isinstance(node.input, FieldReferenceNode)

    def test_cast_python_type(self):
        expr = ma.col("x").cast(int)
        node = expr._node
        assert isinstance(node, CastNode)
        assert node.target_type == "i64"

    def test_cast_bool(self):
        expr = ma.col("x").cast(bool)
        node = expr._node
        assert isinstance(node, CastNode)
        assert node.target_type == "bool"
```

- [ ] **Step 2: Write test_ast_null.py**

```python
"""AST construction tests for null handling API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NULL


class TestNullMethods:
    """Test that null handling methods create correct ScalarFunctionNode."""

    def test_fill_null(self):
        expr = ma.col("x").fill_null(0)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NULL.FILL_NULL
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 0

    def test_null_if(self):
        expr = ma.col("x").null_if("UNKNOWN")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NULL.NULL_IF
        assert len(node.arguments) == 2
        assert node.arguments[1].value == "UNKNOWN"

    def test_fill_nan(self):
        expr = ma.col("x").fill_nan(0)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NULL.FILL_NAN
        assert len(node.arguments) == 2
        assert node.arguments[1].value == 0
```

- [ ] **Step 3: Write test_ast_native.py**

```python
"""AST construction tests for native expression API builder."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ExpressionNode


class TestNativeMethod:
    """Test that as_native creates correct node."""

    def test_native_wraps_expression(self):
        """Native expression should preserve the inner node."""
        expr = ma.native("raw_backend_expr")
        # native() wraps a raw value — the node should exist
        assert expr._node is not None
```

- [ ] **Step 4: Run all three test files**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_cast.py tests/unit/api_builders/test_ast_null.py tests/unit/api_builders/test_ast_native.py -v`
Expected: 7 PASSED

- [ ] **Step 5: Commit**

```bash
git add tests/unit/api_builders/test_ast_cast.py tests/unit/api_builders/test_ast_null.py tests/unit/api_builders/test_ast_native.py
git commit -m "test: add AST construction tests for cast, null, and native API builders"
```

---

### Task 4: Set and Name tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_scalar_set.py`
- Create: `tests/unit/api_builders/test_ast_name.py`

- [ ] **Step 1: Write test_ast_scalar_set.py**

```python
"""AST construction tests for set operations API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_SET,
    FKEY_MOUNTAINASH_SCALAR_SET,
)


class TestSetMethods:
    """Test that set methods create correct ScalarFunctionNode."""

    def test_is_in_list(self):
        expr = ma.col("x").is_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_SET.IS_IN
        assert isinstance(node.arguments[0], FieldReferenceNode)
        # 1 (self) + 3 values = 4 arguments
        assert len(node.arguments) == 4

    def test_is_in_varargs(self):
        expr = ma.col("x").is_in(1, 2, 3)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_SET.IS_IN
        assert len(node.arguments) == 4

    def test_is_not_in(self):
        expr = ma.col("x").is_not_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN
        assert len(node.arguments) == 4

    def test_index_in(self):
        expr = ma.col("x").index_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_SET.INDEX_IN
```

- [ ] **Step 2: Write test_ast_name.py**

```python
"""AST construction tests for name operations API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME


class TestNameMethods:
    """Test that .name methods create correct ScalarFunctionNode."""

    def test_alias(self):
        expr = ma.col("x").name.alias("new_name")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.ALIAS
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == "new_name"

    def test_prefix(self):
        expr = ma.col("x").name.prefix("raw_")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.PREFIX
        assert node.arguments[1].value == "raw_"

    def test_suffix(self):
        expr = ma.col("x").name.suffix("_v2")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.SUFFIX
        assert node.arguments[1].value == "_v2"

    def test_name_to_upper(self):
        expr = ma.col("x").name.name_to_upper()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.NAME_TO_UPPER
        assert len(node.arguments) == 1

    def test_name_to_lower(self):
        expr = ma.col("x").name.name_to_lower()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.NAME_TO_LOWER
        assert len(node.arguments) == 1


class TestNameAliases:
    """Test that name aliases produce identical nodes to canonical methods."""

    def test_to_uppercase_alias(self):
        canonical = ma.col("x").name.name_to_upper()._node
        alias = ma.col("x").name.to_uppercase()._node
        assert canonical.function_key == alias.function_key

    def test_to_lowercase_alias(self):
        canonical = ma.col("x").name.name_to_lower()._node
        alias = ma.col("x").name.to_lowercase()._node
        assert canonical.function_key == alias.function_key
```

- [ ] **Step 3: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_scalar_set.py tests/unit/api_builders/test_ast_name.py -v`
Expected: 11 PASSED

- [ ] **Step 4: Commit**

```bash
git add tests/unit/api_builders/test_ast_scalar_set.py tests/unit/api_builders/test_ast_name.py
git commit -m "test: add AST construction tests for set and name API builders"
```

---

### Task 5: Boolean tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_scalar_boolean.py`

- [ ] **Step 1: Write test file**

```python
"""AST construction tests for boolean API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
    FKEY_MOUNTAINASH_SCALAR_BOOLEAN,
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
)


class TestBooleanBinaryMethods:
    """Test boolean binary methods (take one argument)."""

    def test_and_(self):
        expr = ma.col("a").and_(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND

    def test_or_(self):
        expr = ma.col("a").or_(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR

    def test_and_not(self):
        expr = ma.col("a").and_not(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND_NOT
        assert len(node.arguments) == 2

    def test_xor(self):
        expr = ma.col("a").xor(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.XOR

    def test_not_(self):
        expr = ma.col("a").not_()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT
        assert len(node.arguments) == 1


class TestBooleanExtensionMethods:
    """Test boolean extension methods."""

    def test_xor_parity(self):
        expr = ma.col("a").xor_parity(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_BOOLEAN.XOR_PARITY

    def test_always_true(self):
        expr = ma.col("a").always_true()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_TRUE

    def test_always_false(self):
        expr = ma.col("a").always_false()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_FALSE


class TestBooleanAliases:
    """Test that aliases produce equivalent nodes."""

    def test_xor_alias(self):
        canonical = ma.col("a").xor(ma.col("b"))._node
        alias = ma.col("a").xor_(ma.col("b"))._node
        assert canonical.function_key == alias.function_key
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_scalar_boolean.py -v`
Expected: 9 PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/unit/api_builders/test_ast_scalar_boolean.py
git commit -m "test: add AST construction tests for boolean API builders"
```

---

### Task 6: Conditional tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_conditional.py`

- [ ] **Step 1: Write test file**

The conditional builder uses `IfThenNode` rather than `ScalarFunctionNode`, and has a chained builder pattern: `when()` → `then()` → `otherwise()`. The public API entry point is `ma.when()`.

```python
"""AST construction tests for conditional API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import IfThenNode, FieldReferenceNode, LiteralNode, ScalarFunctionNode


class TestConditionalChain:
    """Test that when/then/otherwise creates correct IfThenNode."""

    def test_simple_when_then_otherwise(self):
        expr = ma.when(ma.col("x").gt(10)).then(ma.lit("big")).otherwise(ma.lit("small"))
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert len(node.conditions) == 1
        # Condition is a ScalarFunctionNode (gt)
        cond, value = node.conditions[0]
        assert isinstance(cond, ScalarFunctionNode)
        assert isinstance(value, LiteralNode)
        assert value.value == "big"
        # Else clause
        assert isinstance(node.else_clause, LiteralNode)
        assert node.else_clause.value == "small"

    def test_chained_when_then(self):
        expr = (
            ma.when(ma.col("x").gt(90)).then(ma.lit("A"))
            .when(ma.col("x").gt(80)).then(ma.lit("B"))
            .otherwise(ma.lit("C"))
        )
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert len(node.conditions) == 2
        assert node.conditions[0][1].value == "A"
        assert node.conditions[1][1].value == "B"
        assert node.else_clause.value == "C"

    def test_instance_when(self):
        """Test when() called on an expression instance (col.when)."""
        expr = ma.col("x").when(ma.col("x").gt(10)).then(ma.lit("y")).otherwise(ma.lit("n"))
        node = expr._node
        assert isinstance(node, IfThenNode)
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_conditional.py -v`
Expected: 3 PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/unit/api_builders/test_ast_conditional.py
git commit -m "test: add AST construction tests for conditional API builders"
```

---

### Task 7: Comparison tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_scalar_comparison.py`

- [ ] **Step 1: Write test file**

```python
"""AST construction tests for comparison API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode, IfThenNode
from mountainash_expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_COMPARISON,
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
)


class TestBinaryComparisons:
    """Test binary comparison methods (self, other) -> ScalarFunctionNode."""

    @pytest.mark.parametrize("method,fkey", [
        ("equal", FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL),
        ("not_equal", FKEY_SUBSTRAIT_SCALAR_COMPARISON.NOT_EQUAL),
        ("lt", FKEY_SUBSTRAIT_SCALAR_COMPARISON.LT),
        ("gt", FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT),
        ("lte", FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE),
        ("gte", FKEY_SUBSTRAIT_SCALAR_COMPARISON.GTE),
    ])
    def test_binary_comparison(self, method, fkey):
        expr = getattr(ma.col("x"), method)(42)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 42


class TestUnaryStateChecks:
    """Test unary state check methods (self) -> ScalarFunctionNode."""

    @pytest.mark.parametrize("method,fkey", [
        ("is_true", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_TRUE),
        ("is_not_true", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_TRUE),
        ("is_false", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FALSE),
        ("is_not_false", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_FALSE),
        ("is_null", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL),
        ("is_not_null", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_NULL),
        ("is_nan", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NAN),
        ("is_finite", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FINITE),
        ("is_infinite", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_INFINITE),
    ])
    def test_unary_state_check(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)


class TestNullHandling:
    """Test null handling comparison methods."""

    def test_nullif(self):
        expr = ma.col("x").nullif(0)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.NULL_IF
        assert len(node.arguments) == 2
        assert node.arguments[1].value == 0


class TestVariadicComparisons:
    """Test variadic comparison methods (self, *others)."""

    @pytest.mark.parametrize("method,fkey", [
        ("coalesce", FKEY_SUBSTRAIT_SCALAR_COMPARISON.COALESCE),
        ("least", FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST),
        ("least_skip_null", FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST_SKIP_NULL),
        ("greatest", FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST),
        ("greatest_skip_null", FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST_SKIP_NULL),
    ])
    def test_variadic_method(self, method, fkey):
        expr = getattr(ma.col("x"), method)(ma.col("y"), ma.col("z"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        # self + 2 others = 3 arguments
        assert len(node.arguments) == 3


class TestBetween:
    """Test between method with options."""

    def test_between(self):
        expr = ma.col("x").between(10, 20)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.BETWEEN
        assert len(node.arguments) == 3
        assert node.arguments[1].value == 10
        assert node.arguments[2].value == 20
        assert node.options["closed"] == "both"

    def test_between_closed_left(self):
        expr = ma.col("x").between(10, 20, closed="left")
        node = expr._node
        assert node.options["closed"] == "left"


class TestComparisonAliases:
    """Test that extension aliases produce equivalent nodes."""

    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("eq", "equal"),
        ("ne", "not_equal"),
        ("ge", "gte"),
        ("le", "lte"),
    ])
    def test_short_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("x"), canonical_method)(42)._node
        alias = getattr(ma.col("x"), alias_method)(42)._node
        assert canonical.function_key == alias.function_key
        assert canonical.arguments[1].value == alias.arguments[1].value

    def test_is_between_alias(self):
        canonical = ma.col("x").between(10, 20)._node
        alias = ma.col("x").is_between(10, 20)._node
        assert canonical.function_key == alias.function_key
        assert canonical.options == alias.options


class TestComparisonCompositions:
    """Test extension composition methods that build complex AST trees."""

    def test_is_not_nan(self):
        expr = ma.col("x").is_not_nan()
        node = expr._node
        # is_not_nan = NOT(is_nan(x))
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT
        inner = node.arguments[0]
        assert isinstance(inner, ScalarFunctionNode)
        assert inner.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NAN

    def test_clip_both(self):
        expr = ma.col("x").clip(lower=0, upper=100)
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert len(node.conditions) == 2

    def test_clip_lower_only(self):
        expr = ma.col("x").clip(lower=0)
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert len(node.conditions) == 1

    def test_eq_missing(self):
        expr = ma.col("x").eq_missing(42)
        node = expr._node
        # eq_missing = (x == other) OR (x.is_null AND other.is_null)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR

    def test_ne_missing(self):
        expr = ma.col("x").ne_missing(42)
        node = expr._node
        # ne_missing = NOT(eq_missing)
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT

    def test_is_close(self):
        expr = ma.col("x").is_close(3.14)
        node = expr._node
        # is_close = abs(x - other) <= threshold
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_scalar_comparison.py -v`
Expected: ~32 PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/unit/api_builders/test_ast_scalar_comparison.py
git commit -m "test: add AST construction tests for comparison API builders"
```

---

### Task 8: Arithmetic tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_scalar_arithmetic.py`

- [ ] **Step 1: Write test file**

```python
"""AST construction tests for arithmetic API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
    FKEY_MOUNTAINASH_SCALAR_ARITHMETIC,
)


class TestBinaryArithmetic:
    """Test binary arithmetic methods (self, other) -> ScalarFunctionNode."""

    @pytest.mark.parametrize("method,fkey", [
        ("add", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD),
        ("subtract", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT),
        ("multiply", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY),
        ("divide", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE),
        ("modulus", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO),
        ("power", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER),
    ])
    def test_binary_arithmetic(self, method, fkey):
        expr = getattr(ma.col("x"), method)(5)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 5


class TestReverseArithmetic:
    """Test reverse arithmetic methods (other op self)."""

    @pytest.mark.parametrize("method,fkey", [
        ("rsubtract", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT),
        ("rdivide", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE),
        ("rmodulus", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO),
        ("rpower", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER),
    ])
    def test_reverse_arithmetic(self, method, fkey):
        expr = getattr(ma.col("x"), method)(10)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        # For reverse ops, the literal comes first
        assert isinstance(node.arguments[0], LiteralNode)
        assert node.arguments[0].value == 10
        assert isinstance(node.arguments[1], FieldReferenceNode)


class TestUnaryArithmetic:
    """Test unary arithmetic methods (self) -> ScalarFunctionNode."""

    @pytest.mark.parametrize("method,fkey", [
        ("negate", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE),
        ("sqrt", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT),
        ("exp", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP),
        ("abs", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS),
        ("sign", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN),
    ])
    def test_unary_arithmetic(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)


class TestTrigonometric:
    """Test trigonometric function methods."""

    @pytest.mark.parametrize("method,fkey", [
        ("sin", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN),
        ("cos", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS),
        ("tan", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN),
        ("asin", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN),
        ("acos", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS),
        ("atan", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN),
    ])
    def test_trig_unary(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1

    def test_atan2(self):
        expr = ma.col("y").atan2(ma.col("x"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2
        assert len(node.arguments) == 2


class TestHyperbolic:
    """Test hyperbolic function methods."""

    @pytest.mark.parametrize("method,fkey", [
        ("sinh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH),
        ("cosh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH),
        ("tanh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH),
        ("asinh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH),
        ("acosh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH),
        ("atanh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH),
    ])
    def test_hyperbolic_unary(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1


class TestAngularConversion:
    """Test radians/degrees conversion methods."""

    @pytest.mark.parametrize("method,fkey", [
        ("radians", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS),
        ("degrees", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES),
    ])
    def test_angular_conversion(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1


class TestExtensionArithmetic:
    """Test Mountainash extension arithmetic methods."""

    def test_floor_divide(self):
        expr = ma.col("x").floor_divide(3)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_ARITHMETIC.FLOOR_DIVIDE
        assert len(node.arguments) == 2

    def test_rfloor_divide(self):
        expr = ma.col("x").rfloor_divide(10)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_ARITHMETIC.FLOOR_DIVIDE
        # Reverse: literal first
        assert isinstance(node.arguments[0], LiteralNode)
        assert node.arguments[0].value == 10


class TestArithmeticAliases:
    """Test that extension aliases produce equivalent nodes."""

    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("sub", "subtract"),
        ("mul", "multiply"),
        ("truediv", "divide"),
        ("mod", "modulus"),
        ("pow", "power"),
    ])
    def test_polars_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("x"), canonical_method)(5)._node
        alias = getattr(ma.col("x"), alias_method)(5)._node
        assert canonical.function_key == alias.function_key
        assert canonical.arguments[1].value == alias.arguments[1].value

    def test_neg_alias(self):
        canonical = ma.col("x").negate()._node
        alias = ma.col("x").neg()._node
        assert canonical.function_key == alias.function_key

    def test_floordiv_alias(self):
        canonical = ma.col("x").floor_divide(3)._node
        alias = ma.col("x").floordiv(3)._node
        assert canonical.function_key == alias.function_key

    def test_modulo_alias(self):
        canonical = ma.col("x").modulus(3)._node
        alias = ma.col("x").modulo(3)._node
        assert canonical.function_key == alias.function_key

    def test_rmodulo_alias(self):
        canonical = ma.col("x").rmodulus(3)._node
        alias = ma.col("x").rmodulo(3)._node
        assert canonical.function_key == alias.function_key


class TestBitwiseStubs:
    """Test bitwise methods — protocol stubs, not yet implemented."""

    @pytest.mark.xfail(reason="bitwise_not is a protocol stub, not yet implemented")
    def test_bitwise_not(self):
        expr = ma.col("x").bitwise_not()
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="bitwise_and is a protocol stub, not yet implemented")
    def test_bitwise_and(self):
        expr = ma.col("x").bitwise_and(ma.col("y"))
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="bitwise_or is a protocol stub, not yet implemented")
    def test_bitwise_or(self):
        expr = ma.col("x").bitwise_or(ma.col("y"))
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="bitwise_xor is a protocol stub, not yet implemented")
    def test_bitwise_xor(self):
        expr = ma.col("x").bitwise_xor(ma.col("y"))
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="shift_left is a protocol stub, not yet implemented")
    def test_shift_left(self):
        expr = ma.col("x").shift_left(2)
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="shift_right is a protocol stub, not yet implemented")
    def test_shift_right(self):
        expr = ma.col("x").shift_right(2)
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="shift_right_unsigned is a protocol stub, not yet implemented")
    def test_shift_right_unsigned(self):
        expr = ma.col("x").shift_right_unsigned(2)
        assert isinstance(expr._node, ScalarFunctionNode)
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_scalar_arithmetic.py -v`
Expected: ~42 PASSED + 7 XFAIL

- [ ] **Step 3: Commit**

```bash
git add tests/unit/api_builders/test_ast_scalar_arithmetic.py
git commit -m "test: add AST construction tests for arithmetic API builders"
```

---

### Task 9: String tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_scalar_string.py`

- [ ] **Step 1: Write test file**

```python
"""AST construction tests for string API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING


class TestStringUnary:
    """Test unary string methods (no args beyond self)."""

    @pytest.mark.parametrize("method,fkey", [
        ("lower", FKEY_SUBSTRAIT_SCALAR_STRING.LOWER),
        ("upper", FKEY_SUBSTRAIT_SCALAR_STRING.UPPER),
        ("swapcase", FKEY_SUBSTRAIT_SCALAR_STRING.SWAPCASE),
        ("capitalize", FKEY_SUBSTRAIT_SCALAR_STRING.CAPITALIZE),
        ("title", FKEY_SUBSTRAIT_SCALAR_STRING.TITLE),
        ("initcap", FKEY_SUBSTRAIT_SCALAR_STRING.INITCAP),
        ("char_length", FKEY_SUBSTRAIT_SCALAR_STRING.CHAR_LENGTH),
        ("bit_length", FKEY_SUBSTRAIT_SCALAR_STRING.BIT_LENGTH),
        ("octet_length", FKEY_SUBSTRAIT_SCALAR_STRING.OCTET_LENGTH),
        ("reverse", FKEY_SUBSTRAIT_SCALAR_STRING.REVERSE),
    ])
    def test_unary_string(self, method, fkey):
        expr = getattr(ma.col("x").str, method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)


class TestStringTrimming:
    """Test trim methods (optional chars argument)."""

    @pytest.mark.parametrize("method,fkey", [
        ("trim", FKEY_SUBSTRAIT_SCALAR_STRING.TRIM),
        ("ltrim", FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM),
        ("rtrim", FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM),
    ])
    def test_trim_default(self, method, fkey):
        expr = getattr(ma.col("x").str, method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey

    @pytest.mark.parametrize("method,fkey", [
        ("trim", FKEY_SUBSTRAIT_SCALAR_STRING.TRIM),
        ("ltrim", FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM),
        ("rtrim", FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM),
    ])
    def test_trim_with_chars(self, method, fkey):
        expr = getattr(ma.col("x").str, method)("xy")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) >= 2


class TestStringPadding:
    """Test padding methods."""

    @pytest.mark.parametrize("method,fkey", [
        ("lpad", FKEY_SUBSTRAIT_SCALAR_STRING.LPAD),
        ("rpad", FKEY_SUBSTRAIT_SCALAR_STRING.RPAD),
    ])
    def test_padding(self, method, fkey):
        expr = getattr(ma.col("x").str, method)(10, "*")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey

    def test_center(self):
        expr = ma.col("x").str.center(10, "*")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.CENTER


class TestStringExtraction:
    """Test substring extraction methods."""

    def test_substring(self):
        expr = ma.col("x").str.substring(1, 3)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING

    @pytest.mark.parametrize("method,fkey", [
        ("left", FKEY_SUBSTRAIT_SCALAR_STRING.LEFT),
        ("right", FKEY_SUBSTRAIT_SCALAR_STRING.RIGHT),
    ])
    def test_left_right(self, method, fkey):
        expr = getattr(ma.col("x").str, method)(5)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey

    def test_replace_slice(self):
        expr = ma.col("x").str.replace_slice(1, 3, "XY")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE


class TestStringSearch:
    """Test string search methods."""

    @pytest.mark.parametrize("method,fkey,arg", [
        ("contains", FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS, "abc"),
        ("starts_with", FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH, "pre"),
        ("ends_with", FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH, "suf"),
    ])
    def test_search_method(self, method, fkey, arg):
        expr = getattr(ma.col("x").str, method)(arg)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2

    def test_strpos(self):
        expr = ma.col("x").str.strpos("abc")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.STRPOS

    def test_count_substring(self):
        expr = ma.col("x").str.count_substring("a")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.COUNT_SUBSTRING


class TestStringManipulation:
    """Test string manipulation methods."""

    def test_replace(self):
        expr = ma.col("x").str.replace("old", "new")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE

    def test_repeat(self):
        expr = ma.col("x").str.repeat(3)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT

    def test_concat(self):
        expr = ma.col("x").str.concat(ma.col("y"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT

    def test_concat_ws(self):
        expr = ma.col("x").str.concat_ws(",", ma.col("y"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT_WS

    def test_string_split(self):
        expr = ma.col("x").str.string_split(",")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.SPLIT


class TestStringPattern:
    """Test pattern matching methods."""

    def test_like(self):
        expr = ma.col("x").str.like("%abc%")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.LIKE

    def test_regexp_match_substring(self):
        expr = ma.col("x").str.regexp_match_substring(r"\d+")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH

    def test_regexp_replace(self):
        expr = ma.col("x").str.regexp_replace(r"\d+", "NUM")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE

    def test_regexp_string_split(self):
        expr = ma.col("x").str.regexp_string_split(r"\s+")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_SPLIT

    def test_regex_match(self):
        expr = ma.col("x").str.regex_match(r"^\d+$")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH

    def test_regex_contains(self):
        expr = ma.col("x").str.regex_contains(r"\d+")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_CONTAINS


class TestStringAliases:
    """Test that extension aliases produce equivalent nodes."""

    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("to_uppercase", "upper"),
        ("to_lowercase", "lower"),
    ])
    def test_case_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("x").str, canonical_method)()._node
        alias = getattr(ma.col("x").str, alias_method)()._node
        assert canonical.function_key == alias.function_key

    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("strip_chars", "trim"),
        ("strip_chars_start", "ltrim"),
        ("strip_chars_end", "rtrim"),
    ])
    def test_strip_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("x").str, canonical_method)()._node
        alias = getattr(ma.col("x").str, alias_method)()._node
        assert canonical.function_key == alias.function_key

    @pytest.mark.parametrize("alias_method", ["len_chars", "length", "len"])
    def test_length_alias(self, alias_method):
        canonical = ma.col("x").str.char_length()._node
        alias = getattr(ma.col("x").str, alias_method)()._node
        assert canonical.function_key == alias.function_key

    def test_strip_prefix(self):
        """strip_prefix is a composition — verify it produces a valid node."""
        expr = ma.col("x").str.strip_prefix("pre_")
        assert expr._node is not None

    def test_strip_suffix(self):
        """strip_suffix is a composition — verify it produces a valid node."""
        expr = ma.col("x").str.strip_suffix("_suf")
        assert expr._node is not None
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_scalar_string.py -v`
Expected: ~50 PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/unit/api_builders/test_ast_scalar_string.py
git commit -m "test: add AST construction tests for string API builders"
```

---

### Task 10: Ternary tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_ternary.py`

- [ ] **Step 1: Write test file**

```python
"""AST construction tests for ternary logic API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_TERNARY


class TestTernaryComparisons:
    """Test ternary comparison methods (self, other) -> ScalarFunctionNode."""

    @pytest.mark.parametrize("method,fkey", [
        ("t_eq", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_EQ),
        ("t_ne", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NE),
        ("t_gt", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GT),
        ("t_lt", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LT),
        ("t_ge", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GE),
        ("t_le", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LE),
    ])
    def test_ternary_comparison(self, method, fkey):
        expr = getattr(ma.col("x"), method)(42)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2


class TestTernarySetMembership:
    """Test ternary set membership methods."""

    def test_t_is_in(self):
        expr = ma.col("x").t_is_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN

    def test_t_is_not_in(self):
        expr = ma.col("x").t_is_not_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_NOT_IN


class TestTernaryLogic:
    """Test ternary logical methods."""

    def test_t_and(self):
        expr = ma.col("x").t_gt(10).t_and(ma.col("y").t_lt(20))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_AND

    def test_t_or(self):
        expr = ma.col("x").t_gt(10).t_or(ma.col("y").t_lt(20))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_OR

    def test_t_not(self):
        expr = ma.col("x").t_gt(10).t_not()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NOT
        assert len(node.arguments) == 1

    def test_t_xor(self):
        expr = ma.col("x").t_gt(10).t_xor(ma.col("y").t_lt(20))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR

    def test_t_xor_parity(self):
        expr = ma.col("x").t_gt(10).t_xor_parity(ma.col("y").t_lt(20))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR_PARITY


class TestTernaryBooleanizers:
    """Test ternary booleanizer methods."""

    @pytest.mark.parametrize("method,fkey", [
        ("is_true", FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_TRUE),
        ("is_false", FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_FALSE),
        ("is_unknown", FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_UNKNOWN),
        ("is_known", FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_KNOWN),
        ("maybe_true", FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_TRUE),
        ("maybe_false", FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_FALSE),
    ])
    def test_booleanizer(self, method, fkey):
        # Start with a ternary expression so booleanizer is valid
        ternary_expr = ma.col("x").t_gt(10)
        expr = getattr(ternary_expr, method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1


class TestTernaryConversion:
    """Test ternary conversion method."""

    def test_to_ternary(self):
        expr = ma.col("x").gt(10).to_ternary()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.TO_TERNARY
        assert len(node.arguments) == 1
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_ternary.py -v`
Expected: ~20 PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/unit/api_builders/test_ast_ternary.py
git commit -m "test: add AST construction tests for ternary API builders"
```

---

### Task 11: Datetime tests

**Files:**
- Create: `tests/unit/api_builders/test_ast_scalar_datetime.py`

- [ ] **Step 1: Write test file**

```python
"""AST construction tests for datetime API builders."""

import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME


class TestDatetimeExtraction:
    """Test datetime extraction methods (unary, via .dt namespace)."""

    @pytest.mark.parametrize("method,fkey", [
        ("year", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_YEAR),
        ("month", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MONTH),
        ("day", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_DAY),
        ("hour", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_HOUR),
        ("minute", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MINUTE),
        ("second", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_SECOND),
        ("millisecond", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MILLISECOND),
        ("microsecond", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MICROSECOND),
        ("nanosecond", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_NANOSECOND),
        ("quarter", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_QUARTER),
        ("day_of_year", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_DAY_OF_YEAR),
        ("day_of_week", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEKDAY),
        ("week_of_year", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEK),
        ("iso_year", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_ISO_YEAR),
        ("unix_timestamp", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_UNIX_TIME),
        ("timezone_offset", FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_TIMEZONE_OFFSET),
    ])
    def test_extraction(self, method, fkey):
        expr = getattr(ma.col("ts").dt, method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)


class TestDatetimeBooleanExtraction:
    """Test boolean extraction methods."""

    @pytest.mark.parametrize("method,fkey", [
        ("is_leap_year", FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_LEAP_YEAR),
        ("is_dst", FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST),
    ])
    def test_boolean_extraction(self, method, fkey):
        expr = getattr(ma.col("ts").dt, method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1


class TestDatetimeAdd:
    """Test add_* methods (binary: self, amount)."""

    @pytest.mark.parametrize("method,fkey", [
        ("add_years", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS),
        ("add_months", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS),
        ("add_days", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS),
        ("add_hours", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS),
        ("add_minutes", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES),
        ("add_seconds", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS),
        ("add_milliseconds", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS),
        ("add_microseconds", FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS),
    ])
    def test_add_method(self, method, fkey):
        expr = getattr(ma.col("ts").dt, method)(5)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 5


class TestDatetimeDiff:
    """Test diff_* methods (binary: self, other)."""

    @pytest.mark.parametrize("method,fkey", [
        ("diff_years", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_YEARS),
        ("diff_months", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_MONTHS),
        ("diff_days", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_DAYS),
        ("diff_hours", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_HOURS),
        ("diff_minutes", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_MINUTES),
        ("diff_seconds", FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_SECONDS),
    ])
    def test_diff_method(self, method, fkey):
        expr = getattr(ma.col("ts").dt, method)(ma.col("other_ts"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2


class TestDatetimeTruncation:
    """Test truncation and rounding methods."""

    @pytest.mark.parametrize("method,fkey", [
        ("truncate", FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE),
        ("round", FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND),
        ("ceil", FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL),
        ("floor", FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR),
    ])
    def test_truncation(self, method, fkey):
        expr = getattr(ma.col("ts").dt, method)("1d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey


class TestDatetimeTimezone:
    """Test timezone methods."""

    def test_to_timezone(self):
        expr = ma.col("ts").dt.to_timezone("UTC")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE

    def test_assume_timezone(self):
        expr = ma.col("ts").dt.assume_timezone("UTC")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.ASSUME_TIMEZONE


class TestDatetimeFormatting:
    """Test formatting methods."""

    def test_strftime(self):
        expr = ma.col("ts").dt.strftime("%Y-%m-%d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.STRFTIME


class TestDatetimeComponents:
    """Test date/time component extraction."""

    def test_date(self):
        expr = ma.col("ts").dt.date()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.DATE

    def test_time(self):
        expr = ma.col("ts").dt.time()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME


class TestDatetimeCalendar:
    """Test calendar helper methods."""

    def test_month_start(self):
        expr = ma.col("ts").dt.month_start()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START

    def test_month_end(self):
        expr = ma.col("ts").dt.month_end()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END

    def test_days_in_month(self):
        expr = ma.col("ts").dt.days_in_month()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH


class TestDatetimeNaturalLanguage:
    """Test natural language duration methods."""

    def test_offset_by(self):
        expr = ma.col("ts").dt.offset_by("1d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY

    def test_within_last(self):
        expr = ma.col("ts").dt.within_last("7d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)

    def test_older_than(self):
        expr = ma.col("ts").dt.older_than("30d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)

    def test_newer_than(self):
        expr = ma.col("ts").dt.newer_than("1h")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)

    def test_within_next(self):
        expr = ma.col("ts").dt.within_next("24h")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)

    def test_between_last(self):
        expr = ma.col("ts").dt.between_last("1d", "7d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)


class TestDatetimeAliases:
    """Test that datetime aliases produce equivalent nodes."""

    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("week", "week_of_year"),
        ("weekday", "day_of_week"),
        ("ordinal_day", "day_of_year"),
    ])
    def test_extraction_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("ts").dt, canonical_method)()._node
        alias = getattr(ma.col("ts").dt, alias_method)()._node
        assert canonical.function_key == alias.function_key

    def test_convert_time_zone_alias(self):
        canonical = ma.col("ts").dt.to_timezone("UTC")._node
        alias = ma.col("ts").dt.convert_time_zone("UTC")._node
        assert canonical.function_key == alias.function_key

    def test_replace_time_zone_alias(self):
        canonical = ma.col("ts").dt.assume_timezone("UTC")._node
        alias = ma.col("ts").dt.replace_time_zone("UTC")._node
        assert canonical.function_key == alias.function_key

    def test_epoch_alias(self):
        canonical = ma.col("ts").dt.unix_timestamp()._node
        alias = ma.col("ts").dt.epoch()._node
        assert canonical.function_key == alias.function_key
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/test_ast_scalar_datetime.py -v`
Expected: ~57 PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/unit/api_builders/test_ast_scalar_datetime.py
git commit -m "test: add AST construction tests for datetime API builders"
```

---

### Task 12: Final verification — run all AST builder tests together

**Files:** None (verification only)

- [ ] **Step 1: Run all API builder AST tests**

Run: `hatch run test:test-target-quick tests/unit/api_builders/ -v`
Expected: ~200+ PASSED + 7 XFAIL + 0 FAILED

- [ ] **Step 2: Run full test suite to check no regressions**

Run: `hatch run test:test-quick`
Expected: All existing tests still pass (2583+ passed)

- [ ] **Step 3: Commit any fixups if needed, then done**

No commit needed unless fixups were required.
