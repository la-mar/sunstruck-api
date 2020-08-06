import logging
from datetime import timedelta
from typing import Dict

import pytest

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
