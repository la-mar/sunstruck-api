import logging
from datetime import timedelta
from typing import Dict

import pytest
from jose import jwt

import config as conf
import util.security as security
from util.dt import utcnow

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio

path: str = "/api/v1/users/"


class TestCreateAccessToken:
    async def test_with_default_expiration(self):
        token = security.create_access_token(subject="name")

        contents: Dict = security.decode_token(token)

        before = utcnow() + timedelta(minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES - 10)
        after = utcnow() + timedelta(minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES)

        assert contents["sub"] == "name"
        assert before.timestamp() < contents["exp"]
        assert after.timestamp() > contents["exp"]

    async def test_with_expiration(self):
        token = security.create_access_token(
            subject="name", expires_delta=timedelta(days=30)
        )

        contents: Dict = security.decode_token(token)

        before = utcnow() + timedelta(days=29)
        after = utcnow() + timedelta(days=30)

        assert contents["sub"] == "name"
        assert before.timestamp() < contents["exp"]
        assert after.timestamp() > contents["exp"]


class TestVerifyPassword:
    def test_valid(self):
        password = "password"
        hashed_password = security.get_password_hash(password)
        assert security.verify_password(password, hashed_password)

    def test_invalid(self):
        password = "password"
        hashed_password = security.get_password_hash("not password")
        assert not security.verify_password(password, hashed_password)


def test_generate_password_reset_token():
    now = int(utcnow().timestamp())
    token = security.generate_password_reset_token("user@example.com")
    content = security.decode_token(token)

    assert (content["exp"] - now) // 60 == conf.EMAIL_RESET_TOKEN_EXPIRE_MINUTES
    assert content["nbf"] - now == 0


class TestVerifyPasswordResetToken:
    def test_valid(self):
        email = "user@example.com"
        hashed_password = "786iftyy7t8o6fyulvb"
        token = security.generate_password_reset_token(email, secret=hashed_password)
        actual = security.verify_password_reset_token(token, secret=hashed_password)
        assert email == actual["sub"]

    def test_expired(self):
        email = "user@example.com"
        hashed_password = "786iftyy7t8o6fyulvb"
        expires_timedelta = timedelta(hours=-1)
        token = security.generate_password_reset_token(
            email, expires_timedelta, secret=hashed_password
        )
        actual = security.verify_password_reset_token(token, secret=hashed_password)
        assert actual is None


class TestGetUnverifiedSubject:
    def test_valid(self):
        email = "user@example.com"
        hashed_password = "786iftyy7t8o6fyulvb"
        token = security.generate_password_reset_token(email, secret=hashed_password)

        assert security.get_unverified_subject(token) == email

    def test_missing_subject(self):
        token = jwt.encode({"exp": utcnow()}, "secret")
        assert security.get_unverified_subject(token) is None
