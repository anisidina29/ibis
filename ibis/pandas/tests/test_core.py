import pytest

import pandas as pd

import ibis
import ibis.expr.datatypes as dt
import ibis.expr.types as ir

pytest.importorskip('multipledispatch')

from ibis.pandas.execution import (
    execute, execute_node, execute_first
)  # noqa: E402
from multipledispatch.conflict import ambiguities  # noqa: E402

pytestmark = pytest.mark.pandas


@pytest.mark.parametrize('func', [execute, execute_node, execute_first])
def test_no_execute_ambiguities(func):
    assert not ambiguities(func.funcs)


def test_execute_first_accepts_scope_keyword_argument(t, df):

    param = ibis.param(dt.int64)
    types = ir.Node, pd.DataFrame

    @execute_first.register(*types)
    def foo(op, data, scope=None, **kwargs):
        assert scope is not None
        return data.dup_strings.str.len() + scope[param.op()]

    expr = t.dup_strings.length() + param
    assert expr.execute(params={param: 2}) is not None
    del execute_first.funcs[types]
    execute_first.reorder()
    execute_first._cache.clear()
