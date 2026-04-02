"""Conform — compile type specifications to relation/expression operations.

Provides ConformBuilder, the user-facing DSL for conforming DataFrames
to a TypeSpec via the mountainash relations/expressions layer.
"""
from mountainash.conform.builder import ConformBuilder

__all__ = ["ConformBuilder"]
