from typing import Dict, List, Optional

from pydantic import root_validator
from pydantic.fields import ModelField

from schemas.bases import BaseModel


class FilterParam(BaseModel):
    conjunctive: Optional[str]
    field_name: str
    sep: str
    inverter: Optional[str]
    operator: str
    value: str

    @root_validator(pre=True)
    def empty_strings_to_none(cls, values):
        return {k: v if v != "" else None for k, v in values.items()}


class FilterParams(BaseModel):
    params: List[FilterParam]

    @property
    def __first_field__(self) -> ModelField:
        return list(FilterParams.__fields__.values())[0]

    def records(self, **kwargs) -> List[Dict]:
        return self.dict(**kwargs)[self.__first_field__.name]
