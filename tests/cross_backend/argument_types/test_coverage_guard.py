"""Meta-tests for argument/option parameter classification.

- test_every_argument_param_is_tested: every argument-kind protocol param has a TESTED_PARAMS entry
- test_no_unclassified_params: no ambiguously-typed params in protocols
- test_option_params_not_widened_by_backends: option-typed protocol params are not widened to
  accept expressions in any backend implementation (mixed-capability drift detection)
"""
from __future__ import annotations

import inspect
import typing
from typing import get_type_hints

from cross_backend.argument_types._coverage_guard_helpers import (
    KnownGap,
    TestedParamRef,
    collect_tested_params,
)
from cross_backend.argument_types._introspection import (
    introspect_protocols,
    _iter_protocol_classes,
    _CATEGORY_MAP,
)

_CATEGORY_MODULES = [
    "test_arg_types_string",
    "test_arg_types_arithmetic",
    "test_arg_types_comparison",
    "test_arg_types_boolean",
    "test_arg_types_null",
    "test_arg_types_rounding",
    "test_arg_types_logarithmic",
    "test_arg_types_datetime",
    "test_arg_types_name",
    "test_arg_types_window",
    "test_arg_types_aggregate",
    "test_arg_types_misc",
    "test_arg_types_list",
    "test_arg_types_struct",
]


def _collect_tested_param_refs() -> set[TestedParamRef]:
    return collect_tested_params(_CATEGORY_MODULES)


def _collect_tested_params() -> set[tuple[str, str]]:
    return {(ref.op_name, ref.param_name) for ref in _collect_tested_param_refs()}


_KNOWN_UNTESTED_ARGUMENT_PARAMS: dict[tuple[str, str, str], KnownGap] = {
    # List ops - mostly Polars-only, argument expression support is backend-specific
    **{
        key: KnownGap(
            reason="List argument expression support is backend-specific",
            since="2026-05-12",
        )
        for key in {
            ("MountainAshScalarListExpressionSystemProtocol", "list_all", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_any", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_arg_max", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_arg_min", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_agg", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_agg", "expr"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_concat", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_concat", "other"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_count_matches", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_count_matches", "item"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_diff", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_drop_nulls", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_filter", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_filter", "mask"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_gather", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_gather", "indices"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_gather_every", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_gather_every", "n"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_head", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_head", "n"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_item", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_median", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_n_unique", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_reverse", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_sample", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_sample", "n"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_set_difference", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_set_difference", "other"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_set_intersection", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_set_intersection", "other"),
            (
                "MountainAshScalarListExpressionSystemProtocol",
                "list_set_symmetric_difference",
                "x",
            ),
            (
                "MountainAshScalarListExpressionSystemProtocol",
                "list_set_symmetric_difference",
                "other",
            ),
            ("MountainAshScalarListExpressionSystemProtocol", "list_set_union", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_set_union", "other"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_shift", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_shift", "n"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_slice", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_slice", "offset"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_std", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_tail", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_tail", "n"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_to_array", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_to_struct", "x"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_var", "x"),
        }
    },
    # Duration extraction - Ibis has no total_* methods
    **{
        key: KnownGap(
            reason="Ibis has no total_* duration extraction methods",
            since="2026-05-12",
        )
        for key in {
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "total_days", "x"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "total_hours", "x"),
            (
                "MountainAshScalarDatetimeExpressionSystemProtocol",
                "total_nanoseconds",
                "x",
            ),
        }
    },
}


_KNOWN_UNTESTED_OPTION_PARAMS: dict[tuple[str, str, str], KnownGap] = {
    key: KnownGap(
        reason=(
            "Option behavior coverage is not implemented yet; tracked explicitly "
            "by option-param guard"
        ),
        since="2026-05-12",
    )
    for key in {
        ("MountainAshNameExpressionSystemProtocol", "alias", "name"),
        ("MountainAshNameExpressionSystemProtocol", "prefix", "prefix"),
        ("MountainAshNameExpressionSystemProtocol", "suffix", "suffix"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "assume_timezone", "timezone"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "ceil", "unit"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "extract", "component"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "extract", "timezone"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "extract_boolean", "component"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "floor", "unit"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "is_dst", "timezone"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "offset_by", "offset"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "round", "unit"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "strftime", "format"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "to_timezone", "timezone"),
        ("MountainAshScalarDatetimeExpressionSystemProtocol", "truncate", "unit"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_diff", "n"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_diff", "null_behavior"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_gather", "null_on_oob"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_gather_every", "offset"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_get", "index"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_item", "index"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_join", "separator"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_sample", "fraction"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_sample", "seed"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_sample", "shuffle"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_sample", "with_replacement"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_slice", "length"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_sort", "descending"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_std", "ddof"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_to_array", "width"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_to_struct", "fields"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_to_struct", "n_field_strategy"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_to_struct", "upper_bound"),
        ("MountainAshScalarListExpressionSystemProtocol", "list_var", "ddof"),
        ("MountainAshScalarStringExpressionSystemProtocol", "decode", "encoding"),
        ("MountainAshScalarStringExpressionSystemProtocol", "decode", "strict"),
        ("MountainAshScalarStringExpressionSystemProtocol", "encode", "encoding"),
        ("MountainAshScalarStringExpressionSystemProtocol", "extract_groups", "pattern"),
        ("MountainAshScalarStringExpressionSystemProtocol", "json_decode", "dtype"),
        ("MountainAshScalarStringExpressionSystemProtocol", "json_path_match", "json_path"),
        ("MountainAshScalarStringExpressionSystemProtocol", "regex_contains", "case_sensitivity"),
        ("MountainAshScalarStringExpressionSystemProtocol", "regex_contains", "pattern"),
        ("MountainAshScalarStringExpressionSystemProtocol", "strip_suffix", "suffix"),
        ("MountainAshScalarStringExpressionSystemProtocol", "to_integer", "base"),
        ("MountainAshScalarStringExpressionSystemProtocol", "to_time", "format"),
        ("MountainAshScalarStructExpressionSystemProtocol", "struct_field", "field_name"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "collect_values", "values"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_eq", "left_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_eq", "right_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_ge", "left_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_ge", "right_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_gt", "left_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_gt", "right_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_is_in", "unknown_values"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_is_not_in", "unknown_values"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_le", "left_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_le", "right_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_lt", "left_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_lt", "right_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_ne", "left_unknown"),
        ("MountainAshScalarTernaryExpressionSystemProtocol", "t_ne", "right_unknown"),
        ("MountainashWindowExpressionSystemProtocol", "backward_fill", "limit"),
        ("MountainashWindowExpressionSystemProtocol", "cum_count", "reverse"),
        ("MountainashWindowExpressionSystemProtocol", "cum_max", "reverse"),
        ("MountainashWindowExpressionSystemProtocol", "cum_min", "reverse"),
        ("MountainashWindowExpressionSystemProtocol", "cum_prod", "reverse"),
        ("MountainashWindowExpressionSystemProtocol", "cum_sum", "reverse"),
        ("MountainashWindowExpressionSystemProtocol", "diff", "n"),
        ("MountainashWindowExpressionSystemProtocol", "forward_fill", "limit"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "avg", "overflow"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "corr", "rounding"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "median", "rounding"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "product", "overflow"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "quantile", "rounding"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "std_dev", "distribution"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "std_dev", "rounding"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "sum", "overflow"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "sum0", "overflow"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "variance", "distribution"),
        ("SubstraitAggregateArithmeticExpressionSystemProtocol", "variance", "rounding"),
        ("SubstraitAggregateGenericExpressionSystemProtocol", "any_value", "ignore_nulls"),
        ("SubstraitAggregateGenericExpressionSystemProtocol", "count", "overflow"),
        ("SubstraitAggregateGenericExpressionSystemProtocol", "count_records", "overflow"),
        ("SubstraitAggregateStringExpressionSystemProtocol", "string_agg", "separator"),
        ("SubstraitCastExpressionSystemProtocol", "cast", "dtype"),
        ("SubstraitLiteralExpressionSystemProtocol", "lit", "x"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "abs", "overflow"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "acos", "on_domain_error"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "acos", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "acosh", "on_domain_error"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "acosh", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "add", "overflow"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "asin", "on_domain_error"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "asin", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "asinh", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "atan", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "atan2", "on_domain_error"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "atan2", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "atanh", "on_domain_error"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "atanh", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "cos", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "cosh", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "degrees", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "divide", "on_division_by_zero"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "divide", "on_domain_error"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "divide", "overflow"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "exp", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "factorial", "overflow"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "modulus", "division_type"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "modulus", "on_domain_error"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "modulus", "overflow"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "multiply", "overflow"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "negate", "overflow"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "power", "overflow"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "radians", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "sin", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "sinh", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "sqrt", "on_domain_error"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "sqrt", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "subtract", "overflow"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "tan", "rounding"),
        ("SubstraitScalarArithmeticExpressionSystemProtocol", "tanh", "rounding"),
        ("SubstraitScalarComparisonExpressionSystemProtocol", "between", "closed"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "assume_timezone", "timezone"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "extract", "component"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "extract", "timezone"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "extract_boolean", "component"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "local_timestamp", "timezone"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_calendar", "multiple"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_calendar", "origin"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_calendar", "rounding"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_calendar", "unit"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_temporal", "multiple"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_temporal", "origin"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_temporal", "rounding"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_temporal", "unit"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "strftime", "format"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_date", "format"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_time", "format"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_timestamp", "format"),
        ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_timestamp", "timezone"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "ln", "on_domain_error"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "ln", "on_log_zero"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "ln", "rounding"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log10", "on_domain_error"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log10", "on_log_zero"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log10", "rounding"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log1p", "on_domain_error"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log1p", "on_log_zero"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log1p", "rounding"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log2", "on_domain_error"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log2", "on_log_zero"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log2", "rounding"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "logb", "on_domain_error"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "logb", "on_log_zero"),
        ("SubstraitScalarLogarithmicExpressionSystemProtocol", "logb", "rounding"),
        ("SubstraitScalarRoundingExpressionSystemProtocol", "round", "rounding"),
        ("SubstraitScalarRoundingExpressionSystemProtocol", "round", "s"),
        ("SubstraitScalarStringExpressionSystemProtocol", "capitalize", "char_set"),
        ("SubstraitScalarStringExpressionSystemProtocol", "center", "padding"),
        ("SubstraitScalarStringExpressionSystemProtocol", "concat", "null_handling"),
        ("SubstraitScalarStringExpressionSystemProtocol", "contains", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "count_substring", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "ends_with", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "initcap", "char_set"),
        ("SubstraitScalarStringExpressionSystemProtocol", "like", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "lower", "char_set"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_count_substring", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_count_substring", "dotall"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_count_substring", "multiline"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_count_substring", "position"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring", "dotall"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring", "group"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring", "multiline"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring", "occurrence"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring", "position"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring_all", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring_all", "dotall"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring_all", "group"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring_all", "multiline"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring_all", "position"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_replace", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_replace", "dotall"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_replace", "multiline"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_replace", "occurrence"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_replace", "position"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_string_split", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_string_split", "dotall"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_string_split", "multiline"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_strpos", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_strpos", "dotall"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_strpos", "multiline"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_strpos", "occurrence"),
        ("SubstraitScalarStringExpressionSystemProtocol", "regexp_strpos", "position"),
        ("SubstraitScalarStringExpressionSystemProtocol", "replace", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "starts_with", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "strpos", "case_sensitivity"),
        ("SubstraitScalarStringExpressionSystemProtocol", "substring", "negative_start"),
        ("SubstraitScalarStringExpressionSystemProtocol", "swapcase", "char_set"),
        ("SubstraitScalarStringExpressionSystemProtocol", "title", "char_set"),
        ("SubstraitScalarStringExpressionSystemProtocol", "upper", "char_set"),
        ("SubstraitWindowArithmeticExpressionSystemProtocol", "dense_rank", "descending"),
        ("SubstraitWindowArithmeticExpressionSystemProtocol", "rank", "descending"),
        ("SubstraitWindowArithmeticExpressionSystemProtocol", "row_number", "descending"),
    }
}


_KNOWN_UNWIRED_TESTED_OPS: dict[tuple[str, str], KnownGap] = {
    ("SubstraitFieldReferenceExpressionSystemProtocol", "col"): KnownGap(
        reason="Special node type (FieldReferenceNode), not dispatched through scalar function registry",
        since="2026-05-12",
    ),
    ("SubstraitLiteralExpressionSystemProtocol", "lit"): KnownGap(
        reason="Special node type (LiteralNode), not dispatched through scalar function registry",
        since="2026-05-12",
    ),
    **{
        key: KnownGap(
            reason="TESTED_PARAMS operation is covered, but registry protocol_method wiring is not in place yet",
            since="2026-05-12",
        )
        for key in {
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "day"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "day_of_week"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "day_of_year"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "hour"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "iso_year"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "microsecond"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "millisecond"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "minute"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "month"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "nanosecond"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "quarter"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "second"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "timezone_offset"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "to_timezone"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "unix_timestamp"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "week_of_year"),
            ("MountainAshScalarDatetimeExpressionSystemProtocol", "year"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_contains"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_explode"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_get"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_join"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_len"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_max"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_mean"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_min"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_sort"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_sum"),
            ("MountainAshScalarListExpressionSystemProtocol", "list_unique"),
            ("MountainAshScalarStringExpressionSystemProtocol", "decode"),
            ("MountainAshScalarStringExpressionSystemProtocol", "encode"),
            ("MountainAshScalarStringExpressionSystemProtocol", "extract_groups"),
            ("MountainAshScalarStringExpressionSystemProtocol", "json_decode"),
            ("MountainAshScalarStringExpressionSystemProtocol", "json_path_match"),
            ("MountainAshScalarStringExpressionSystemProtocol", "strip_suffix"),
            ("MountainAshScalarStringExpressionSystemProtocol", "to_integer"),
            ("MountainAshScalarStringExpressionSystemProtocol", "to_time"),
            ("MountainAshScalarStructExpressionSystemProtocol", "struct_field"),
            ("MountainAshScalarTernaryExpressionSystemProtocol", "is_false_ternary"),
            ("MountainAshScalarTernaryExpressionSystemProtocol", "is_true_ternary"),
            ("MountainashExtensionAggregateExpressionSystemProtocol", "n_unique"),
            ("MountainashWindowExpressionSystemProtocol", "backward_fill"),
            ("MountainashWindowExpressionSystemProtocol", "cum_count"),
            ("MountainashWindowExpressionSystemProtocol", "cum_max"),
            ("MountainashWindowExpressionSystemProtocol", "cum_min"),
            ("MountainashWindowExpressionSystemProtocol", "cum_prod"),
            ("MountainashWindowExpressionSystemProtocol", "cum_sum"),
            ("MountainashWindowExpressionSystemProtocol", "diff"),
            ("MountainashWindowExpressionSystemProtocol", "forward_fill"),
            ("SubstraitAggregateArithmeticExpressionSystemProtocol", "sum0"),
            ("SubstraitScalarArithmeticExpressionSystemProtocol", "factorial"),
            ("SubstraitScalarArithmeticExpressionSystemProtocol", "modulus"),
            ("SubstraitScalarBooleanExpressionSystemProtocol", "and_"),
            ("SubstraitScalarBooleanExpressionSystemProtocol", "not_"),
            ("SubstraitScalarBooleanExpressionSystemProtocol", "or_"),
            ("SubstraitScalarComparisonExpressionSystemProtocol", "is_distinct_from"),
            ("SubstraitScalarComparisonExpressionSystemProtocol", "is_not_distinct_from"),
            ("SubstraitScalarComparisonExpressionSystemProtocol", "nullif"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "add"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "add_intervals"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "gt"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "gte"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "local_timestamp"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "lt"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "lte"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "multiply"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_calendar"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "round_temporal"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_date"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_time"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "strptime_timestamp"),
            ("SubstraitScalarDatetimeExpressionSystemProtocol", "subtract"),
            ("SubstraitScalarLogarithmicExpressionSystemProtocol", "ln"),
            ("SubstraitScalarLogarithmicExpressionSystemProtocol", "log1p"),
            ("SubstraitScalarStringExpressionSystemProtocol", "regexp_count_substring"),
            ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring"),
            ("SubstraitScalarStringExpressionSystemProtocol", "regexp_match_substring_all"),
            ("SubstraitScalarStringExpressionSystemProtocol", "regexp_string_split"),
            ("SubstraitScalarStringExpressionSystemProtocol", "regexp_strpos"),
            ("SubstraitScalarStringExpressionSystemProtocol", "string_split"),
        }
    },
}


_KNOWN_UNRESOLVED_TESTED_PARAMS: dict[tuple[str, str], KnownGap] = {
    ("buffer", "buffer_radius"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.buffer",
        since="2026-05-12",
    ),
    ("buffer", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.buffer",
        since="2026-05-12",
    ),
    ("cast", "x"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitCastExpressionSystemProtocol.cast",
        since="2026-05-12",
    ),
    ("centroid", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.centroid",
        since="2026-05-12",
    ),
    ("col", "x"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitFieldReferenceExpressionSystemProtocol.col",
        since="2026-05-12",
    ),
    ("collection_extract", "geom_collection"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.collection_extract",
        since="2026-05-12",
    ),
    ("dimension", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.dimension",
        since="2026-05-12",
    ),
    ("envelope", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.envelope",
        since="2026-05-12",
    ),
    ("flip_coordinates", "geom_collection"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.flip_coordinates",
        since="2026-05-12",
    ),
    ("geometry_type", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.geometry_type",
        since="2026-05-12",
    ),
    ("if_then_else", "condition"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitConditionalExpressionSystemProtocol.if_then_else",
        since="2026-05-12",
    ),
    ("if_then_else", "if_false"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitConditionalExpressionSystemProtocol.if_then_else",
        since="2026-05-12",
    ),
    ("if_then_else", "if_true"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitConditionalExpressionSystemProtocol.if_then_else",
        since="2026-05-12",
    ),
    ("is_closed", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.is_closed",
        since="2026-05-12",
    ),
    ("is_empty", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.is_empty",
        since="2026-05-12",
    ),
    ("is_ring", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.is_ring",
        since="2026-05-12",
    ),
    ("is_simple", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.is_simple",
        since="2026-05-12",
    ),
    ("is_valid", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.is_valid",
        since="2026-05-12",
    ),
    ("make_line", "geom1"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.make_line",
        since="2026-05-12",
    ),
    ("make_line", "geom2"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.make_line",
        since="2026-05-12",
    ),
    ("minimum_bounding_circle", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.minimum_bounding_circle",
        since="2026-05-12",
    ),
    ("num_points", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.num_points",
        since="2026-05-12",
    ),
    ("point", "x"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.point",
        since="2026-05-12",
    ),
    ("point", "y"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.point",
        since="2026-05-12",
    ),
    ("remove_repeated_points", "geom"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.remove_repeated_points",
        since="2026-05-12",
    ),
    ("x_coordinate", "point"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.x_coordinate",
        since="2026-05-12",
    ),
    ("y_coordinate", "point"): KnownGap(
        reason="String TESTED_PARAMS entry lives in misc; protocol is SubstraitScalarGeometryExpressionSystemProtocol.y_coordinate",
        since="2026-05-12",
    ),
}


_KNOWN_SPECIAL_NODE_UNWIRED_OPS: dict[tuple[str, str], KnownGap] = {
    ("SubstraitFieldReferenceExpressionSystemProtocol", "col"): _KNOWN_UNWIRED_TESTED_OPS[
        ("SubstraitFieldReferenceExpressionSystemProtocol", "col")
    ],
    ("SubstraitLiteralExpressionSystemProtocol", "lit"): _KNOWN_UNWIRED_TESTED_OPS[
        ("SubstraitLiteralExpressionSystemProtocol", "lit")
    ],
}


_KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_ALIASES: dict[
    tuple[str, str],
    tuple[str, str, str],
] = {
    ("buffer", "buffer_radius"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "buffer",
        "buffer_radius",
    ),
    ("buffer", "geom"): ("SubstraitScalarGeometryExpressionSystemProtocol", "buffer", "geom"),
    ("centroid", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "centroid",
        "geom",
    ),
    ("col", "x"): ("SubstraitFieldReferenceExpressionSystemProtocol", "col", "x"),
    ("collection_extract", "geom_collection"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "collection_extract",
        "geom_collection",
    ),
    ("dimension", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "dimension",
        "geom",
    ),
    ("envelope", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "envelope",
        "geom",
    ),
    ("flip_coordinates", "geom_collection"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "flip_coordinates",
        "geom_collection",
    ),
    ("geometry_type", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "geometry_type",
        "geom",
    ),
    ("is_closed", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "is_closed",
        "geom",
    ),
    ("is_empty", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "is_empty",
        "geom",
    ),
    ("is_ring", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "is_ring",
        "geom",
    ),
    ("is_simple", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "is_simple",
        "geom",
    ),
    ("is_valid", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "is_valid",
        "geom",
    ),
    ("make_line", "geom1"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "make_line",
        "geom1",
    ),
    ("make_line", "geom2"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "make_line",
        "geom2",
    ),
    ("minimum_bounding_circle", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "minimum_bounding_circle",
        "geom",
    ),
    ("num_points", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "num_points",
        "geom",
    ),
    ("point", "x"): ("SubstraitScalarGeometryExpressionSystemProtocol", "point", "x"),
    ("point", "y"): ("SubstraitScalarGeometryExpressionSystemProtocol", "point", "y"),
    ("remove_repeated_points", "geom"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "remove_repeated_points",
        "geom",
    ),
    ("x_coordinate", "point"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "x_coordinate",
        "point",
    ),
    ("y_coordinate", "point"): (
        "SubstraitScalarGeometryExpressionSystemProtocol",
        "y_coordinate",
        "point",
    ),
}


_KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_GAPS: dict[tuple[str, str], KnownGap] = {
    source: KnownGap(
        reason=(
            "String TESTED_PARAMS entry is covered but cannot yet be resolved to a "
            "protocol-qualified key by the category resolver"
        ),
        since="2026-05-12",
    )
    for source in _KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_ALIASES
}


_KNOWN_TESTED_ARGUMENT_PARAM_ALIASES: dict[
    tuple[str, str, str],
    tuple[str, str, str],
] = {
    (
        "SubstraitScalarDatetimeExpressionSystemProtocol",
        "assume_timezone",
        "x",
    ): ("MountainAshScalarDatetimeExpressionSystemProtocol", "assume_timezone", "x"),
    (
        "SubstraitScalarDatetimeExpressionSystemProtocol",
        "extract",
        "x",
    ): ("MountainAshScalarDatetimeExpressionSystemProtocol", "extract", "x"),
    (
        "SubstraitScalarDatetimeExpressionSystemProtocol",
        "extract_boolean",
        "x",
    ): ("MountainAshScalarDatetimeExpressionSystemProtocol", "extract_boolean", "x"),
    (
        "SubstraitScalarDatetimeExpressionSystemProtocol",
        "strftime",
        "x",
    ): ("MountainAshScalarDatetimeExpressionSystemProtocol", "strftime", "x"),
    (
        "SubstraitScalarSetExpressionSystemProtocol",
        "is_in",
        "haystack",
    ): ("MountainAshScalarSetExpressionSystemProtocol", "is_in", "haystack"),
    (
        "SubstraitScalarSetExpressionSystemProtocol",
        "is_in",
        "needle",
    ): ("MountainAshScalarSetExpressionSystemProtocol", "is_in", "needle"),
    (
        "SubstraitScalarSetExpressionSystemProtocol",
        "is_not_in",
        "haystack",
    ): ("MountainAshScalarSetExpressionSystemProtocol", "is_not_in", "haystack"),
    (
        "SubstraitScalarSetExpressionSystemProtocol",
        "is_not_in",
        "needle",
    ): ("MountainAshScalarSetExpressionSystemProtocol", "is_not_in", "needle"),
}


def test_every_argument_param_is_tested():
    introspected = {
        (p.protocol_name, p.op_name, p.param_name)
        for p in introspect_protocols()
        if p.kind == "argument"
    }
    tested_refs = _collect_tested_param_refs()
    tested_protocol_keys = {
        ref.protocol_param_key
        for ref in tested_refs
        if ref.protocol_param_key is not None
    }
    unresolved_tested_keys = {
        (ref.op_name, ref.param_name)
        for ref in tested_refs
        if ref.protocol_param_key is None
    }
    tested = {
        protocol_key
        for protocol_key in tested_protocol_keys
        if protocol_key not in _KNOWN_TESTED_ARGUMENT_PARAM_ALIASES
        or protocol_key in introspected
    } | {
        target_key
        for source_key, target_key in _KNOWN_TESTED_ARGUMENT_PARAM_ALIASES.items()
        if source_key in tested_protocol_keys
    } | {
        target_key
        for source_key, target_key in _KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_ALIASES.items()
        if source_key in unresolved_tested_keys
    }
    known = set(_KNOWN_UNTESTED_ARGUMENT_PARAMS)
    newly_missing = introspected - tested - known
    extra = tested - introspected
    stale_known = known - introspected
    overlap = known & tested
    stale_unresolved_aliases = (
        set(_KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_ALIASES) - unresolved_tested_keys
    )
    stale_protocol_aliases = set(_KNOWN_TESTED_ARGUMENT_PARAM_ALIASES) - tested_protocol_keys
    assert not newly_missing, (
        "New argument params with no test "
        f"(add test or register in _KNOWN_UNTESTED_ARGUMENT_PARAMS): {sorted(newly_missing)}"
    )
    assert not extra, f"Tested params with no protocol: {sorted(extra)}"
    assert not stale_known, (
        "Entries in _KNOWN_UNTESTED_ARGUMENT_PARAMS that no longer exist in protocols "
        f"(remove them): {sorted(stale_known)}"
    )
    assert not overlap, (
        "Entries in _KNOWN_UNTESTED_ARGUMENT_PARAMS that are already tested "
        f"(remove from _KNOWN_UNTESTED_ARGUMENT_PARAMS): {sorted(overlap)}"
    )
    assert not stale_unresolved_aliases, (
        "Entries in _KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_ALIASES no longer match "
        f"unresolved TESTED_PARAMS rows: {sorted(stale_unresolved_aliases)}"
    )
    assert not stale_protocol_aliases, (
        "Entries in _KNOWN_TESTED_ARGUMENT_PARAM_ALIASES no longer match tested "
        f"protocol-qualified rows: {sorted(stale_protocol_aliases)}"
    )


def test_every_option_param_is_tested_or_registered():
    introspected = {
        (p.protocol_name, p.op_name, p.param_name)
        for p in introspect_protocols()
        if p.kind == "option"
    }
    tested_options: set[tuple[str, str, str]] = set()
    known = set(_KNOWN_UNTESTED_OPTION_PARAMS)
    newly_missing = introspected - tested_options - known
    stale_known = known - introspected
    overlap = known & tested_options
    assert not newly_missing, (
        "Option params with no behavior test or known-gap entry "
        f"(add tests or _KNOWN_UNTESTED_OPTION_PARAMS entries): {sorted(newly_missing)}"
    )
    assert not stale_known, (
        "Entries in _KNOWN_UNTESTED_OPTION_PARAMS that no longer exist in protocols "
        f"(remove them): {sorted(stale_known)}"
    )
    assert not overlap, (
        "Entries in _KNOWN_UNTESTED_OPTION_PARAMS that are already tested "
        f"(remove from _KNOWN_UNTESTED_OPTION_PARAMS): {sorted(overlap)}"
    )


def test_tested_params_have_registry_wiring_or_named_gap():
    tested = _collect_tested_param_refs()
    unwired = {
        ref.operation_key
        for ref in tested
        if ref.operation_key is not None
        and not ref.registry_wired
        and ref.operation_key not in _KNOWN_UNWIRED_TESTED_OPS
    }
    unresolved = {
        (ref.op_name, ref.param_name)
        for ref in tested
        if ref.operation_key is None
        and (ref.op_name, ref.param_name) not in _KNOWN_UNRESOLVED_TESTED_PARAMS
    }
    stale_unresolved_known = {
        key for key in _KNOWN_UNRESOLVED_TESTED_PARAMS
        if key not in {(ref.op_name, ref.param_name) for ref in tested}
    }
    tested_operation_keys = {ref.operation_key for ref in tested}
    stale_known = {
        key for key in _KNOWN_UNWIRED_TESTED_OPS
        if key not in tested_operation_keys
        and key not in _KNOWN_SPECIAL_NODE_UNWIRED_OPS
    }
    stale_special_nodes = {
        key for key in _KNOWN_SPECIAL_NODE_UNWIRED_OPS
        if not any((p.protocol_name, p.op_name) == key for p in introspect_protocols())
    }
    assert not unresolved, f"TESTED_PARAMS entries with no protocol match: {sorted(unresolved)}"
    assert not unwired, (
        "TESTED_PARAMS operations with no function registry wiring "
        f"(add enum/registry wiring or _KNOWN_UNWIRED_TESTED_OPS entry): {sorted(unwired)}"
    )
    assert not stale_known, (
        "Entries in _KNOWN_UNWIRED_TESTED_OPS no longer referenced by TESTED_PARAMS "
        f"(remove them): {sorted(stale_known)}"
    )
    assert not stale_unresolved_known, (
        "Entries in _KNOWN_UNRESOLVED_TESTED_PARAMS no longer referenced by TESTED_PARAMS "
        f"(remove them): {sorted(stale_unresolved_known)}"
    )
    assert not stale_special_nodes, (
        "Entries in _KNOWN_SPECIAL_NODE_UNWIRED_OPS no longer exist in protocols "
        f"(remove them): {sorted(stale_special_nodes)}"
    )


def test_all_protocols_categorized():
    """Every protocol class discovered by _iter_protocol_classes must be in _CATEGORY_MAP."""
    uncategorized = [name for name, _ in _iter_protocol_classes() if name not in _CATEGORY_MAP]
    assert uncategorized == [], f"Uncategorized protocols (add to _CATEGORY_MAP): {uncategorized}"


def test_no_unclassified_params():
    unclassified = [p for p in introspect_protocols() if p.kind == "unclassified"]
    assert not unclassified, (
        f"Protocol params with ambiguous typing (fix in Phase 0): "
        f"{[(p.protocol_name, p.op_name, p.param_name, p.annotation) for p in unclassified]}"
    )


def test_all_protocols_registered_in_category_map():
    """Every expression system protocol must be registered in _CATEGORY_MAP.

    If this fails, a new protocol was added but not registered in
    _introspection._CATEGORY_MAP. Add it with the appropriate category
    so drift detection covers it.
    """
    from cross_backend.argument_types._introspection import _iter_protocol_classes, _CATEGORY_MAP

    unregistered = [
        name for name, _ in _iter_protocol_classes()
        if name not in _CATEGORY_MAP
    ]
    assert not unregistered, (
        f"Expression system protocols not in _CATEGORY_MAP "
        f"(add them to _introspection._CATEGORY_MAP): {sorted(unregistered)}"
    )


# ---------------------------------------------------------------------------
# Mixed-capability drift detection
# ---------------------------------------------------------------------------

_BACKEND_CLASSES: list[tuple[str, type]] = []


def _get_backend_classes() -> list[tuple[str, type]]:
    """Lazily import the three composed expression system classes."""
    if _BACKEND_CLASSES:
        return _BACKEND_CLASSES
    from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
    from mountainash.expressions.backends.expression_systems.ibis import IbisExpressionSystem
    from mountainash.expressions.backends.expression_systems.narwhals import NarwhalsExpressionSystem
    _BACKEND_CLASSES.extend([
        ("Polars", PolarsExpressionSystem),
        ("Ibis", IbisExpressionSystem),
        ("Narwhals", NarwhalsExpressionSystem),
    ])
    return _BACKEND_CLASSES


_EXPR_TYPE_MARKERS = {"Expr", "ExpressionT", "PolarsExpr", "NarwhalsExpr", "IbisNumericExpr",
                      "IbisValueExpr", "IbisBooleanExpr", "IbisStringExpr", "IbisColumnExpr"}


def _backend_accepts_expr(backend_cls: type, method_name: str, param_name: str) -> bool:
    """Check if a backend method's parameter annotation suggests it accepts expressions."""
    method = getattr(backend_cls, method_name, None)
    if method is None:
        return False
    try:
        hints = get_type_hints(method)
    except Exception:
        hints = {}
    sig = inspect.signature(method)
    param = sig.parameters.get(param_name)
    if param is None:
        return False
    ann = hints.get(param_name, param.annotation)
    ann_str = str(ann)
    if any(marker in ann_str for marker in _EXPR_TYPE_MARKERS):
        return True
    origin = typing.get_origin(ann)
    if origin is typing.Union:
        return any(any(m in str(a) for m in _EXPR_TYPE_MARKERS) for a in typing.get_args(ann))
    return False


def test_option_params_not_widened_by_backends():
    """Detect mixed-capability drift: option-typed protocol params that a backend widens.

    If a backend accepts expressions for a parameter that the protocol types as
    option (concrete int/str/bool), the protocol needs updating to argument channel.
    See: e.cross-backend/arguments-vs-options.md "Mixed-capability parameters".
    """
    option_params = [p for p in introspect_protocols() if p.kind == "option"]
    mismatches = []
    for p in option_params:
        for backend_name, backend_cls in _get_backend_classes():
            if _backend_accepts_expr(backend_cls, p.op_name, p.param_name):
                mismatches.append(
                    f"{p.protocol_name}.{p.op_name}({p.param_name}) is option "
                    f"in protocol but {backend_name} accepts expressions"
                )
    assert not mismatches, (
        "Option-typed protocol params widened by backends (should be arguments):\n"
        + "\n".join(f"  - {m}" for m in mismatches)
    )
