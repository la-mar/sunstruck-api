import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

import orjson

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return int(obj.total_seconds())
        else:
            return super().default(obj)


class ObjectEncoder(json.JSONEncoder):
    """Class to convert an object into json"""

    def default(self, obj: Any):
        """Convert `obj` to json"""

        if isinstance(obj, (int, float, str, list, dict, tuple, bool)):
            # return super().default(obj)
            return obj
        elif hasattr(obj, "to_dict"):
            return self.default(obj.to_dict())
        elif hasattr(obj, "dict"):
            return self.default(obj.dict())
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, Path):
            return str(obj)

        else:
            # generic fallback
            cls = type(obj)
            result = {
                "__custom__": True,
                "__module__": cls.__module__,
                "__name__": cls.__name__,
            }
            return result


class UniversalEncoder(DateTimeEncoder, ObjectEncoder):
    pass


def orjson_dumps(v: Any, *, default: Callable = None) -> str:
    return orjson.dumps(v, default=default, option=orjson.OPT_NAIVE_UTC).decode()


def to_string(data: Union[List, Dict], pretty: bool = True) -> str:
    indent = 4 if pretty else 0
    return json.dumps(data, indent=indent, cls=UniversalEncoder)


def dumps(data: Union[List, Dict], pretty: bool = True) -> str:
    """ alias for jsontools.to_string """
    return to_string(data, pretty)


def loads(data: str) -> Union[List, Dict]:
    """ deserialize a json string into a python collection """
    return json.loads(data)


def to_json(d: Union[List, Dict], path: Union[Path, str], cls=UniversalEncoder):
    with open(path, "w") as f:
        json.dump(d, f, cls=cls, indent=4)


def load_json(path: Union[Path, str]):
    with open(path, "r") as f:
        return json.load(f)


def make_repr(data: Union[List, Dict], pretty: bool = True) -> str:
    """wraps jsontools.to_string to encapsulate repr specific edge cases """
    return to_string(data=data, pretty=pretty)
