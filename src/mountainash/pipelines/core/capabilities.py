from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any, Iterator, Sequence


@dataclass(frozen=True)
class ParamSpec:
    """Declares one parameter a pipeline step accepts."""
    name: str
    type: type
    required: bool = True
    default: Any = None


@dataclass(frozen=True)
class ParamAxis:
    """One axis of parameterised iteration (like pytest.mark.parametrize).

    names: a single param name (str) or a tuple of param names for multi-value rows.
    values: a sequence of values (or tuples when names is a tuple).
    """
    names: str | tuple[str, ...]
    values: Sequence[Any]

    def __post_init__(self) -> None:
        if isinstance(self.names, tuple):
            if len(self.names) == 0:
                raise ValueError("ParamAxis names tuple must not be empty")
            for i, v in enumerate(self.values):
                if not isinstance(v, tuple) or len(v) != len(self.names):
                    raise ValueError(
                        f"Value at index {i} must be a tuple of length {len(self.names)}, "
                        f"got {v!r}"
                    )


def expand_axes(*axes: ParamAxis) -> Iterator[dict[str, Any]]:
    """Yield one param dict per combination across axes (cartesian product).

    - No axes: yields one empty dict.
    - One axis with empty values: yields nothing.
    - Multiple axes: cartesian product across all axes.
    - Tuple axis: each tuple value is exploded into the named params.
    - Duplicate param names across axes: raises ValueError.
    """
    # Validate no duplicate names across axes
    all_names: list[str] = []
    for axis in axes:
        names = [axis.names] if isinstance(axis.names, str) else list(axis.names)
        for name in names:
            if name in all_names:
                raise ValueError(
                    f"duplicate param name '{name}' across axes"
                )
            all_names.append(name)

    if not axes:
        yield {}
        return

    # Build per-axis list of (name_list, value) pairs
    axis_rows: list[list[tuple[tuple[str, ...], Any]]] = []
    for axis in axes:
        names_tuple = (axis.names,) if isinstance(axis.names, str) else axis.names
        rows = [(names_tuple, v) for v in axis.values]
        axis_rows.append(rows)

    for combo in product(*axis_rows):
        record: dict[str, Any] = {}
        for names_tuple, value in combo:
            if len(names_tuple) == 1:
                record[names_tuple[0]] = value
            else:
                for name, val in zip(names_tuple, value):
                    record[name] = val
        yield record
