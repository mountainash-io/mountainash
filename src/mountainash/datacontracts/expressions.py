"""Reusable expression combinators for data validation rules."""
from __future__ import annotations

from functools import reduce
import operator
from typing import Any

import mountainash as ma
from mountainash.expressions import BaseExpressionAPI


# --- Null patterns ---

def any_not_null(*cols: str) -> BaseExpressionAPI:
    """True if any of the named columns is not null."""
    return reduce(operator.or_, (ma.col(c).is_not_null() for c in cols))


def all_not_null(*cols: str) -> BaseExpressionAPI:
    """True if all of the named columns are not null."""
    return reduce(operator.and_, (ma.col(c).is_not_null() for c in cols))


def any_null(*cols: str) -> BaseExpressionAPI:
    """True if any of the named columns is null."""
    return reduce(operator.or_, (ma.col(c).is_null() for c in cols))


def all_null(*cols: str) -> BaseExpressionAPI:
    """True if all of the named columns are null."""
    return reduce(operator.and_, (ma.col(c).is_null() for c in cols))


# --- Value patterns ---

def col_equals(col: str, value: Any) -> BaseExpressionAPI:
    """True if column equals the given value."""
    return ma.col(col).eq(ma.lit(value))


def col_not_equals(col: str, value: Any) -> BaseExpressionAPI:
    """True if column does not equal the given value."""
    return ma.col(col).ne(ma.lit(value))


def col_in(col: str, values: list) -> BaseExpressionAPI:
    """True if column value is in the given list."""
    return ma.col(col).is_in(values)


# --- Cross-column patterns ---

def col_le_col(col_a: str, col_b: str) -> BaseExpressionAPI:
    """True if col_a <= col_b."""
    return ma.col(col_a).le(ma.col(col_b))


def col_ge_col(col_a: str, col_b: str) -> BaseExpressionAPI:
    """True if col_a >= col_b."""
    return ma.col(col_a).ge(ma.col(col_b))
