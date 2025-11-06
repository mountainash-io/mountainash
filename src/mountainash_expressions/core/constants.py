from typing import Optional
from enum import Enum, StrEnum, IntEnum, auto

class CONST_VISITOR_BACKENDS(Enum):
    """
    Enumeration for different dataframe frameworks.

    Attributes:
        - PANDAS (str): Pandas dataframe framework.
        - POLARS (str): Polars dataframe framework.
        - IBIS (str): Ibis dataframe framework.
        - PYARROW (str): PyArrow framework.
        - NARWHALS (str): Narwhals cross-backend framework.
    """
    PANDAS =   "pandas"
    POLARS =   "polars"
    IBIS =     "ibis"
    PYARROW =  "pyarrow"
    NARWHALS = "narwhals"

    # NUMPY =    "numpy"
    # XARRAY = "xarray"
    # PYSPARK = "pyspark"

class CONST_LOGIC_TYPES(Enum):
    """
    Enumeration for different logic systems.

    Attributes:
        - BOOLEAN (str): Boolean (binary) logic system.
        - TERNARY (str): Ternary (three-valued) logic system.
        - FUZZY (str): Fuzzy logic system.
    """
    BOOLEAN =   "boolean"
    TERNARY =   "ternary"
    FUZZY =     "fuzzy"

class CONST_EXPRESSION_NODE_TYPES(Enum):
    """
    Enumeration for different expression node types.

    Attributes:
        - NATIVE_BACKEND: Backend-native expression passthrough
        - SOURCE: Source data reference (columns)
        - LITERAL: Literal values
        - CAST: Type casting operations
        - LOGICAL_CONSTANT: Logical constants (ALWAYS_TRUE, ALWAYS_FALSE, etc.)
        - UNARY: Unary operations (NOT, IS_NULL, etc.)
        - LOGICAL: Logical operations (AND, OR, XOR)
        - COMPARISON: Comparison operations (EQ, NE, GT, LT, GE, LE)
        - COLLECTION: Collection operations (IN, NOT_IN)
        - ARITHMETIC: Arithmetic operations (ADD, SUB, MUL, DIV)
        - STRING: String operations (UPPER, LOWER, TRIM, etc.)
        - CONDITIONAL_IF_ELSE: Conditional if-else expressions
    """
    NATIVE =        "native_backend"
    SOURCE =                "source"
    LITERAL =               "literal"
    CAST =                  "cast"
    ALIAS =                  "alias"
    LOGICAL =               "logical"
    LOGICAL_COMPARISON =            "comparison"
    LOGICAL_CONSTANT =      "logical_constant"
    LOGICAL_UNARY =                 "unary"
    COLLECTION =            "collection"
    ARITHMETIC =            "arithmetic"
    STRING =                "string"
    CONDITIONAL_IF_ELSE =   "conditional_if_else"


class CONST_EXPRESSION_NATIVE_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    NATIVE = auto()

class CONST_EXPRESSION_CAST_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    CAST = auto()


class CONST_EXPRESSION_SOURCE_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    COL = auto()
    IS_NULL = auto()
    IS_NOT_NULL = auto()

    # ALIAS = auto()

class CONST_EXPRESSION_LITERAL_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    LIT = auto()

class CONST_EXPRESSION_ALIAS_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    ALIAS = auto()


class CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    IS_TRUE = auto()
    IS_FALSE = auto()

    #Ternary Only
    IS_UNKNOWN = auto()
    IS_KNOWN  = auto()   # Ternary Only
    MAYBE_TRUE = auto()
    MAYBE_FALSE = auto()

class CONST_EXPRESSION_LOGICAL_CONSTANT_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    ALWAYS_TRUE = auto()
    ALWAYS_FALSE = auto()
    ALWAYS_UNKNOWN = auto()

class CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS(Enum):
    """
    Enumeration for expression logical operators.
    """

    # Comparison operators
    EQ =  auto()
    NE =  auto()
    GT =  auto()
    LT =  auto()
    GE =  auto()
    LE =  auto()
    # BETWEEN =  auto()

class CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS(Enum):
    """
    Enumeration for expression logical collection operators.
    """

    # Comparison operators
    IN =  auto()
    NOT_IN =  auto()


class CONST_EXPRESSION_ARITHMETIC_OPERATORS(Enum):
    """
    Enumeration for arithmetic operators.

    Attributes:
        - ADD: Addition (+)
        - SUBTRACT: Subtraction (-)
        - MULTIPLY: Multiplication (*)
        - DIVIDE: Division (/)
        - MODULO: Modulo (%)
        - POWER: Exponentiation (**)
        - FLOOR_DIVIDE: Floor division (//)
    """
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    POWER = auto()
    FLOOR_DIVIDE = auto()


class CONST_EXPRESSION_STRING_OPERATORS(Enum):
    """
    Enumeration for string operators.

    Attributes:
        - UPPER: Convert to uppercase
        - LOWER: Convert to lowercase
        - TRIM: Trim whitespace
        - LTRIM: Left trim whitespace
        - RTRIM: Right trim whitespace
        - SUBSTRING: Extract substring
        - CONCAT: Concatenate strings
        - LENGTH: Get string length
        - REPLACE: Replace substring
        - CONTAINS: Check if string contains substring
        - STARTS_WITH: Check if starts with prefix
        - ENDS_WITH: Check if ends with suffix
    """
    UPPER = auto()
    LOWER = auto()
    TRIM = auto()
    LTRIM = auto()
    RTRIM = auto()
    SUBSTRING = auto()
    CONCAT = auto()
    LENGTH = auto()
    REPLACE = auto()
    CONTAINS = auto()
    STARTS_WITH = auto()
    ENDS_WITH = auto()


class CONST_EXPRESSION_LOGICAL_OPERATORS(Enum):
    """
    Enumeration for expression logical operators.
    """
    # Source and literal operations
    # COL =  "COL"
    # LIT =  "LIT"
    # CAST = "CAST"

    # # Comparison operators
    # EQ =  "EQ"
    # NE =  "NE"
    # GT =  "GT"
    # LT =  "LT"
    # GE =  "GE"
    # LE =  "LE"

    # Collection operators
    # IN =     "IN"
    # NOT_IN = "NOT_IN"

    # Null checks
    # IS_NULL =     "IS_NULL"
    # IS_NOT_NULL = "IS_NOT_NULL"

    # Range operations
    # BETWEEN = "BETWEEN"

    # Logical operators
    NOT = "NOT"
    AND = "AND"
    OR =  "OR"

    # XOR variations
    XOR_EXCLUSIVE = "XOR_EXCLUSIVE"
    XOR_PARITY =    "XOR_PARITY"  # Boolean Only

    # Logical constants
    # ALWAYS_TRUE =    "ALWAYS_TRUE"
    # ALWAYS_FALSE =   "ALWAYS_FALSE"
    # ALWAYS_UNKNOWN = "ALWAYS_UNKNOWN"  # Ternary Only

    # Truth value checks
    # IS_TRUE =    "IS_TRUE"
    # IS_FALSE =   "IS_FALSE"
    # IS_UNKNOWN = "IS_UNKNOWN"  # Ternary Only

    # # Ternary-specific checks
    # MAYBE_TRUE =  "MAYBE_TRUE"   # Ternary Only
    # MAYBE_FALSE = "MAYBE_FALSE"  # Ternary Only
    # IS_KNOWN =    "IS_KNOWN"     # Ternary Only


"""
Ternary Logic Constants
"""


class CONST_TERNARY_LOGIC_VALUES(IntEnum):
    """Ternary logic constants optimized for mathematical vectorization.
    """

    TERNARY_FALSE = -1     # Represents FALSE in ternary logic
    TERNARY_UNKNOWN = 0   # Represents UNKNOWN/NULL in ternary logic
    TERNARY_TRUE = 1      # Represents TRUE in ternary logic


    @classmethod
    def from_boolean(cls, value: Optional[bool]) -> int:
        """Convert boolean value to ternary logic value.

        Args:
            value: Boolean value or None

        Returns:
            Corresponding ternary value
        """
        if value is None:
            return cls.TERNARY_UNKNOWN
        return cls.TERNARY_TRUE if value else cls.TERNARY_FALSE

    @classmethod
    def to_boolean(cls, ternary_value: int) -> Optional[bool]:
        """Convert ternary logic prime to boolean (None for UNKNOWN).

        Args:
            ternary_value: Ternary prime value

        Returns:
            Boolean value or None for UNKNOWN

        Raises:
            ValueError: If ternary_value is not a valid ternary number
        """
        if ternary_value == cls.TERNARY_TRUE:
            return True
        elif ternary_value == cls.TERNARY_FALSE:
            return False
        elif ternary_value == cls.TERNARY_UNKNOWN:
            return None
        else:
            raise ValueError(f"Invalid ternary value: {ternary_value}")
