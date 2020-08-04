import json
import logging

import pytest

from loggers import ColorizingStreamHandler, config, get_formatter, mlevel, mlevelname
from tests.utils import rand_str

logger = logging.getLogger(__name__)
logger.setLevel(10)


@pytest.fixture
def test_logger():
    logger = logging.getLogger(rand_str())
    logger.setLevel(10)
    yield logger


class TestLogger:
    @pytest.mark.parametrize(
        "qualifier,expected",
        [
            ("debug", 10),
            ("info", 20),
            ("warning", 30),
            ("error", 40),
            ("critical", 50),
            (10, 10),
            (20, 20),
            (30, 30),
            (40, 40),
            (50, 50),
        ],
    )
    def test_mlevel(self, qualifier, expected):
        assert mlevel(qualifier) == expected

    @pytest.mark.parametrize(
        "qualifier,expected",
        [
            (10, "debug"),
            (20, "info"),
            (30, "warning"),
            (40, "error"),
            (50, "critical"),
        ],
    )
    def test_mlevelname(self, qualifier, expected):
        assert mlevelname(qualifier) == expected.upper()

    @pytest.mark.parametrize("qualifier", ["", None, 100, "100"])
    def test_handle_bad_qualifier(self, qualifier):
        with pytest.raises(ValueError):
            mlevel(qualifier)

    def test_json_formatter(self, capfd):
        fmt = get_formatter("json")
        handler = ColorizingStreamHandler()
        handler.setFormatter(fmt)
        if logger.handlers:
            logger.removeHandler(logger.handlers[0])
        logger.addHandler(handler)
        logger.info("json message")
        captured = capfd.readouterr()
        message_keys = json.loads(captured.err).keys()
        expected_keys = [
            "timestamp",
            "logger.name",
            "logger.method_name",
            "message",
            "funcName",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
        ]
        for key in expected_keys:
            assert key in message_keys

    def test_json_formatter_with_exc_info(self, capfd):

        locallogger = logging.getLogger(rand_str())
        locallogger.setLevel(10)

        fmt = get_formatter("json")
        handler = ColorizingStreamHandler()
        handler.setFormatter(fmt)
        if locallogger.handlers:
            locallogger.removeHandler(locallogger.handlers[0])
        locallogger.addHandler(handler)

        locallogger.info("json message", exc_info=Exception(":("))
        captured = capfd.readouterr()
        message_keys = json.loads(captured.err).keys()

        expected_keys = [
            "error.kind",
            "error.message",
            "error.stack",
        ]
        for key in expected_keys:
            assert key in message_keys

    def test_configure_non_existing_logger(self):
        with pytest.raises(ValueError):
            config(logger="not.real")

    def test_configure_existing_logger_by_name(self, test_logger):
        expected = test_logger.level
        config(logger=test_logger.name)
        actual = test_logger.level
        assert expected == actual
