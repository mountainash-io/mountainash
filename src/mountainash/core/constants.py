from __future__ import annotations
from typing import Optional
from enum import Enum, IntEnum, StrEnum, auto
from dataclasses import dataclass


class CONST_BACKEND(StrEnum):
    """
    Unified backend enumeration — detection level.
    "What library produced this object?"
    Uses StrEnum so CONST_BACKEND.POLARS == "polars" — preserving
    string-based registry lookups while providing enum identity comparison.
    """
    POLARS   = "polars"
    PANDAS   = "pandas"
    PYARROW  = "pyarrow"
    IBIS     = "ibis"
    NARWHALS = "narwhals"


class CONST_BACKEND_SYSTEM(StrEnum):
    """
    Backend routing targets — system level.
    "Which system implementation handles this type?"
    Three routing targets:
    - POLARS: Native Polars operations
    - NARWHALS: pandas, PyArrow, cuDF routed through Narwhals adapter
    - IBIS: SQL backends (DuckDB, PostgreSQL, etc.)
    """
    POLARS   = "polars"
    NARWHALS = "narwhals"
    IBIS     = "ibis"


class CONST_DATAFRAME_TYPE(Enum):
    """
    Granular DataFrame variant types.
    "What specific DataFrame type is this?"
    Used by schema, pydata, and core factories for strategy dispatch.
    """
    IBIS_TABLE           = auto()
    PANDAS_DATAFRAME     = auto()
    POLARS_DATAFRAME     = auto()
    POLARS_LAZYFRAME     = auto()
    PYARROW_TABLE        = auto()
    NARWHALS_DATAFRAME   = auto()
    NARWHALS_LAZYFRAME   = auto()


class CONST_IBIS_INMEMORY_BACKEND(StrEnum):
    """
    Ibis in-memory backend variants.
    "Which SQL engine is Ibis using?"
    """
    POLARS = "polars"
    DUCKDB = "duckdb"
    SQLITE = "sqlite"


def backend_to_system(backend: CONST_BACKEND) -> CONST_BACKEND_SYSTEM:
    """
    Map a detected backend to its system routing target.
    """
    mapping = {
        CONST_BACKEND.POLARS:   CONST_BACKEND_SYSTEM.POLARS,
        CONST_BACKEND.PANDAS:   CONST_BACKEND_SYSTEM.NARWHALS,
        CONST_BACKEND.PYARROW:  CONST_BACKEND_SYSTEM.NARWHALS,
        CONST_BACKEND.IBIS:     CONST_BACKEND_SYSTEM.IBIS,
        CONST_BACKEND.NARWHALS: CONST_BACKEND_SYSTEM.NARWHALS,
    }
    return mapping[backend]


# Backwards-compat alias for expressions code
CONST_VISITOR_BACKENDS = CONST_BACKEND

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
        - COLUMN: Source data reference (columns)
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
        - TEMPORAL: Temporal/datetime operations (YEAR, MONTH, DAY, etc.)
    """
    NATIVE =                auto()
    COLUMN =                auto()
    LITERAL =               auto()
    CAST =                  auto()
    ALIAS =                 auto()
    LOGICAL =               auto()
    LOGICAL_COMPARISON =    auto()
    LOGICAL_CONSTANT =      auto()
    LOGICAL_UNARY =         auto()
    COLLECTION =            auto()
    ARITHMETIC =            auto()
    STRING =                auto()
    PATTERN =               auto()
    CONDITIONAL_IF_ELSE =   auto()
    TEMPORAL =              auto()


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


class CONST_EXPRESSION_PATTERN_OPERATORS(Enum):
    """
    Enumeration for pattern matching operators.

    Attributes:
        - LIKE: SQL-style pattern matching (% and _ wildcards)
        - REGEX_MATCH: Check if string matches regex pattern (full match)
        - REGEX_CONTAINS: Check if string contains regex pattern
        - REGEX_REPLACE: Replace text using regex pattern
    """
    LIKE = auto()
    REGEX_MATCH = auto()
    REGEX_CONTAINS = auto()
    REGEX_REPLACE = auto()


class CONST_EXPRESSION_CONDITIONAL_OPERATORS(Enum):
    """
    Enumeration for conditional operators.

    Attributes:
        - WHEN: Conditional if-then-else expression
        - COALESCE: Return first non-null value
        - FILL_NULL: Replace null values with specified value
    """
    WHEN = auto()
    COALESCE = auto()
    FILL_NULL = auto()


class CONST_EXPRESSION_TEMPORAL_OPERATORS(Enum):
    """
    Enumeration for temporal/datetime operators.

    Attributes:
        Date/Time Extraction:
        - YEAR: Extract year from datetime
        - MONTH: Extract month from datetime
        - DAY: Extract day from datetime
        - HOUR: Extract hour from datetime
        - MINUTE: Extract minute from datetime
        - SECOND: Extract second from datetime
        - WEEKDAY: Extract day of week from datetime
        - WEEK: Extract week number from datetime
        - QUARTER: Extract quarter from datetime

        Date Arithmetic (Add):
        - ADD_DAYS: Add days to a date
        - ADD_HOURS: Add hours to a datetime
        - ADD_MINUTES: Add minutes to a datetime
        - ADD_SECONDS: Add seconds to a datetime
        - ADD_MONTHS: Add months to a date
        - ADD_YEARS: Add years to a date

        Date Arithmetic (Difference):
        - DIFF_DAYS: Calculate difference in days between dates
        - DIFF_HOURS: Calculate difference in hours between datetimes
        - DIFF_MINUTES: Calculate difference in minutes between datetimes
        - DIFF_SECONDS: Calculate difference in seconds between datetimes
        - DIFF_MONTHS: Calculate difference in months between dates
        - DIFF_YEARS: Calculate difference in years between dates

        Date Truncation:
        - TRUNCATE: Truncate datetime to specified unit (day, hour, month, year, etc.)

        Flexible Operations:
        - OFFSET_BY: Add/subtract flexible duration using string format (e.g., "1d", "2h30m", "-3mo")
    """
    # Date/Time Extraction
    YEAR = auto()
    MONTH = auto()
    DAY = auto()
    HOUR = auto()
    MINUTE = auto()
    SECOND = auto()
    WEEKDAY = auto()
    WEEK = auto()
    QUARTER = auto()

    # Date Arithmetic - Add
    ADD_DAYS = auto()
    ADD_HOURS = auto()
    ADD_MINUTES = auto()
    ADD_SECONDS = auto()
    ADD_MONTHS = auto()
    ADD_YEARS = auto()

    # Date Arithmetic - Difference
    DIFF_DAYS = auto()
    DIFF_HOURS = auto()
    DIFF_MINUTES = auto()
    DIFF_SECONDS = auto()
    DIFF_MONTHS = auto()
    DIFF_YEARS = auto()

    # Date Truncation
    TRUNCATE = auto()

    # Flexible Operations
    OFFSET_BY = auto()


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


class ENUM_TERNARY_OPERATORS(Enum):
    """
    Enumeration for ternary logic operators.

    Ternary logic uses three values: TRUE (1), FALSE (-1), UNKNOWN (0).
    All comparison operations return these integer values, enabling
    NULL-aware comparisons and three-valued logic.

    Prefixed with T_ to distinguish from boolean operators.
    """
    # Column reference (with sentinel config for UNKNOWN detection)
    T_COL = auto()

    # Comparisons (return -1/0/1)
    T_EQ = auto()
    T_NE = auto()
    T_GT = auto()
    T_LT = auto()
    T_GE = auto()
    T_LE = auto()
    T_IS_IN = auto()
    T_IS_NOT_IN = auto()

    # Logical operations (use min/max semantics)
    T_AND = auto()
    T_OR = auto()
    T_NOT = auto()
    T_XOR = auto()           # Exclusive: exactly one TRUE
    T_XOR_PARITY = auto()    # Parity: odd number of TRUEs

    # Constants
    ALWAYS_TRUE = auto()
    ALWAYS_FALSE = auto()
    ALWAYS_UNKNOWN = auto()

    # Conversions (ternary → boolean)
    IS_TRUE = auto()         # 1 → True, else → False
    IS_FALSE = auto()        # -1 → True, else → False
    IS_UNKNOWN = auto()      # 0 → True, else → False
    IS_KNOWN = auto()        # 1 or -1 → True, 0 → False
    MAYBE_TRUE = auto()      # 1 or 0 → True, -1 → False
    MAYBE_FALSE = auto()     # -1 or 0 → True, 1 → False

    # Boolean → Ternary conversion
    TO_TERNARY = auto()      # True → 1, False → -1


# Ternary operators that produce boolean output (terminal conversion)
TERNARY_TERMINAL_OPERATORS = frozenset({
    ENUM_TERNARY_OPERATORS.IS_TRUE,
    ENUM_TERNARY_OPERATORS.IS_FALSE,
    ENUM_TERNARY_OPERATORS.IS_UNKNOWN,
    ENUM_TERNARY_OPERATORS.IS_KNOWN,
    ENUM_TERNARY_OPERATORS.MAYBE_TRUE,
    ENUM_TERNARY_OPERATORS.MAYBE_FALSE,
})

# Ternary operators that produce ternary (-1/0/1) output (non-terminal)
TERNARY_NON_TERMINAL_OPERATORS = frozenset({
    ENUM_TERNARY_OPERATORS.T_COL,
    ENUM_TERNARY_OPERATORS.T_EQ,
    ENUM_TERNARY_OPERATORS.T_NE,
    ENUM_TERNARY_OPERATORS.T_GT,
    ENUM_TERNARY_OPERATORS.T_LT,
    ENUM_TERNARY_OPERATORS.T_GE,
    ENUM_TERNARY_OPERATORS.T_LE,
    ENUM_TERNARY_OPERATORS.T_IS_IN,
    ENUM_TERNARY_OPERATORS.T_IS_NOT_IN,
    ENUM_TERNARY_OPERATORS.T_AND,
    ENUM_TERNARY_OPERATORS.T_OR,
    ENUM_TERNARY_OPERATORS.T_NOT,
    ENUM_TERNARY_OPERATORS.T_XOR,
    ENUM_TERNARY_OPERATORS.T_XOR_PARITY,
    ENUM_TERNARY_OPERATORS.ALWAYS_TRUE,
    ENUM_TERNARY_OPERATORS.ALWAYS_FALSE,
    ENUM_TERNARY_OPERATORS.ALWAYS_UNKNOWN,
    ENUM_TERNARY_OPERATORS.TO_TERNARY,
})


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


# --- Relational AST Enums ---

class ProjectOperation(Enum):
    """Variants of the Substrait ProjectRel."""
    SELECT = auto()
    WITH_COLUMNS = auto()
    DROP = auto()
    RENAME = auto()


class JoinType(StrEnum):
    """Join types aligned with Substrait JoinRel."""
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    OUTER = "outer"
    SEMI = "semi"
    ANTI = "anti"
    CROSS = "cross"
    ASOF = "asof"


class ExecutionTarget(Enum):
    """Which side of a join to execute on."""
    LEFT = auto()
    RIGHT = auto()


class SetType(Enum):
    """Substrait SetRel operation types."""
    UNION_ALL = auto()
    UNION_DISTINCT = auto()


class ExtensionRelOperation(Enum):
    """Mountainash extension relation operations (not in Substrait)."""
    DROP_NULLS = auto()
    WITH_ROW_INDEX = auto()
    EXPLODE = auto()
    SAMPLE = auto()
    UNPIVOT = auto()
    PIVOT = auto()
    TOP_K = auto()


@dataclass(frozen=True)
class SortField:
    """A single sort specification."""
    column: str
    descending: bool = False
    nulls_last: bool = True


class WindowBoundType(str, Enum):
    """Frame bound types for window functions."""
    CURRENT_ROW = "current_row"
    PRECEDING = "preceding"
    FOLLOWING = "following"
    UNBOUNDED_PRECEDING = "unbounded_preceding"
    UNBOUNDED_FOLLOWING = "unbounded_following"
