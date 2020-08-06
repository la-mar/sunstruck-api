from typing import Optional

from pydantic import EmailStr, Field, validator

import util.security as security
from schemas.bases import BaseModel, ORMBase

__all__ = ["User", "UserCreateIn", "UserUpdateIn", "UserOut"]


class User(BaseModel):
    """ Base model defining properties shared across schemas """

    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    country_code: Optional[str]


class UserCreateIn(User):
    """ Properties available to POST requests """

    first_name: str
    last_name: str
    email: EmailStr
    hashed_password: str = Field(..., alias="password")

    @validator("hashed_password")
    def hash_password(v: str) -> str:
        return security.get_password_hash(v)


class UserUpdateIn(User):
    """ Properties available to PUT/PATCH requests """

    hashed_password: Optional[str] = Field(None, alias="password")

    @validator("hashed_password")
    def hash_password(v: str) -> str:
        return security.get_password_hash(v)


class UserOut(ORMBase, User):
    """ Properties to include in API responses """

    first_name: str
    last_name: str
    email: EmailStr


class UserInDB(ORMBase, User):
    """ Internal only properties """

    hashed_password: str
