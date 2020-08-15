from typing import Callable, Dict, List, Optional

from pydantic import root_validator, validator
from pydantic.fields import ModelField
from sqlalchemy import and_, or_

from const import FilterOperator
from schemas.bases import BaseModel


class FilterParam(BaseModel):
    conjunctive: Optional[Callable]
    field_name: Optional[str]
    sep: Optional[Callable]
    inverter: Optional[str]
    operator: FilterOperator
    value: str

    @root_validator(pre=True)
    def empty_strings_to_none(cls, values):
        return {k: v if v != "" else None for k, v in values.items()}

    @validator("conjunctive", "sep", pre=True)
    def to_callable(cls, v: str) -> Optional[Callable]:
        if v:
            if v == ":":
                return and_
            elif v == "|":
                return or_
            else:
                raise ValueError(f"Conjunctive must be one of [':','|'], not {v}")

        return None


class FilterParams(BaseModel):
    params: List[FilterParam]

    @property
    def __first_field__(self) -> ModelField:
        return list(FilterParams.__fields__.values())[0]

    def records(self, **kwargs) -> List[Dict]:
        return self.dict(**kwargs)[self.__first_field__.name]
