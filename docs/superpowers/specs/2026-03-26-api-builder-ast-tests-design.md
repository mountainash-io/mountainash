# API Builder AST Construction Tests — Design Spec

> **Date:** 2026-03-26
> **Status:** Draft
> **Triggered by:** Coverage audit revealed that API builder methods have no systematic unit tests verifying AST node construction — only end-to-end cross-backend tests exist for a subset of methods

## Problem Statement

The API builder layer (25 protocol files, 28 implementation files, ~250 methods) has two kinds of existing test coverage:

1. **Structural alignment** (`test_protocol_alignment.py`) — verifies protocol method names and signatures match implementations. Does not call any method.
2. **Cross-backend behavioral** (`tests/cross_backend/`) — tests ~30-40% of operations end-to-end through compile + DataFrame execution. Does not systematically cover every builder method.

The gap: **no test verifies that each API builder method constructs the correct AST node** (right node type, right function key, right arguments). A builder method could exist, match its protocol signature, but produce the wrong `ScalarFunctionNode` — and this would only be caught if a cross-backend test happened to exercise that specific path.

## Design

### Test Level

Pure AST construction — no backend, no DataFrame, no compilation. Each test calls an API builder method through the public API (`ma.col("x").method(...)`) and asserts on the resulting `._node`:

- Node type (e.g., `ScalarFunctionNode`, `CastNode`, `IfThenNode`)
- Function key enum value (e.g., `FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL`)
- Argument count and types
- Literal argument values

### Test Patterns

**Standard method test:**
```python
def test_equal():
    expr = ma.col("x").equal(42)
    node = expr._node
    assert isinstance(node, ScalarFunctionNode)
    assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL
    assert len(node.arguments) == 2
    assert isinstance(node.arguments[0], FieldReferenceNode)
    assert isinstance(node.arguments[1], LiteralNode)
    assert node.arguments[1].value == 42
```

**Namespace method test (`.str`, `.dt`, `.name`):**
```python
def test_str_upper():
    expr = ma.col("x").str.upper()
    node = expr._node
    assert isinstance(node, ScalarFunctionNode)
    assert node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.UPPER
    assert len(node.arguments) == 1
```

**Alias equivalence test:**
```python
def test_eq_alias():
    canonical = ma.col("x").equal(42)._node
    alias = ma.col("x").eq(42)._node
    assert canonical.function_key == alias.function_key
    assert canonical.arguments[1].value == alias.arguments[1].value
```

**Unimplemented protocol method:**
```python
@pytest.mark.xfail(reason="protocol exists but builder not yet implemented")
def test_bitwise_not():
    expr = ma.col("x").bitwise_not()
    assert isinstance(expr._node, ScalarFunctionNode)
```

### File Structure

All test files in `tests/unit/api_builders/`:

| File | Source builder(s) | Methods to test |
|------|-------------------|-----------------|
| `test_ast_scalar_comparison.py` | `api_bldr_scalar_comparison` + `ext_ma_scalar_comparison` | 22 canonical + 10 aliases/compositions |
| `test_ast_scalar_boolean.py` | `api_bldr_scalar_boolean` + `ext_ma_scalar_boolean` | 5 canonical + 4 aliases/extensions |
| `test_ast_scalar_arithmetic.py` | `api_bldr_scalar_arithmetic` + `ext_ma_scalar_arithmetic` | 38 canonical + 11 aliases |
| `test_ast_scalar_string.py` | `api_bldr_scalar_string` + `ext_ma_scalar_string` | 40 canonical + 10 aliases |
| `test_ast_scalar_rounding.py` | `api_bldr_scalar_rounding` | 3 canonical |
| `test_ast_scalar_logarithmic.py` | `api_bldr_scalar_logarithmic` | 4 canonical |
| `test_ast_scalar_datetime.py` | `api_bldr_scalar_datetime` + `ext_ma_scalar_datetime` | 3 substrait + 48 extension + 6 aliases |
| `test_ast_scalar_set.py` | `api_bldr_scalar_set` + `ext_ma_scalar_set` | 1 substrait + 2 extension |
| `test_ast_conditional.py` | `api_bldr_conditional` | 3 (when/then/otherwise chain) |
| `test_ast_cast.py` | `api_bldr_cast` | 1 canonical |
| `test_ast_null.py` | `ext_ma_null` | 3 canonical |
| `test_ast_name.py` | `ext_ma_name` | 5 canonical + 2 aliases |
| `test_ast_ternary.py` | `ext_ma_scalar_ternary` | 20 canonical |
| `test_ast_native.py` | `ext_ma_native` | 1 canonical |

### Method Inventory

#### Substrait Scalar Comparison (22 methods + 10 extension)

**Canonical methods in builder:**
`equal`, `not_equal`, `lt`, `gt`, `lte`, `gte`, `between`, `is_true`, `is_not_true`, `is_false`, `is_not_false`, `is_null`, `is_not_null`, `is_nan`, `is_finite`, `is_infinite`, `nullif`, `coalesce`, `least`, `least_skip_null`, `greatest`, `greatest_skip_null`

**Extension aliases:** `eq`, `ne`, `ge`, `le`, `is_between`
**Extension compositions:** `is_not_nan`, `clip`, `eq_missing`, `ne_missing`, `is_close`

#### Substrait Scalar Boolean (5 methods + 4 extension)

**Canonical:** `and_`, `or_`, `and_not`, `xor`, `not_`
**Extension:** `xor_` (alias for xor), `xor_parity`, `always_true`, `always_false`

#### Substrait Scalar Arithmetic (38 methods + 11 extension)

**Canonical:** `add`, `subtract`, `rsubtract`, `multiply`, `divide`, `rdivide`, `modulus`, `rmodulus`, `power`, `rpower`, `negate`, `sqrt`, `exp`, `abs`, `sign`, `sin`, `cos`, `tan`, `sinh`, `cosh`, `tanh`, `asin`, `acos`, `atan`, `asinh`, `acosh`, `atanh`, `atan2`, `radians`, `degrees`, `bitwise_not`, `bitwise_and`, `bitwise_or`, `bitwise_xor`, `shift_left`, `shift_right`, `shift_right_unsigned`, `factorial`

**Extension:** `floor_divide`, `rfloor_divide`, `sub`, `mul`, `truediv`, `floordiv`, `mod`, `pow`, `neg`, `modulo`, `rmodulo`

Note: Bitwise operations and `factorial` may be stubs (xfail if they raise `NotImplementedError` or produce no valid node).

#### Substrait Scalar String (40 methods + 10 extension)

**Canonical:** `lower`, `upper`, `swapcase`, `capitalize`, `title`, `initcap`, `ltrim`, `rtrim`, `trim`, `lpad`, `rpad`, `center`, `substring`, `left`, `right`, `replace_slice`, `contains`, `starts_with`, `ends_with`, `strpos`, `count_substring`, `char_length`, `bit_length`, `octet_length`, `concat`, `concat_ws`, `replace`, `repeat`, `reverse`, `like`, `regexp_match_substring`, `regexp_match_substring_all`, `regexp_strpos`, `regexp_count_substring`, `regexp_replace`, `regex_replace`, `string_split`, `regexp_string_split`, `regex_match`, `regex_contains`

**Extension aliases:** `to_uppercase`, `to_lowercase`, `strip_chars`, `strip_chars_start`, `strip_chars_end`, `len_chars`, `length`, `len`
**Extension compositions:** `strip_prefix`, `strip_suffix`

#### Substrait Scalar Rounding (3 methods)

`ceil`, `floor`, `round`

#### Substrait Scalar Logarithmic (4 methods)

`ln`, `log10`, `log2`, `log`

#### Substrait Scalar Datetime (3 substrait + 48 extension + 6 aliases)

**Substrait:** `local_timestamp`, `assume_timezone`, `strftime`

**Extension canonical:** `year`, `month`, `day`, `hour`, `minute`, `second`, `millisecond`, `microsecond`, `nanosecond`, `quarter`, `day_of_year`, `day_of_week`, `week_of_year`, `iso_year`, `unix_timestamp`, `timezone_offset`, `is_leap_year`, `is_dst`, `add_years`, `add_months`, `add_days`, `add_hours`, `add_minutes`, `add_seconds`, `add_milliseconds`, `add_microseconds`, `diff_years`, `diff_months`, `diff_days`, `diff_hours`, `diff_minutes`, `diff_seconds`, `truncate`, `round`, `ceil`, `floor`, `to_timezone`, `offset_by`, `within_last`, `older_than`, `newer_than`, `within_next`, `between_last`, `date`, `time`, `month_start`, `month_end`, `days_in_month`

**Extension aliases:** `week = week_of_year`, `weekday = day_of_week`, `ordinal_day = day_of_year`, `convert_time_zone = to_timezone`, `replace_time_zone = assume_timezone`, `epoch = unix_timestamp`

#### Scalar Set (1 substrait + 2 extension)

**Substrait:** `index_in`
**Extension:** `is_in`, `is_not_in`

#### Conditional (3 methods across 3 classes)

`when` → `then` → `otherwise`

#### Cast (1 method)

`cast`

#### Null Extension (3 methods)

`fill_null`, `null_if`, `fill_nan`

#### Name Extension (5 methods + 2 aliases)

**Canonical:** `alias`, `prefix`, `suffix`, `name_to_upper`, `name_to_lower`
**Aliases:** `to_lowercase = name_to_lower`, `to_uppercase = name_to_upper`

#### Ternary Extension (20 methods)

`t_eq`, `t_ne`, `t_gt`, `t_lt`, `t_ge`, `t_le`, `t_is_in`, `t_is_not_in`, `t_and`, `t_or`, `t_not`, `t_xor`, `t_xor_parity`, `is_true`, `is_false`, `is_unknown`, `is_known`, `maybe_true`, `maybe_false`, `to_ternary`

#### Native Extension (1 method)

`as_native`

### Estimated Test Count

| Category | Canonical | Alias equiv | Xfail stubs | Total |
|----------|-----------|-------------|-------------|-------|
| Comparison | 22 | 10 | 0 | 32 |
| Boolean | 5 | 4 | 0 | 9 |
| Arithmetic | 30 | 11 | 8 (bitwise + factorial) | 49 |
| String | 40 | 10 | 0 | 50 |
| Rounding | 3 | 0 | 0 | 3 |
| Logarithmic | 4 | 0 | 0 | 4 |
| Datetime | 51 | 6 | 0 | 57 |
| Set | 3 | 0 | 0 | 3 |
| Conditional | 3 | 0 | 0 | 3 |
| Cast | 1 | 0 | 0 | 1 |
| Null | 3 | 0 | 0 | 3 |
| Name | 5 | 2 | 0 | 7 |
| Ternary | 20 | 0 | 0 | 20 |
| Native | 1 | 0 | 0 | 1 |
| **Total** | **191** | **43** | **8** | **242** |

### What This Does NOT Cover

- Backend compilation correctness (covered by cross-backend tests)
- Parameter sensitivity (covered by `test_parameter_sensitivity.py`)
- Value correctness across backends (covered by cross-backend tests)
- End-to-end DataFrame execution
- Window functions (not yet in API builders)

## Out of Scope

- Implementing missing builder methods for unimplemented protocol stubs
- Refactoring existing cross-backend tests
- Adding new cross-backend behavioral tests
- Modifying any source code — this is a test-only change
