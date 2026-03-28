"""Mountainash extension expression nodes.

These nodes are not part of the Substrait standard but provide
Mountainash-specific functionality like Polars-style .over() windowing.
"""

from .exn_ext_ma_over import OverNode

__all__ = ["OverNode"]
