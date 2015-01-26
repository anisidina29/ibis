# Copyright 2014 Cloudera Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Here we are working on the basic data structure for building Ibis expressions
# (an intermediate representation which can be compiled to a target backend,
# e.g. Impala SQL)
#
# The design and class structure here must be explicitly guided by the kind of
# user experience (i.e., highly interactive, suitable for introspection and
# console/notebook use) we want to deliver.
#
# All data structures should be treated as immutable (as much as Python objects
# are immutable; we'll behave as if they are).
#
# Expressions can be parameterized both by tables (known schema, but not bound
# to a particular table in any database), fields, and literal values. In order
# to execute an expression containing parameters, the user must perform a
# actual data. Mixing table and field parameters can lead to tricky binding
# scenarios -- essentially all unbound field parameters within a particular
# table expression must originate from the same concrete table. Internally we
# can identify the "logical tables" in the expression and present those to the
# user for the binding. Good introspection capability will be important
# here. Literal parameters are much simpler. A literal parameter is declared
# and used however many times the user wishes; binding in that case simply
# introduces the actual value to be used.
#
# In some cases, we'll want to be able to indicate that a parameter can either
# be a scalar or array expression. In this case the binding requirements may be
# somewhat more lax.


import operator

from ibis.common import RelationError
import ibis.common as com
import ibis.util as util


class Parameter(object):

    """
    Placeholder, to be implemented
    """

    pass


#----------------------------------------------------------------------


class Schema(object):

    """
    Holds table schema information
    """

    def __init__(self, names, types):
        if not isinstance(names, list):
            names = list(names)
        self.names = names
        self.types = [_validate_type(x) for x in types]

        self._name_locs = dict((v, i) for i, v in enumerate(self.names))

        if len(self._name_locs) < len(self.names):
            raise com.IntegrityError('Duplicate column names')

    def __repr__(self):
        return self._repr()

    def _repr(self):
        return "%s(%s, %s)" % (type(self).__name__, repr(self.names),
                               repr(self.types))

    def __contains__(self, name):
        return name in self._name_locs

    @classmethod
    def from_tuples(cls, values):
        names, types = zip(*values)
        return Schema(names, types)

    @classmethod
    def from_dict(cls, values):
        names = list(values.keys())
        types = values.values()
        return Schema(names, types)

    def equals(self, other):
        return ((self.names == other.names) and
                (self.types == other.types))

    def get_type(self, name):
        return self.types[self._name_locs[name]]

    def append(self, schema):
        names = self.names + schema.names
        types = self.types + schema.types
        return Schema(names, types)


def _validate_type(t):
    if t not in _array_types:
        raise ValueError('Invalid type: %s' % repr(t))
    return t


class HasSchema(object):

    """
    Base class representing a structured dataset with a well-defined
    schema.

    Base implementation is for tables that do not reference a particular
    concrete dataset or database table.
    """

    def __init__(self, schema, name=None):
        assert isinstance(schema, Schema)
        self._schema = schema
        self._name = name

    def __repr__(self):
        return self._repr()

    def _repr(self):
        return "%s(%s)" % (type(self).__name__, repr(self.schema))

    @property
    def schema(self):
        return self._schema

    @property
    def name(self):
        return self._name

    def equals(self, other):
        if type(self) != type(other):
            return False
        return self.schema.equals(other.schema)

    def root_tables(self):
        return [self]

    def get_type(self, name):
        return self.schema.get_type(name)


#----------------------------------------------------------------------


class Expr(object):

    """

    """

    def __init__(self, arg):
        # TODO: all inputs must inherit from a common table API
        self._arg = arg

    def __repr__(self):
        return self._repr()

    def _repr(self):
        from ibis.expr.format import ExprFormatter
        return ExprFormatter(self).get_result()

    def equals(self, other):
        if type(self) != type(other):
            return False
        return self._arg.equals(other._arg)

    def op(self):
        raise NotImplementedError

    def _can_compare(self, other):
        return False

    def _root_tables(self):
        return self.op().root_tables()

    def _get_unbound_tables(self):
        # The expression graph may contain one or more tables of a particular
        # known schema
        pass



class Node(object):

    """
    Node is the base class for all relational algebra and analytical
    functionality. It transforms the input expressions into an output
    expression.

    Each node implementation is responsible for validating the inputs,
    including any type promotion and / or casting issues, and producing a
    well-typed expression

    Note that Node is deliberately not made an expression subclass: think
    of Node as merely a typed expression builder.
    """

    def __init__(self, args):
        self.args = args

    def __repr__(self):
        return self._repr()

    def _repr(self):
        # Quick and dirty to get us started
        opname = type(self).__name__
        pprint_args = [repr(x) for x in self.args]
        return '%s(%s)' % (opname, ', '.join(pprint_args))

    def equals(self, other):
        if type(self) != type(other):
            return False

        if len(self.args) != len(other.args):
            return False

        def is_equal(left, right):
            if isinstance(left, list):
                if not isinstance(right, list):
                    return False
                for a, b in zip(left, right):
                    if not is_equal(a, b):
                        return False
                return True

            if hasattr(left, 'equals'):
                return left.equals(right)
            else:
                return left == right
            return True

        for left, right in zip(self.args, other.args):
            if not is_equal(left, right):
                return False
        return True

    def to_expr(self):
        """
        This function must resolve the output type of the expression and return
        the node wrapped in the appropriate ValueExpr type.
        """
        raise NotImplementedError


class ValueNode(Node):

    def to_expr(self):
        klass = self.output_type()
        return klass(self)

    def _ensure_value(self, expr):
        if not isinstance(expr, ValueExpr):
            raise TypeError('Must be a value, got: %s' % repr(expr))

    def _ensure_array(self, expr):
        if not isinstance(expr, ArrayExpr):
            raise TypeError('Must be an array, got: %s' % repr(expr))

    def _ensure_scalar(self, expr):
        if not isinstance(expr, ScalarExpr):
            raise TypeError('Must be a scalar, got: %s' % repr(expr))

    def output_type(self):
        raise NotImplementedError

    def resolve_name(self):
        raise NotImplementedError



class Literal(ValueNode):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return 'Literal(%s)' % repr(self.value)

    @property
    def args(self):
        return [self.value]

    def equals(self, other):
        if not isinstance(other, Literal):
            return False
        return (type(self.value) == type(other.value)
                and self.value == other.value)

    def output_type(self):
        if isinstance(self.value, bool):
            klass = BooleanScalar
        elif isinstance(self.value, (int, long)):
            int_type = _int_literal_class(self.value)
            klass = scalar_class(int_type)
        elif isinstance(self.value, float):
            klass = DoubleScalar
        elif isinstance(self.value, basestring):
            klass = StringScalar

        return klass

    def root_tables(self):
        return []



class ArrayNode(ValueNode):

    def __init__(self, expr):
        self._ensure_array(expr)
        ValueNode.__init__(self, [expr])


class TableNode(Node):
    pass


class BlockingTableNode(TableNode):
    # Try to represent the fact that whatever lies here is a semantically
    # distinct table. Like projections, aggregations, and so forth
    pass


class PhysicalTable(BlockingTableNode, HasSchema):

    pass


class UnboundTable(PhysicalTable):

    def __init__(self, schema, name=None):
        TableNode.__init__(self, [schema, name])
        HasSchema.__init__(self, schema, name=name)


class DatabaseTable(PhysicalTable):

    """

    """

    def __init__(self, name, schema, source):
        self.source = source

        TableNode.__init__(self, [name, schema, source])
        HasSchema.__init__(self, schema, name=name)


class SQLQueryResult(TableNode, HasSchema):

    """
    A table sourced from the result set of a select query
    """

    def __init__(self, query, schema, source):
        self.query = query
        TableNode.__init__(self, [query, schema, source])
        HasSchema.__init__(self, schema)


class TableColumn(ArrayNode):

    """
    Selects a column from a TableExpr
    """

    def __init__(self, name, table_expr):
        Node.__init__(self, [name, table_expr])
        self.name = name
        self.table = table_expr

    def parent(self):
        return self.table

    def resolve_name(self):
        return self.name

    def root_tables(self):
        return self.table._root_tables()

    def to_expr(self):
        ctype = self.table._get_type(self.name)
        klass = array_class(ctype)
        return klass(self, name=self.name)


class UnaryOp(ValueNode):

    def __init__(self, arg):
        self.arg = arg
        ValueNode.__init__(self, [arg])

    def root_tables(self):
        return self.arg._root_tables()

    def resolve_name(self):
        return self.arg.get_name()


class Cast(ValueNode):

    def __init__(self, value_expr, target_type):
        self._ensure_value(value_expr)

        self.value_expr = value_expr
        self.target_type = target_type.lower()

        # TODO: shorthand type aliases, e.g. int
        _validate_type(self.target_type)

        ValueNode.__init__(self, [value_expr, target_type])

    def resolve_name(self):
        return self.value_expr.get_name()

    def output_type(self):
        # TODO: error handling for invalid casts
        return _shape_like(self.value_expr, self.target_type)


class Negate(UnaryOp):

    def output_type(self):
        return type(self.arg)


class IsNull(UnaryOp):

    def output_type(self):
        return _shape_like(self.arg, 'boolean')


class NotNull(UnaryOp):

    def output_type(self):
        return _shape_like(self.arg, 'boolean')


def _shape_like(arg, out_type):
    if isinstance(arg, ScalarExpr):
        return scalar_class(out_type)
    else:
        return array_class(out_type)


class RealUnaryOp(UnaryOp):

    _allow_boolean = True

    def output_type(self):
        if not isinstance(self.arg, NumericValue):
            raise TypeError('Only implemented for numeric types')
        elif isinstance(self.arg, BooleanValue) and not self._allow_boolean:
            raise TypeError('Not implemented for boolean types')

        return _shape_like(self.arg, 'double')


class Exp(RealUnaryOp):
    pass


class Sqrt(RealUnaryOp):
    pass


class Log(RealUnaryOp):

    _allow_boolean = False


class Log2(RealUnaryOp):

    _allow_boolean = False


class Log10(RealUnaryOp):

    _allow_boolean = False

#----------------------------------------------------------------------


class BinaryOp(ValueNode):

    """
    A binary operation

    """
    # Casting rules for type promotions (for resolving the output type) may
    # depend in some cases on the target backend.
    #
    # TODO: how will overflows be handled? Can we provide anything useful in
    # Ibis to help the user avoid them?

    def __init__(self, left_expr, right_expr):
        self.left = left_expr
        self.right = right_expr
        ValueNode.__init__(self, [left_expr, right_expr])

    def root_tables(self):
        return _distinct_roots(self.left, self.right)

    def output_type(self):
        raise NotImplementedError


def _distinct_roots(*args):
    all_roots = []
    for arg in args:
        all_roots.extend(arg._root_tables())
    return util.unique_by_key(all_roots, id)


#----------------------------------------------------------------------


class Reduction(ArrayNode):

    def __init__(self, arg):
        self.arg = arg
        ArrayNode.__init__(self, arg)

    def root_tables(self):
        return self.arg._root_tables()

    def resolve_name(self):
        return self.arg.get_name()

    def to_expr(self):
        klass = self.output_type()
        return klass(self)


class Count(Reduction):
    # TODO: count(col) takes down Impala, must always do count(*) in generated
    # SQL

    def __init__(self, expr):
        # TODO: counts are actually table-level operations. Let's address
        # during the SQL generation exercise
        if not isinstance(expr, (ArrayExpr, TableExpr)):
            raise TypeError
        self.arg = expr
        ValueNode.__init__(self, [expr])

    def output_type(self):
        return Int64Scalar


class Sum(Reduction):

    def output_type(self):
        if isinstance(self.arg, (IntegerValue, BooleanValue)):
            return Int64Scalar
        elif isinstance(self.arg, FloatingValue):
            return DoubleScalar
        else:
            raise TypeError(self.arg)


class Mean(Reduction):

    def output_type(self):
        if isinstance(self.arg, NumericValue):
            return DoubleScalar
        else:
            raise NotImplementedError


class StdDeviation(Reduction):
    pass


class Max(Reduction):

    def output_type(self):
        return scalar_class(self.arg.type())


class Min(Reduction):

    def output_type(self):
        return scalar_class(self.arg.type())


#----------------------------------------------------------------------


class SingleCase(ValueNode):

    def __init__(self, case_expr, check_exprs, result_exprs,
                 default_expr):
        pass


class MultiCase(ValueNode):

    def __init__(self, case_exprs, result_exprs, default_expr):
        pass


class Join(TableNode):

    def __init__(self, left, right, join_predicates):
        if not isinstance(left, TableExpr):
            raise TypeError('Can only join table expressions, got %s for '
                            'left table' % type(left))

        if not isinstance(right, TableExpr):
            raise TypeError('Can only join table expressions, got %s for '
                            'right table' % type(left))

        self.left = left
        self.right = right
        self.predicates = [substitute_parents(x) for x in join_predicates]

        # Validate join predicates. Each predicate must be valid jointly when
        # considering the roots of each input table
        validator = ExprValidator(left._root_tables() + right._root_tables())
        validator.validate_all(self.predicates)

        Node.__init__(self, [left, right, self.predicates])

    def _get_schema(self):
        # For joins retaining both table schemas, merge them together here
        left = self.left
        right = self.right

        if not left._is_materialized():
            left = left.materialize()

        if not right._is_materialized():
            right = right.materialize()

        sleft = left.schema()
        sright = right.schema()

        overlap = set(sleft.names) & set(sright.names)
        if overlap:
            raise RelationError('Joined tables have overlapping names: %s'
                                % str(list(overlap)))

        return sleft.append(sright)

    def materialize(self):
        return MaterializedJoin(self)

    def root_tables(self):
        return _distinct_roots(self.left, self.right)


class InnerJoin(Join):
    pass


class LeftJoin(Join):
    pass


class RightJoin(Join):
    pass


class OuterJoin(Join):
    pass


class LeftSemiJoin(Join):

    """

    """

    def _get_schema(self):
        return self.left.schema()


class LeftAntiJoin(Join):

    """

    """

    def _get_schema(self):
        return self.left.schema()


class MaterializedJoin(TableNode, HasSchema):

    def __init__(self, join_expr):
        assert isinstance(join_expr, Join)
        self.join = join_expr

        TableNode.__init__(self, [join_expr])
        schema = self.join._get_schema()
        HasSchema.__init__(self, schema)

    def root_tables(self):
        return self.join._root_tables()


class CrossJoin(InnerJoin):

    """
    Some databases have a CROSS JOIN operator, that may be preferential to use
    over an INNER JOIN with no predicates.
    """

    def __init__(self, left, right, predicates=[]):
        InnerJoin.__init__(self, left, right, [])


class Filter(TableNode):

    def __init__(self, table_expr, predicates):
        self.table = table_expr
        self.predicates = predicates

        table_expr._assert_valid(predicates)
        TableNode.__init__(self, [table_expr, predicates])

    def root_tables(self):
        tables = self.table._root_tables()
        return tables


class FilterWithSchema(Filter, HasSchema):

    def __init__(self, table_expr, predicates):
        Filter.__init__(self, table_expr, predicates)
        HasSchema.__init__(self, table_expr.schema())



def _filter(expr, predicates):
    klass = FilterWithSchema if expr._is_materialized() else Filter
    return klass(expr, predicates)


class Limit(TableNode):

    def __init__(self, table, n, offset):
        self.table = table
        self.n = n
        self.offset = offset
        TableNode.__init__(self, [table, n, offset])

    def root_tables(self):
        return self.table._root_tables()


class SortBy(TableNode, HasSchema):

    # Q: Will SortBy always require a materialized schema?

    def __init__(self, table_expr, sort_keys):
        self.table = table_expr
        self.keys = [_to_sort_key(self.table, k) for k in sort_keys]

        TableNode.__init__(self, [self.table, self.keys])
        HasSchema.__init__(self, self.table.schema())


class SortKey(object):

    def __init__(self, expr, ascending=True):
        if not isinstance(expr, ArrayExpr):
            raise com.ExpressionError('Must be an array/column expression')

        self.expr = expr
        self.ascending = ascending

    def __repr__(self):
        # Temporary
        rows = ['Sort key:',
                '  ascending: {!s}'.format(self.ascending),
                util.indent(repr(self.expr), 2)]
        return '\n'.join(rows)

    def equals(self, other):
        return (isinstance(other, SortKey) and self.expr.equals(other.expr)
                and self.ascending == other.ascending)


def desc(expr):
    return SortKey(expr, ascending=False)


def _to_sort_key(table, key):
    if isinstance(key, SortKey):
        return key

    if isinstance(key, (tuple, list)):
        key, sort_order = key
    else:
        sort_order = True

    if not isinstance(key, Expr):
        key = table._ensure_expr(key)

    if isinstance(sort_order, basestring):
        if sort_order.lower() in ('desc', 'descending'):
            sort_order = False
        elif not isinstance(sort_order, bool):
            sort_order = bool(sort_order)

    return SortKey(key, ascending=sort_order)




class SelfReference(BlockingTableNode, HasSchema):

    def __init__(self, table_expr):
        self.table = table_expr
        TableNode.__init__(self, [table_expr])
        HasSchema.__init__(self, table_expr.schema(),
                           name=table_expr.op().name)

    def root_tables(self):
        # The dependencies of this operation are not walked, which makes the
        # table expression holding this relationally distinct from other
        # expressions, so things like self-joins are possible
        return [self]


class Projection(BlockingTableNode, HasSchema):

    def __init__(self, table_expr, proj_exprs):
        # Need to validate that the column expressions are compatible with the
        # input table; this means they must either be scalar expressions or
        # array expressions originating from the same root table expression
        validator = ExprValidator(table_expr._root_tables())

        # Resolve schema and initialize
        types = []
        names = []
        clean_exprs = []
        for expr in proj_exprs:
            if isinstance(expr, basestring):
                expr = table[expr]

            validator.assert_valid(expr)
            if isinstance(expr, ValueExpr):
                try:
                    name = expr.get_name()
                except NotImplementedError:
                    raise ValueError("Expression is unnamed: %s" % repr(expr))
                names.append(name)
                types.append(expr.type())
            elif isinstance(expr, TableExpr):
                schema = expr.schema()
                names.extend(schema.names)
                types.extend(schema.types)
            else:
                raise NotImplementedError

            clean_exprs.append(expr)

        # validate uniqueness
        schema = Schema(names, types)

        HasSchema.__init__(self, schema)
        Node.__init__(self, [table_expr] + [clean_exprs])

        self.table = table_expr
        self.selections = clean_exprs

    def substitute_table(self, table_expr):
        return Projection(table_expr, self.selections)

    def root_tables(self):
        tables = self.table._root_tables()
        return tables


class ExprValidator(object):

    def __init__(self, roots):
        self.roots = roots
        self.root_ids = set(id(x) for x in self.roots)

    def validate(self, expr):
        # TODO: in the case of a join, or multiple joins, the table_expr will
        # have multiple root input tables. We must validate set containment
        # among the root tables in the column expressions
        expr_roots = expr._root_tables()
        for root in expr_roots:
            if id(root) not in self.root_ids:
                return False
        return True

    def validate_all(self, exprs):
        for expr in exprs:
            self.assert_valid(expr)

    def assert_valid(self, expr):
        if not self.validate(expr):
            msg = ('The expression %s does not fully originate from '
                   'dependencies of the table expression.' % repr(expr))
            raise RelationError(msg)


class Aggregation(BlockingTableNode, HasSchema):

    """
    agg_exprs : per-group scalar aggregates
    by : group expressions
    having : post-aggregation predicate

    TODO: not putting this in the aggregate operation yet
    where : pre-aggregation predicate
    """

    def __init__(self, table, agg_exprs, by=None, having=None):
        # For tables, like joins, that are not materialized
        self.table = table

        self.agg_exprs = agg_exprs

        by = by or []
        self.by = self.table._resolve(by)
        self.by = [substitute_parents(x) for x in self.by]

        # TODO: aggregates in having may need to be included among the
        # aggregation expressions
        self.having = having or []
        self._validate()

        TableNode.__init__(self, [table, agg_exprs, self.by, self.having])

        schema = self._result_schema()
        HasSchema.__init__(self, schema)

    def substitute_table(self, table_expr):
        return Aggregation(table_expr, self.agg_exprs, by=self.by,
                           having=self.having)

    def _validate(self):
        # All aggregates are valid
        for expr in self.agg_exprs:
            if not isinstance(expr, ScalarExpr) or not expr.is_reduction():
                raise TypeError('Passed a non-aggregate expression: %s' %
                                repr(expr))

        # All non-scalar refs originate from the input table
        all_exprs = self.agg_exprs + self.by + self.having
        self.table._assert_valid(all_exprs)

    def _result_schema(self):
        names = []
        types = []
        for e in self.by + self.agg_exprs:
            names.append(e.get_name())
            types.append(e.type())

        return Schema(names, types)


class Add(BinaryOp):

    def output_type(self):
        helper = BinaryPromoter(self.left, self.right, operator.add)
        return helper.get_result()


class Multiply(BinaryOp):

    def output_type(self):
        helper = BinaryPromoter(self.left, self.right, operator.mul)
        return helper.get_result()


class Power(BinaryOp):

    def output_type(self):
        return PowerPromoter(self.left, self.right).get_result()


class Subtract(BinaryOp):

    def output_type(self):
        helper = BinaryPromoter(self.left, self.right, operator.sub)
        return helper.get_result()


class Divide(BinaryOp):

    def output_type(self):
        if not util.all_of(self.args, NumericValue):
            raise TypeError('One argument was non-numeric')

        if util.any_of(self.args, ArrayExpr):
            return DoubleArray
        else:
            return DoubleScalar


class LogicalBinaryOp(BinaryOp):

    def output_type(self):
        if not util.all_of(self.args, BooleanValue):
            raise TypeError('Only valid with boolean data')
        return (BooleanArray if util.any_of(self.args, ArrayExpr)
                else BooleanScalar)


class And(LogicalBinaryOp):
    pass


class Or(LogicalBinaryOp):
    pass


class Xor(LogicalBinaryOp):
    pass


class Comparison(BinaryOp):

    def output_type(self):
        self._assert_can_compare()
        return (BooleanArray if util.any_of(self.args, ArrayExpr)
                else BooleanScalar)

    def _assert_can_compare(self):
        if not self.left._can_compare(self.right):
            raise TypeError('Cannot compare argument types')



class Equals(Comparison):
    pass


class NotEquals(Comparison):
    pass


class GreaterEqual(Comparison):
    pass


class Greater(Comparison):
    pass


class LessEqual(Comparison):
    pass


class Less(Comparison):
    pass


class BinaryPromoter(object):
    # placeholder for type promotions for basic binary arithmetic

    def __init__(self, left, right, op):
        self.args = [left, right]
        self.left = left
        self.right = right
        self.op = op

        self._check_compatibility()

    def get_result(self):
        promoted_type = self._get_type()
        if util.any_of(self.args, ArrayExpr):
            return array_class(promoted_type)
        else:
            return scalar_class(promoted_type)

    def _get_type(self):
        if util.any_of(self.args, FloatingValue):
            if util.any_of(self.args, DoubleValue):
                return 'double'
            else:
                return 'float'
        elif util.all_of(self.args, IntegerValue):
            return self._get_int_type()
        else:
            raise NotImplementedError

    def _get_int_type(self):
        deps = [x.op() for x in self.args]

        if util.all_of(deps, Literal):
            return _smallest_int_containing(
                [self.op(deps[0].value, deps[1].value)])
        elif util.any_of(deps, Literal):
            if isinstance(deps[0], Literal):
                val = deps[0].value
                atype = self.args[1].type()
            else:
                val = deps[1].value
                atype = self.args[0].type()
            return _int_one_literal_promotion(atype, val, self.op)
        else:
            return _int_bounds_promotion(self.left.type(),
                                         self.right.type(), self.op)

    def _check_compatibility(self):
        if (util.any_of(self.args, StringValue) and
                not util.all_of(self.args, StringValue)):
            raise TypeError('String and non-string incompatible')


class PowerPromoter(BinaryPromoter):

    def __init__(self, left, right):
        super(PowerPromoter, self).__init__(left, right, operator.pow)

    def _get_type(self):
        rval = self.args[1].op()

        if util.any_of(self.args, FloatingValue):
            if util.any_of(self.args, DoubleValue):
                return 'double'
            else:
                return 'float'
        elif isinstance(rval, Literal) and rval.value < 0:
            return 'double'
        elif util.all_of(self.args, IntegerValue):
            return self._get_int_type()
        else:
            raise NotImplementedError


def _int_bounds_promotion(ltype, rtype, op):
    lmin, lmax = _int_bounds[ltype]
    rmin, rmax = _int_bounds[rtype]

    values = [op(lmin, rmin), op(lmin, rmax),
              op(lmax, rmin), op(lmax, rmax)]

    return _smallest_int_containing(values, allow_overflow=True)


def _int_one_literal_promotion(atype, lit_val, op):
    amin, amax = _int_bounds[atype]
    bound_type = _smallest_int_containing([op(amin, lit_val),
                                           op(amax, lit_val)],
                                          allow_overflow=True)
    # In some cases, the bounding type might be int8, even though neither of
    # the types are that small. We want to ensure the containing type is _at
    # least_ as large as the smallest type in the expression
    return _largest_int([bound_type, atype])


def _smallest_int_containing(values, allow_overflow=False):
    containing_types = [_int_literal_class(x, allow_overflow=allow_overflow)
                        for x in values]
    return _largest_int(containing_types)


class Contains(ArrayNode):

    def __init__(self, values_expr, match_expr):
        # If match_expr is a table, and it contains one column, we select that
        # column here
        pass


class ReplaceValues(ArrayNode):

    """
    Apply a multi-value replacement on a particular column. As an example from
    SQL, given DAYOFWEEK(timestamp_col), replace 1 through 5 to "WEEKDAY" and 6
    and 7 to "WEEKEND"
    """
    pass


def _binop_expr(name, klass):
    def f(self, other):
        if not isinstance(other, Expr):
            other = literal(other)

        op = klass(self, other)
        return op.to_expr()

    f.__name__ = name

    return f


def _rbinop_expr(name, klass):
    # For reflexive binary ops, like radd, etc.
    def f(self, other):
        if not isinstance(other, Expr):
            other = literal(other)
        op = klass(other, self)
        return op.to_expr()

    f.__name__ = name
    return f


def _unary_op(name, klass):
    def f(self):
        return klass(self).to_expr()
    f.__name__ = name
    return f


class ValueExpr(Expr):

    """
    Base class for a data generating expression having a fixed and known type,
    either a single value (scalar)
    """

    def __init__(self, arg, name=None):
        Expr.__init__(self, arg)
        self._name = name

    def type(self):
        return self._typename

    def op(self):
        return self._arg

    def get_name(self):
        if self._name is not None:
            # This value has been explicitly named
            return self._name

        # In some but not all cases we can get a name from the node that
        # produces the value
        return self.op().resolve_name()

    def name(self, name):
        return type(self)(self._arg, name=name)

    def cast(self, target_type):
        """
        Cast value(s) to indicated data type. Values that cannot be
        successfully casted

        Parameters
        ----------
        target_type : data type name

        Returns
        -------
        cast_expr : ValueExpr
        """
        # validate
        op = Cast(self, target_type)

        if op.target_type == self.type():
            # noop case if passed type is the same
            return self
        else:
            return op.to_expr()

    isnull = _unary_op('isnull', IsNull)
    notnull = _unary_op('notnull', NotNull)

    def ifnull(self, sub_expr):
        pass

    __add__ = _binop_expr('__add__', Add)
    __sub__ = _binop_expr('__sub__', Subtract)
    __mul__ = _binop_expr('__mul__', Multiply)
    __div__ = _binop_expr('__div__', Divide)
    __pow__ = _binop_expr('__pow__', Power)

    __radd__ = _rbinop_expr('__radd__', Add)
    __rsub__ = _rbinop_expr('__rsub__', Subtract)
    __rmul__ = _rbinop_expr('__rmul__', Multiply)
    __rdiv__ = _rbinop_expr('__rdiv__', Divide)
    __rpow__ = _binop_expr('__rpow__', Power)

    __eq__ = _binop_expr('__eq__', Equals)
    __ne__ = _binop_expr('__ne__', NotEquals)
    __ge__ = _binop_expr('__ge__', GreaterEqual)
    __gt__ = _binop_expr('__gt__', Greater)
    __le__ = _binop_expr('__le__', LessEqual)
    __lt__ = _binop_expr('__lt__', Less)


class ScalarExpr(ValueExpr):

    def is_reduction(self):
        # Aggregations yield typed scalar expressions, since the result of an
        # aggregation is a single value. When creating an table expression
        # containing a GROUP BY equivalent, we need to be able to easily check
        # that we are looking at the result of an aggregation.
        #
        # As an example, the expression we are looking at might be something
        # like: foo.sum().log10() + bar.sum().log10()
        #
        # We examine the operator DAG in the expression to determine if there
        # are aggregations present.
        #
        # A bound aggregation referencing a separate table is a "false
        # aggregation" in a GROUP BY-type expression and should be treated a
        # literal, and must be computed as a separate query and stored in a
        # temporary variable (or joined, for bound aggregations with keys)
        def has_reduction(op):
            if isinstance(op, Reduction):
                return True

            for arg in op.args:
                if isinstance(arg, ScalarExpr) and has_reduction(arg.op()):
                    return True

            return False

        return has_reduction(self.op())


class ArrayExpr(ValueExpr):

    def parent(self):
        return self._arg

    def to_projection(self):
        """
        Promote this column expression to a table projection
        """
        pass


class TableExpr(Expr):

    def op(self):
        return self._arg

    def _assert_valid(self, exprs):
        ExprValidator(self._root_tables()).validate_all(exprs)

    def __getitem__(self, what):
        if isinstance(what, basestring):
            return self.get_column(what)
        elif isinstance(what, (list, tuple)):
            # Projection case
            return self.projection(what)
        elif isinstance(what, BooleanArray):
            # Boolean predicate
            return self.filter([what])
        else:
            raise NotImplementedError

    def __getattr__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            if not self._is_materialized() or key not in self.schema():
                raise

            return self.get_column(key)

    def __dir__(self):
        attrs = dir(type(self))
        if self._is_materialized():
            attrs = list(sorted(set(attrs + self.schema().names)))
        return attrs

    def _resolve(self, exprs):
        # Stash this helper method here for now
        out_exprs = []
        for expr in exprs:
            if not isinstance(expr, ValueExpr):
                expr = self[expr]
            out_exprs.append(expr)
        return out_exprs

    def _get_type(self, name):
        return self._arg.get_type(name)

    def _is_materialized(self):
        # The schema is known and set
        return isinstance(self.op(), HasSchema)

    def materialize(self):
        if self._is_materialized():
            return self
        else:
            return TableExpr(self.op().materialize())

    def get_columns(self, iterable):
        return [self.get_column(x) for x in iterable]

    def get_column(self, name):
        ref = TableColumn(name, self)
        return ref.to_expr()

    def schema(self):
        if not self._is_materialized():
            raise Exception('Table operation is not yet materialized')
        return self.op().schema

    def view(self):
        """
        Create a new table expression that is semantically equivalent to the
        current one, but is considered a distinct relation for evaluation
        purposes (e.g. in SQL).

        For doing any self-referencing operations, like a self-join, you will
        use this operation to create a reference to the current table
        expression.

        Returns
        -------
        expr : TableExpr
        """
        return TableExpr(SelfReference(self))

    def add_column(self, expr, name=None):
        if not isinstance(expr, ArrayExpr):
            raise TypeError('Must pass array expression')

        if name is not None:
            expr = expr.name(name)

        # New column originates from this table expression if at all
        self._assert_valid([expr])
        return self.projection([self, expr])

    def add_columns(self, what):
        raise NotImplementedError

    def count(self):
        return Count(self).to_expr()

    def cross_join(self, other, prefixes=None):
        """

        """
        op = CrossJoin(self, other)
        return TableExpr(op)

    def inner_join(self, other, predicates, prefixes=None):
        """

        """
        op = InnerJoin(self, other, predicates)
        return TableExpr(op)

    def left_join(self, other, predicates, prefixes=None):
        """

        """
        op = LeftJoin(self, other, predicates)
        return TableExpr(op)

    def outer_join(self, other, predicates, prefixes=None):
        """

        """
        op = OuterJoin(self, other, predicates)
        return TableExpr(op)

    def semi_join(self, other, predicates, prefixes=None):
        """

        """
        op = LeftSemiJoin(self, other, predicates)
        return TableExpr(op)

    def anti_join(self, other, predicates, prefixes=None):
        """

        """
        raise NotImplementedError

    def projection(self, col_exprs):
        """

        """
        clean_exprs = []
        for expr in col_exprs:
            expr = self._ensure_expr(expr)

            expr = substitute_parents(expr)
            clean_exprs.append(expr)

        op = _maybe_fuse_projection(self, clean_exprs)
        return TableExpr(op)

    def _ensure_expr(self, expr):
        if isinstance(expr, basestring):
            expr = self[expr]

        return expr

    def filter(self, predicates):
        """

        Parameters
        ----------

        Returns
        -------
        filtered_expr : TableExpr
        """
        # Fusion opportunity
        parent = self.op()

        # This prevents the broken ref issue (described in more detail in
        # #59). If substitution is not possible, we will expect an error
        # during filter validation
        clean_preds = [substitute_parents(x) for x in predicates]

        if isinstance(parent, Filter):
            op = _filter(parent.table, parent.predicates + clean_preds)
        else:
            op = apply_filter(self, clean_preds)

        return TableExpr(op)

    def aggregate(self, agg_exprs, by=None, having=None):
        """
        Parameters
        ----------

        Returns
        -------
        agg_expr : TableExpr
        """
        op = Aggregation(self, agg_exprs, by=by, having=having)
        return TableExpr(op)

    def limit(self, n, offset=None):
        """

        Parameters
        ----------

        Returns
        -------
        limited : TableExpr
        """
        op = Limit(self, n, offset=offset)
        return TableExpr(op)

    def sort_by(self, what):
        if not isinstance(what, list):
            what = [what]

        op = SortBy(self, what)
        return TableExpr(op)


#------------------------------------------------------------------------------
# Declare all typed ValueExprs. This is what the user will actually interact
# with: an instance of each is well-typed and includes all valid methods
# defined for each type.


def _boolean_binary_op(name, klass):
    def f(self, other):
        if not isinstance(other, Expr):
            other = literal(other)

        if not isinstance(other, BooleanValue):
            raise TypeError(other)

        op = klass(self, other)
        return op.to_expr()

    f.__name__ = name

    return f


def _boolean_binary_rop(name, klass):
    def f(self, other):
        if not isinstance(other, Expr):
            other = literal(other)

        if not isinstance(other, BooleanValue):
            raise TypeError(other)

        op = klass(other, self)
        return op.to_expr()

    f.__name__ = name
    return f


def _agg_function(name, klass):
    def f(self):
        return klass(self).to_expr()
    f.__name__ = name
    return f


class NumericValue(ValueExpr):

    __neg__ = _unary_op('__neg__', Negate)

    exp = _unary_op('exp', Exp)
    sqrt = _unary_op('sqrt', Sqrt)

    log = _unary_op('log', Log)
    log2 = _unary_op('log2', Log2)
    log10 = _unary_op('log10', Log10)

    def _can_compare(self, other):
        return isinstance(other, NumericValue)


class IntegerValue(NumericValue):
    pass


class BooleanValue(NumericValue):

    _typename = 'boolean'

    # TODO: logical binary operators for BooleanValue
    __and__ = _boolean_binary_op('__and__', And)
    __or__ = _boolean_binary_op('__or__', Or)
    __xor__ = _boolean_binary_op('__xor__', Xor)

    __rand__ = _boolean_binary_rop('__rand__', And)
    __ror__ = _boolean_binary_rop('__ror__', Or)
    __rxor__ = _boolean_binary_rop('__rxor__', Xor)

    def ifelse(self, true_expr, false_expr):
        """
        Shorthand for implementing ternary expressions

        bool_expr.ifelse(0, 1)
        e.g., in SQL: CASE WHEN bool_expr THEN 0 else 1 END
        """
        # Result will be the result of promotion of true/false exprs. These
        # might be conflicting types; same type resolution as case expressions
        # must be used.
        raise NotImplementedError


class Int8Value(IntegerValue):

    _typename = 'int8'


class Int16Value(IntegerValue):

    _typename = 'int16'


class Int32Value(IntegerValue):

    _typename = 'int32'


class Int64Value(IntegerValue):

    _typename = 'int64'


class FloatingValue(NumericValue):
    pass


class FloatValue(FloatingValue):

    _typename = 'float'


class DoubleValue(FloatingValue):

    _typename = 'double'


class StringValue(ValueExpr):

    _typename = 'string'

    def _can_compare(self, other):
        return isinstance(other, StringValue)


class DecimalValue(NumericValue):

    _typename = 'decimal'


class TimestampValue(ValueExpr):

    _typename = 'timestamp'


class NumericArray(ArrayExpr, NumericValue):

    def count(self):
        # TODO: should actually get the parent table expression here
        return Count(self).to_expr()

    sum = _agg_function('sum', Sum)
    mean = _agg_function('mean', Mean)
    min = _agg_function('min', Min)
    max = _agg_function('max', Max)


class BooleanScalar(ScalarExpr, BooleanValue):
    pass


class BooleanArray(NumericArray, BooleanValue):

    def any(self):
        raise NotImplementedError

    def all(self):
        raise NotImplementedError


class Int8Scalar(ScalarExpr, Int8Value):
    pass


class Int8Array(NumericArray, Int8Value):
    pass


class Int16Scalar(ScalarExpr, Int16Value):
    pass


class Int16Array(NumericArray, Int16Value):
    pass


class Int32Scalar(ScalarExpr, Int32Value):
    pass


class Int32Array(NumericArray, Int32Value):
    pass


class Int64Scalar(ScalarExpr, Int64Value):
    pass


class Int64Array(NumericArray, Int64Value):
    pass


class FloatScalar(ScalarExpr, FloatValue):
    pass


class FloatArray(NumericArray, FloatValue):
    pass


class DoubleScalar(ScalarExpr, DoubleValue):
    pass


class DoubleArray(NumericArray, DoubleValue):
    pass


class StringScalar(ScalarExpr, StringValue):
    pass


class StringArray(ArrayExpr, StringValue):
    pass


_scalar_types = {
    'boolean': BooleanScalar,
    'int8': Int8Scalar,
    'int16': Int16Scalar,
    'int32': Int32Scalar,
    'int64': Int64Scalar,
    'float': FloatScalar,
    'double': DoubleScalar,
    'string': StringScalar
}

_nbytes = {
    'int8': 1,
    'int16': 2,
    'int32': 4,
    'int64': 8
}


_int_bounds = {
    'int8': (-128, 127),
    'int16': (-32768, 32767),
    'int32': (-2147483648, 2147483647),
    'int64': (-9223372036854775808, 9223372036854775807)
}

_array_types = {
    'boolean': BooleanArray,
    'int8': Int8Array,
    'int16': Int16Array,
    'int32': Int32Array,
    'int64': Int64Array,
    'float': FloatArray,
    'double': DoubleArray,
    'string': StringArray
}


def scalar_class(name):
    return _scalar_types[name]


def array_class(name):
    return _array_types[name]


def literal(value, name=None):
    return Literal(value).to_expr()


def _int_literal_class(value, allow_overflow=False):
    if -128 <= value <= 127:
        scalar_type = 'int8'
    elif -32768 <= value <= 32767:
        scalar_type = 'int16'
    elif -2147483648 <= value <= 2147483647:
        scalar_type = 'int32'
    else:
        if value < -9223372036854775808 or value > 9223372036854775807:
            if not allow_overflow:
                raise OverflowError(value)
        scalar_type = 'int64'
    return scalar_type


def _largest_int(int_types):
    nbytes = max(_nbytes[t] for t in int_types)
    return 'int%d' % (8 * nbytes)


def table(schema, name=None):
    if not isinstance(schema, Schema):
        if isinstance(schema, list):
            schema = Schema.from_tuples(schema)
        else:
            schema = Schema.from_dict(schema)

    node = UnboundTable(schema, name=name)
    return TableExpr(node)


#----------------------------------------------------------------------
# Some expression metaprogramming / graph transformations to support
# compilation later

class ExprSimplifier(object):
    """
    Rewrite the input expression by replacing any table expressions part of a
    "commutative table operation unit" (for lack of scientific term, a set of
    operations that can be written down in any order and still yield the same
    semantic result)
    """
    def __init__(self, expr, lift_memo=None):
        self.expr = expr
        self.lift_memo = lift_memo or {}
        self.unchanged = True

    def get_result(self):
        expr = self.expr
        node = expr.op()
        if isinstance(node, Literal):
            return expr

        # For table column references, in the event that we're on top of a
        # projection, we need to check whether the ref comes from the base
        # table schema or is a derived field.
        if isinstance(node, TableColumn):
            tnode = node.table.op()
            root = _base_table(tnode)

            if isinstance(root, Projection):
                can_lift = False
                for val in root.selections:
                    if (isinstance(val, TableExpr) and
                        node.name in val.schema()):

                        can_lift = True
                        lifted_root = self.lift(val)
                    elif (isinstance(val.op(), TableColumn)
                          and node.name == val.get_name()):
                        can_lift = True
                        lifted_root = self.lift(val.op().table)

                if can_lift:
                    lifted_node = TableColumn(node.name, lifted_root)
                    return type(expr)(lifted_node, name=expr._name)

        lifted_args = []
        for arg in node.args:
            if isinstance(arg, (tuple, list)):
                lifted_arg = [self._lift_arg(x) for x in arg]
            else:
                lifted_arg = self._lift_arg(arg)
            lifted_args.append(lifted_arg)

        # Do not modify unnecessarily
        if self.unchanged:
            return expr

        lifted_node = type(node)(*lifted_args)
        if isinstance(expr, ValueExpr):
            result = type(expr)(lifted_node, name=expr._name)
        else:
            result = type(expr)(lifted_node)

        return result

    def _lift_arg(self, arg):
        if isinstance(arg, Expr):
            lifted_arg = self.lift(arg)
            if lifted_arg is not arg:
                self.unchanged = False
        else:
            # a string or some other thing
            lifted_arg = arg

        return lifted_arg

    def _sub(self, expr):
        return ExprSimplifier(expr, lift_memo=self.lift_memo).get_result()

    def lift(self, expr):
        key = id(expr.op())
        if key in self.lift_memo:
            return self.lift_memo[key]

        op = expr.op()
        if isinstance(op, (ValueNode, ArrayNode)):
            return self._sub(expr)
        elif isinstance(op, Filter):
            result = self.lift(op.table)
        elif isinstance(op, Join):
            left_lifted = self.lift(op.left)
            right_lifted = self.lift(op.right)

            # Fix predicates
            lifted_preds = [self._sub(x) for x in op.predicates]
            lifted_join = type(op)(left_lifted, right_lifted, lifted_preds)
            result = TableExpr(lifted_join)
        elif isinstance(op, (TableNode, HasSchema)):
            return expr
        else:
            raise NotImplementedError

        # If we get here, time to record the modified expression in our memo to
        # avoid excessive graph-walking
        self.lift_memo[key] = result
        return result


def substitute_parents(expr, lift_memo=None):
    rewriter = ExprSimplifier(expr, lift_memo=lift_memo)
    return rewriter.get_result()


def _base_table(table_node):
    # Find the aggregate or projection root. Not proud of this
    if isinstance(table_node, BlockingTableNode):
        return table_node
    else:
        return _base_table(table_node.table.op())


def apply_filter(expr, predicates):
    # This will attempt predicate pushdown in the cases where we can do it
    # easily

    op = expr.op()
    if isinstance(op, (Projection, Aggregation)):
        # if any of the filter predicates have the parent expression among
        # their roots, then pushdown (at least of that predicate) is not
        # possible
        # TODO: is partial pushdown something we should consider
        # doing? Seems reasonable
        can_pushdown = True
        for pred in predicates:
            roots = pred._root_tables()
            if expr in roots:
                can_pushdown = False

        if can_pushdown:
            # this will further fuse, if possible
            filtered = op.table.filter(predicates)
            result = op.substitute_table(filtered)
        else:
            result = _filter(expr, predicates)
    else:
        result = _filter(expr, predicates)

    return result


def _maybe_fuse_projection(expr, clean_exprs):
    node = expr.op()

    if isinstance(node, Projection):
        roots = [node]
    else:
        roots = node.root_tables()

    if len(roots) == 1 and isinstance(roots[0], Projection):
        root = roots[0]

        roots = root.root_tables()
        validator = ExprValidator(roots)
        fused_exprs = []
        can_fuse = True
        for val in clean_exprs:
            # a * projection
            if (isinstance(val, TableExpr) and
                (val is expr or

                 # gross we share the same table root. Better way to detect?
                 len(roots) == 1 and val._root_tables()[0] is roots[0])
            ):
                continue
            elif not validator.validate(val):
                can_fuse = False
            else:
                fused_exprs.append(val)

        if can_fuse:
            return Projection(root.table, root.selections + fused_exprs)

    return Projection(expr, clean_exprs)


#----------------------------------------------------------------------
# Impala table interface
