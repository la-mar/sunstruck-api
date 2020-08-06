import logging

import pandas as pd
import pytest
from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError

from db.mixins import BulkIOMixin
from tests.fixtures.models import TestModel as Model
from tests.utils import rand_email, rand_str

logger = logging.getLogger(__name__)


pytestmark = pytest.mark.asyncio  # mark all tests as async


@pytest.fixture
def ids():
    yield list(range(1, 6))


@pytest.fixture
def records(ids):
    yield [
        {"id": i, "username": rand_str(), "email": rand_email(min=3, max=25)}
        for i in ids
    ]


@pytest.fixture
def records2(ids):
    yield [
        {"id": i, "username": rand_str(), "email": rand_email(min=3, max=25)}
        for i in ids
    ]


class TestBulkIO:
    async def test_make_log_prefix(self):
        actual = BulkIOMixin.log_prefix(ConnectionError())
        assert actual == "(BulkIOMixin) ConnectionError"

    @pytest.mark.parametrize("error_strategy", ["fracture", "raise"])
    async def test_bulk_upsert_update_on_conflict(
        self, bind, records, records2, error_strategy
    ):

        await Model.bulk_upsert(records, error_strategy=error_strategy)
        await Model.bulk_upsert(
            records2, conflict_action="update", error_strategy=error_strategy
        )

        results = await Model.query.gino.load((Model.id, Model.username)).all()
        expected = [(d["id"], d["username"]) for d in records2]
        assert results == expected

    @pytest.mark.parametrize("error_strategy", ["fracture", "raise"])
    async def test_bulk_upsert_ignore_on_conflict(
        self, bind, records, records2, error_strategy
    ):

        await Model.bulk_upsert(records, error_strategy=error_strategy)
        await Model.bulk_upsert(
            records2, conflict_action="ignore", error_strategy=error_strategy
        )

        results = await Model.query.gino.load((Model.id, Model.username)).all()
        expected = [(d["id"], d["username"]) for d in records]
        assert results == expected

    async def test_bulk_upsert_invalid_error_strategy(self, bind, records):

        with pytest.raises(ValueError):
            await Model.bulk_upsert(records, error_strategy="horeb")

    async def test_bulk_insert(self, bind, records):

        await Model.bulk_insert(records)

        results = await Model.query.gino.load((Model.id, Model.username)).all()
        expected = [(d["id"], d["username"]) for d in records]
        assert results == expected

    async def test_bulk_insert_raise_integrity_error(self, bind, caplog, records):
        caplog.set_level(50)

        await Model.bulk_insert(records)

        with pytest.raises((IntegrityError, UniqueViolationError)):
            await Model.bulk_insert(records)

    async def test_bulk_upsert_handle_data_error(self, bind, caplog, records, ids):
        caplog.set_level(50)

        records.append(
            {"id": 99999999999999999999, "username": rand_str(), "email": rand_email()}
        )
        await Model.bulk_upsert(records)

        assert await Model.pk.values == ids

    async def test_bulk_upsert_handle_data_error_no_retry(
        self, bind, caplog, records, ids
    ):
        caplog.set_level(10)

        records.append(
            {"id": 99999999999999999999, "username": rand_str(), "email": rand_email()}
        )
        with pytest.raises(Exception):
            await Model.bulk_upsert(records, error_strategy="raise")

    async def test_bulk_upsert_handle_generic_error(self, bind, caplog, records):
        caplog.set_level(50)

        with pytest.raises(Exception):
            records = [{"username": rand_str()}, {}]
            await Model.bulk_upsert(records)
            assert await Model.pk.values == []


if __name__ == "__main__":
    from tests.utils import unpack_fixture

    ids = unpack_fixture(ids)
    records = unpack_fixture(records, ids=ids)
    records2 = unpack_fixture(records2, ids=ids)
    df = pd.DataFrame(records)
    df2 = pd.DataFrame(records2)
