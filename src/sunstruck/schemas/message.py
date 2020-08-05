from pydantic import BaseModel

__all__ = ["Message"]


class Message(BaseModel):
    message: str
