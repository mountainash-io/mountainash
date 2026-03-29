"""
Type aliases for Python data structures supported by the convert module.

These types represent the various Python data structures that can be
automatically converted to DataFrames via PydataConverterFactory.
"""

from __future__ import annotations
from typing import Any, Dict, List, Set, FrozenSet, Union

# Individual Python data types (matching convert module formats)

# PYLIST - List of dictionaries (row-oriented data)
PyListData = List[Dict[str, Any]]

# PYDICT - Dictionary of lists (column-oriented data)
PyDictData = Dict[str, List[Any]]

# COLLECTION - List, set, or frozenset of scalar values
CollectionData = Union[List[Any], Set[Any], FrozenSet[Any]]

# TUPLE - List of plain tuples (without _fields attribute)
TupleData = List[tuple]

# NAMEDTUPLE - List of named tuples
# Note: Can't type precisely without runtime inspection due to dynamic nature of namedtuple
NamedTupleData = List[Any]

# INDEXED_DATA - Dictionary with keys mapping to lists of rows
# Format: {key: [row1, row2, ...], ...}
IndexedData = Dict[Any, List[Any]]

# SERIES_DICT - Dictionary of Series objects (Polars or Pandas)
# Note: Can't type Series without importing backends, so use Any
SeriesDictData = Dict[str, Any]

# Composite type for all supported Python data structures
SupportedPythonData = Union[
    PyListData,        # List of dicts
    PyDictData,        # Dict of lists
    CollectionData,    # List/set/frozenset of scalars
    TupleData,         # List of tuples
    NamedTupleData,    # List of named tuples
    IndexedData,       # Dict of indexed rows
    SeriesDictData,    # Dict of Series
    Any                # Include Any for dataclass/Pydantic (can't type without runtime inspection)
]

# Combined type for methods that accept both DataFrames and Python data
# Import SupportedDataFrames from parent typing module to avoid circular imports
if False:  # TYPE_CHECKING equivalent for runtime
    from . import SupportedDataFrames
    DataFrameOrPythonData = Union[SupportedDataFrames, SupportedPythonData]
else:
    # At runtime, just use Any to avoid import issues
    DataFrameOrPythonData = Any

__all__ = [
    'PyListData',
    'PyDictData',
    'CollectionData',
    'TupleData',
    'NamedTupleData',
    'IndexedData',
    'SeriesDictData',
    'SupportedPythonData',
    'DataFrameOrPythonData',
]
