# -*- coding: utf-8 -*-
from setuptools import setup

packages = [
    "ibis",
    "ibis.backends",
    "ibis.backends.base",
    "ibis.backends.base.file",
    "ibis.backends.base.sql",
    "ibis.backends.base.sql.alchemy",
    "ibis.backends.base.sql.compiler",
    "ibis.backends.base.sql.registry",
    "ibis.backends.clickhouse",
    "ibis.backends.clickhouse.tests",
    "ibis.backends.csv",
    "ibis.backends.csv.tests",
    "ibis.backends.dask",
    "ibis.backends.dask.execution",
    "ibis.backends.dask.tests",
    "ibis.backends.dask.tests.execution",
    "ibis.backends.hdf5",
    "ibis.backends.hdf5.tests",
    "ibis.backends.impala",
    "ibis.backends.impala.tests",
    "ibis.backends.mysql",
    "ibis.backends.mysql.tests",
    "ibis.backends.pandas",
    "ibis.backends.pandas.execution",
    "ibis.backends.pandas.tests",
    "ibis.backends.pandas.tests.execution",
    "ibis.backends.parquet",
    "ibis.backends.parquet.tests",
    "ibis.backends.postgres",
    "ibis.backends.postgres.tests",
    "ibis.backends.pyspark",
    "ibis.backends.pyspark.tests",
    "ibis.backends.sqlite",
    "ibis.backends.sqlite.tests",
    "ibis.backends.tests",
    "ibis.common",
    "ibis.expr",
    "ibis.tests",
    "ibis.tests.expr",
    "ibis.tests.sql",
    "ibis.udf",
]

package_data = {"": ["*"]}

install_requires = [
    "cached_property>=1,<2",
    "cytoolz>=0.11,<0.12",
    "multipledispatch>=0.6,<0.7",
    "numpy>=1,<2",
    "pandas>=1.2.5,<2.0.0",
    "parsy>=1.3.0,<2.0.0",
    "pytz>=2021.1,<2022.0",
    "regex>=2021.7.6,<2022.0.0",
    "toolz>=0.11,<0.12",
]

extras_require = {
    ':python_version < "3.8"': ["importlib-metadata>=4,<5"],
    "all": [
        "clickhouse-driver>=0.1,<0.3.0",
        "clickhouse-sqlalchemy>=0.1.4,<0.2.0",
        "dask[array,dataframe]>=2021.2.0,<2022.0.0",
        "geoalchemy2>=0.6,<0.7",
        "geopandas>=0.6,<0.7",
        "graphviz>=0.16,<0.17",
        "hdfs[kerberos]>=2,<3",
        "impyla[kerberos]>=0.17,<0.19",
        "psycopg2>=2.7,<3.0",
        "pyarrow>=1,<6",
        "pymysql>=1,<2",
        "pyspark>=2.4.3,<4",
        "requests>=2,<3",
        "shapely>=1.6,<2.0",
        "sqlalchemy>=1.3,<1.4",
        "tables>=3,<4",
    ],
    "clickhouse": [
        "clickhouse-driver>=0.1,<0.3.0",
        "clickhouse-sqlalchemy>=0.1.4,<0.2.0",
        "sqlalchemy>=1.3,<1.4",
    ],
    "dask": ["dask[array,dataframe]>=2021.2.0,<2022.0.0", "pyarrow>=1,<6"],
    "geospatial": [
        "geoalchemy2>=0.6,<0.7",
        "geopandas>=0.6,<0.7",
        "shapely>=1.6,<2.0",
    ],
    "hdf5": ["tables>=3,<4"],
    "impala": [
        "hdfs[kerberos]>=2,<3",
        "impyla[kerberos]>=0.17,<0.19",
        "requests>=2,<3",
        "sqlalchemy>=1.3,<1.4",
    ],
    "mysql": ["pymysql>=1,<2", "sqlalchemy>=1.3,<1.4"],
    "parquet": ["pyarrow>=1,<6"],
    "postgres": ["psycopg2>=2.7,<3.0", "sqlalchemy>=1.3,<1.4"],
    "pyspark": ["pyarrow>=1,<6", "pyspark>=2.4.3,<4"],
    "sqlite": ["sqlalchemy>=1.3,<1.4"],
    "visualization": ["graphviz>=0.16,<0.17"],
}

entry_points = {
    "ibis.backends": [
        "clickhouse = ibis.backends.clickhouse",
        "csv = ibis.backends.csv",
        "dask = ibis.backends.dask",
        "hdf5 = ibis.backends.hdf5",
        "impala = ibis.backends.impala",
        "mysql = ibis.backends.mysql",
        "pandas = ibis.backends.pandas",
        "parquet = ibis.backends.parquet",
        "postgres = ibis.backends.postgres",
        "pyspark = ibis.backends.pyspark",
        "spark = ibis.backends.pyspark",
        "sqlite = ibis.backends.sqlite",
    ]
}

setup_kwargs = {
    "name": "ibis-framework",
    "version": "2.0.0",
    "description": "Productivity-centric Python Big Data Framework",
    "long_description": "# Ibis: Python data analysis framework for Hadoop and SQL engines\n\n|Service|Status|\n| -------------: | :---- |\n| Documentation  | [![Documentation Status](https://img.shields.io/badge/docs-docs.ibis--project.org-blue.svg)](http://ibis-project.org) |\n| Conda packages | [![Anaconda-Server Badge](https://anaconda.org/conda-forge/ibis-framework/badges/version.svg)](https://anaconda.org/conda-forge/ibis-framework) |\n| PyPI           | [![PyPI](https://img.shields.io/pypi/v/ibis-framework.svg)](https://pypi.org/project/ibis-framework) |\n| GitHub Actions | [![Build status](https://github.com/ibis-project/ibis/actions/workflows/main.yml/badge.svg)](https://github.com/ibis-project/ibis/actions/workflows/main.yml?query=branch%3Amaster) |\n| Coverage       | [![Codecov branch](https://img.shields.io/codecov/c/github/ibis-project/ibis/master.svg)](https://codecov.io/gh/ibis-project/ibis) |\n\n\nIbis is a toolbox to bridge the gap between local Python environments, remote\nstorage, execution systems like Hadoop components (HDFS, Impala, Hive, Spark)\nand SQL databases. Its goal is to simplify analytical workflows and make you\nmore productive.\n\nInstall Ibis from PyPI with:\n\n```sh\npip install ibis-framework\n```\n\nor from conda-forge with\n\n```sh\nconda install ibis-framework -c conda-forge\n```\n\nIbis currently provides tools for interacting with the following systems:\n\n- [Apache Impala](https://impala.apache.org/)\n- [Apache Kudu](https://kudu.apache.org/)\n- [Hadoop Distributed File System (HDFS)](https://hadoop.apache.org/)\n- [PostgreSQL](https://www.postgresql.org/)\n- [MySQL](https://www.mysql.com/)\n- [SQLite](https://www.sqlite.org/)\n- [Pandas](https://pandas.pydata.org/) [DataFrames](http://pandas.pydata.org/pandas-docs/stable/dsintro.html#dataframe)\n- [Clickhouse](https://clickhouse.yandex)\n- [BigQuery](https://cloud.google.com/bigquery)\n- [OmniSciDB](https://www.omnisci.com)\n- [PySpark](https://spark.apache.org)\n- [Dask](https://dask.org/) (Experimental)\n\nLearn more about using the library at http://ibis-project.org.\n",
    "author": "Ibis Contributors",
    "author_email": None,
    "maintainer": "Ibis Contributors",
    "maintainer_email": None,
    "url": "https://ibis-project.org",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "extras_require": extras_require,
    "entry_points": entry_points,
    "python_requires": ">=3.7.1,<4",
}


setup(**setup_kwargs)
