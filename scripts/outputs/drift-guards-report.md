# Drift Guard Report

Generated: 2026-05-13 03:28 UTC  |  Commit: 91f46f8

## Summary

| Suite | Logical gaps | Est. xfail cases |
|-------|-------------|-----------------|
| Protocol alignment (KNOWN_ASPIRATIONAL) | 42 | 42 |
| Argument types — fully unsupported ops | 9 | 104 |
| Argument types — expression-limited ops (KEL) | 47 | 154 |
| Argument types — manual xfail blocks (active) | 2 | ~8 |
| **Total** | **100** | **~308** |

## Protocol Alignment — KNOWN_ASPIRATIONAL

Each entry generates one `test_aspirational_method` xfail case.

| Protocol | Method | Reason | Since |
|----------|--------|--------|-------|
| **MountainAshScalarDatetimeExpressionSystemProtocol** | | | |
| | `assume_timezone` | No function mapping registered | 2026-05-12 |
| | `extract` | No function mapping registered | 2026-05-12 |
| | `extract_boolean` | No function mapping registered | 2026-05-12 |
| | `strftime` | No function mapping registered | 2026-05-12 |
| | `to_timezone` | No function mapping registered | 2026-05-12 |
| **SubstraitAggregateArithmeticExpressionSystemProtocol** | | | |
| | `sum0` | No function mapping registered yet | 2026-05-12 |
| **SubstraitAggregateStringExpressionSystemProtocol** | | | |
| | `string_agg` | No function mapping registered yet | 2026-05-12 |
| **SubstraitFieldReferenceExpressionSystemProtocol** | | | |
| | `col` | Special node type (FieldReferenceNode), not dispatched via function registry | 2026-05-12 |
| **SubstraitLiteralExpressionSystemProtocol** | | | |
| | `lit` | Special node type (LiteralNode), not dispatched via function registry | 2026-05-12 |
| **SubstraitScalarArithmeticExpressionSystemProtocol** | | | |
| | `factorial` | No backend support yet | 2026-05-12 |
| **SubstraitScalarComparisonExpressionSystemProtocol** | | | |
| | `is_distinct_from` | No ENUM, no function mapping, no API builder | 2026-05-12 |
| | `is_not_distinct_from` | No ENUM, no function mapping, no API builder | 2026-05-12 |
| **SubstraitScalarDatetimeExpressionSystemProtocol** | | | |
| | `add` | Datetime dispatch via Mountainash extensions | 2026-05-12 |
| | `gt` | Datetime comparisons handled by scalar_comparison | 2026-05-12 |
| | `gte` | Datetime comparisons handled by scalar_comparison | 2026-05-12 |
| | `local_timestamp` | No function mapping registered | 2026-05-12 |
| | `lt` | Datetime comparisons handled by scalar_comparison | 2026-05-12 |
| | `lte` | Datetime comparisons handled by scalar_comparison | 2026-05-12 |
| | `multiply` | Datetime dispatch via Mountainash extensions | 2026-05-12 |
| | `round_calendar` | No function mapping registered | 2026-05-12 |
| | `round_temporal` | No function mapping registered | 2026-05-12 |
| | `strptime_time` | No function mapping registered | 2026-05-12 |
| | `subtract` | Datetime dispatch via Mountainash extensions | 2026-05-12 |
| **SubstraitScalarGeometryExpressionSystemProtocol** | | | |
| | `buffer` | No function mapping registered yet | 2026-05-12 |
| | `centroid` | No function mapping registered yet | 2026-05-12 |
| | `collection_extract` | No function mapping registered yet | 2026-05-12 |
| | `dimension` | No function mapping registered yet | 2026-05-12 |
| | `envelope` | No function mapping registered yet | 2026-05-12 |
| | `flip_coordinates` | No function mapping registered yet | 2026-05-12 |
| | `geometry_type` | No function mapping registered yet | 2026-05-12 |
| | `is_closed` | No function mapping registered yet | 2026-05-12 |
| | `is_empty` | No function mapping registered yet | 2026-05-12 |
| | `is_ring` | No function mapping registered yet | 2026-05-12 |
| | `is_simple` | No function mapping registered yet | 2026-05-12 |
| | `is_valid` | No function mapping registered yet | 2026-05-12 |
| | `make_line` | No function mapping registered yet | 2026-05-12 |
| | `minimum_bounding_circle` | No function mapping registered yet | 2026-05-12 |
| | `num_points` | No function mapping registered yet | 2026-05-12 |
| | `point` | No function mapping registered yet | 2026-05-12 |
| | `remove_repeated_points` | No function mapping registered yet | 2026-05-12 |
| | `x_coordinate` | No function mapping registered yet | 2026-05-12 |
| | `y_coordinate` | No function mapping registered yet | 2026-05-12 |

## Argument Types — Fully Unsupported Operations

Operations that raise for **all** input types on the listed backend(s).
Source: `_NARWHALS_FULLY_UNSUPPORTED` and `_IBIS_FULLY_UNSUPPORTED` in `test_arg_types_string.py`.

| Operation | Param | Backends | Est. cases |
|-----------|-------|---------|-----------|
| `decode` | `x` | narwhals, ibis | 12 |
| `encode` | `x` | narwhals, ibis | 12 |
| `extract_groups` | `x` | narwhals, ibis | 12 |
| `json_path_match` | `x` | narwhals, ibis | 12 |
| `regexp_count` | `pattern` | narwhals, ibis | 12 |
| `regexp_match_all` | `pattern` | narwhals, ibis | 12 |
| `regexp_strpos` | `pattern` | narwhals, ibis | 12 |
| `repeat` | `count` | narwhals | 8 |
| `to_time` | `x` | narwhals, ibis | 12 |

## Argument Types — Expression-Limited Operations (KEL)

Operations that accept raw/lit arguments but reject `col`/`complex` expressions.
Source: `KNOWN_EXPR_LIMITATIONS` in each backend base class.
Est. cases: polars=2, narwhals=4 (2 sub-backends), ibis=2 per entry.

| Backend | Operation | Param | Est. cases | Message |
|---------|-----------|-------|-----------|---------|
| ibis | `add_days` | `days` | 2 | Ibis datetime offset operations require literal integer values |
| ibis | `add_hours` | `hours` | 2 | Ibis datetime offset operations require literal integer values |
| ibis | `add_microseconds` | `microseconds` | 2 | Ibis datetime offset operations require literal integer values |
| ibis | `add_milliseconds` | `milliseconds` | 2 | Ibis datetime offset operations require literal integer values |
| ibis | `add_minutes` | `minutes` | 2 | Ibis datetime offset operations require literal integer values |
| ibis | `add_months` | `months` | 2 | Ibis datetime offset operations require literal integer values |
| ibis | `add_seconds` | `seconds` | 2 | Ibis datetime offset operations require literal integer values |
| ibis | `add_years` | `years` | 2 | Ibis datetime offset operations require literal integer values |
| narwhals | `add_days` | `days` | 4 | Narwhals datetime offset operations require literal integer values |
| narwhals | `add_hours` | `hours` | 4 | Narwhals datetime offset operations require literal integer values |
| narwhals | `add_microseconds` | `microseconds` | 4 | Narwhals datetime offset operations require literal integer values |
| narwhals | `add_milliseconds` | `milliseconds` | 4 | Narwhals datetime offset operations require literal integer values |
| narwhals | `add_minutes` | `minutes` | 4 | Narwhals datetime offset operations require literal integer values |
| narwhals | `add_months` | `months` | 4 | Narwhals datetime offset operations require literal integer values |
| narwhals | `add_seconds` | `seconds` | 4 | Narwhals datetime offset operations require literal integer values |
| narwhals | `add_years` | `years` | 4 | Narwhals datetime offset operations require literal integer values |
| narwhals | `contains` | `substring` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `ends_with` | `substring` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `left` | `count` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `like` | `match` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `lpad` | `characters` | 4 | Narwhals str.lpad() requires a single literal fill character, not a column expre… |
| narwhals | `lpad` | `length` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `ltrim` | `characters` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `regex_contains` | `pattern` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `regexp_replace` | `pattern` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `regexp_replace` | `replacement` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `replace` | `replacement` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `replace` | `substring` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `right` | `count` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `rpad` | `characters` | 4 | Narwhals str.rpad() requires a single literal fill character, not a column expre… |
| narwhals | `rpad` | `length` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `rtrim` | `characters` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `starts_with` | `substring` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `substring` | `length` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `substring` | `start` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| narwhals | `t_is_in` | `collection` | 4 | Narwhals (as of 2.19.0) does not accept expression arguments for list.contains o… |
| narwhals | `t_is_not_in` | `collection` | 4 | Narwhals (as of 2.19.0) does not accept expression arguments for list.contains o… |
| narwhals | `trim` | `characters` | 4 | Narwhals string methods require literal values, not column references, on the pa… |
| polars | `center` | `character` | 2 | Polars str.center() requires a single literal fill character, not a column expre… |
| polars | `center` | `length` | 2 | Polars str.center() requires a literal integer length, not a column expression |
| polars | `lpad` | `characters` | 2 | Polars str.lpad() requires a single literal fill character, not a column express… |
| polars | `regexp_replace` | `pattern` | 2 | Polars does not support dynamic column patterns in str.replace_all/str.replace w… |
| polars | `repeat` | `count` | 2 | Polars str.repeat() requires a literal integer count, not a column expression |
| polars | `replace` | `substring` | 2 | Polars does not support dynamic column patterns in str.replace |
| polars | `replace_slice` | `length` | 2 | Polars str.replace_slice() requires a literal integer length, not a column expre… |
| polars | `replace_slice` | `start` | 2 | Polars str.replace_slice() requires a literal integer start, not a column expres… |
| polars | `rpad` | `characters` | 2 | Polars str.rpad() requires a single literal fill character, not a column express… |

## Argument Types — Manual xfail Blocks

Module-level `*_XFAIL` variables in `test_arg_types_*.py` files.
**Active**: referenced inside `_params()`. **Inactive**: dead code.

| Variable | File | Active | Reason |
|----------|------|--------|--------|
| `_ATAN2_NW_XFAIL` | `test_arg_types_arithmetic.py` | ✓ active | atan2() is not supported by the Narwhals backend. |
| `_DIFF_NW_XFAIL` | `test_arg_types_datetime.py` | ✗ inactive (dead code) | Narwhals ExprDateTimeNamespace lacks total_days/total_hours/etc methods |
| `_NW_XFAIL` | `test_arg_types_list.py` | ✓ active | Narwhals list namespace not supported on pandas; expression handling issues on polars |
