from typing import Optional

from pydantic import BaseModel, Field

__all__ = ["Token", "TokenPayload"]


class Token(BaseModel):
    access_token: str
    token_type: str = Field("Bearer", example="Bearer")


class TokenPayload(BaseModel):
    sub: Optional[int] = Field(
        None,
        description="Subject, or purpose, of the token. For example, a url or user's email. ",
    )
