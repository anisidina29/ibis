"""Pandas backend execution of struct fields and literals."""

import collections
import functools

import pandas as pd
from pandas.core.groupby import SeriesGroupBy

import ibis.expr.operations as ops
from ibis.backends.pandas.dispatch import execute_node


@execute_node.register(ops.StructField, collections.abc.Mapping)
def execute_node_struct_field_dict(op, data, **kwargs):
    return data[op.field]


@execute_node.register(ops.StructField, type(None))
def execute_node_struct_field_none(op, data, **kwargs):
    return None


@execute_node.register(ops.StructField, pd.Series)
def execute_node_struct_field_series(op, data, **kwargs):
    field = op.field
    return data.map(functools.partial(_safe_getter, field=field)).rename(field)


def _safe_getter(value, field: str):
    try:
        return value[field]
    except TypeError:
        return value


@execute_node.register(ops.StructField, SeriesGroupBy)
def execute_node_struct_field_series_group_by(op, data, **kwargs):
    field = op.field

    return (
        data.obj.map(functools.partial(_safe_getter, field=field))
        .rename(field)
        .groupby(data.grouper.groupings)
    )
