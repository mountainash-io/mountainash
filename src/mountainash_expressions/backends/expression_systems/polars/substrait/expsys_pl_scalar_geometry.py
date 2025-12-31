"""Polars ScalarGeometryExpressionProtocol implementation.

Implements geometry operations for the Polars backend.

Note: Geometry operations are not natively supported by Polars.
All methods raise NotImplementedError.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import PolarsBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarGeometryExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import PolarsExpr


class SubstraitPolarsScalarGeometryExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarGeometryExpressionSystemProtocol):
    """Polars implementation of ScalarGeometryExpressionProtocol.

    Note: Geometry operations are not supported by Polars.
    All methods raise NotImplementedError.
    Consider using GeoPolars or a dedicated geometry library for spatial operations.
    """

    # =========================================================================
    # Point Operations
    # =========================================================================

    def point(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        """Returns a 2D point with the given x and y coordinate values.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "point() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def make_line(self, geom1: PolarsExpr, geom2: PolarsExpr, /) -> PolarsExpr:
        """Returns a linestring connecting two geometries.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "make_line() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def x_coordinate(self, point: PolarsExpr, /) -> PolarsExpr:
        """Return the x coordinate of the point.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "x_coordinate() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def y_coordinate(self, point: PolarsExpr, /) -> PolarsExpr:
        """Return the y coordinate of the point.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "y_coordinate() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    # =========================================================================
    # Geometry Property Checks
    # =========================================================================

    def num_points(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return the number of points in the geometry.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "num_points() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def is_empty(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return true if the geometry is an empty geometry.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "is_empty() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def is_closed(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return true if the geometry's start and end points are the same.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "is_closed() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def is_simple(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return true if the geometry does not self intersect.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "is_simple() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def is_ring(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return true if closed and simple.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "is_ring() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def is_valid(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return true if the input geometry is a valid 2D geometry.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "is_valid() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def geometry_type(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return the type of geometry as a string.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "geometry_type() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def dimension(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return the dimension of the input geometry.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "dimension() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    # =========================================================================
    # Geometry Analysis
    # =========================================================================

    def envelope(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return the minimum bounding box for the input geometry.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "envelope() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def centroid(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return the geometric center of mass.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "centroid() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    # =========================================================================
    # Geometry Transformations
    # =========================================================================

    def buffer(self, geom: PolarsExpr, buffer_radius: PolarsExpr, /) -> PolarsExpr:
        """Compute an expanded version of the input geometry.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "buffer() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def minimum_bounding_circle(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return the smallest circle polygon that contains the geometry.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "minimum_bounding_circle() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def collection_extract(self, geom_collection: PolarsExpr, /) -> PolarsExpr:
        """Return a homogenous multi-geometry from a collection.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "collection_extract() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def flip_coordinates(self, geom_collection: PolarsExpr, /) -> PolarsExpr:
        """Return a version with X and Y axis flipped.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "flip_coordinates() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )

    def remove_repeated_points(self, geom: PolarsExpr, /) -> PolarsExpr:
        """Return a version with duplicate consecutive points removed.

        Raises:
            NotImplementedError: Polars doesn't support geometry.
        """
        raise NotImplementedError(
            "remove_repeated_points() is not supported by the Polars backend. "
            "Consider using GeoPolars for spatial operations."
        )
