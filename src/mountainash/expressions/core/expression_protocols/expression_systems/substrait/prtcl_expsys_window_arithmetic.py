"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT


class SubstraitWindowArithmeticExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for window arithmetic operations.

    Auto-generated from Substrait arithmetic extension.
    Function type: window
    """

    def row_number(self, *, order_by_col: ExpressionT | None = None, descending: bool = False) -> ExpressionT:
        """the number of the current row within its partition, starting at 1

        Substrait: row_number
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def rank(self, *, order_by_col: ExpressionT | None = None, descending: bool = False) -> ExpressionT:
        """the rank of the current row, with gaps.

        Substrait: rank
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def dense_rank(self, *, order_by_col: ExpressionT | None = None, descending: bool = False) -> ExpressionT:
        """the rank of the current row, without gaps.

        Substrait: dense_rank
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def percent_rank(self) -> ExpressionT:
        """the relative rank of the current row.

        Substrait: percent_rank
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def cume_dist(self) -> ExpressionT:
        """the cumulative distribution.

        Substrait: cume_dist
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def ntile(self, x: ExpressionT, /) -> ExpressionT:
        """Return an integer ranging from 1 to the argument value,dividing the partition as equally as possible.

        Substrait: ntile
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def first_value(self, x: ExpressionT, /) -> ExpressionT:
        """Returns the first value in the window.


        Substrait: first_value
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def last_value(self, x: ExpressionT, /) -> ExpressionT:
        """Returns the last value in the window.


        Substrait: last_value
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def nth_value(self, x: ExpressionT, /, window_offset: ExpressionT = 1) -> ExpressionT:  # type: ignore[assignment]
        """Returns a value from the nth row based on the `window_offset`. `window_offset` should be a positive integer. If the value of the `window_offset` is outside the range of the window, `null` is returned.
The `on_domain_error` option governs behavior in cases where `window_offset` is not a positive integer or `null`.


        Substrait: nth_value
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def lead(self, x: ExpressionT, /) -> ExpressionT:
        """Return a value from a following row based on a specified physical offset. This allows you to compare a value in the current row against a following row.
The `expression` is evaluated against a row that comes after the current row based on the `row_offset`.  The `row_offset` should be a positive integer and is set to 1 if not specified explicitly. If the `row_offset` is negative, the expression will be evaluated against a row coming before the current row, similar to the `lag` function. A `row_offset` of `null` will return `null`. The function returns the `default` input value if `row_offset` goes beyond the scope of the window. If a `default` value is not specified, it is set to `null`.
Example comparing the sales of the current year to the following year. `row_offset` of 1. | year | sales  | next_year_sales | | 2019 | 20.50  | 30.00           | | 2020 | 30.00  | 45.99           | | 2021 | 45.99  | null            |


        Substrait: lead
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def lag(self, x: ExpressionT, /) -> ExpressionT:
        """Return a column value from a previous row based on a specified physical offset. This allows you to compare a value in the current row against a previous row.
The `expression` is evaluated against a row that comes before the current row based on the `row_offset`.  The `expression` can be a column, expression or subquery that evaluates to a single value. The `row_offset` should be a positive integer and is set to 1 if not specified explicitly. If the `row_offset` is negative, the expression will be evaluated against a row coming after the current row, similar to the `lead` function. A `row_offset` of `null` will return `null`. The function returns the `default` input value if `row_offset` goes beyond the scope of the partition. If a `default` value is not specified, it is set to `null`.
Example comparing the sales of the current year to the previous year. `row_offset` of 1. | year | sales  | previous_year_sales | | 2019 | 20.50  | null                | | 2020 | 30.00  | 20.50               | | 2021 | 45.99  | 30.00               |


        Substrait: lag
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...
