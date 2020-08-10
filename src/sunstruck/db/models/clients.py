from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import relationship

from db.models.bases import BaseTable, db
from db.models.users import User
from util.security import get_password_hash, verify_password

__all__ = ["OAuth2Client"]


class OAuth2Client(BaseTable):
    __tablename__ = "oauth2_clients"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    client_id = db.Column(db.String(50))
    hashed_client_secret = db.Column(db.String(150))
    owner_id = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    owner = relationship("User", back_populates="oauth2_clients")
    ix_owner_id = db.Index(f"ix_{__tablename__}_owner_id", "owner_id")
    ix_client_id = db.Index(f"ix_{__tablename__}_client_id", "client_id")
    uq_client_id = db.UniqueConstraint("client_id")

    @classmethod
    async def get_by_client_id(cls, client_id: str) -> Optional[OAuth2Client]:
        return await cls.query.where(cls.client_id == client_id).gino.first()

    @classmethod
    async def get_by_owner(cls, owner_id: int) -> List[OAuth2Client]:
        return await cls.query.where(cls.owner_id == owner_id).gino.all()

    @classmethod
    async def authenticate(cls, client_id: str, client_secret: str) -> Optional[User]:

        client = (
            await OAuth2Client.load(owner=User.on(OAuth2Client.owner_id == User.id))
            .where(OAuth2Client.client_id == client_id)
            .gino.one_or_none()
        )
        if not client:
            return None

        if not verify_password(client_secret, client.hashed_client_secret):
            return None

        return client.owner

    @classmethod
    def create(cls, **values):
        secret: Optional[str] = values.pop("client_secret", None)
        if secret:
            values["hashed_client_secret"] = get_password_hash(secret)
        return super().create(**values)
