from __future__ import annotations

from typing import Optional

from db.models.bases import BaseTable, db
from util.security import get_password_hash, verify_password

__all__ = ["User"]


class User(BaseTable):
    __tablename__ = "users"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.EmailType, nullable=False)
    is_active = db.Column(db.Boolean(), default=True)
    is_superuser = db.Column(db.Boolean(), default=False)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    phone_number = db.Column(db.Unicode(20))
    country_code = db.Column(db.Unicode(20))
    hashed_password = db.Column(db.String(), nullable=False)
    uq_username = db.UniqueConstraint("username")
    uq_email = db.UniqueConstraint("email")
    ix_username = db.Index("ix_username", "username")
    ix_email = db.Index("ix_email", "email")

    @classmethod
    async def get_by_email(cls, email: str) -> Optional[User]:
        return await cls.query.where(User.email == email).gino.first()

    @classmethod
    async def get_by_username(cls, username: str) -> Optional[User]:
        return await cls.query.where(User.username == username).gino.first()

    @classmethod
    async def get_by_email_or_username(
        cls, email_or_username: str, prefer: str = None
    ) -> Optional[User]:
        email_coro = cls.get_by_email(email_or_username)
        username_coro = cls.get_by_username(email_or_username)

        if prefer == "email":
            result = await email_coro or await username_coro
        else:
            result = await username_coro or await email_coro

        return result

    @classmethod
    async def authenticate(
        cls, email_or_username: str, password: str, prefer: str = None
    ) -> Optional[User]:
        user = await cls.get_by_email_or_username(email_or_username, prefer=prefer)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def create(cls, **values):
        password: Optional[str] = values.get("password")
        if password:
            values["hashed_password"] = get_password_hash(password)
        return super().create(**values)
