from typing import Optional

from pydantic import EmailStr

from schemas.bases import BaseModel, ORMBase

__all__ = ["User", "UserCreateIn", "UserUpdateIn"]


class User(BaseModel):
    """ Base model defining properties shared across schemas """

    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    country_code: Optional[str]


class UserCreateIn(User):
    """ Schema defining properties to available to post requests """

    first_name: str
    last_name: str
    email: EmailStr


class UserUpdateIn(User):
    """ Schema defining properties available to put/patch requests """


class UserOut(ORMBase, User):
    """ Schema defining properties to include in API responses """

    first_name: str
    last_name: str
    email: EmailStr
