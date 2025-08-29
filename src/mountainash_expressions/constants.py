from typing import Union, Optional, Set
from mountainash_constants import BaseValueConstant


class CONST_DATAFRAME_FRAMEWORK(BaseValueConstant):
    """
    Enumeration for different dataframe frameworks.

    Attributes:
        - PANDAS (str): Pandas dataframe framework.
        - POLARS (str): Polars dataframe framework.
        - IBIS (str): Ibis dataframe framework.
        - NUMPY (str): Numpy array framework.
        - PYARROW_RECORDBATCH (str): PyArrow RecordBatch framework.
        - PYARROW_TABLE (str): PyArrow Table framework.
    """
    PANDAS =   "pandas"
    POLARS =   "polars"
    IBIS =     "ibis"
    PYARROW_RECORDBATCH = "pyarrow_recordbatch"
    PYARROW_TABLE = "pyarrow_table"
    # NUMPY =    "numpy"
    # XARRAY = "xarray"
    # PYSPARK = "pyspark"

class CONST_EXPRESSION_LOGIC_TYPES(BaseValueConstant):
    """
    Enumeration for different dataframe frameworks.

    Attributes:
        - PANDAS (str): Pandas dataframe framework.
        - POLARS (str): Polars dataframe framework.
        - IBIS (str): Ibis dataframe framework.
        - NUMPY (str): Numpy array framework.
        - PYARROW_RECORDBATCH (str): PyArrow RecordBatch framework.
        - PYARROW_TABLE (str): PyArrow Table framework.
    """
    BOOLEAN =   "boolean"
    TERNARY =   "ternary"
    FUZZY =     "fuzzy"

class CONST_EXPRESSION_NODE_TYPES(BaseValueConstant):
    """
    Enumeration for different dataframe frameworks.

    Attributes:
        - PANDAS (str): Pandas dataframe framework.
        - POLARS (str): Polars dataframe framework.
        - IBIS (str): Ibis dataframe framework.
        - NUMPY (str): Numpy array framework.
        - PYARROW_RECORDBATCH (str): PyArrow RecordBatch framework.
        - PYARROW_TABLE (str): PyArrow Table framework.
    """
    LITERAL =   "literal"
    COLUMN =    "column"
    LOGICAL =   "logical"


class CONST_EXPRESSION_LOGIC_OPERATORS(BaseValueConstant):

    EQ =  "EQ"
    NE =  "NE"
    GT =  "GT"
    LT =  "LT"
    GE =  "GE"
    LE =  "LE"
    IN =  "IN"

    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"
    BETWEEN = "BETWEEN"
    NOT = "NOT"

    AND = "AND"
    OR = "OR"

    XOR_EXCLUSIVE = "XOR_EXCLUSIVE"
    # Boolean Only - XOR variations
    XOR_PARITY = "XOR_PARITY"

    ALWAYS_TRUE = "ALWAYS_TRUE"
    ALWAYS_FALSE = "ALWAYS_FALSE"
    ALWAYS_UNKNOWN = "ALWAYS_UNKNOWN"

    IS_TRUE = "IS_TRUE"
    IS_FALSE = "IS_FALSE"
    IS_UNKNOWN = "IS_UNKNOWN"

    MAYBE_TRUE = "MAYBE_TRUE"
    MAYBE_FALSE = "MAYBE_FALSE"
    IS_KNOWN = "IS_KNOWN"


"""
Ternary Logic Constants
"""



class CONST_TERNARY_LOGIC_VALUES(BaseValueConstant):
    """Ternary logic constants optimized for mathematical vectorization.
    """

    TERNARY_FALSE = -1     # Represents FALSE in ternary logic
    TERNARY_UNKNOWN = 0   # Represents UNKNOWN/NULL in ternary logic
    TERNARY_TRUE = 1      # Represents TRUE in ternary logic


    @classmethod
    def from_boolean(cls, value: Optional[bool]) -> int:
        """Convert boolean value to ternary logic prime.

        Args:
            value: Boolean value or None

        Returns:
            Corresponding ternary prime value
        """
        if value is None:
            return cls.TERNARY_UNKNOWN
        return cls.TERNARY_TRUE if value else cls.TERNARY_FALSE

    @classmethod
    def to_boolean(cls, ternary_value: int) -> Optional[bool]:
        """Convert ternary logic prime to boolean (None for UNKNOWN).

        Args:
            prime_value: Ternary prime value

        Returns:
            Boolean value or None for UNKNOWN

        Raises:
            ValueError: If prime_value is not a valid ternary prime
        """
        if ternary_value == cls.TERNARY_TRUE:
            return True
        elif ternary_value == cls.TERNARY_FALSE:
            return False
        elif ternary_value == cls.TERNARY_UNKNOWN:
            return None
        else:
            raise ValueError(f"Invalid ternary value: {ternary_value}")
