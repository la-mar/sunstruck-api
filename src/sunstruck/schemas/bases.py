from datetime import datetime
from typing import Union

import orjson
import pytz
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic import parse_obj_as, validator

from util.jsontools import orjson_dumps


class ValidationError(PydanticValidationError):
    """ Root Validation Error """


class BaseModel(PydanticBaseModel):
    """ Base class for all Pydantic models """

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps

    @staticmethod
    def localize(v: Union[str, datetime]) -> datetime:
        """ Attempt to parse a string representation of a datetime and ensure it
            is UTC. If parsing is successful, or a datetime object is passed
            directly, the datetime object is ensured to have a timezone, assuming
            it to be UTC if no timezone info is present.

        Arguments:
            v {Union[str, datetime]} -- string or datetime object

        Raises:
            e: Exception -- all exceptions are propagated

        Returns:
            datetime -- UTC datetime object
        """
        try:
            dt: datetime = parse_obj_as(datetime, v)
            if not dt.tzinfo:
                dt = pytz.utc.localize(dt)
            return pytz.utc.normalize(dt)
        except Exception as e:
            raise e


class ORMBase(BaseModel):
    """ Base class for all Pydantic models representing a database model.  The ORMBase
        differs from other bases in that the id, created_at, and updated_at fields are
        required by default.
    """

    id: int
    created_at: datetime
    updated_at: datetime

    class Config(BaseModel.Config):
        orm_mode = True

    @validator("created_at", "updated_at")
    def parse_dates(cls, v: Union[str, datetime]) -> datetime:
        return super().localize(v)
