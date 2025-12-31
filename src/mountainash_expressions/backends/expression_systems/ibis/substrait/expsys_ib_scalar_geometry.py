"""Ibis ScalarGeometryExpressionProtocol implementation.

Implements geometry operations for the Ibis backend.

Note: Geometry operations may be partially supported by some Ibis backends
(e.g., PostGIS, DuckDB Spatial). This implementation provides stubs that
raise NotImplementedError for most operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import IbisBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarGeometryExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import IbisExpr


class SubstraitIbisScalarGeometryExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarGeometryExpressionSystemProtocol):
    """Ibis implementation of ScalarGeometryExpressionProtocol.

    Note: Geometry operations depend on the underlying backend.
    PostGIS and DuckDB Spatial may support some operations.
    Most methods raise NotImplementedError.
    """

    # =========================================================================
    # Point Operations
    # =========================================================================

    def point(self, x: IbisExpr, y: IbisExpr, /) -> IbisExpr:
        """Returns a 2D point with the given x and y coordinate values.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "point() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def make_line(self, geom1: IbisExpr, geom2: IbisExpr, /) -> IbisExpr:
        """Returns a linestring connecting two geometries.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "make_line() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def x_coordinate(self, point: IbisExpr, /) -> IbisExpr:
        """Return the x coordinate of the point.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "x_coordinate() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def y_coordinate(self, point: IbisExpr, /) -> IbisExpr:
        """Return the y coordinate of the point.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "y_coordinate() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    # =========================================================================
    # Geometry Property Checks
    # =========================================================================

    def num_points(self, geom: IbisExpr, /) -> IbisExpr:
        """Return the number of points in the geometry.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "num_points() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def is_empty(self, geom: IbisExpr, /) -> IbisExpr:
        """Return true if the geometry is an empty geometry.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "is_empty() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def is_closed(self, geom: IbisExpr, /) -> IbisExpr:
        """Return true if the geometry's start and end points are the same.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "is_closed() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def is_simple(self, geom: IbisExpr, /) -> IbisExpr:
        """Return true if the geometry does not self intersect.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "is_simple() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def is_ring(self, geom: IbisExpr, /) -> IbisExpr:
        """Return true if closed and simple.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "is_ring() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def is_valid(self, geom: IbisExpr, /) -> IbisExpr:
        """Return true if the input geometry is a valid 2D geometry.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "is_valid() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def geometry_type(self, geom: IbisExpr, /) -> IbisExpr:
        """Return the type of geometry as a string.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "geometry_type() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def dimension(self, geom: IbisExpr, /) -> IbisExpr:
        """Return the dimension of the input geometry.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "dimension() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    # =========================================================================
    # Geometry Analysis
    # =========================================================================

    def envelope(self, geom: IbisExpr, /) -> IbisExpr:
        """Return the minimum bounding box for the input geometry.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "envelope() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def centroid(self, geom: IbisExpr, /) -> IbisExpr:
        """Return the geometric center of mass.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "centroid() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    # =========================================================================
    # Geometry Transformations
    # =========================================================================

    def buffer(self, geom: IbisExpr, buffer_radius: IbisExpr, /) -> IbisExpr:
        """Compute an expanded version of the input geometry.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "buffer() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def minimum_bounding_circle(self, geom: IbisExpr, /) -> IbisExpr:
        """Return the smallest circle polygon that contains the geometry.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "minimum_bounding_circle() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def collection_extract(self, geom_collection: IbisExpr, /) -> IbisExpr:
        """Return a homogenous multi-geometry from a collection.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "collection_extract() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def flip_coordinates(self, geom_collection: IbisExpr, /) -> IbisExpr:
        """Return a version with X and Y axis flipped.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "flip_coordinates() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )

    def remove_repeated_points(self, geom: IbisExpr, /) -> IbisExpr:
        """Return a version with duplicate consecutive points removed.

        Raises:
            NotImplementedError: Requires backend-specific geometry support.
        """
        raise NotImplementedError(
            "remove_repeated_points() requires backend-specific geometry support. "
            "Consider using PostGIS or DuckDB Spatial backend."
        )
