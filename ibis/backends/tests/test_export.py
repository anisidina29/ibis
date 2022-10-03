import sys

import pyarrow as pa
import pytest
from pytest import param

# Adds `to_pyarrow` to created schema objects
from ibis.backends.pyarrow.datatypes import sch  # noqa: F401


class PackageDiscarder:
    def __init__(self):
        self.pkgnames = []

    def find_spec(self, fullname, path, target=None):
        if fullname in self.pkgnames:
            raise ImportError()


@pytest.fixture
def no_pyarrow(backend):
    _pyarrow = sys.modules.pop('pyarrow', None)
    d = PackageDiscarder()
    d.pkgnames.append('pyarrow')
    sys.meta_path.insert(0, d)
    yield
    sys.meta_path.remove(d)
    if _pyarrow is not None:
        sys.modules["pyarrow"] = _pyarrow


limit = [
    param(
        42,
        id='limit',
        marks=[
            pytest.mark.notimpl(
                [
                    # limit not implemented for pandas backend execution
                    "clickhouse",
                    "dask",
                    "datafusion",
                    "impala",
                    "pandas",
                    "pyspark",
                    "snowflake",
                ]
            ),
        ],
    ),
]

no_limit = [
    param(
        None,
        id='nolimit',
        marks=[
            pytest.mark.notimpl(
                [
                    "clickhouse",
                    "dask",
                    "impala",
                    "pyspark",
                    "snowflake",
                ]
            ),
        ],
    ),
]

limit_no_limit = limit + no_limit


@pytest.mark.notyet(
    ["pandas"], reason="DataFrames have no option for outputting in batches"
)
@pytest.mark.parametrize("limit", limit_no_limit)
def test_table_to_pyarrow_batches(limit, backend, awards_players):
    batch_reader = awards_players.to_pyarrow_batches(limit=limit)
    assert isinstance(batch_reader, pa.RecordBatchReader)
    batch = batch_reader.read_next_batch()
    assert isinstance(batch, pa.RecordBatch)
    if limit is not None:
        assert len(batch) == limit


@pytest.mark.notyet(
    ["pandas"], reason="DataFrames have no option for outputting in batches"
)
@pytest.mark.parametrize("limit", limit_no_limit)
def test_column_to_pyarrow_batches(limit, backend, awards_players):
    batch_reader = awards_players.awardID.to_pyarrow_batches(limit=limit)
    assert isinstance(batch_reader, pa.RecordBatchReader)
    batch = batch_reader.read_next_batch()
    assert isinstance(batch, pa.RecordBatch)
    if limit is not None:
        assert len(batch) == limit


@pytest.mark.parametrize("limit", limit_no_limit)
def test_table_to_pyarrow_table(limit, backend, awards_players):
    table = awards_players.to_pyarrow(limit=limit)
    assert isinstance(table, pa.Table)
    if limit is not None:
        assert len(table) == limit


@pytest.mark.parametrize("limit", limit_no_limit)
def test_column_to_pyarrow_array(limit, backend, awards_players):
    array = awards_players.awardID.to_pyarrow(limit=limit)
    assert isinstance(array, pa.Array)
    if limit is not None:
        assert len(array) == limit


@pytest.mark.parametrize("limit", no_limit)
def test_empty_column_to_pyarrow(limit, backend, awards_players):
    array = awards_players.filter(
        awards_players.awardID == "DEADBEEF"
    ).awardID.to_pyarrow(limit=limit)
    assert isinstance(array, pa.Array)
    assert len(array) == 0


@pytest.mark.notyet(
    ["datafusion"], reason="DataFusion backend doesn't support sum"
)
@pytest.mark.parametrize("limit", no_limit)
def test_empty_scalar_to_pyarrow(limit, backend, awards_players):
    array = (
        awards_players.filter(awards_players.awardID == "DEADBEEF")
        .yearID.sum()
        .to_pyarrow(limit=limit)
    )
    assert isinstance(array, pa.Scalar)


@pytest.mark.notyet(
    ["datafusion"], reason="DataFusion backend doesn't support sum"
)
@pytest.mark.parametrize("limit", no_limit)
def test_scalar_to_pyarrow_scalar(limit, backend, awards_players):
    scalar = awards_players.yearID.sum().to_pyarrow(limit=limit)
    assert isinstance(scalar, pa.Scalar)


@pytest.mark.notimpl(["dask", "clickhouse", "impala", "pyspark"])
@pytest.mark.notyet(
    ["datafusion"],
    reason="""
        fields' nullability from frame.schema() is not always consistent with
        the first record batch's schema
""",
)
def test_table_to_pyarrow_table_schema(backend, awards_players):
    table = awards_players.to_pyarrow()
    assert isinstance(table, pa.Table)
    assert table.schema == awards_players.schema().to_pyarrow()


@pytest.mark.notimpl(["dask", "clickhouse", "impala", "pyspark"])
def test_column_to_pyarrow_table_schema(backend, awards_players):
    expr = awards_players.awardID
    array = expr.to_pyarrow()
    assert isinstance(array, pa.Array)
    assert array.type == expr.type().to_pyarrow()


@pytest.mark.notimpl(
    ["pandas", "dask", "clickhouse", "impala", "pyspark", "datafusion"]
)
def test_table_pyarrow_batch_chunk_size(backend, awards_players):
    batch_reader = awards_players.to_pyarrow_batches(
        limit=2050, chunk_size=2048
    )
    assert isinstance(batch_reader, pa.RecordBatchReader)
    batch = batch_reader.read_next_batch()
    assert isinstance(batch, pa.RecordBatch)
    assert len(batch) == 2048


@pytest.mark.notimpl(
    ["pandas", "dask", "clickhouse", "impala", "pyspark", "datafusion"]
)
def test_column_pyarrow_batch_chunk_size(backend, awards_players):
    batch_reader = awards_players.awardID.to_pyarrow_batches(
        limit=2050, chunk_size=2048
    )
    assert isinstance(batch_reader, pa.RecordBatchReader)
    batch = batch_reader.read_next_batch()
    assert isinstance(batch, pa.RecordBatch)
    assert len(batch) == 2048


@pytest.mark.notimpl(
    ["pandas", "dask", "clickhouse", "impala", "pyspark", "datafusion"]
)
@pytest.mark.broken(
    ["sqlite"],
    raises=pa.ArrowException,
    reason="Test data has empty strings in columns typed as int64",
)
def test_to_pyarrow_batches_borked_types(backend, batting):
    """This is a temporary test to expose an(other) issue with sqlite typing
    shenanigans."""
    batch_reader = batting.to_pyarrow_batches(limit=42)
    assert isinstance(batch_reader, pa.RecordBatchReader)
    batch = batch_reader.read_next_batch()
    assert isinstance(batch, pa.RecordBatch)
    assert len(batch) == 42


def test_no_pyarrow_message(backend, awards_players, no_pyarrow):
    with pytest.raises(ModuleNotFoundError) as excinfo:
        awards_players.to_pyarrow()

        assert "requires `pyarrow` but" in str(excinfo.value)
