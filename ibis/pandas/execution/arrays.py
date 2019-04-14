import operator

import pandas as pd
from pandas.core.groupby import SeriesGroupBy

import ibis.expr.operations as ops
from ibis.pandas.dispatch import execute_node


@execute_node.register(ops.ArrayLength, pd.Series)
def execute_array_length(op, data, **kwargs):
    return data.apply(len)


@execute_node.register(ops.ArrayLength, list)
def execute_array_length_scalar(op, data, **kwargs):
    return len(data)


@execute_node.register(ops.ArraySlice, pd.Series, int, (int, type(None)))
def execute_array_slice(op, data, start, stop, **kwargs):
    return data.apply(operator.itemgetter(slice(start, stop)))


@execute_node.register(ops.ArraySlice, list, int, (int, type(None)))
def execute_array_slice_scalar(op, data, start, stop, **kwargs):
    return data[start:stop]


@execute_node.register(ops.ArrayIndex, pd.Series, int)
def execute_array_index(op, data, index, **kwargs):
    return data.apply(
        lambda array, index=index: (
            array[index] if -len(array) <= index < len(array) else None
        )
    )


@execute_node.register(ops.ArrayIndex, list, int)
def execute_array_index_scalar(op, data, index, **kwargs):
    try:
        return data[index]
    except IndexError:
        return None


@execute_node.register(ops.ArrayConcat, pd.Series, (pd.Series, list))
@execute_node.register(ops.ArrayConcat, list, pd.Series)
@execute_node.register(ops.ArrayConcat, list, list)
def execute_array_concat(op, left, right, **kwargs):
    return left + right


@execute_node.register(ops.ArrayRepeat, pd.Series, pd.Series)
@execute_node.register(ops.ArrayRepeat, int, (pd.Series, list))
@execute_node.register(ops.ArrayRepeat, (pd.Series, list), int)
def execute_array_repeat(op, left, right, **kwargs):
    return left * right


@execute_node.register(ops.ArrayCollect, (pd.Series, SeriesGroupBy))
def execute_array_collect(op, data, aggcontext=None, **kwargs):
    return aggcontext.agg(data, list)
