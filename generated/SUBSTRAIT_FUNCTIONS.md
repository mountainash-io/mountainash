# Substrait Functions Report

Generated: 2025-12-30T19:58:00.698091

## Summary

Total functions: **204**

| Function Type | Count |
|---------------|-------|
| Scalar | 164 |
| Aggregate | 29 |
| Window | 11 |

### By Category

| Category | Scalar | Aggregate | Window | Total |
|----------|--------|-----------|--------|-------|
| aggregate_approx | 0 | 1 | 0 | 1 |
| aggregate_generic | 0 | 3 | 0 | 3 |
| aggregate_decimal | 0 | 3 | 0 | 3 |
| arithmetic | 34 | 12 | 11 | 57 |
| arithmetic_decimal | 12 | 5 | 0 | 17 |
| boolean | 5 | 2 | 0 | 7 |
| comparison | 24 | 0 | 0 | 24 |
| datetime | 18 | 2 | 0 | 20 |
| geometry | 19 | 0 | 0 | 19 |
| logarithmic | 5 | 0 | 0 | 5 |
| rounding | 3 | 0 | 0 | 3 |
| rounding_decimal | 3 | 0 | 0 | 3 |
| set | 1 | 0 | 0 | 1 |
| string | 40 | 1 | 0 | 41 |

## Functions by Category and Type

### Aggregate_Approx

#### Aggregate Functions (1)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `approx_count_distinct` | `approx_count_distinct` | 1 | - | Calculates the approximate number of rows that con... |

### Aggregate_Generic

#### Aggregate Functions (3)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `count` | `count` | 1 | overflow | Count a set of values |
| `count` | `count` | 0 | overflow | Count a set of records (not field referenced) |
| `any_value` | `any_value` | 1 | ignore_nulls | Selects an arbitrary value from a group of values.... |

### Aggregate_Decimal

#### Aggregate Functions (3)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `count` | `count` | 1 | overflow | Count a set of values. Result is returned as a dec... |
| `count` | `count` | 0 | overflow | Count a set of records (not field referenced). Res... |
| `approx_count_distinct` | `approx_count_distinct` | 1 | - | Calculates the approximate number of rows that con... |

### Arithmetic

#### Scalar Functions (34)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `add` | `add` | 2 | overflow | Add two values. |
| `subtract` | `subtract` | 2 | overflow | Subtract one value from another. |
| `multiply` | `multiply` | 2 | overflow | Multiply two values. |
| `divide` | `divide` | 2 | overflow, on_domain_error, on_division_by_zero | Divide x by y. In the case of integer division, pa... |
| `negate` | `negate` | 1 | overflow | Negation of the value |
| `modulus` | `modulus` | 2 | division_type, overflow, on_domain_error | Calculate the remainder (r) when dividing dividend... |
| `power` | `power` | 2 | overflow | Take the power with x as the base and y as exponen... |
| `sqrt` | `sqrt` | 1 | rounding, on_domain_error | Square root of the value |
| `exp` | `exp` | 1 | rounding | The mathematical constant e, raised to the power o... |
| `cos` | `cos` | 1 | rounding | Get the cosine of a value in radians. |
| `sin` | `sin` | 1 | rounding | Get the sine of a value in radians. |
| `tan` | `tan` | 1 | rounding | Get the tangent of a value in radians. |
| `cosh` | `cosh` | 1 | rounding | Get the hyperbolic cosine of a value in radians. |
| `sinh` | `sinh` | 1 | rounding | Get the hyperbolic sine of a value in radians. |
| `tanh` | `tanh` | 1 | rounding | Get the hyperbolic tangent of a value in radians. |
| `acos` | `acos` | 1 | rounding, on_domain_error | Get the arccosine of a value in radians. |
| `asin` | `asin` | 1 | rounding, on_domain_error | Get the arcsine of a value in radians. |
| `atan` | `atan` | 1 | rounding | Get the arctangent of a value in radians. |
| `acosh` | `acosh` | 1 | rounding, on_domain_error | Get the hyperbolic arccosine of a value in radians... |
| `asinh` | `asinh` | 1 | rounding | Get the hyperbolic arcsine of a value in radians. |
| `atanh` | `atanh` | 1 | rounding, on_domain_error | Get the hyperbolic arctangent of a value in radian... |
| `atan2` | `atan2` | 2 | rounding, on_domain_error | Get the arctangent of values given as x/y pairs. |
| `radians` | `radians` | 1 | rounding | Converts angle `x` in degrees to radians.
 |
| `degrees` | `degrees` | 1 | rounding | Converts angle `x` in radians to degrees.
 |
| `abs` | `abs` | 1 | overflow | Calculate the absolute value of the argument.
Inte... |
| `sign` | `sign` | 1 | - | Return the signedness of the argument.
Integer val... |
| `factorial` | `factorial` | 1 | overflow | Return the factorial of a given integer input.
The... |
| `bitwise_not` | `bitwise_not` | 1 | - | Return the bitwise NOT result for one integer inpu... |
| `bitwise_and` | `bitwise_and` | 2 | - | Return the bitwise AND result for two integer inpu... |
| `bitwise_or` | `bitwise_or` | 2 | - | Return the bitwise OR result for two given integer... |
| `bitwise_xor` | `bitwise_xor` | 2 | - | Return the bitwise XOR result for two integer inpu... |
| `shift_left` | `shift_left` | 2 | - | Bitwise shift left. The vacant (least-significant)... |
| `shift_right` | `shift_right` | 2 | - | Bitwise (signed) shift right. The vacant (most-sig... |
| `shift_right_unsigned` | `shift_right_unsigned` | 2 | - | Bitwise unsigned shift right. The vacant (most-sig... |

#### Aggregate Functions (12)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `sum` | `sum` | 1 | overflow | Sum a set of values. The sum of zero elements yiel... |
| `sum0` | `sum0` | 1 | overflow | Sum a set of values. The sum of zero elements yiel... |
| `avg` | `avg` | 1 | overflow | Average a set of values. For integral types, this ... |
| `min` | `min` | 1 | - | Min a set of values. |
| `max` | `max` | 1 | - | Max a set of values. |
| `product` | `product` | 1 | overflow | Product of a set of values. Returns 1 for empty in... |
| `std_dev` | `std_dev` | 1 | rounding, distribution | Calculates standard-deviation for a set of values. |
| `variance` | `variance` | 1 | rounding, distribution | Calculates variance for a set of values. |
| `corr` | `corr` | 2 | rounding | Calculates the value of Pearson's correlation coef... |
| `mode` | `mode` | 1 | - | Calculates mode for a set of values. If there is n... |
| `median` | `median` | 2 | rounding | Calculate the median for a set of values.
Returns ... |
| `quantile` | `quantile` | 4 | rounding | Calculates quantiles for a set of values.
This fun... |

#### Window Functions (11)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `row_number` | `row_number` | 0 | - | the number of the current row within its partition... |
| `rank` | `rank` | 0 | - | the rank of the current row, with gaps. |
| `dense_rank` | `dense_rank` | 0 | - | the rank of the current row, without gaps. |
| `percent_rank` | `percent_rank` | 0 | - | the relative rank of the current row. |
| `cume_dist` | `cume_dist` | 0 | - | the cumulative distribution. |
| `ntile` | `ntile` | 1 | - | Return an integer ranging from 1 to the argument v... |
| `first_value` | `first_value` | 1 | - | Returns the first value in the window.
 |
| `last_value` | `last_value` | 1 | - | Returns the last value in the window.
 |
| `nth_value` | `nth_value` | 2 | on_domain_error | Returns a value from the nth row based on the `win... |
| `lead` | `lead` | 1 | - | Return a value from a following row based on a spe... |
| `lag` | `lag` | 1 | - | Return a column value from a previous row based on... |

### Arithmetic_Decimal

#### Scalar Functions (12)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `add` | `add` | 2 | overflow | Add two decimal values. |
| `subtract` | `subtract` | 2 | overflow |  |
| `multiply` | `multiply` | 2 | overflow |  |
| `divide` | `divide` | 2 | overflow |  |
| `modulus` | `modulus` | 2 | overflow |  |
| `abs` | `abs` | 1 | - | Calculate the absolute value of the argument. |
| `bitwise_and` | `bitwise_and` | 2 | - | Return the bitwise AND result for two decimal inpu... |
| `bitwise_or` | `bitwise_or` | 2 | - | Return the bitwise OR result for two given decimal... |
| `bitwise_xor` | `bitwise_xor` | 2 | - | Return the bitwise XOR result for two given decima... |
| `sqrt` | `sqrt` | 1 | - | Square root of the value. Sqrt of 0 is 0 and sqrt ... |
| `factorial` | `factorial` | 1 | - | Return the factorial of a given decimal input. Sca... |
| `power` | `power` | 2 | overflow, complex_number_result | Take the power with x as the base and y as exponen... |

#### Aggregate Functions (5)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `sum` | `sum` | 1 | overflow | Sum a set of values. |
| `avg` | `avg` | 1 | overflow | Average a set of values. |
| `min` | `min` | 1 | - | Min a set of values. |
| `max` | `max` | 1 | - | Max a set of values. |
| `sum0` | `sum0` | 1 | overflow | Sum a set of values. The sum of zero elements yiel... |

### Boolean

#### Scalar Functions (5)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `or` | `or_` | variadic | - | The boolean `or` using Kleene logic.
This function... |
| `and` | `and_` | variadic | - | The boolean `and` using Kleene logic.
This functio... |
| `and_not` | `and_not` | 2 | - | The boolean `and` of one value and the negation of... |
| `xor` | `xor` | 2 | - | The boolean `xor` of two values using Kleene logic... |
| `not` | `not_` | 1 | - | The `not` of a boolean value.
When a null is input... |

#### Aggregate Functions (2)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `bool_and` | `bool_and` | 1 | - | If any value in the input is false, false is retur... |
| `bool_or` | `bool_or` | 1 | - | If any value in the input is true, true is returne... |

### Comparison

#### Scalar Functions (24)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `not_equal` | `not_equal` | 2 | - | Whether two values are not_equal.
`not_equal(x, y)... |
| `equal` | `equal` | 2 | - | Whether two values are equal.
`equal(x, y) := (x =... |
| `is_not_distinct_from` | `is_not_distinct_from` | 2 | - | Whether two values are equal.
This function treats... |
| `is_distinct_from` | `is_distinct_from` | 2 | - | Whether two values are not equal.
This function tr... |
| `lt` | `lt` | 2 | - | Less than.
lt(x, y) := (x < y)
If either/both of `... |
| `gt` | `gt` | 2 | - | Greater than.
gt(x, y) := (x > y)
If either/both o... |
| `lte` | `lte` | 2 | - | Less than or equal to.
lte(x, y) := (x <= y)
If ei... |
| `gte` | `gte` | 2 | - | Greater than or equal to.
gte(x, y) := (x >= y)
If... |
| `between` | `between` | 3 | - | Whether the `expression` is greater than or equal ... |
| `is_true` | `is_true` | 1 | - | Whether a value is true. |
| `is_not_true` | `is_not_true` | 1 | - | Whether a value is not true. |
| `is_false` | `is_false` | 1 | - | Whether a value is false. |
| `is_not_false` | `is_not_false` | 1 | - | Whether a value is not false. |
| `is_null` | `is_null` | 1 | - | Whether a value is null. NaN is not null. |
| `is_not_null` | `is_not_null` | 1 | - | Whether a value is not null. NaN is not null. |
| `is_nan` | `is_nan` | 1 | - | Whether a value is not a number.
If `x` is `null`,... |
| `is_finite` | `is_finite` | 1 | - | Whether a value is finite (neither infinite nor Na... |
| `is_infinite` | `is_infinite` | 1 | - | Whether a value is infinite.
If `x` is `null`, `nu... |
| `nullif` | `nullif` | 2 | - | If two values are equal, return null. Otherwise, r... |
| `coalesce` | `coalesce` | variadic | - | Evaluate arguments from left to right and return t... |
| `least` | `least` | variadic | - | Evaluates each argument and returns the smallest o... |
| `least_skip_null` | `least_skip_null` | variadic | - | Evaluates each argument and returns the smallest o... |
| `greatest` | `greatest` | variadic | - | Evaluates each argument and returns the largest on... |
| `greatest_skip_null` | `greatest_skip_null` | variadic | - | Evaluates each argument and returns the largest on... |

### Datetime

#### Scalar Functions (18)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `extract` | `extract` | 3 | - | Extract portion of a date/time value. * YEAR Retur... |
| `extract_boolean` | `extract_boolean` | 2 | - | Extract boolean values of a date/time value. * IS_... |
| `add` | `add` | 2 | - | Add an interval to a date/time type.
Timezone stri... |
| `multiply` | `multiply` | 2 | - | Multiply an interval by an integral number. |
| `add_intervals` | `add_intervals` | 2 | - | Add two intervals together. |
| `subtract` | `subtract` | 2 | - | Subtract an interval from a date/time type.
Timezo... |
| `lte` | `lte` | 2 | - | less than or equal to |
| `lt` | `lt` | 2 | - | less than |
| `gte` | `gte` | 2 | - | greater than or equal to |
| `gt` | `gt` | 2 | - | greater than |
| `assume_timezone` | `assume_timezone` | 2 | - | Convert local timestamp to UTC-relative timestamp_... |
| `local_timestamp` | `local_timestamp` | 2 | - | Convert UTC-relative timestamp_tz to local timesta... |
| `strptime_time` | `strptime_time` | 2 | - | Parse string into time using provided format, see ... |
| `strptime_date` | `strptime_date` | 2 | - | Parse string into date using provided format, see ... |
| `strptime_timestamp` | `strptime_timestamp` | 3 | - | Parse string into timestamp using provided format,... |
| `strftime` | `strftime` | 2 | - | Convert timestamp/date/time to string using provid... |
| `round_temporal` | `round_temporal` | 5 | - | Round a given timestamp/date/time to a multiple of... |
| `round_calendar` | `round_calendar` | 5 | - | Round a given timestamp/date/time to a multiple of... |

#### Aggregate Functions (2)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `min` | `min` | 1 | - | Min a set of values. |
| `max` | `max` | 1 | - | Max a set of values. |

### Geometry

#### Scalar Functions (19)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `point` | `point` | 2 | - | Returns a 2D point with the given `x` and `y` coor... |
| `make_line` | `make_line` | 2 | - | Returns a linestring connecting the endpoint of ge... |
| `x_coordinate` | `x_coordinate` | 1 | - | Return the x coordinate of the point.  Return null... |
| `y_coordinate` | `y_coordinate` | 1 | - | Return the y coordinate of the point.  Return null... |
| `num_points` | `num_points` | 1 | - | Return the number of points in the geometry.  The ... |
| `is_empty` | `is_empty` | 1 | - | Return true is the geometry is an empty geometry.
 |
| `is_closed` | `is_closed` | 1 | - | Return true if the geometry's start and end points... |
| `is_simple` | `is_simple` | 1 | - | Return true if the geometry does not self intersec... |
| `is_ring` | `is_ring` | 1 | - | Return true if the geometry's start and end points... |
| `geometry_type` | `geometry_type` | 1 | - | Return the type of geometry as a string.
 |
| `envelope` | `envelope` | 1 | - | Return the minimum bounding box for the input geom... |
| `dimension` | `dimension` | 1 | - | Return the dimension of the input geometry.  If th... |
| `is_valid` | `is_valid` | 1 | - | Return true if the input geometry is a valid 2D ge... |
| `collection_extract` | `collection_extract` | 1 | - | Given the input geometry collection, return a homo... |
| `flip_coordinates` | `flip_coordinates` | 1 | - | Return a version of the input geometry with the X ... |
| `remove_repeated_points` | `remove_repeated_points` | 1 | - | Return a version of the input geometry with duplic... |
| `buffer` | `buffer` | 2 | - | Compute and return an expanded version of the inpu... |
| `centroid` | `centroid` | 1 | - | Return a point which is the geometric center of ma... |
| `minimum_bounding_circle` | `minimum_bounding_circle` | 1 | - | Return the smallest circle polygon that contains t... |

### Logarithmic

#### Scalar Functions (5)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `ln` | `ln` | 1 | rounding, on_domain_error, on_log_zero | Natural logarithm of the value |
| `log10` | `log10` | 1 | rounding, on_domain_error, on_log_zero | Logarithm to base 10 of the value |
| `log2` | `log2` | 1 | rounding, on_domain_error, on_log_zero | Logarithm to base 2 of the value |
| `logb` | `logb` | 2 | rounding, on_domain_error, on_log_zero | Logarithm of the value with the given base
logb(x,... |
| `log1p` | `log1p` | 1 | rounding, on_domain_error, on_log_zero | Natural logarithm (base e) of 1 + x
log1p(x) => lo... |

### Rounding

#### Scalar Functions (3)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `ceil` | `ceil` | 1 | - | Rounding to the ceiling of the value `x`.
 |
| `floor` | `floor` | 1 | - | Rounding to the floor of the value `x`.
 |
| `round` | `round` | 2 | rounding | Rounding the value `x` to `s` decimal places.
 |

### Rounding_Decimal

#### Scalar Functions (3)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `ceil` | `ceil` | 1 | - | Rounding to the ceiling of the value `x`.
 |
| `floor` | `floor` | 1 | - | Rounding to the floor of the value `x`.
 |
| `round` | `round` | 2 | rounding | Rounding the value `x` to `s` decimal places.
 |

### Set

#### Scalar Functions (1)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `index_in` | `index_in` | 2 | nan_equality | Checks the membership of a value in a list of valu... |

### String

#### Scalar Functions (40)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `concat` | `concat` | variadic | null_handling | Concatenate strings.
The `null_handling` option de... |
| `like` | `like` | 2 | case_sensitivity | Are two strings like each other.
The `case_sensiti... |
| `substring` | `substring` | 3 | negative_start | Extract a substring of a specified `length` starti... |
| `regexp_match_substring` | `regexp_match_substring` | 5 | case_sensitivity, multiline, dotall | Extract a substring that matches the given regular... |
| `regexp_match_substring` | `regexp_match_substring` | 2 | case_sensitivity, multiline, dotall | Extract a substring that matches the given regular... |
| `regexp_match_substring_all` | `regexp_match_substring_all` | 4 | case_sensitivity, multiline, dotall | Extract all substrings that match the given regula... |
| `starts_with` | `starts_with` | 2 | case_sensitivity | Whether the `input` string starts with the `substr... |
| `ends_with` | `ends_with` | 2 | case_sensitivity | Whether `input` string ends with the substring.
Th... |
| `contains` | `contains` | 2 | case_sensitivity | Whether the `input` string contains the `substring... |
| `strpos` | `strpos` | 2 | case_sensitivity | Return the position of the first occurrence of a s... |
| `regexp_strpos` | `regexp_strpos` | 4 | case_sensitivity, multiline, dotall | Return the position of an occurrence of the given ... |
| `count_substring` | `count_substring` | 2 | case_sensitivity | Return the number of non-overlapping occurrences o... |
| `regexp_count_substring` | `regexp_count_substring` | 3 | case_sensitivity, multiline, dotall | Return the number of non-overlapping occurrences o... |
| `regexp_count_substring` | `regexp_count_substring` | 2 | case_sensitivity, multiline, dotall | Return the number of non-overlapping occurrences o... |
| `replace` | `replace` | 3 | case_sensitivity | Replace all occurrences of the substring with the ... |
| `concat_ws` | `concat_ws` | variadic | - | Concatenate strings together separated by a separa... |
| `repeat` | `repeat` | 2 | - | Repeat a string `count` number of times. |
| `reverse` | `reverse` | 1 | - | Returns the string in reverse order. |
| `replace_slice` | `replace_slice` | 4 | - | Replace a slice of the input string.  A specified ... |
| `lower` | `lower` | 1 | char_set | Transform the string to lower case characters. Imp... |
| `upper` | `upper` | 1 | char_set | Transform the string to upper case characters. Imp... |
| `swapcase` | `swapcase` | 1 | char_set | Transform the string's lowercase characters to upp... |
| `capitalize` | `capitalize` | 1 | char_set | Capitalize the first character of the input string... |
| `title` | `title` | 1 | char_set | Converts the input string into titlecase. Capitali... |
| `initcap` | `initcap` | 1 | char_set | Capitalizes the first character of each word in th... |
| `char_length` | `char_length` | 1 | - | Return the number of characters in the input strin... |
| `bit_length` | `bit_length` | 1 | - | Return the number of bits in the input string. |
| `octet_length` | `octet_length` | 1 | - | Return the number of bytes in the input string. |
| `regexp_replace` | `regexp_replace` | 5 | case_sensitivity, multiline, dotall | Search a string for a substring that matches a giv... |
| `regexp_replace` | `regexp_replace` | 3 | case_sensitivity, multiline, dotall | Search a string for a substring that matches a giv... |
| `ltrim` | `ltrim` | 2 | - | Remove any occurrence of the characters from the l... |
| `rtrim` | `rtrim` | 2 | - | Remove any occurrence of the characters from the r... |
| `trim` | `trim` | 2 | - | Remove any occurrence of the characters from the l... |
| `lpad` | `lpad` | 3 | - | Left-pad the input string with the string of 'char... |
| `rpad` | `rpad` | 3 | - | Right-pad the input string with the string of 'cha... |
| `center` | `center` | 3 | padding | Center the input string by padding the sides with ... |
| `left` | `left` | 2 | - | Extract `count` characters starting from the left ... |
| `right` | `right` | 2 | - | Extract `count` characters starting from the right... |
| `string_split` | `string_split` | 2 | - | Split a string into a list of strings, based on a ... |
| `regexp_string_split` | `regexp_string_split` | 2 | case_sensitivity, multiline, dotall | Split a string into a list of strings, based on a ... |

#### Aggregate Functions (1)

| Substrait Name | Python Name | Args | Options | Description |
|----------------|-------------|------|---------|-------------|
| `string_agg` | `string_agg` | 2 | - | Concatenates a column of string values with a sepa... |
