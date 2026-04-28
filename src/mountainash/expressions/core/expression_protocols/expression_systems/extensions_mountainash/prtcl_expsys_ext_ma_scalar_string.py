"""Mountainash string extension protocol.

Mountainash Extension: String
URI: file://extensions/functions_string.yaml

Extensions beyond Substrait standard:
- regex_contains: Regex containment check (Substrait CONTAINS is literal-only)
"""

from __future__ import annotations

from typing import Optional, Protocol

from mountainash.core.types import ExpressionT


class MountainAshScalarStringExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for Mountainash string extensions.

    These operations extend beyond the Substrait standard string functions.
    """

    def regex_contains(
        self,
        input: ExpressionT,
        /,
        *,
        pattern: str,
        case_sensitivity: Optional[str] = None,
    ) -> ExpressionT:
        """Check if string contains a match for a regex pattern.

        Mountainash extension — Substrait has no regexp_contains primitive.
        Backends should implement this natively (e.g. polars str.contains
        with literal=False, ibis re_search) so null propagation is correct
        and on-match returns boolean directly.

        Args:
            input: String expression.
            pattern: Regex pattern as a literal ``str`` (kw-only, never an
                expression — see arguments-vs-options.md).
            case_sensitivity: "CASE_SENSITIVE" or "CASE_INSENSITIVE".

        Returns:
            Boolean expression — True on match, False on no-match,
            null when input is null (backend-dependent for narwhals).
        """
        ...

    def strip_suffix(self, x: ExpressionT, /, *, suffix: str) -> ExpressionT:
        """Remove suffix from end of string if present."""
        ...
