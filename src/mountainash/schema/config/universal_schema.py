"""DEPRECATED: Use mountainash.typespec.spec instead.

Re-exports with old names for backward compatibility with pydata.
"""
from mountainash.typespec.spec import TypeSpec as TableSchema  # noqa: F401
from mountainash.typespec.spec import FieldSpec as SchemaField  # noqa: F401
from mountainash.typespec.spec import FieldConstraints  # noqa: F401
from mountainash.typespec.spec import SpecDiff as SchemaDiff  # noqa: F401
from mountainash.typespec.spec import compare_specs as compare_schemas  # noqa: F401
