"""ConformBuilder — user-facing DSL for conforming DataFrames to a TypeSpec.

Accepts a dict-based column spec or an existing TypeSpec, and exposes:
- .spec            → the underlying TypeSpec
- .apply(df)       → compile and execute against a DataFrame (lazy import)
- .to_frictionless() → export as a Frictionless Table Schema dict
- .from_frictionless() → classmethod constructor from a Frictionless descriptor
"""
from __future__ import annotations

from typing import Any, Dict, Union

from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType, normalize_type


class ConformBuilder:
    """User-facing DSL for data conformance operations.

    Accepts either a target-oriented column dict or an existing TypeSpec.

    Column dict format::

        {
            "target_col_name": {
                "cast": "integer",       # optional — UniversalType string
                "rename_from": "src",    # optional — source column name
                "null_fill": 0,          # optional — fill value for nulls
            },
            ...
        }

    Args:
        source: A dict mapping target column names to field configuration
            dicts, or an existing TypeSpec (passed through unchanged).
    """

    def __init__(self, source: Union[Dict[str, Dict[str, Any]], TypeSpec]) -> None:
        if isinstance(source, TypeSpec):
            self._spec = source
        elif isinstance(source, dict):
            self._spec = self._dict_to_spec(source)
        else:
            raise TypeError(
                f"ConformBuilder expects a dict or TypeSpec, got {type(source).__name__}"
            )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def spec(self) -> TypeSpec:
        """The underlying TypeSpec."""
        return self._spec

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_frictionless(
        cls,
        data: Union[Dict[str, Any], str],
    ) -> "ConformBuilder":
        """Construct a ConformBuilder from a Frictionless Table Schema descriptor.

        Args:
            data: A Frictionless Table Schema descriptor dict, a JSON string,
                or a path to a JSON file.

        Returns:
            A new ConformBuilder wrapping the parsed TypeSpec.
        """
        spec = TypeSpec.from_frictionless(data)
        return cls(spec)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_frictionless(self) -> Dict[str, Any]:
        """Export the underlying TypeSpec as a Frictionless Table Schema dict.

        Mountainash extensions (rename_from, null_fill) are stored under
        ``x-mountainash`` keys per field.

        Returns:
            A Frictionless-compatible descriptor dict.
        """
        return self._spec.to_frictionless()

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def apply(self, df: Any) -> Any:
        """Compile the TypeSpec and apply it to a DataFrame.

        Performs backend detection and delegates compilation to
        ``mountainash.conform.compiler.compile_conform``.

        Args:
            df: A DataFrame (Polars, pandas, PyArrow, or Ibis table).

        Returns:
            A conformed DataFrame in the same backend as the input.
        """
        from .compiler import compile_conform  # noqa: PLC0415 — lazy import (Task 6)
        return compile_conform(self._spec, df)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dict_to_spec(columns: Dict[str, Dict[str, Any]]) -> TypeSpec:
        """Convert a target-oriented column dict to a TypeSpec.

        Each key is the target column name; the value is a config dict with
        optional keys ``cast``, ``rename_from``, and ``null_fill``.

        Missing ``cast`` defaults to ``UniversalType.ANY``.

        Args:
            columns: Mapping of target column name → field config dict.

        Returns:
            A TypeSpec with one FieldSpec per entry.
        """
        fields = []
        for target_name, config in columns.items():
            cast_str = config.get("cast")
            if cast_str is not None:
                # Check if the cast string is a recognized UniversalType value.
                # normalize_type() silently returns ANY for unknown types rather
                # than raising, so we must check membership ourselves.
                if cast_str in UniversalType._value2member_map_:
                    universal_type: UniversalType = normalize_type(cast_str)
                    custom: str | None = None
                else:
                    universal_type = UniversalType.ANY
                    custom = cast_str
            else:
                universal_type = UniversalType.ANY
                custom = None

            rename_from = config.get("rename_from")
            null_fill = config.get("null_fill")

            fields.append(
                FieldSpec(
                    name=target_name,
                    type=universal_type,
                    custom_cast=custom,
                    rename_from=rename_from,
                    null_fill=null_fill,
                )
            )
        return TypeSpec(fields=fields)
