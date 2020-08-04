# from typing import Optional

# from pydantic import EmailStr

# from schemas.bases import BaseModel, ORMBase

# __all__ = ["User", "UserCreateIn", "UserUpdateIn"]


# class User(ORMBase):
#     first_name: Optional[str]
#     last_name: Optional[str]
#     email: Optional[EmailStr]
#     phone_number: Optional[str]
#     country_code: Optional[str]


# class UserCreateIn(BaseModel):
#     first_name: Optional[str]
#     last_name: Optional[str]
#     email: Optional[EmailStr]
#     phone_number: Optional[str]
#     country_code: Optional[str]


# class UserUpdateIn(BaseModel):
#     first_name: Optional[str]
#     last_name: Optional[str]
#     email: Optional[EmailStr]
#     phone_number: Optional[str]
#     country_code: Optional[str]
