from __future__ import annotations

from typing import Optional

from db.models.bases import BaseTable, db
from util.security import get_password_hash, verify_password

__all__ = ["User"]


class User(BaseTable):
    __tablename__ = "users"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.EmailType, nullable=False)
    phone_number = db.Column(db.Unicode(20))
    country_code = db.Column(db.Unicode(20))
    hashed_password = db.Column(db.String())  # , nullable=False
    is_superuser = db.Column(db.Boolean(), default=False)
    is_active = db.Column(db.Boolean(), default=True)
    uq_email = db.UniqueConstraint("email")

    @classmethod
    async def get_by_email(cls, email: str) -> Optional[User]:
        return await cls.query.where(User.email == email).gino.first()

    @classmethod
    async def authenticate(cls, email: str, password: str) -> Optional[User]:
        user = await cls.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def create(cls, *, password: str, **values):
        values["hashed_password"] = get_password_hash(password)
        return super().create(**values)
