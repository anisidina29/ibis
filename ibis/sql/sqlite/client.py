# Copyright 2015 Cloudera Inc.
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

import os
import re
import inspect
import functools

import sqlalchemy as sa

from ibis.client import Database
from .compiler import SQLiteDialect
import ibis.sql.alchemy as alch
import ibis.common as com


class SQLiteTable(alch.AlchemyTable):
    pass


class SQLiteDatabase(Database):
    pass


def _ibis_sqlite_regex_search(string, regex):
    """Return whether `regex` exists in `string`.

    Parameters
    ----------
    string : str
    regex : str

    Returns
    -------
    found : bool
    """
    if string is None or regex is None:
        return None
    return re.search(regex, string) is not None


def _ibis_sqlite_regex_replace(string, pattern, replacement):
    """Replace occurences of `pattern` in `string` with `replacement`.

    Parameters
    ----------
    string : str
    pattern : str
    replacement : str

    Returns
    -------
    result : str
    """
    if string is None or pattern is None or replacement is None:
        return None
    return re.sub(pattern, replacement, string)


def _ibis_sqlite_regex_extract(string, pattern, index):
    """Extract match of regular expression `pattern` from `string` at `index`.

    Parameters
    ----------
    string : str
    pattern : str
    index : int

    Returns
    -------
    result : str or None
    """
    if string is None or pattern is None or index is None:
        return None

    result = re.search(pattern, string)
    if result is not None and 0 <= index <= result.lastindex:
        return result.group(index)
    else:
        return None


def _register_function(func, con):
    """Register a Python callable with a SQLite connection `con`.

    Parameters
    ----------
    func : callable
    con : sqlalchemy.Connection
    """
    argspec = inspect.getargspec(func)

    if argspec.varargs is not None:
        raise TypeError(
            'Variable length arguments not supported in Ibis SQLite function '
            'registration'
        )

    if argspec.keywords is not None:
        raise NotImplementedError(
            'Keyword arguments not implemented for Ibis SQLite function '
            'registration'
        )

    if argspec.defaults is not None:
        raise NotImplementedError(
            'Keyword arguments not implemented for Ibis SQLite function '
            'registration'
        )

    con.connection.connection.create_function(
        func.__name__, len(argspec.args), func
    )


class SQLiteClient(alch.AlchemyClient):

    """
    The Ibis SQLite client class
    """

    dialect = SQLiteDialect
    database_class = SQLiteDatabase

    def __init__(self, path=None, create=False):
        super(SQLiteClient, self).__init__(sa.create_engine('sqlite://'))
        self.name = path
        self.database_name = 'default'

        if path is not None:
            self.attach(self.database_name, path, create=create)

        for func in (
            _ibis_sqlite_regex_search,
            _ibis_sqlite_regex_replace,
            _ibis_sqlite_regex_extract,
        ):
            self.con.run_callable(functools.partial(_register_function, func))

    @property
    def current_database(self):
        return self.database_name

    def list_databases(self):
        raise NotImplementedError(
            'Listing databases in SQLite is not implemented'
        )

    def set_database(self, name):
        raise NotImplementedError('set_database is not implemented for SQLite')

    def attach(self, name, path, create=False):
        """Connect another SQLite database file

        Parameters
        ----------
        name : string
            Database name within SQLite
        path : string
            Path to sqlite3 file
        create : boolean, optional
            If file does not exist, create file if True otherwise raise an
            Exception
        """
        if not os.path.exists(path) and not create:
            raise com.IbisError('File {!r} does not exist'.format(path))

        self.raw_sql(
            "ATTACH DATABASE {path!r} AS {name}".format(
                path=path,
                name=self.con.dialect.identifier_preparer.quote(name),
            )
        )

    @property
    def client(self):
        return self

    def table(self, name, database=None):
        """
        Create a table expression that references a particular table in the
        SQLite database

        Parameters
        ----------
        name : string
        database : string, optional
          name of the attached database that the table is located in.

        Returns
        -------
        table : TableExpr
        """
        alch_table = self._get_sqla_table(name, schema=database)
        node = SQLiteTable(alch_table, self)
        return self._table_expr_klass(node)

    def list_tables(self, like=None, database=None, schema=None):
        if database is None:
            database = self.database_name
        return super(SQLiteClient, self).list_tables(like, schema=database)
