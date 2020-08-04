import logging
from datetime import datetime
from typing import List, Optional

import pytest
import pytz
from pydantic import ValidationError, validator

from schemas.bases import BaseModel, ORMBase
from util.jsontools import orjson, orjson_dumps

logger = logging.getLogger(__name__)


class Model(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = None

    @validator("created_at")
    def localize(cls, v) -> datetime:
        return super().localize(v)


class OtherModel(BaseModel):
    id: Optional[int] = None
    alias: Optional[str] = None


class OptionalScalars(BaseModel):
    class Config:
        conflict_prefix = "events"

    id: Optional[int] = None
    name: Optional[str] = None


class ModelSet(BaseModel):
    id: Optional[int]
    events: List[OptionalScalars] = []
    other: Optional[OtherModel] = None


class NestedModelSet(BaseModel):
    sets: List[ModelSet]


class ORMModel(ORMBase):
    pass


@pytest.fixture
def history():
    yield [
        {"id": 1, "name": "pearl harbor", "created_at": "1941-12-07T07:55:00-00:00"},
        {"id": 2, "name": "d day", "created_at": "1944-06-06T00:00:00"},
        {"id": 3, "name": "v-e day", "created_at": "1945-05-08T06:00:00-06:00"},
        {"id": 4, "name": "v-j day", "created_at": "1945-09-02T00:00"},
    ]


@pytest.fixture
def others():
    yield [
        {"id": 5},
        {"id": 6, "alias": "alias-6"},
        {"id": 7, "alias": "alias-7"},
    ]


@pytest.fixture
def model(history):
    yield Model(**history[0])


@pytest.fixture
def nested_model_set(history, others):
    sets = [
        ModelSet(id=100, events=history[0:2], other=others[0],),
        ModelSet(id=101, events=history[1:3], other=others[0],),
        ModelSet(id=102, events=history[2:4], other=others[0]),
    ]
    yield NestedModelSet(sets=sets)


class TestBaseModel:
    def test_serializers(self, model):
        assert model.Config.json_loads is orjson.loads
        assert model.Config.json_dumps is orjson_dumps

    @pytest.mark.parametrize(
        "value",
        [
            "2020-01-01T00:00:00-00:00",
            "2019-12-31T18:00:00-06:00",
            "2020-01-01T00:00:00-00:00",
        ],
    )
    def test_localize(self, value):
        value = str(Model.localize(value))
        assert value == "2020-01-01 00:00:00+00:00"

    def test_localize_error_propagation(self):
        with pytest.raises(ValidationError):
            Model.localize("x")


class TestORMBase:
    def test_config(self):
        assert ORMModel.Config.orm_mode

    def test_init(self):
        orm_model = ORMBase(
            id=0,
            created_at="1969-07-16T09:32:00-00:00",
            updated_at="1969-07-24T23:07:08-00:00",
        )

        exp_created_at = datetime(
            year=1969, month=7, day=16, hour=9, minute=32, second=0, tzinfo=pytz.utc
        )
        exp_updated_at = datetime(
            year=1969, month=7, day=24, hour=23, minute=7, second=8, tzinfo=pytz.utc
        )

        assert orm_model.id == 0
        assert orm_model.created_at == exp_created_at
        assert orm_model.updated_at == exp_updated_at


if __name__ == "__main__":
    from tests.utils import unpack_fixture

    history = unpack_fixture(history)
    others = unpack_fixture(others)
    model = unpack_fixture(model, history=history)
