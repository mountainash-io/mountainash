"""
Value Mapping System for Ternary Logic

This module provides configurable mappings between real-world data values
and internal prime-based ternary logic representation.
"""

from typing import Any, Dict, Optional, Set, Union
from dataclasses import dataclass

import ibis

@dataclass
class TernaryValueMappings:
    """Configurable mappings for ternary logic values in different data types."""

    # String mappings
    string_unknown: str = "<NA>"
    string_not_set: str = "<NOT_SET>"

    # Numeric mappings
    numeric_unknown: Union[int, float] = -999999999
    numeric_not_set: Union[int, float] = -999999998

    # Boolean mappings (for completeness)
    boolean_unknown: Optional[bool] = None

    # Additional configurable values
    additional_unknown_values: Optional[Set[Any]] = None
    additional_not_set_values: Optional[Set[Any]] = None

    def __post_init__(self):
        """Initialize additional value sets if not provided."""
        if self.additional_unknown_values is None:
            self.additional_unknown_values = set()
        if self.additional_not_set_values is None:
            self.additional_not_set_values = set()

    # @lru_cache(maxsize=None)
    def is_unknown_value(self, value: Any) -> bool:
        """Check if a value represents UNKNOWN in ternary logic.

        Args:
            value: Value to check

        Returns:
            True if value represents UNKNOWN
        """
        if value is None:  # Standard NULL
            return True
        if value == self.string_unknown:  # Configured string unknown
            return True
        if value == self.numeric_unknown:  # Configured numeric unknown
            return True
        if value in self.additional_unknown_values:  # Additional configured unknowns
            return True
        return False

    # @lru_cache(maxsize=None)
    def is_not_set_value(self, value: Any) -> bool:
        """Check if a value represents NOT_SET in ternary logic.

        Args:
            value: Value to check

        Returns:
            True if value represents NOT_SET
        """
        if value == self.string_not_set:  # Configured string not_set
            return True
        if value == self.numeric_not_set:  # Configured numeric not_set
            return True
        if value in self.additional_not_set_values:  # Additional configured not_set
            return True
        return False


    # @lru_cache(maxsize=None)
    def get_all_unknown_values(self) -> Set[Any]:
        """Get all values that represent UNKNOWN.

        Returns:
            Set of all UNKNOWN values
        """
        unknown_values = {
            None,  # Standard NULL
            self.string_unknown,
            self.numeric_unknown,
            self.boolean_unknown
        }
        if self.additional_unknown_values:
            unknown_values.update(self.additional_unknown_values)
        return unknown_values

    # @lru_cache(maxsize=None)
    def get_all_not_set_values(self) -> Set[Any]:
        """Get all values that represent NOT_SET.

        Returns:
            Set of all NOT_SET values
        """
        not_set_values = {
            self.string_not_set,
            self.numeric_not_set
        }
        if self.additional_not_set_values:
            not_set_values.update(self.additional_not_set_values)
        return not_set_values


    # @lru_cache(maxsize=None)
    def get_all_unknown_values_ibis(self) -> Set[Any]:
        """Get all values that represent UNKNOWN.

        Returns:
            Set of all UNKNOWN values
        """
        unknown_values = {
            ibis.literal(None),  # Standard NULL
            ibis.literal(self.string_unknown),
            ibis.literal(self.numeric_unknown),
            ibis.literal(self.boolean_unknown)
        }
        if self.additional_unknown_values:
            additional_unknown_values_ibis = {ibis.literal(val) for val in self.additional_unknown_values}
            unknown_values.update(additional_unknown_values_ibis)
        return unknown_values

    # @lru_cache(maxsize=None)
    def get_all_not_set_values_ibis(self) -> Set[Any]:
        """Get all values that represent NOT_SET.

        Returns:
            Set of all NOT_SET values
        """
        not_set_values = {
            ibis.literal(self.string_not_set),
            ibis.literal(self.numeric_not_set)
        }
        if self.additional_not_set_values:
            additional_not_set_values_ibis = {ibis.literal(val) for val in self.additional_not_set_values}
            not_set_values.update(additional_not_set_values_ibis)
        return not_set_values




class TernaryValueMapper:
    """Main mapper for converting between real-world values and ternary primes."""

    def __init__(self, mappings: Optional[TernaryValueMappings] = None):
        """Initialize mapper with optional custom mappings.

        Args:
            mappings: Custom value mappings, uses defaults if None
        """
        self.mappings = mappings or TernaryValueMappings()

    def is_column_ternary_aware(self, column_values: list) -> bool:
        """Check if a column contains ternary-aware values.

        Args:
            column_values: List of values in the column

        Returns:
            True if column contains UNKNOWN or NOT_SET values
        """
        for value in column_values:
            if (self.mappings.is_unknown_value(value) or
                self.mappings.is_not_set_value(value)):
                return True
        return False

    def get_ternary_column_stats(self, column_values: list) -> Dict[str, int]:
        """Get statistics about ternary values in a column.

        Args:
            column_values: List of values in the column

        Returns:
            Dictionary with counts of different ternary states
        """
        stats = {
            'total': len(column_values),
            'known': 0,
            'unknown': 0,
            'not_set': 0
        }

        for value in column_values:
            if self.mappings.is_unknown_value(value):
                stats['unknown'] += 1
            elif self.mappings.is_not_set_value(value):
                stats['not_set'] += 1
            else:
                stats['known'] += 1

        return stats


# Global default mapper instance
DEFAULT_TERNARY_MAPPER = TernaryValueMapper()


def get_default_mappings() -> TernaryValueMappings:
    """Get default ternary value mappings compatible with RuleConstants.

    Returns:
        TernaryValueMappings with standard unknown values
    """
    return TernaryValueMappings(
        string_unknown="<NA>",
        string_not_set="<NOT_SET>",
        numeric_unknown=-999999999,
        numeric_not_set=-999999998,
        boolean_unknown=None
    )


def configure_ternary_mappings(
    string_unknown: str = "<NA>",
    string_not_set: str = "<NOT_SET>",
    numeric_unknown: Union[int, float] = -999999999,
    numeric_not_set: Union[int, float] = -999999998,
    additional_unknown: Optional[Set[Any]] = None,
    additional_not_set: Optional[Set[Any]] = None
) -> TernaryValueMappings:
    """Configure custom ternary value mappings.

    Args:
        string_unknown: String representation of UNKNOWN
        string_not_set: String representation of NOT_SET
        numeric_unknown: Numeric representation of UNKNOWN
        numeric_not_set: Numeric representation of NOT_SET
        additional_unknown: Additional values to treat as UNKNOWN
        additional_not_set: Additional values to treat as NOT_SET

    Returns:
        Configured TernaryValueMappings instance
    """
    return TernaryValueMappings(
        string_unknown=string_unknown,
        string_not_set=string_not_set,
        numeric_unknown=numeric_unknown,
        numeric_not_set=numeric_not_set,
        additional_unknown_values=additional_unknown or set(),
        additional_not_set_values=additional_not_set or set()
    )
