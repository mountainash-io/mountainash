"""Narwhals ScalarGeometryExpressionProtocol implementation.

Implements geometry operations for the Narwhals backend.

Note: Geometry operations are not supported by Narwhals.
All methods raise NotImplementedError.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarGeometryExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class SubstraitNarwhalsScalarGeometryExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarGeometryExpressionSystemProtocol):
    """Narwhals implementation of ScalarGeometryExpressionProtocol.

    Note: Geometry operations are not supported by Narwhals.
    All methods raise NotImplementedError.
    """

    # =========================================================================
    # Point Operations
    # =========================================================================

    def point(self, x: NarwhalsExpr, y: NarwhalsExpr, /) -> NarwhalsExpr:
        """Returns a 2D point with the given x and y coordinate values.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "point() is not supported by the Narwhals backend."
        )

    def make_line(self, geom1: NarwhalsExpr, geom2: NarwhalsExpr, /) -> NarwhalsExpr:
        """Returns a linestring connecting two geometries.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "make_line() is not supported by the Narwhals backend."
        )

    def x_coordinate(self, point: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the x coordinate of the point.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "x_coordinate() is not supported by the Narwhals backend."
        )

    def y_coordinate(self, point: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the y coordinate of the point.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "y_coordinate() is not supported by the Narwhals backend."
        )

    # =========================================================================
    # Geometry Property Checks
    # =========================================================================

    def num_points(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the number of points in the geometry.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "num_points() is not supported by the Narwhals backend."
        )

    def is_empty(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return true if the geometry is an empty geometry.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "is_empty() is not supported by the Narwhals backend."
        )

    def is_closed(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return true if the geometry's start and end points are the same.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "is_closed() is not supported by the Narwhals backend."
        )

    def is_simple(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return true if the geometry does not self intersect.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "is_simple() is not supported by the Narwhals backend."
        )

    def is_ring(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return true if closed and simple.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "is_ring() is not supported by the Narwhals backend."
        )

    def is_valid(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return true if the input geometry is a valid 2D geometry.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "is_valid() is not supported by the Narwhals backend."
        )

    def geometry_type(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the type of geometry as a string.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "geometry_type() is not supported by the Narwhals backend."
        )

    def dimension(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the dimension of the input geometry.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "dimension() is not supported by the Narwhals backend."
        )

    # =========================================================================
    # Geometry Analysis
    # =========================================================================

    def envelope(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the minimum bounding box for the input geometry.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "envelope() is not supported by the Narwhals backend."
        )

    def centroid(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the geometric center of mass.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "centroid() is not supported by the Narwhals backend."
        )

    # =========================================================================
    # Geometry Transformations
    # =========================================================================

    def buffer(self, geom: NarwhalsExpr, /, buffer_radius: NarwhalsExpr) -> NarwhalsExpr:
        """Compute an expanded version of the input geometry.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "buffer() is not supported by the Narwhals backend."
        )

    def minimum_bounding_circle(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return the smallest circle polygon that contains the geometry.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "minimum_bounding_circle() is not supported by the Narwhals backend."
        )

    def collection_extract(self, geom_collection: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return a homogenous multi-geometry from a collection.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "collection_extract() is not supported by the Narwhals backend."
        )

    def flip_coordinates(self, geom_collection: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return a version with X and Y axis flipped.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "flip_coordinates() is not supported by the Narwhals backend."
        )

    def remove_repeated_points(self, geom: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return a version with duplicate consecutive points removed.

        Raises:
            NotImplementedError: Narwhals doesn't support geometry.
        """
        raise NotImplementedError(
            "remove_repeated_points() is not supported by the Narwhals backend."
        )
