from datetime import datetime
from typing import Union

import pytz

from util.jsontools import make_repr

__FORMATS__ = {"no_seconds": "%Y-%m-%d %H:%m"}


class DateTimeFormats(dict):
    def __init__(self, *args, **kwargs):
        super(DateTimeFormats, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def __repr__(self):
        return make_repr(self.__dict__)


def utcnow() -> datetime:
    """ Get the current datetime in utc as a datetime object with timezone information

    Returns:
        datetime -- UTC datetime with tzinfo
    """
    return datetime.now().astimezone(pytz.utc)


def localnow(tz: Union[pytz.BaseTzInfo, str] = "US/Central") -> datetime:
    """ Get the current datetime as a localized datetime object with timezone information

    Keyword Arguments:
        tz {Union[pytz.timezone, str]} -- localize datetime to this timezone (default: "US/Central")

    Returns:
        datetime -- localized datetime with tzinfo
    """

    if isinstance(tz, str):
        tz = pytz.timezone(tz)

    return datetime.now().astimezone(tz)


formats = DateTimeFormats(__FORMATS__)
