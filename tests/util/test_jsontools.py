import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import pytz

from util.jsontools import (
    DateTimeEncoder,
    ObjectEncoder,
    load_json,
    orjson_dumps,
    to_json,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def kv():
    yield {"key": datetime.utcfromtimestamp(0)}


@pytest.fixture
def datetime_encoder():
    yield DateTimeEncoder()


class TestDatetimeEncoder:
    def test_encode_datetime(self, datetime_encoder):
        data = {"key": datetime.utcfromtimestamp(0)}
        expected = '{"key": "1970-01-01T00:00:00"}'
        result = datetime_encoder.encode(data)
        assert result == expected

    def test_encode_non_datetime(self, datetime_encoder):
        data = {"key": "test123", "key2": "test234"}
        expected = '{"key": "test123", "key2": "test234"}'
        result = datetime_encoder.encode(data)
        assert result == expected

    def test_dump_datetime(self):
        data = {"key": datetime.utcfromtimestamp(0)}
        expected = '{"key": "1970-01-01T00:00:00"}'
        result = json.dumps(data, cls=DateTimeEncoder)
        assert result == expected

    def test_super_class_raise_type_error(self, datetime_encoder):
        with pytest.raises(TypeError):
            datetime_encoder.default(0)

    def test_encode_timedelta(self):
        data = {"test_obj": timedelta(hours=1)}
        expected = '{"test_obj": 3600}'
        result = json.dumps(data, cls=DateTimeEncoder)
        assert result == expected


class TestObjectEncoder:
    def test_encode_with_to_dict_attribute(self):
        class ObjectForEncoding:
            key = "value"

            def to_dict(self):
                return {"key": self.key}

        data = {"test_obj": ObjectForEncoding()}
        expected = '{"test_obj": {"key": "value"}}'
        assert json.dumps(data, cls=ObjectEncoder) == expected

    def test_encode_with_dict_attribute(self):
        class ObjectForEncoding:
            key = "value"

            def dict(self):
                return {"key": self.key}

        data = {"test_obj": ObjectForEncoding()}
        expected = '{"test_obj": {"key": "value"}}'
        assert json.dumps(data, cls=ObjectEncoder) == expected

    def test_encode_with_pathlib_path(self):
        path = Path(".").resolve()
        data = {"path": path}
        expected = json.dumps({"path": str(path)}, cls=ObjectEncoder)
        assert json.dumps(data, cls=ObjectEncoder) == expected

    def test_encode_list(self):
        data = [1, 2, 2, "house", "of", "voodoo"]
        expected = '[1, 2, 2, "house", "of", "voodoo"]'
        assert json.dumps(data, cls=ObjectEncoder) == expected

    def test_encode_set(self):
        data = {1, 2, 3, "you", "dont", "know", "about", "me"}
        expected = json.dumps(list(data), cls=ObjectEncoder)

        assert json.dumps(data, cls=ObjectEncoder) == expected

    def test_encode_scalar(self):
        data = 1
        expected = "1"
        assert json.dumps(data, cls=ObjectEncoder) == expected


class TestIO:
    def test_json_file(self, tmpdir):
        path = tmpdir.mkdir("test").join("test.json")
        data = {"key": "value"}
        to_json(data, path)
        loaded = load_json(path)
        assert data == loaded


def test_utc_to_utc():
    dt = datetime(year=2019, month=1, day=1, hour=6)
    assert orjson_dumps({"dt": dt}) == orjson_dumps(
        {"dt": pytz.UTC.localize(dt).isoformat()}
    )
