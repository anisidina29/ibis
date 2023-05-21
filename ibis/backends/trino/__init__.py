"""Trino backend."""

from __future__ import annotations

import warnings
from functools import cached_property
from typing import Iterator

import sqlalchemy as sa
import toolz
from trino.sqlalchemy.datatype import ROW as _ROW

import ibis.expr.datatypes as dt
from ibis import util
from ibis.backends.base.sql.alchemy import BaseAlchemyBackend
from ibis.backends.base.sql.alchemy.datatypes import ArrayType
from ibis.backends.trino.compiler import TrinoSQLCompiler
from ibis.backends.trino.datatypes import ROW, parse


class Backend(BaseAlchemyBackend):
    name = "trino"
    compiler = TrinoSQLCompiler
    supports_create_or_replace = False
    supports_temporary_tables = False

    def current_database(self) -> str:
        raise NotImplementedError(type(self))

    @cached_property
    def version(self) -> str:
        with self.begin() as con:
            return con.execute(sa.select(sa.func.version())).scalar()

    def do_connect(
        self,
        user: str = "user",
        password: str | None = None,
        host: str = "localhost",
        port: int = 8080,
        database: str | None = None,
        schema: str | None = None,
        **connect_args,
    ) -> None:
        """Create an Ibis client connected to a Trino database."""
        database = "/".join(filter(None, (database, schema)))
        url = sa.engine.URL.create(
            drivername="trino",
            username=user,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        connect_args.setdefault("timezone", "UTC")
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"The dbapi\(\) classmethod on dialect classes has been renamed",
                category=sa.exc.SADeprecationWarning,
            )
            super().do_connect(
                sa.create_engine(
                    url, connect_args=connect_args, poolclass=sa.pool.StaticPool
                )
            )

    @staticmethod
    def _new_sa_metadata():
        meta = sa.MetaData()

        @sa.event.listens_for(meta, "column_reflect")
        def column_reflect(inspector, table, column_info):
            if isinstance(typ := column_info["type"], _ROW):
                column_info["type"] = ROW(typ.attr_types)
            elif isinstance(typ, sa.ARRAY):
                column_info["type"] = toolz.nth(
                    typ.dimensions or 1, toolz.iterate(ArrayType, typ.item_type)
                )

        return meta

    def _metadata(self, query: str) -> Iterator[tuple[str, dt.DataType]]:
        tmpname = f"_ibis_trino_output_{util.guid()[:6]}"
        with self.begin() as con:
            con.exec_driver_sql(f"PREPARE {tmpname} FROM {query}")
            for name, type in toolz.pluck(
                ["Column Name", "Type"],
                con.exec_driver_sql(f"DESCRIBE OUTPUT {tmpname}").mappings(),
            ):
                ibis_type = parse(type)
                yield name, ibis_type(nullable=True)
            con.exec_driver_sql(f"DEALLOCATE PREPARE {tmpname}")
