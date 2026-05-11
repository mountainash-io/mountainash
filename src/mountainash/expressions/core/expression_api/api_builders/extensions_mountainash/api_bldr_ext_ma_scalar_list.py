"""List operations API builder."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarListAPIBuilderProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarListAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarListAPIBuilderProtocol):
    """API builder for the .list namespace."""

    def sum(self) -> BaseExpressionAPI:
        """Sum all elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SUM,
            arguments=[self._node],
        )
        return self._build(node)

    def min(self) -> BaseExpressionAPI:
        """Minimum element in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MIN,
            arguments=[self._node],
        )
        return self._build(node)

    def max(self) -> BaseExpressionAPI:
        """Maximum element in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MAX,
            arguments=[self._node],
        )
        return self._build(node)

    def mean(self) -> BaseExpressionAPI:
        """Mean of elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MEAN,
            arguments=[self._node],
        )
        return self._build(node)

    def len(self) -> BaseExpressionAPI:
        """Count of elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.LEN,
            arguments=[self._node],
        )
        return self._build(node)

    def contains(self, item: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Check if each list contains the given item.

        Args:
            item: Value or expression to search for.
        """
        item_node = self._to_substrait_node(item)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS,
            arguments=[self._node, item_node],
        )
        return self._build(node)

    def sort(self, *, descending: bool = False) -> BaseExpressionAPI:
        """Sort elements in each list.

        Args:
            descending: Sort in descending order. Not supported on Ibis.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SORT,
            arguments=[self._node],
            options={"descending": descending},
        )
        return self._build(node)

    def unique(self) -> BaseExpressionAPI:
        """Distinct elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.UNIQUE,
            arguments=[self._node],
        )
        return self._build(node)

    def explode(self) -> BaseExpressionAPI:
        """Expand each list element into a separate row."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE,
            arguments=[self._node],
        )
        return self._build(node)

    def join(self, separator: str = ",") -> BaseExpressionAPI:
        """Concatenate list elements into a single string.

        Args:
            separator: String to place between elements.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.JOIN,
            arguments=[self._node],
            options={"separator": separator},
        )
        return self._build(node)

    def get(self, index: int) -> BaseExpressionAPI:
        """Get element at the given index.

        Args:
            index: Zero-based index. Negative indices count from the end.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.GET,
            arguments=[self._node],
            options={"index": index},
        )
        return self._build(node)

    def first(self) -> BaseExpressionAPI:
        """First element of each list."""
        return self.get(0)

    def last(self) -> BaseExpressionAPI:
        """Last element of each list."""
        return self.get(-1)

    def all(self) -> BaseExpressionAPI:
        """Check if all elements in each list are true."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ALL,
            arguments=[self._node],
        )
        return self._build(node)

    def any(self) -> BaseExpressionAPI:
        """Check if any element in each list is true."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ANY,
            arguments=[self._node],
        )
        return self._build(node)

    def drop_nulls(self) -> BaseExpressionAPI:
        """Remove null values from each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS,
            arguments=[self._node],
        )
        return self._build(node)

    def median(self) -> BaseExpressionAPI:
        """Median of elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MEDIAN,
            arguments=[self._node],
        )
        return self._build(node)

    def std(self, *, ddof: int = 1) -> BaseExpressionAPI:
        """Standard deviation of elements in each list.

        Args:
            ddof: Delta degrees of freedom. Default is 1 (sample std dev).
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.STD,
            arguments=[self._node],
            options={"ddof": ddof},
        )
        return self._build(node)

    def var(self, *, ddof: int = 1) -> BaseExpressionAPI:
        """Variance of elements in each list.

        Args:
            ddof: Delta degrees of freedom. Default is 1 (sample variance).
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.VAR,
            arguments=[self._node],
            options={"ddof": ddof},
        )
        return self._build(node)

    def n_unique(self) -> BaseExpressionAPI:
        """Count distinct elements in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE,
            arguments=[self._node],
        )
        return self._build(node)

    def count_matches(self, item: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Count occurrences of a value in each list.

        Args:
            item: Value or expression to count.
        """
        item_node = self._to_substrait_node(item)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES,
            arguments=[self._node, item_node],
        )
        return self._build(node)

    def item(self, *, index: int = 0) -> BaseExpressionAPI:
        """Get element at the given index, returning null on out-of-bounds.

        Args:
            index: Zero-based index. Negative indices count from the end.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ITEM,
            arguments=[self._node],
            options={"index": index},
        )
        return self._build(node)

    def reverse(self) -> BaseExpressionAPI:
        """Reverse each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE,
            arguments=[self._node],
        )
        return self._build(node)

    def head(self, n: int = 5) -> BaseExpressionAPI:
        """Return the first n elements of each list.

        Args:
            n: Number of elements to take from the start.
        """
        n_node = self._to_substrait_node(n)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.HEAD,
            arguments=[self._node, n_node],
        )
        return self._build(node)

    def tail(self, n: int = 5) -> BaseExpressionAPI:
        """Return the last n elements of each list.

        Args:
            n: Number of elements to take from the end.
        """
        n_node = self._to_substrait_node(n)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.TAIL,
            arguments=[self._node, n_node],
        )
        return self._build(node)

    def slice(self, offset: Union[BaseExpressionAPI, Any], *, length: int | None = None) -> BaseExpressionAPI:
        """Return a slice of each list starting at offset.

        Args:
            offset: Start index (can be an expression).
            length: Number of elements to include. None means take all remaining.
        """
        offset_node = self._to_substrait_node(offset)
        opts: dict[str, Any] = {}
        if length is not None:
            opts["length"] = length
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SLICE,
            arguments=[self._node, offset_node],
            options=opts,
        )
        return self._build(node)

    def gather(self, indices: Union[BaseExpressionAPI, Any], *, null_on_oob: bool = False) -> BaseExpressionAPI:
        """Gather elements at the given indices.

        Args:
            indices: List of indices (can be an expression).
            null_on_oob: Return null instead of raising on out-of-bounds.
        """
        indices_node = self._to_substrait_node(indices)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.GATHER,
            arguments=[self._node, indices_node],
            options={"null_on_oob": null_on_oob},
        )
        return self._build(node)

    def gather_every(self, n: Union[BaseExpressionAPI, Any], *, offset: int = 0) -> BaseExpressionAPI:
        """Take every nth element of each list.

        Args:
            n: Step size.
            offset: Starting offset before sampling.
        """
        n_node = self._to_substrait_node(n)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY,
            arguments=[self._node, n_node],
            options={"offset": offset},
        )
        return self._build(node)

    def shift(self, n: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Shift list values by n positions, filling with null.

        Args:
            n: Number of positions to shift. Positive shifts right, negative shifts left.
        """
        n_node = self._to_substrait_node(n)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT,
            arguments=[self._node, n_node],
        )
        return self._build(node)

    def diff(self, *, n: int = 1, null_behavior: str = "ignore") -> BaseExpressionAPI:
        """Compute element-wise differences within each list.

        Args:
            n: Number of slots to shift before differencing.
            null_behavior: How to handle nulls: "ignore" or "drop".
        """
        opts: dict[str, Any] = {"n": n}
        if null_behavior != "ignore":
            opts["null_behavior"] = null_behavior
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.DIFF,
            arguments=[self._node],
            options=opts,
        )
        return self._build(node)

    def set_union(self, other: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Union of two lists, returning unique elements from both.

        Args:
            other: List column or expression to union with.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_UNION,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def set_intersection(self, other: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Elements common to both lists (deduplicated).

        Args:
            other: List column or expression to intersect with.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_INTERSECTION,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def set_difference(self, other: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Elements in self that are not in other (deduplicated).

        Args:
            other: List column or expression to subtract.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def set_symmetric_difference(self, other: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Elements in either list but not both.

        Args:
            other: List column or expression to compare with.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_SYMMETRIC_DIFFERENCE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def concat(self, other: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Concatenate two list columns element-wise.

        Args:
            other: List column or expression to append.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.CONCAT,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def filter(self, mask: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Filter list elements using a boolean predicate expression.

        The mask expression is evaluated per element (use ``pl.element()``
        in Polars context, or a deferred predicate in Ibis).

        Args:
            mask: Boolean predicate expression applied to each element.
        """
        mask_node = self._to_substrait_node(mask)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.FILTER,
            arguments=[self._node, mask_node],
        )
        return self._build(node)

    def to_struct(self, *, n_field_strategy: str = "first_non_null", fields: list[str] | None = None, upper_bound: int | None = None) -> BaseExpressionAPI:
        """Convert each list to a struct.

        Args:
            n_field_strategy: How to determine the number of fields. One of
                "first_non_null", "max_width". Default "first_non_null".
            fields: Optional list of field names. If None, fields are named
                "field_0", "field_1", etc.
            upper_bound: Optional upper bound on the number of struct fields.
                Only used when n_field_strategy is "max_width".
        """
        opts: dict[str, Any] = {"n_field_strategy": n_field_strategy}
        if fields is not None:
            opts["fields"] = fields
        if upper_bound is not None:
            opts["upper_bound"] = upper_bound
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT,
            arguments=[self._node],
            options=opts,
        )
        return self._build(node)

    def to_array(self, *, width: int) -> BaseExpressionAPI:
        """Convert each list to a fixed-width array.

        Args:
            width: The fixed width of the resulting array. All lists must have
                exactly this many elements.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY,
            arguments=[self._node],
            options={"width": width},
        )
        return self._build(node)

    def arg_min(self) -> BaseExpressionAPI:
        """Return the index of the minimum value in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN,
            arguments=[self._node],
        )
        return self._build(node)

    def arg_max(self) -> BaseExpressionAPI:
        """Return the index of the maximum value in each list."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX,
            arguments=[self._node],
        )
        return self._build(node)

    def sample(self, n: Union[BaseExpressionAPI, Any] = None, *, fraction: float | None = None, with_replacement: bool = False, shuffle: bool = False, seed: int | None = None) -> BaseExpressionAPI:
        """Sample elements from each list.

        Either ``n`` or ``fraction`` must be provided, but not both.

        Args:
            n: Number of elements to sample. Can be an expression.
            fraction: Fraction of elements to sample (0.0 – 1.0).
            with_replacement: Allow sampling with replacement.
            shuffle: Shuffle the result after sampling.
            seed: Random seed for reproducibility.
        """
        args = [self._node]
        if n is not None:
            args.append(self._to_substrait_node(n))
        opts: dict[str, Any] = {}
        if fraction is not None:
            opts["fraction"] = fraction
        if with_replacement:
            opts["with_replacement"] = True
        if shuffle:
            opts["shuffle"] = True
        if seed is not None:
            opts["seed"] = seed
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SAMPLE,
            arguments=args,
            options=opts,
        )
        return self._build(node)

    def agg(self, expr: Union[BaseExpressionAPI, Any]) -> BaseExpressionAPI:
        """Aggregate the elements of each list with an expression.

        The expression is evaluated over each list's elements in a sub-context
        (similar to Polars ``pl.element()``).

        Args:
            expr: Aggregation expression applied to each list's elements.
        """
        expr_node = self._to_substrait_node(expr)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.AGG,
            arguments=[self._node, expr_node],
        )
        return self._build(node)
