"""Ibis expression API definitions."""

from __future__ import annotations

import datetime
import numbers
from typing import Iterable, Mapping, Sequence, TypeVar

import dateutil.parser
import pandas as pd

import ibis.expr.builders as bl
import ibis.expr.datatypes as dt
import ibis.expr.operations as ops
import ibis.expr.schema as sch
import ibis.expr.types as ir
from ibis.expr.random import random  # noqa
from ibis.expr.schema import Schema
from ibis.expr.types import (  # noqa
    ArrayColumn,
    ArrayScalar,
    ArrayValue,
    BooleanColumn,
    BooleanScalar,
    BooleanValue,
    CategoryScalar,
    CategoryValue,
    ColumnExpr,
    DateColumn,
    DateScalar,
    DateValue,
    DecimalColumn,
    DecimalScalar,
    DecimalValue,
    DestructColumn,
    DestructScalar,
    DestructValue,
    Expr,
    FloatingColumn,
    FloatingScalar,
    FloatingValue,
    GeoSpatialColumn,
    GeoSpatialScalar,
    GeoSpatialValue,
    IntegerColumn,
    IntegerScalar,
    IntegerValue,
    IntervalColumn,
    IntervalScalar,
    IntervalValue,
    LineStringColumn,
    LineStringScalar,
    LineStringValue,
    MapColumn,
    MapScalar,
    MapValue,
    MultiLineStringColumn,
    MultiLineStringScalar,
    MultiLineStringValue,
    MultiPointColumn,
    MultiPointScalar,
    MultiPointValue,
    MultiPolygonColumn,
    MultiPolygonScalar,
    MultiPolygonValue,
    NullColumn,
    NullScalar,
    NullValue,
    NumericColumn,
    NumericScalar,
    NumericValue,
    PointColumn,
    PointScalar,
    PointValue,
    PolygonColumn,
    PolygonScalar,
    PolygonValue,
    ScalarExpr,
    StringColumn,
    StringScalar,
    StringValue,
    StructColumn,
    StructScalar,
    StructValue,
    TableExpr,
    TimeColumn,
    TimeScalar,
    TimestampColumn,
    TimestampScalar,
    TimestampValue,
    TimeValue,
    ValueExpr,
    array,
    literal,
    map,
    null,
    struct,
)
from ibis.expr.types.groupby import GroupedTableExpr  # noqa
from ibis.expr.window import (
    cumulative_window,
    range_window,
    rows_with_max_lookback,
    trailing_range_window,
    trailing_window,
    window,
)

__all__ = (
    'aggregate',
    'array',
    'case',
    'coalesce',
    'cross_join',
    'cumulative_window',
    'date',
    'desc',
    'asc',
    'Expr',
    'geo_area',
    'geo_as_binary',
    'geo_as_ewkb',
    'geo_as_ewkt',
    'geo_as_text',
    'geo_azimuth',
    'geo_buffer',
    'geo_centroid',
    'geo_contains',
    'geo_contains_properly',
    'geo_covers',
    'geo_covered_by',
    'geo_crosses',
    'geo_d_fully_within',
    'geo_disjoint',
    'geo_difference',
    'geo_d_within',
    'geo_envelope',
    'geo_equals',
    'geo_geometry_n',
    'geo_geometry_type',
    'geo_intersection',
    'geo_intersects',
    'geo_is_valid',
    'geo_line_locate_point',
    'geo_line_merge',
    'geo_line_substring',
    'geo_ordering_equals',
    'geo_overlaps',
    'geo_touches',
    'geo_distance',
    'geo_end_point',
    'geo_length',
    'geo_max_distance',
    'geo_n_points',
    'geo_n_rings',
    'geo_perimeter',
    'geo_point',
    'geo_point_n',
    'geo_simplify',
    'geo_srid',
    'geo_start_point',
    'geo_transform',
    'geo_unary_union',
    'geo_union',
    'geo_within',
    'geo_x',
    'geo_x_max',
    'geo_x_min',
    'geo_y',
    'geo_y_max',
    'geo_y_min',
    'greatest',
    'ifelse',
    'infer_dtype',
    'infer_schema',
    'interval',
    'join',
    'least',
    'literal',
    'map',
    'NA',
    'negate',
    'now',
    'null',
    'param',
    'pi',
    'prevent_rewrite',
    'random',
    'range_window',
    'row_number',
    'rows_with_max_lookback',
    'schema',
    'Schema',
    'sequence',
    'struct',
    'table',
    'time',
    'timestamp',
    'trailing_range_window',
    'trailing_window',
    'where',
    'window',
)


infer_dtype = dt.infer
infer_schema = sch.infer


NA = null()

T = TypeVar("T")

negate = ir.NumericValue.negate


def param(type: dt.DataType) -> ir.ScalarExpr:
    """Create a deferred parameter of a given type.

    Parameters
    ----------
    type
        The type of the unbound parameter, e.g., double, int64, date, etc.

    Returns
    -------
    ScalarExpr
        A scalar expression backend by a parameter

    Examples
    --------
    >>> import ibis
    >>> import ibis.expr.datatypes as dt
    >>> start = ibis.param(dt.date)
    >>> end = ibis.param(dt.date)
    >>> schema = [('timestamp_col', 'timestamp'), ('value', 'double')]
    >>> t = ibis.table(schema)
    >>> predicates = [t.timestamp_col >= start, t.timestamp_col <= end]
    >>> expr = t.filter(predicates).value.sum()
    """
    return ops.ScalarParameter(dt.dtype(type)).to_expr()


def sequence(values: Sequence[T | None]) -> ir.ListExpr:
    """Wrap a list of Python values as an Ibis sequence type.

    Parameters
    ----------
    values
        Should all be None or the same type

    Returns
    -------
    ListExpr
        A list expression
    """
    return ops.ValueList(values).to_expr()


def schema(
    pairs: Iterable[tuple[str, dt.DataType]]
    | Mapping[str, dt.DataType]
    | None = None,
    names: Iterable[str] | None = None,
    types: Iterable[str | dt.DataType] | None = None,
) -> sch.Schema:
    """Validate and return an Schema object.

    Parameters
    ----------
    pairs
        List or dictionary of name, type pairs. Mutually exclusive with `names`
        and `types`.
    names
        Field names. Mutually exclusive with `pairs`.
    types
        Field types. Mutually exclusive with `pairs`.

    Examples
    --------
    >>> from ibis import schema
    >>> sc = schema([('foo', 'string'),
    ...              ('bar', 'int64'),
    ...              ('baz', 'boolean')])
    >>> sc2 = schema(names=['foo', 'bar', 'baz'],
    ...              types=['string', 'int64', 'boolean'])

    Returns
    -------
    Schema
        An ibis schema
    """  # noqa: E501
    if pairs is not None:
        return Schema.from_dict(dict(pairs))
    else:
        return Schema(names, types)


_schema = schema


def table(schema: sch.Schema, name: str | None = None) -> ir.TableExpr:
    """Create an unbound table for build expressions without data.


    Parameters
    ----------
    schema
        A schema for the table
    name
        Name for the table

    Returns
    -------
    TableExpr
        An unbound table expression
    """
    if not isinstance(schema, Schema):
        schema = _schema(pairs=schema)

    node = ops.UnboundTable(schema, name=name)
    return node.to_expr()


def desc(expr: ir.ColumnExpr | str) -> ir.SortExpr | ops.DeferredSortKey:
    """Create a descending sort key from `expr` or column name.

    Parameters
    ----------
    expr
        The expression or column name to use for sorting

    Examples
    --------
    >>> import ibis
    >>> t = ibis.table([('g', 'string')])
    >>> result = t.group_by('g').size('count').sort_by(ibis.desc('count'))

    Returns
    -------
    ops.DeferredSortKey
        A deferred sort key
    """
    if not isinstance(expr, Expr):
        return ops.DeferredSortKey(expr, ascending=False)
    else:
        return ops.SortKey(expr, ascending=False).to_expr()


def asc(expr: ir.ColumnExpr | str) -> ir.SortExpr | ops.DeferredSortKey:
    """Create a ascending sort key from `asc` or column name.

    Parameters
    ----------
    expr
        The expression or column name to use for sorting

    Examples
    --------
    >>> import ibis
    >>> t = ibis.table([('g', 'string')])
    >>> result = t.group_by('g').size('count').sort_by(ibis.asc('count'))

    Returns
    -------
    ops.DeferredSortKey
        A deferred sort key
    """
    if not isinstance(expr, Expr):
        return ops.DeferredSortKey(expr)
    else:
        return ops.SortKey(expr).to_expr()


def timestamp(
    value: str | numbers.Integral,
    timezone: str | None = None,
) -> ir.TimestampScalar:
    """Construct a timestamp literal if `value` is coercible to a timestamp.

    Parameters
    ----------
    value
        The value to use for constructing the timestamp
    timezone
        The timezone of the timestamp

    Returns
    -------
    TimestampScalar
        A timestamp expression
    """
    if isinstance(value, str):
        try:
            value = pd.Timestamp(value, tz=timezone)
        except pd.errors.OutOfBoundsDatetime:
            value = dateutil.parser.parse(value)
    if isinstance(value, numbers.Integral):
        raise TypeError(
            (
                "Passing an integer to ibis.timestamp is not supported. Use "
                "ibis.literal({value}).to_timestamp() to create a timestamp "
                "expression from an integer."
            ).format(value=value)
        )
    return literal(value, type=dt.Timestamp(timezone=timezone))


def date(value: str) -> ir.DateScalar:
    """Return a date literal if `value` is coercible to a date.

    Parameters
    ----------
    value
        Date string

    Returns
    -------
    DateScalar
        A date expression
    """
    if isinstance(value, str):
        value = pd.to_datetime(value).date()
    return literal(value, type=dt.date)


def time(value: str) -> ir.TimeScalar:
    """Return a time literal if `value` is coercible to a time.

    Parameters
    ----------
    value
        Time string

    Returns
    -------
    TimeScalar
        A time expression
    """
    if isinstance(value, str):
        value = pd.to_datetime(value).time()
    return literal(value, type=dt.time)


def interval(
    value: int | datetime.timedelta | None = None,
    unit: str = 's',
    years: int | None = None,
    quarters: int | None = None,
    months: int | None = None,
    weeks: int | None = None,
    days: int | None = None,
    hours: int | None = None,
    minutes: int | None = None,
    seconds: int | None = None,
    milliseconds: int | None = None,
    microseconds: int | None = None,
    nanoseconds: int | None = None,
) -> ir.IntervalScalar:
    """Return an interval literal expression.

    Parameters
    ----------
    value
        Interval value. If passed, must be combined with `unit`.
    unit
        Unit of `value`
    years
        Number of years
    quarters
        Number of quarters
    months
        Number of months
    weeks
        Number of weeks
    days
        Number of days
    hours
        Number of hours
    minutes
        Number of minutes
    seconds
        Number of seconds
    milliseconds
        Number of milliseconds
    microseconds
        Number of microseconds
    nanoseconds
        Number of nanoseconds

    Returns
    -------
    IntervalScalar
        An interval expression
    """
    if value is not None:
        if isinstance(value, datetime.timedelta):
            unit = 's'
            value = int(value.total_seconds())
        elif not isinstance(value, int):
            raise ValueError('Interval value must be an integer')
    else:
        kwds = [
            ('Y', years),
            ('Q', quarters),
            ('M', months),
            ('W', weeks),
            ('D', days),
            ('h', hours),
            ('m', minutes),
            ('s', seconds),
            ('ms', milliseconds),
            ('us', microseconds),
            ('ns', nanoseconds),
        ]
        defined_units = [(k, v) for k, v in kwds if v is not None]

        if len(defined_units) != 1:
            raise ValueError('Exactly one argument is required')

        unit, value = defined_units[0]

    value_type = literal(value).type()
    type = dt.Interval(unit, value_type)

    return literal(value, type=type).op().to_expr()


def case() -> bl.SearchedCaseBuilder:
    """Begin constructing a case expression.

    Notes
    -----
    Use the `.when` method on the resulting object followed by .end to create a
    complete case.

    Examples
    --------
    >>> import ibis
    >>> cond1 = ibis.literal(1) == 1
    >>> cond2 = ibis.literal(2) == 1
    >>> result1 = 3
    >>> result2 = 4
    >>> expr = (ibis.case()
    ...         .when(cond1, result1)
    ...         .when(cond2, result2).end())

    Returns
    -------
    SearchedCaseBuilder
        A builder object to use for constructing a case expression.
    """
    return bl.SearchedCaseBuilder()


def now() -> ir.TimestampScalar:
    """Return an expression that will compute the current timestamp.

    Returns
    -------
    TimestampScalar
        A "now" expression
    """
    return ops.TimestampNow().to_expr()


def row_number() -> ir.IntegerColumn:
    """Return an analytic function expression for the current row number.

    Returns
    -------
    IntegerColumn
        A column expression enumerating rows
    """
    return ops.RowNumber().to_expr()


e = ops.E().to_expr()

pi = ops.Pi().to_expr()


def _add_methods(klass, method_table):
    for k, v in method_table.items():
        setattr(klass, k, v)


def where(
    boolean_expr: ir.BooleanValue,
    true_expr: ir.ValueExpr,
    false_null_expr: ir.ValueExpr,
) -> ir.ValueExpr:
    """Return `true_expr` if `boolean_expr` is `True` else `false_null_expr`.

    Parameters
    ----------
    boolean_expr
        A boolean expression
    true_expr
        Value returned if `boolean_expr` is `True`
    false_null_expr
        Value returned if `boolean_expr` is `False` or `NULL`

    Returns
    -------
    ir.ValueExpr
        An expression
    """
    op = ops.Where(boolean_expr, true_expr, false_null_expr)
    return op.to_expr()


coalesce = ir.AnyValue.coalesce
greatest = ir.AnyValue.greatest
least = ir.AnyValue.least


def category_label(
    arg: ir.CategoryValue,
    labels: Sequence[str],
    nulls: str | None = None,
) -> ir.StringValue:
    """Format a known number of categories as strings.

    Parameters
    ----------
    arg
        A category value
    labels
        Labels to use for formatting categories
    nulls
        How to label any null values among the categories

    Returns
    -------
    StringValue
        Labeled categories
    """
    op = ops.CategoryLabel(arg, labels, nulls)
    return op.to_expr()


# ----------------------------------------------------------------------
# GeoSpatial API


def geo_area(arg: ir.GeoSpatialValue) -> ir.FloatingValue:
    """Compute the area of a geospatial value.

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    FloatingValue
        The area of `arg`
    """
    op = ops.GeoArea(arg)
    return op.to_expr()


def geo_as_binary(arg: ir.GeoSpatialValue) -> ir.BinaryValue:
    """Get the geometry as well-known bytes (WKB) without the SRID data.

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    BinaryValue
        Binary value
    """
    op = ops.GeoAsBinary(arg)
    return op.to_expr()


def geo_as_ewkt(arg: ir.GeoSpatialValue) -> ir.StringValue:
    """Get the geometry as well-known text (WKT) with the SRID data.

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    StringValue
        String value
    """
    op = ops.GeoAsEWKT(arg)
    return op.to_expr()


def geo_as_text(arg: ir.GeoSpatialValue) -> ir.StringValue:
    """Get the geometry as well-known text (WKT) without the SRID data.

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    StringValue
        String value
    """
    op = ops.GeoAsText(arg)
    return op.to_expr()


def geo_as_ewkb(arg: ir.GeoSpatialValue) -> ir.BinaryValue:
    """Get the geometry as well-known bytes (WKB) with the SRID data.

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    BinaryValue
        WKB value
    """
    op = ops.GeoAsEWKB(arg)
    return op.to_expr()


def geo_contains(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the `left` geometry contains the `right` one.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether left contains right
    """
    op = ops.GeoContains(left, right)
    return op.to_expr()


def geo_contains_properly(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """
    Check if the first geometry contains the second one,
    with no common border points.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether left contains right, properly.
    """
    op = ops.GeoContainsProperly(left, right)
    return op.to_expr()


def geo_covers(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the first geometry covers the second one.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether `left` covers `right`
    """
    op = ops.GeoCovers(left, right)
    return op.to_expr()


def geo_covered_by(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the first geometry is covered by the second one.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether `left` is covered by `right`
    """
    op = ops.GeoCoveredBy(left, right)
    return op.to_expr()


def geo_crosses(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the geometries have at least one interior point in common.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether `left` and `right` have at least one common interior point.
    """
    op = ops.GeoCrosses(left, right)
    return op.to_expr()


def geo_d_fully_within(
    left: ir.GeoSpatialValue,
    right: ir.GeoSpatialValue,
    distance: ir.FloatingValue,
) -> ir.BooleanValue:
    """Check if the `left` is entirely within `distance` from `right`.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry
    distance
        Distance to check

    Returns
    -------
    BooleanValue
        Whether `left` is within a specified distance from `right`.
    """
    op = ops.GeoDFullyWithin(left, right, distance)
    return op.to_expr()


def geo_disjoint(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the geometries have no points in common.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether `left` and `right` are disjoin
    """
    op = ops.GeoDisjoint(left, right)
    return op.to_expr()


def geo_d_within(
    left: ir.GeoSpatialValue,
    right: ir.GeoSpatialValue,
    distance: ir.FloatingValue,
) -> ir.BooleanValue:
    """Check if `left` is partially within `distance` from `right`.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry
    distance
        Distance to check

    Returns
    -------
    BooleanValue
        Whether `left` is partially within `distance` from `right`.
    """
    op = ops.GeoDWithin(left, right, distance)
    return op.to_expr()


def geo_equals(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the geometries are equal.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether `left` equals `right`
    """
    op = ops.GeoEquals(left, right)
    return op.to_expr()


def geo_geometry_n(
    arg: ir.GeoSpatialValue, n: int | ir.IntegerValue
) -> ir.GeoSpatialValue:
    """Get the 1-based Nth geometry of a multi geometry.

    Parameters
    ----------
    arg
        Geometry expression
    n
        Nth geometry index

    Returns
    -------
    GeoSpatialValue
        Geometry value
    """
    op = ops.GeoGeometryN(arg, n)
    return op.to_expr()


def geo_geometry_type(arg: ir.GeoSpatialValue) -> ir.StringValue:
    """Get the type of a geometry.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    StringValue
        String representing the type of `arg`.
    """
    op = ops.GeoGeometryType(arg)
    return op.to_expr()


def geo_intersects(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the geometries share any points.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether `left` intersects `right`
    """
    op = ops.GeoIntersects(left, right)
    return op.to_expr()


def geo_is_valid(arg: ir.GeoSpatialValue) -> ir.BooleanValue:
    """Check if the geometry is valid.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    BooleanValue
        Whether `arg` is valid
    """
    op = ops.GeoIsValid(arg)
    return op.to_expr()


def geo_line_locate_point(
    left: ir.LineStringValue, right: ir.PointValue
) -> ir.FloatingValue:
    """Locate the distance a point falls along the length of a line.

    Returns a float between zero and one representing the location of the
    closest point on the linestring to the given point, as a fraction of the
    total 2d line length.

    Parameters
    ----------
    left
        Linestring geometry
    right
        Point geometry

    Returns
    -------
    FloatingValue
        Fraction of the total line length
    """
    op = ops.GeoLineLocatePoint(left, right)
    return op.to_expr()


def geo_line_merge(arg: ir.GeoSpatialValue) -> ir.GeoSpatialValue:
    """Merge a `MultiLineString` into a `LineString`.

    Returns a (set of) LineString(s) formed by sewing together the
    constituent line work of a MultiLineString. If a geometry other than
    a LineString or MultiLineString is given, this will return an empty
    geometry collection.

    Parameters
    ----------
    arg
        Multiline string

    Returns
    -------
    ir.GeoSpatialValue
        Merged linestrings
    """
    op = ops.GeoLineMerge(arg)
    return op.to_expr()


def geo_line_substring(
    arg: ir.LineStringValue, start: ir.FloatingValue, end: ir.FloatingValue
) -> ir.LineStringValue:
    """Clip a substring from a LineString.

    Returns a linestring that is a substring of the input one, starting
    and ending at the given fractions of the total 2d length. The second
    and third arguments are floating point values between zero and one.
    This only works with linestrings.

    Parameters
    ----------
    arg
        Linestring value
    start
        Start value
    end
        End value

    Returns
    -------
    LineStringValue
        Clipped linestring
    """
    op = ops.GeoLineSubstring(arg, start, end)
    return op.to_expr()


def geo_ordering_equals(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if two geometries are equal and have the same point ordering.

    Returns true if the two geometries are equal and the coordinates
    are in the same order.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether points and orderings are equal.
    """
    op = ops.GeoOrderingEquals(left, right)
    return op.to_expr()


def geo_overlaps(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the geometries share space, have the same dimension, and are
    not completely contained by each other.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Overlaps indicator
    """
    op = ops.GeoOverlaps(left, right)
    return op.to_expr()


def geo_point(
    left: NumericValue | int | float,
    right: NumericValue | int | float,
) -> ir.PointValue:
    """Return a point constructed from the coordinate values.

    Constant coordinates result in construction of a POINT literal.

    Parameters
    ----------
    left
        X coordinate
    right
        Y coordinate

    Returns
    -------
    PointValue
        Points
    """
    op = ops.GeoPoint(left, right)
    return op.to_expr()


def geo_touches(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the geometries have at least one point in common, but do not
    intersect.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether left and right are touching
    """
    op = ops.GeoTouches(left, right)
    return op.to_expr()


def geo_distance(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.FloatingValue:
    """Compute the distance between two geospatial expressions.

    Parameters
    ----------
    left
        Left geometry or geography
    right
        Right geometry or geography

    Returns
    -------
    FloatingValue
        Distance between `left` and `right`
    """
    op = ops.GeoDistance(left, right)
    return op.to_expr()


def geo_length(arg: ir.GeoSpatialValue) -> ir.FloatingValue:
    """Compute the length of a geospatial expression.

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    FloatingValue
        Length of `arg`
    """
    op = ops.GeoLength(arg)
    return op.to_expr()


def geo_perimeter(arg: ir.GeoSpatialValue) -> ir.FloatingValue:
    """Compute the perimeter of a geospatial expression.

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    FloatingValue
        Perimeter of `arg`
    """
    op = ops.GeoPerimeter(arg)
    return op.to_expr()


def geo_max_distance(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.FloatingValue:
    """Returns the 2-dimensional maximum distance between two geometries in
    projected units.

    If `left` and `right` are the same geometry the function will return the
    distance between the two vertices most far from each other in that
    geometry.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    FloatingValue
        Maximum distance
    """
    op = ops.GeoMaxDistance(left, right)
    return op.to_expr()


def geo_unary_union(arg: ir.GeoSpatialValue) -> ir.GeoSpatialScalar:
    """Aggregate a set of geometries into a union.

    This corresponds to the aggregate version of the PostGIS ST_Union.
    We give it a different name (following the corresponding method
    in GeoPandas) to avoid name conflicts with the non-aggregate version.

    Parameters
    ----------
    arg
        Geometry expression column

    Returns
    -------
    GeoSpatialScalar
        Union of geometries
    """
    expr = ops.GeoUnaryUnion(arg).to_expr()
    expr = expr.name('union')
    return expr


def geo_union(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.GeoSpatialValue:
    """Merge two geometries into a union geometry.

    Returns the pointwise union of the two geometries.
    This corresponds to the non-aggregate version the PostGIS ST_Union.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    GeoSpatialValue
        Union of geometries
    """
    op = ops.GeoUnion(left, right)
    return op.to_expr()


def geo_x(arg: ir.GeoSpatialValue) -> ir.FloatingValue:
    """Return the X coordinate of `arg`, or NULL if not available.

    Input must be a point.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    FloatingValue
        X coordinate of `arg`
    """
    op = ops.GeoX(arg)
    return op.to_expr()


def geo_y(arg: ir.GeoSpatialValue) -> ir.FloatingValue:
    """Return the Y coordinate of `arg`, or NULL if not available.

    Input must be a point.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    FloatingValue
        Y coordinate of `arg`
    """
    op = ops.GeoY(arg)
    return op.to_expr()


def geo_x_min(arg: ir.GeoSpatialValue) -> ir.FloatingValue:
    """Return the X minima of a geometry.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    FloatingValue
        X minima
    """
    op = ops.GeoXMin(arg)
    return op.to_expr()


def geo_x_max(arg: ir.GeoSpatialValue) -> ir.FloatingValue:
    """Return the X maxima of a geometry.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    FloatingValue
        X maxima
    """
    op = ops.GeoXMax(arg)
    return op.to_expr()


def geo_y_min(arg: ir.GeoSpatialValue) -> ir.FloatingValue:
    """Return the Y minima of a geometry.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    FloatingValue
        Y minima
    """
    op = ops.GeoYMin(arg)
    return op.to_expr()


def geo_y_max(arg: ir.GeoSpatialValue) -> ir.FloatingValue:
    """Return the Y maxima of a geometry.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    FloatingValue
        Y maxima
    YMax : double scalar
    """
    op = ops.GeoYMax(arg)
    return op.to_expr()


def geo_start_point(arg: ir.GeoSpatialValue) -> ir.PointValue:
    """Return the first point of a `LINESTRING` geometry as a `POINT`.

    Return NULL if the input parameter is not a `LINESTRING`

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    PointValue
        Start point
    """
    op = ops.GeoStartPoint(arg)
    return op.to_expr()


def geo_end_point(arg: ir.GeoSpatialValue) -> ir.PointValue:
    """Return the last point of a `LINESTRING` geometry as a `POINT`.

    Return NULL if the input parameter is not a LINESTRING

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    PointValue
        End point
    """
    op = ops.GeoEndPoint(arg)
    return op.to_expr()


def geo_point_n(arg: ir.GeoSpatialValue, n: ir.IntegerValue) -> ir.PointValue:
    """Return the Nth point in a single linestring in the geometry.
    Negative values are counted backwards from the end of the LineString,
    so that -1 is the last point. Returns NULL if there is no linestring in
    the geometry

    Parameters
    ----------
    arg
        Geometry expression
    n
        Nth point index

    Returns
    -------
    PointValue
        Nth point in `arg`
    """
    op = ops.GeoPointN(arg, n)
    return op.to_expr()


def geo_n_points(arg: ir.GeoSpatialValue) -> ir.IntegerValue:
    """Return the number of points in a geometry. Works for all geometries

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    IntegerValue
        Number of points
    """
    op = ops.GeoNPoints(arg)
    return op.to_expr()


def geo_n_rings(arg: ir.GeoSpatialValue) -> ir.IntegerValue:
    """Return the number of rings for polygons and multipolygons.

    Outer rings are counted as well.

    Parameters
    ----------
    arg
        Geometry or geography

    Returns
    -------
    IntegerValue
        Number of rings
    """
    op = ops.GeoNRings(arg)
    return op.to_expr()


def geo_srid(arg: ir.GeoSpatialValue) -> ir.IntegerValue:
    """Return the spatial reference identifier for the ST_Geometry.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    IntegerValue
        SRID
    """
    op = ops.GeoSRID(arg)
    return op.to_expr()


def geo_set_srid(
    arg: ir.GeoSpatialValue, srid: ir.IntegerValue
) -> ir.GeoSpatialValue:
    """Set the spatial reference identifier for the ST_Geometry

    Parameters
    ----------
    arg
        Geometry expression
    srid
        SRID integer value

    Returns
    -------
    GeoSpatialValue
        `arg` with SRID set to `srid`
    """
    op = ops.GeoSetSRID(arg, srid)
    return op.to_expr()


def geo_buffer(
    arg: ir.GeoSpatialValue, radius: float | ir.FloatingValue
) -> ir.GeoSpatialValue:
    """Returns a geometry that represents all points whose distance from this
    Geometry is less than or equal to distance. Calculations are in the
    Spatial Reference System of this Geometry.

    Parameters
    ----------
    arg
        Geometry expression
    radius
        Floating expression

    Returns
    -------
    ir.GeoSpatialValue
        Geometry expression
    """
    op = ops.GeoBuffer(arg, radius)
    return op.to_expr()


def geo_centroid(arg: ir.GeoSpatialValue) -> ir.PointValue:
    """Returns the centroid of the geometry.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    PointValue
        The centroid
    """
    op = ops.GeoCentroid(arg)
    return op.to_expr()


def geo_envelope(arg: ir.GeoSpatialValue) -> ir.PolygonValue:
    """Returns a geometry representing the bounding box of the arg.

    Parameters
    ----------
    arg
        Geometry expression

    Returns
    -------
    PolygonValue
        A polygon
    """
    op = ops.GeoEnvelope(arg)
    return op.to_expr()


def geo_within(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.BooleanValue:
    """Check if the first geometry is completely inside of the second.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    BooleanValue
        Whether `left` is in `right`.
    """
    op = ops.GeoWithin(left, right)
    return op.to_expr()


def geo_azimuth(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.FloatingValue:
    """Return the angle in radians from the horizontal of the vector defined by
    `left` and `right`.

    Angle is computed clockwise from down-to-up on the clock:
    12=0; 3=PI/2; 6=PI; 9=3PI/2.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    FloatingValue
        azimuth
    """
    op = ops.GeoAzimuth(left, right)
    return op.to_expr()


def geo_intersection(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.GeoSpatialValue:
    """Return the intersection of two geometries.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    GeoSpatialValue
        Intersection of `left` and `right`
    """
    op = ops.GeoIntersection(left, right)
    return op.to_expr()


def geo_difference(
    left: ir.GeoSpatialValue, right: ir.GeoSpatialValue
) -> ir.GeoSpatialValue:
    """Return the difference of two geometries.

    Parameters
    ----------
    left
        Left geometry
    right
        Right geometry

    Returns
    -------
    GeoSpatialValue
        Difference of `left` and `right`
    """
    op = ops.GeoDifference(left, right)
    return op.to_expr()


def geo_simplify(
    arg: ir.GeoSpatialValue,
    tolerance: ir.FloatingValue,
    preserve_collapsed: ir.BooleanValue,
) -> ir.GeoSpatialValue:
    """Simplify a given geometry.

    Parameters
    ----------
    arg
        Geometry expression
    tolerance
        Tolerance
    preserve_collapsed
        Whether to preserve collapsed geometries

    Returns
    -------
    GeoSpatialValue
        Simplified geometry
    """
    op = ops.GeoSimplify(arg, tolerance, preserve_collapsed)
    return op.to_expr()


def geo_transform(
    arg: ir.GeoSpatialValue, srid: ir.IntegerValue
) -> ir.GeoSpatialValue:
    """Transform a geometry into a new SRID.

    Parameters
    ----------
    arg
        Geometry expression
    srid
        Integer expression

    Returns
    -------
    GeoSpatialValue
        Transformed geometry
    """
    op = ops.GeoTransform(arg, srid)
    return op.to_expr()


_geospatial_value_methods = {
    'area': geo_area,
    'as_binary': geo_as_binary,
    'as_ewkb': geo_as_ewkb,
    'as_ewkt': geo_as_ewkt,
    'as_text': geo_as_text,
    'azimuth': geo_azimuth,
    'buffer': geo_buffer,
    'centroid': geo_centroid,
    'contains': geo_contains,
    'contains_properly': geo_contains_properly,
    'covers': geo_covers,
    'covered_by': geo_covered_by,
    'crosses': geo_crosses,
    'd_fully_within': geo_d_fully_within,
    'difference': geo_difference,
    'disjoint': geo_disjoint,
    'distance': geo_distance,
    'd_within': geo_d_within,
    'end_point': geo_end_point,
    'envelope': geo_envelope,
    'geo_equals': geo_equals,
    'geometry_n': geo_geometry_n,
    'geometry_type': geo_geometry_type,
    'intersection': geo_intersection,
    'intersects': geo_intersects,
    'is_valid': geo_is_valid,
    'line_locate_point': geo_line_locate_point,
    'line_merge': geo_line_merge,
    'line_substring': geo_line_substring,
    'length': geo_length,
    'max_distance': geo_max_distance,
    'n_points': geo_n_points,
    'n_rings': geo_n_rings,
    'ordering_equals': geo_ordering_equals,
    'overlaps': geo_overlaps,
    'perimeter': geo_perimeter,
    'point_n': geo_point_n,
    'set_srid': geo_set_srid,
    'simplify': geo_simplify,
    'srid': geo_srid,
    'start_point': geo_start_point,
    'touches': geo_touches,
    'transform': geo_transform,
    'union': geo_union,
    'within': geo_within,
    'x': geo_x,
    'x_max': geo_x_max,
    'x_min': geo_x_min,
    'y': geo_y,
    'y_max': geo_y_max,
    'y_min': geo_y_min,
}
_geospatial_column_methods = {'unary_union': geo_unary_union}

_add_methods(ir.GeoSpatialValue, _geospatial_value_methods)
_add_methods(ir.GeoSpatialColumn, _geospatial_column_methods)

ifelse = ir.BooleanValue.ifelse

# ----------------------------------------------------------------------
# Category API


_category_value_methods = {'label': category_label}

_add_methods(ir.CategoryValue, _category_value_methods)

prevent_rewrite = ir.TableExpr.prevent_rewrite
aggregate = ir.TableExpr.aggregate
cross_join = ir.TableExpr.cross_join
join = ir.TableExpr.join
asof_join = ir.TableExpr.asof_join
