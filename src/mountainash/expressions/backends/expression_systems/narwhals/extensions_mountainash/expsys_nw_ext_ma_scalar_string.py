"""Narwhals MountainAsh string extension implementation.

Implements regex_contains natively using Narwhals str.contains (regex by default).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class SubstraitNarwhalsScalarStringExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of MountainAsh string extensions."""

    def regex_contains(
        self,
        input: NarwhalsExpr,
        /,
        *,
        pattern: str,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Regex containment via Narwhals str.contains (regex by default).

        Note: narwhals/pandas may return False (not None) for null input.
        """
        return input.str.contains(pattern)

    def strip_suffix(self, x, /, *, suffix: str):
        pattern = re.escape(suffix) + "$"
        return x.str.replace(pattern, "")

    def to_time(self, x, /, format: str):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Narwhals does not support str.to_time(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME,
        )

    def to_integer(self, x, /, base: int = 10):
        if base != 10:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
            raise BackendCapabilityError(
                f"Narwhals does not support str.to_integer() with base={base}. "
                "Only base=10 is supported. Use Polars backend for arbitrary bases.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_STRING.TO_INTEGER,
            )
        return x.cast(nw.Int64)

    def json_decode(self, x, /, dtype=None):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Narwhals does not support str.json_decode(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE,
        )

    def json_path_match(self, x, /, json_path: str):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Narwhals does not support str.json_path_match(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH,
        )

    def encode(self, x, /, encoding: str):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Narwhals does not support str.encode(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE,
        )

    def decode(self, x, /, encoding: str, strict: bool = True):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Narwhals does not support str.decode(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.DECODE,
        )

    def extract_groups(self, x, /, pattern: str):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Narwhals does not support str.extract_groups(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS,
        )
