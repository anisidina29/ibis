import pytest

from ibis.common import IbisTypeError
import ibis.expr.operations as ops
import ibis.expr.types as ir
from ibis.expr import rules


class MyExpr(ir.Expr):
    pass


def test_enum_validator():
    enum = pytest.importorskip('enum')

    class Foo(enum.Enum):
        a = 1
        b = 2

    class Bar(enum.Enum):
        a = 1
        b = 2

    class MyOp(ops.Node):

        input_type = [rules.enum(Foo, name='value')]

        def __init__(self, value):
            super(MyOp, self).__init__([value])

        def output_type(self):
            return MyExpr

    assert MyOp(2) is not None
    assert MyOp(Foo.b) is not None

    with pytest.raises(IbisTypeError):
        MyOp(3)

    with pytest.raises(IbisTypeError):
        MyOp(Bar.a)

    op = MyOp(Foo.a)
    assert op._validate_args(op.args) == [Foo.a]


def test_duplicate_enum():
    enum = pytest.importorskip('enum')

    class Dup(enum.Enum):
        a = 1
        b = 1
        c = 2

    class MyOp(ops.Node):

        input_type = [rules.enum(Dup, name='value')]

        def __init__(self, value):
            super(MyOp, self).__init__([value])

        def output_type(self):
            return MyExpr

    with pytest.raises(IbisTypeError):
        MyOp(1)

    assert MyOp(2) is not None
