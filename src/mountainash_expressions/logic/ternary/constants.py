"""
Ternary Logic Constants

Prime-based ternary logic constants optimized for mathematical vectorization.
The use of prime numbers (2, 3, 5) provides unique mathematical properties for optimization.
"""

from mountainash_constants import BaseValueConstant
from typing import Union, Optional, Set


class TernaryLogicValues(BaseValueConstant):
    """Prime-based ternary logic constants optimized for mathematical vectorization.

    The use of prime numbers (2, 3, 5) provides:
    - Unique mathematical properties for optimization
    - Efficient vectorized operations across backends
    - Collision resistance in expression building
    - Optimal memory representation for ternary states
    """
    PRIME_FALSE = 2     # Represents FALSE in ternary logic
    PRIME_TRUE = 3      # Represents TRUE in ternary logic
    PRIME_UNKNOWN = 5   # Represents UNKNOWN/NULL in ternary logic

    TERNARY_FALSE = -1     # Represents FALSE in ternary logic
    TERNARY_UNKNOWN = 0   # Represents UNKNOWN/NULL in ternary logic
    TERNARY_TRUE = 1      # Represents TRUE in ternary logic



    @classmethod
    def validate_ternary_value(cls, value: Union[int, None]) -> bool:
        """Validate that a value is a valid ternary logic prime.

        Args:
            value: Value to validate

        Returns:
            True if value is a valid ternary prime, False otherwise
        """
        if value is None:
            return False
        return value in {cls.PRIME_TRUE, cls.PRIME_FALSE, cls.PRIME_UNKNOWN}

    @classmethod
    def from_boolean(cls, value: Optional[bool]) -> int:
        """Convert boolean value to ternary logic prime.

        Args:
            value: Boolean value or None

        Returns:
            Corresponding ternary prime value
        """
        if value is None:
            return cls.PRIME_UNKNOWN
        return cls.PRIME_TRUE if value else cls.PRIME_FALSE

    @classmethod
    def to_boolean(cls, prime_value: int) -> Optional[bool]:
        """Convert ternary logic prime to boolean (None for UNKNOWN).

        Args:
            prime_value: Ternary prime value

        Returns:
            Boolean value or None for UNKNOWN

        Raises:
            ValueError: If prime_value is not a valid ternary prime
        """
        if prime_value == cls.PRIME_TRUE:
            return True
        elif prime_value == cls.PRIME_FALSE:
            return False
        elif prime_value == cls.PRIME_UNKNOWN:
            return None
        else:
            raise ValueError(f"Invalid ternary prime value: {prime_value}")

    @classmethod
    def get_all_values(cls) -> Set[int]:
        """Get set of all valid ternary prime values.

        Returns:
            Set containing all valid ternary prime values
        """
        return {cls.PRIME_TRUE, cls.PRIME_FALSE, cls.PRIME_UNKNOWN}


# class TernaryOperators(BaseValueConstant):
#     """Ternary logic operators for three-valued logic operations."""

#     # Ternary logical operators
#     TERNARY_AND = "ternary_and"
#     TERNARY_OR = "ternary_or"
#     TERNARY_NOT = "ternary_not"

#     # Ternary value detection operators
#     IS_TRUE = "is_true"
#     IS_FALSE = "is_false"
#     IS_UNKNOWN = "is_unknown"

#     # Ternary comparison operators
#     TERNARY_EQUAL = "ternary_equal"
#     TERNARY_NOT_EQUAL = "ternary_not_equal"

#     @classmethod
#     def get_logical_operators(cls) -> Set[str]:
#         """Get set of logical operators for ternary logic.

#         Returns:
#             Set of ternary logical operator strings
#         """
#         return {cls.TERNARY_AND, cls.TERNARY_OR, cls.TERNARY_NOT}

#     @classmethod
#     def get_detection_operators(cls) -> Set[str]:
#         """Get set of value detection operators.

#         Returns:
#             Set of ternary detection operator strings
#         """
#         return {cls.IS_TRUE, cls.IS_FALSE, cls.IS_UNKNOWN}

#     @classmethod
#     def get_comparison_operators(cls) -> Set[str]:
#         """Get set of comparison operators.

#         Returns:
#             Set of ternary comparison operator strings
#         """
#         return {cls.TERNARY_EQUAL, cls.TERNARY_NOT_EQUAL}

#     @classmethod
#     def get_all_operators(cls) -> Set[str]:
#         """Get set of all ternary operators.

#         Returns:
#             Set of all ternary operator strings
#         """
#         return (cls.get_logical_operators() |
#                 cls.get_detection_operators() |
#                 cls.get_comparison_operators())
