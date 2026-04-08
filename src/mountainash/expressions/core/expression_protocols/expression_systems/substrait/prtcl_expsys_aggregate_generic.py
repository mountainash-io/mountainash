"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Optional

from mountainash.core.types import ExpressionT


class SubstraitAggregateGenericExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for aggregate_generic operations.

    Auto-generated from Substrait aggregate_generic extension.
    """

    def count(self, x: ExpressionT, /, overflow: Optional[str] = None) -> ExpressionT:
        """Count a set of values

        Substrait: count
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml
        """
        ...

    def count_records(
        self,
        /,
        overflow: Optional[str] = None,
    ) -> ExpressionT:
        """Substrait ``count()`` — zero-arg overload of the Substrait ``count`` function.

        From ``extensions/functions_aggregate_generic.yaml`` in the Substrait spec:
        "Count the number of records (not field-referenced)." Distinct from
        :meth:`count`, which is the 1-arg overload that counts non-null values
        of a specific column. Both serialize to Substrait wire format as the
        function name ``count``; arity distinguishes the two impls.

        The Python identifier ``count_records`` is mountainash-internal — a
        label so the two Substrait overloads can each have their own enum key,
        function mapping entry, and api-builder call site per the six-layer
        wiring matrix.

        Args:
            overflow: Optional overflow handling mode (Substrait-standard option).

        Returns:
            A backend-native expression that resolves to the row count when
            evaluated inside an aggregate context.
        """
        ...

    def any_value(self, x: ExpressionT, /, ignore_nulls: Optional[bool] = None) -> ExpressionT:
        """Selects an arbitrary value from a group of values.
If the input is empty, the function returns null.

        Substrait: any_value
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml
        """
        ...
