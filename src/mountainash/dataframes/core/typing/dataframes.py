"""
DataFrame type aliases and detection utilities.

Type aliases and guards are imported from mountainash.core.types (single source of truth).
This module re-exports them and adds dataframes-specific callable type aliases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import TypeAlias
from collections.abc import Callable

# Re-export all shared types from core
from mountainash.core.types import (
    # Runtime modules (needed for callable type aliases below)
    DataFrameT,
    ExpressionT,
)


# ============================================================================
# Callable Type Aliases (dataframes-specific)
# ============================================================================

if TYPE_CHECKING:
    DataFrameTransform: TypeAlias = Callable[[DataFrameT], DataFrameT]
    ExpressionBuilder: TypeAlias = Callable[[str], ExpressionT]
    FilterPredicate: TypeAlias = Callable[[DataFrameT], DataFrameT]
