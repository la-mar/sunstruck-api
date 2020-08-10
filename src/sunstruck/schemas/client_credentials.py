import secrets
import uuid
from typing import Optional

from pydantic import validator

from schemas.bases import BaseModel, ORMBase

__all__ = [
    "ClientCredentials",
    "ClientCredentialsCreateIn",
    "ClientCredentialsUpdateIn",
    "ClientCredentialsOut",
]


class ClientCredentials(BaseModel):
    """ Base model defining properties shared across schemas """

    client_id: str


class ClientCredentialsCreateIn(ClientCredentials):
    """ Properties available to POST requests.

        client_id and client_secret are populated with suitable defaults if no value
        is provided.
    """

    client_id: str = ""
    client_secret: str = ""

    @validator("client_id", pre=True, always=True)
    def default_client_id(cls, v: Optional[str]) -> str:
        return v or str(uuid.uuid4().hex)

    @validator("client_secret", pre=True, always=True)
    def default_client_secret(cls, v: Optional[str]) -> str:
        return v or secrets.token_hex(64)


class ClientCredentialsUpdateIn(ClientCredentials):
    """ Properties available to POST requests """


class ClientCredentialsOut(ORMBase, BaseModel):
    """ Properties to include in API responses """

    client_id: str
    client_secret: Optional[str]

    @validator("id")
    def null_id(v: int):
        return None


class ClientCredentialsInDB(ORMBase, ClientCredentials):
    """ Internal only properties """

    hashed_client_secret: str


if __name__ == "__main__":
    client_id = uuid.uuid4().hex
    client_secret = secrets.token_hex(64)
    # ClientCredentialsCreateIn(client_secret=client_secret).dict()
    ClientCredentialsCreateIn().dict()

    # ClientCredentialsCreateIn(client_id=client_id, client_secret=client_secret).dict()
