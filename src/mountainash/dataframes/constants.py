from enum import Enum,StrEnum, auto


# TODO: Move to mountainash-dataframes
class CONST_DATAFRAME_FRAMEWORK(StrEnum):
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
    PYARROW =  "pyarrow"
    NARWHALS =  "narwhals"
    # NUMPY =    "numpy"
    # PYARROW_RECORDBATCH = "pyarrow_recordbatch"
    # PYARROW_TABLE = "pyarrow_table"
    # XARRAY = "xarray"
    # PYSPARK = "pyspark"

# TODO: Move to mountainash-dataframes
class CONST_IBIS_INMEMORY_BACKEND(StrEnum):
    """
    Enumeration for different ibis backend_schema frameworks.

    Attributes:
        - POLARS (str): Polars ibis backend_schema.
        - DUCKDB (str): Duckdb ibis backend_schema.
        - SQLITE (str): sqlite ibis backend_schema.
    """
    POLARS =   "polars"
    DUCKDB =   "duckdb"
    SQLITE =   "sqlite"


class CONST_DATAFRAME_TYPE(Enum):
    IBIS_TABLE = auto()
    PANDAS_DATAFRAME = auto()
    POLARS_DATAFRAME = auto()
    POLARS_LAZYFRAME = auto()
    PYARROW_TABLE = auto()
    NARWHALS_DATAFRAME = auto()
    NARWHALS_LAZYFRAME = auto()

class CONST_DATAFRAME_BACKEND(Enum):
    IBIS = auto()
    PANDAS = auto()
    POLARS = auto()
    PYARROW = auto()
    NARWHALS = auto()

class CONST_EXPRESSION_TYPE(Enum):
    IBIS = auto()
    POLARS = auto()
    NARWHALS = auto()
    PANDAS = auto()

class CONST_JOIN_BACKEND_TYPE(Enum):
    IBIS = auto()
    POLARS = auto()
    NARWHALS = auto()


class CONST_PYTHON_DATAFORMAT(Enum):
    DATACLASS = auto()
    PYDANTIC = auto()
    PYDICT = auto()
    PYLIST = auto()
    NAMEDTUPLE = auto()
    TUPLE = auto()
    INDEXED_DATA = auto()
    SERIES_DICT = auto()
    COLLECTION = auto()
    UNKNOWN = auto()
