"""Ibis MountainAsh string extension implementation.

Implements regex_contains natively using Ibis re_search.
"""

from __future__ import annotations

import re
from typing import Any

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol



class SubstraitIbisScalarStringExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol["IbisBooleanExpr"]):
    """Ibis implementation of MountainAsh string extensions."""

    def regex_contains(
        self,
        input,
        /,
        *,
        pattern: str,
        case_sensitivity: Any = None,
    ):
        """Regex containment via Ibis re_search.

        re_search returns a true boolean and propagates null on null input.
        """
        return input.re_search(pattern)

    def strip_suffix(self, x, /, *, suffix: str):
        pattern = re.escape(suffix) + "$"
        return x.re_replace(pattern, "")

    def to_time(self, x, /, format: str):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Ibis does not support str.to_time(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME,
        )

    def to_integer(self, x, /, base: int = 10):
        if base != 10:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
            raise BackendCapabilityError(
                f"Ibis does not support str.to_integer() with base={base}. "
                "Only base=10 is supported. Use Polars backend for arbitrary bases.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_STRING.TO_INTEGER,
            )
        import ibis.expr.datatypes as dt
        return x.cast(dt.int64)

    def json_decode(self, x, /, dtype=None):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Ibis does not support str.json_decode(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE,
        )

    def json_path_match(self, x, /, json_path: str):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Ibis does not support str.json_path_match(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH,
        )

    def encode(self, x, /, encoding: str):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Ibis does not support str.encode(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE,
        )

    def decode(self, x, /, encoding: str, strict: bool = True):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Ibis does not support str.decode(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.DECODE,
        )

    def extract_groups(self, x, /, pattern: str):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING
        raise BackendCapabilityError(
            "Ibis does not support str.extract_groups(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS,
        )
