"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union

from mountainash.core.types import ExpressionT


class SubstraitScalarGeometryExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for scalar geometry operations.

    Auto-generated from Substrait geometry extension.
    Function type: scalar
    """

    def point(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """Returns a 2D point with the given `x` and `y` coordinate values.


        Substrait: point
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def make_line(self, geom1: ExpressionT, geom2: ExpressionT, /) -> ExpressionT:
        """Returns a linestring connecting the endpoint of geometry `geom1` to the begin point of geometry `geom2`. Repeated points at the beginning of input geometries are collapsed to a single point.
A linestring can be closed or simple.  A closed linestring starts and ends on the same point. A simple linestring does not cross or touch itself.


        Substrait: make_line
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def x_coordinate(self, point: ExpressionT, /) -> ExpressionT:
        """Return the x coordinate of the point.  Return null if not available.


        Substrait: x_coordinate
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def y_coordinate(self, point: ExpressionT, /) -> ExpressionT:
        """Return the y coordinate of the point.  Return null if not available.


        Substrait: y_coordinate
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def num_points(self, geom: ExpressionT, /) -> ExpressionT:
        """Return the number of points in the geometry.  The geometry should be an linestring or circularstring.


        Substrait: num_points
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_empty(self, geom: ExpressionT, /) -> ExpressionT:
        """Return true is the geometry is an empty geometry.


        Substrait: is_empty
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_closed(self, geom: ExpressionT, /) -> ExpressionT:
        """Return true if the geometry's start and end points are the same.


        Substrait: is_closed
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_simple(self, geom: ExpressionT, /) -> ExpressionT:
        """Return true if the geometry does not self intersect.


        Substrait: is_simple
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_ring(self, geom: ExpressionT, /) -> ExpressionT:
        """Return true if the geometry's start and end points are the same and it does not self intersect.


        Substrait: is_ring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_valid(self, geom: ExpressionT, /) -> ExpressionT:
        """Return true if the input geometry is a valid 2D geometry.
For 3 dimensional and 4 dimensional geometries, the validity is still only tested in 2 dimensions.


        Substrait: is_valid
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...


    def geometry_type(self, geom: ExpressionT, /) -> ExpressionT:
        """Return the type of geometry as a string.


        Substrait: geometry_type
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def dimension(self, geom: ExpressionT, /) -> ExpressionT:
        """Return the dimension of the input geometry.  If the input is a collection of geometries, return the largest dimension from the collection. Dimensionality is determined by the complexity of the input and not the coordinate system being used.
Type dimensions: POINT   - 0 LINE    - 1 POLYGON - 2


        Substrait: dimension
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...


    def envelope(self, geom: ExpressionT, /) -> ExpressionT:
        """Return the minimum bounding box for the input geometry as a geometry.
The returned geometry is defined by the corner points of the bounding box.  If the input geometry is a point or a line, the returned geometry can also be a point or line.


        Substrait: envelope
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def centroid(self, geom: ExpressionT, /) -> ExpressionT:
        """Return a point which is the geometric center of mass of the input geometry.


        Substrait: centroid
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...


    def buffer(self, geom: ExpressionT, /, buffer_radius: ExpressionT) -> ExpressionT:
        """Compute and return an expanded version of the input geometry. All the points of the returned geometry are at a distance of `buffer_radius` away from the points of the input geometry. If a negative `buffer_radius` is provided, the geometry will shrink instead of expand.  A negative `buffer_radius` may shrink the geometry completely, in which case an empty geometry is returned. For input the geometries of points or lines, a negative `buffer_radius` will always return an emtpy geometry.


        Substrait: buffer
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...


    def minimum_bounding_circle(self, geom: ExpressionT, /) -> ExpressionT:
        """Return the smallest circle polygon that contains the input geometry.


        Substrait: minimum_bounding_circle
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def collection_extract(self, geom_collection: ExpressionT, /) -> ExpressionT:
        """Given the input geometry collection, return a homogenous multi-geometry.  All geometries in the multi-geometry will have the same dimension.
If type is not specified, the multi-geometry will only contain geometries of the highest dimension.  If type is specified, the multi-geometry will only contain geometries of that type.  If there are no geometries of the specified type, an empty geometry is returned.  Only points, linestrings, and polygons are supported.
Type numbers: POINT   - 0 LINE    - 1 POLYGON - 2


        Substrait: collection_extract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def flip_coordinates(self, geom_collection: ExpressionT, /) -> ExpressionT:
        """Return a version of the input geometry with the X and Y axis flipped.
This operation can be performed on geometries with more than 2 dimensions. However, only X and Y axis will be flipped.


        Substrait: flip_coordinates
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def remove_repeated_points(self, geom: ExpressionT, /) -> ExpressionT:
        """Return a version of the input geometry with duplicate consecutive points removed.
If the `tolerance` argument is provided, consecutive points within the tolerance distance of one another are considered to be duplicates.


        Substrait: remove_repeated_points
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...
