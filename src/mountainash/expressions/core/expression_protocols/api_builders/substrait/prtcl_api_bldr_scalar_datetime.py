"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class SubstraitScalarDatetimeAPIBuilderProtocol(Protocol):
    """Builder protocol for datetime operations.

    Contains ONLY methods that are direct 1:1 Substrait functions.
    Convenience wrapper methods (year(), add_days(), etc.) are in
    mountainash_extensions/ext_datetime.py.
    """

    # ============================================================
    # Timezone Operations (Direct Substrait functions)
    # ============================================================

    def local_timestamp(
        self,
        timezone: str,
    ) -> BaseExpressionAPI:
        """Convert UTC-relative timestamp_tz to local timestamp.

        Substrait: local_timestamp
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def assume_timezone(
        self,
        timezone: str,
    ) -> BaseExpressionAPI:
        """Convert local timestamp to UTC-relative timestamp_tz.

        Substrait: assume_timezone
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    # ============================================================
    # Extraction (Direct Substrait functions)
    # ============================================================

    def extract(
        self,
        component: str,
        indexing: str | None = None,
        timezone: str | None = None,
    ) -> BaseExpressionAPI:
        """Extract a date/time component.

        Substrait: extract
        """
        ...

    def extract_boolean(
        self,
        component: str,
        timezone: str | None = None,
    ) -> BaseExpressionAPI:
        """Extract a boolean date/time component.

        Substrait: extract_boolean
        """
        ...

    # ============================================================
    # Formatting / Parsing (Direct Substrait functions)
    # ============================================================

    def strftime(
        self,
        format: str,
    ) -> BaseExpressionAPI:
        """Format datetime as string.

        Substrait: strftime
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def add_intervals(
        self,
        y: object,
    ) -> BaseExpressionAPI:
        """Add an interval/duration to a datetime expression.

        Substrait: add_intervals
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    # ============================================================
    # Rounding (Direct Substrait functions)
    # ============================================================

    def round_temporal(
        self,
        rounding: str,
        unit: str,
        multiple: int = 1,
        origin: object = None,
    ) -> BaseExpressionAPI:
        """Round a timestamp/date/time to a multiple of a fixed-duration unit.

        Substrait: round_temporal
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def round_calendar(
        self,
        rounding: str,
        unit: str,
        multiple: int = 1,
        origin: object = None,
    ) -> BaseExpressionAPI:
        """Round a timestamp/date/time to a multiple of a calendar unit.

        Substrait: round_calendar
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...
