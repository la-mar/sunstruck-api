""" Logger definitions """

import logging
import logging.config
import os
from logging import LogRecord
from typing import Any, Dict, Mapping, Optional, Union

import json_log_formatter
import logutils.colorize

import config as conf
from util.jsontools import ObjectEncoder, to_string

LOG_LEVELS: Dict[str, int] = dict(logging._nameToLevel)
LOG_LEVELS.update({str(k): k for k, v in logging._levelToName.items()})  # type: ignore


def mlevel(level: Union[int, str]) -> int:
    """ Convert level name/int to log level integer. Borrowed from Celery, with <3 """
    try:
        if not level:
            raise KeyError
        return LOG_LEVELS[str(level).upper()]
    except KeyError:
        unique_set = set(
            [str(x) for x in list(LOG_LEVELS.keys())]
            + [str(x) for x in list(LOG_LEVELS.values())]
        )
        opts: str = ", ".join(sorted(list(unique_set)))
        raise ValueError(f"Invalid log level: {level}. Available options: {opts}")


def mlevelname(level: Union[int, str]) -> str:
    """ Convert a level name/int to log level name """
    level = mlevel(level)
    return logging._levelToName[level]


class ColorizingStreamHandler(logutils.colorize.ColorizingStreamHandler):
    """
    A stream handler which supports colorizing of console streams
    under Windows, Linux and Mac OS X.

    :param strm: The stream to colorize - typically ``sys.stdout``
                 or ``sys.stderr``.
    """

    # color names to indices
    color_map = {
        "black": 0,
        "red": 1,
        "green": 2,
        "yellow": 3,
        "blue": 4,
        "magenta": 5,
        "cyan": 6,
        "white": 7,
    }

    # levels to (background, foreground, bold/intense)
    if os.name == "nt":
        level_map = {  # nocover
            logging.DEBUG: (None, "blue", True),
            logging.INFO: (None, "white", False),
            logging.WARNING: (None, "yellow", True),
            logging.ERROR: (None, "red", True),
            logging.CRITICAL: ("red", "white", True),
        }
    else:
        "Maps levels to colour/intensity settings."
        level_map = {
            logging.DEBUG: (None, "blue", False),
            logging.INFO: (None, "white", False),
            logging.WARNING: (None, "yellow", False),
            logging.ERROR: (None, "red", False),
            logging.CRITICAL: ("red", "white", True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class JsonFormatter(json_log_formatter.JSONFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record: LogRecord) -> str:
        """Return the record in the format usable by Datadog."""
        json_record: Dict = self.json_record(record.getMessage(), record)
        mutated_record: Dict = self.mutate_json_record(json_record)
        mutated_record = mutated_record if mutated_record is not None else json_record

        return self.to_json(mutated_record)

    def to_json(self, record: Mapping[str, Any]) -> str:
        """Convert record dict to a JSON string.
        Override this method to change the way dict is converted to JSON.
        """
        return self.json_lib.dumps(record, cls=ObjectEncoder)

    def json_record(self, message: str, record: LogRecord) -> Dict:
        """Convert the record to JSON and inject Datadog attributes."""
        record_dict = dict(record.__dict__)

        record_dict["message"] = message

        additional = {
            "timestamp": int(record.created * 1000),
            "severity": record.levelname,
            "logger.name": record.name,
            "logger.method_name": record.funcName,
            "logger.thread_name": record.threadName,
        }

        record_dict = {**additional, **record_dict}

        # Handle exceptions, including those in the formatter itself
        exc_info = record.exc_info
        if exc_info:
            if "error.kind" not in record_dict and exc_info[0] is not None:
                record_dict["error.kind"] = exc_info[0].__name__
            if "error.message" not in record_dict:
                record_dict["error.message"] = str(exc_info[1])
            if "error.stack" not in record_dict:
                record_dict["error.stack"] = self.formatException(exc_info)

        return record_dict


def get_formatter(name: Union[str, None]) -> logging.Formatter:
    formatters = {
        "json": JsonFormatter(),
        "verbose": logging.Formatter(
            fmt="[%(asctime)s - %(filename)s:%(lineno)s - %(funcName)s()] %(levelname)s - %(message)s",  # noqa
            datefmt="%Y-%m-%d %H:%M:%S",
        ),
        "funcname": logging.Formatter(
            fmt="[%(name)s: %(lineno)s - %(funcName)s()] %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ),
        "simple": logging.Formatter(
            fmt="%(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        ),
        "dead_simple": logging.Formatter(
            fmt="%(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        ),
    }
    return formatters[name or "funcname"]  # type: ignore


def loggers() -> Dict[str, logging.Logger]:
    """ Get a mapping of all active loggers by name """
    return dict(logging.root.manager.loggerDict)  # type: ignore


def get_existing_logger_by_name(name: str) -> Optional[logging.Logger]:
    if name in loggers().keys():
        return logging.getLogger(name)
    else:
        active = sorted(loggers())
        raise ValueError(
            f"No active logger with name '{name}' -- Valid options are: {to_string(active)}"
        )


def config(
    level: Union[int, str] = None,
    formatter: str = None,
    logger: Union[str, logging.Logger] = None,
):
    """ Convenience function for manipulating the logging tree

    Keyword Arguments:
        level {Union[int, str]} -- [description] (default: {None})
        formatter {str} -- [description] (default: {None})
        logger {Union[str, logging.Logger]} -- [description] (default: {None})
    """

    if isinstance(logger, str):
        logger = get_existing_logger_by_name(logger)

    if logger:
        root_logger = logger
        if level:
            logger.setLevel(mlevel(level))

    else:
        root_logger = logging.getLogger()
        root_logger.setLevel(mlevel(level or conf.LOG_LEVEL or 20))

    console_handler = ColorizingStreamHandler()
    console_handler.setFormatter(get_formatter(formatter or conf.LOG_FORMAT))

    while len(root_logger.handlers) > 0:
        root_logger.removeHandler(root_logger.handlers[0])

    root_logger.addHandler(console_handler)
    root_logger.debug(f"configured loggers (level={root_logger.level})")


if __name__ == "__main__":

    config(formatter="simple")
    logger = logging.getLogger()
    config(logger=logger, level=30)
    logger.debug("test-debug")
    logger.info("test-info")
    logger.warning("test-warning")
    logger.error("test-error")
