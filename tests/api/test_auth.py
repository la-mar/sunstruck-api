import logging

import pytest

from db.models import User as Model
from tests.utils import seed_model

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio

path: str = "/api/v1/users/"


@pytest.fixture(autouse=True)
async def seed_users(bind):
    await seed_model(Model, 30)


async def test_login_access_token():
    pass
