import logging

import pytest
import starlette.status as codes

from api.v1.endpoints.users import ERROR_404
from db.models import User as Model
from tests.utils import rand_email, rand_str, seed_model

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio

path: str = "/api/v1/users"


@pytest.fixture(autouse=True)
async def seed_users(bind):
    await seed_model(Model, 30)


@pytest.fixture
def user():
    return {
        "username": rand_str(),
        "email": rand_email(),
        "password": rand_str(),
        #
    }


async def test_read_me(client, superuser_token_headers):

    response = await client.get(f"{path}/me", headers=superuser_token_headers)
    logger.warning(response.json())


async def test_create_user(client, user):
    response = await client.post(path, json=user)
    assert response.status_code == codes.HTTP_200_OK
    data = response.json()
    assert data["id"] == 32


async def test_list_users(client):
    expected_record_count = 25
    response = await client.get(path)
    assert response.status_code == codes.HTTP_200_OK
    data = response.json()
    assert len(data) == expected_record_count
    assert response.links["next"] is not None


async def test_get_user(client):
    id = 20
    response = await client.get(f"{path}/{id}")
    assert response.status_code == codes.HTTP_200_OK
    data = response.json()
    assert data["id"] == 20


async def test_update_exising_user(client, user):
    id = 10
    response = await client.put(f"{path}/{id}", json=user)
    assert response.status_code == codes.HTTP_200_OK
    data = response.json()
    assert data["id"] == id
    assert data["username"] == user["username"]


async def test_partial_update_exising_user(client, user):
    id = 10
    response = await client.patch(f"{path}/{id}", json=user)
    assert response.status_code == codes.HTTP_200_OK
    data = response.json()
    assert data["id"] == id
    assert data["username"] == user["username"]


async def test_update_user_not_found(client, user):
    id = 99999
    response = await client.put(f"{path}/{id}", json=user)
    assert response.status_code == codes.HTTP_404_NOT_FOUND


async def test_delete_existing_user(client):
    id = 20
    response = await client.delete(f"{path}/{id}")
    assert response.status_code == codes.HTTP_200_OK
    data = response.json()
    assert data["id"] == id


async def test_delete_user_not_found(client):
    id = 99999
    response = await client.delete(f"{path}/{id}")
    assert response.status_code == codes.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == ERROR_404["detail"]
