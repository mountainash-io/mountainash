"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode


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
