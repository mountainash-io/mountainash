"""Declarative, backend-independent projection name and column-count rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectionRule:
    """Describe naming independently of output cardinality.

    ``operand`` chooses a name, not the sole cardinality-bearing argument.
    ``propagate`` considers all output-affecting operands, preserving empty
    expansions and uncertainty. ``single`` describes columns, not result rows.
    ``contextual`` requires an explicit enum-keyed resolver handler for nested
    list evaluation, struct selection, or window ordering. ``internal_collection``
    is a value collection consumed by a parent, never a projectable column.
    ``value`` is a fixed name or the option key supplying a name/transformation.
    """

    name_kind: str
    cardinality_kind: str
    operand: int = 0
    value: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        names = {
            "operand", "fixed", "option", "alias", "prefix", "suffix",
            "upper", "lower", "first_order", "requires_alias", "internal",
        }
        cardinalities = {
            "propagate", "single", "contextual", "unknown", "internal_collection",
        }
        if self.name_kind not in names or self.cardinality_kind not in cardinalities:
            raise ValueError("Unknown projection rule kind")
        if type(self.operand) is not int or self.operand < 0:
            raise ValueError("Projection operand index must be non-negative")
        if self.name_kind in {"fixed", "option"} and self.value is None:
            raise ValueError("Projection rule requires a value")
        if self.name_kind in {"requires_alias", "internal"} and not self.reason:
            raise ValueError("Projection disposition requires a reason")


PROPAGATE_FIRST = ProjectionRule("operand", "propagate", operand=0)
LITERAL_SINGLE = ProjectionRule("fixed", "single", value="literal")
