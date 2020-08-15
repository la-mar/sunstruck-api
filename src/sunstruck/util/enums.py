from __future__ import annotations

import enum
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

__all__ = ["Enum"]


class EnumMeta(type):
    def __iter__(self):
        return self.values()  # nocover


class Enum(enum.Enum):
    """Extends Enum builtin for easier lookups and iteration """

    __metaclass__ = EnumMeta

    @classmethod
    def value_map(cls) -> Dict[Any, Enum]:
        return cls._value2member_map_  # type: ignore

    @classmethod
    def has_member(cls, value: str) -> bool:
        """ Check if the enum has a member name matching the uppercased passed value """
        return hasattr(cls, str(value).upper())

    @classmethod
    def has_value(cls, value: str) -> bool:
        """ Check if the enum has a member name matching the passed value"""
        return value in cls.values()

    @classmethod
    def values(cls) -> List[Any]:
        return [v.value for v in cls.value_map().values()]

    @classmethod
    def keys(cls) -> List[str]:
        """Get a list of the enumerated attribute names """
        return [v.name for v in cls.value_map().values()]

    @classmethod
    def members(cls) -> List[Enum]:
        """ Get a list of instances containing all enumerated attributes """
        return list(cls.value_map().values())

    @classmethod
    def _missing_(cls, value):

        if value is not None:
            for member in cls._member_map_.values():
                if isinstance(value, str):
                    # case-insensitive membership check
                    if str.casefold(member._value_) == str.casefold(value):
                        return member

                # check if value is a valid member name
                try:
                    return cls._member_map_[str.upper(value)]
                except KeyError:
                    pass

        return super()._missing_(value)
