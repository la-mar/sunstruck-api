import logging

import pytest
import starlette.status as codes

from api.v1.endpoints.users import ERROR_404
from db.models import User as Model
from tests.utils import rand_email, rand_str, seed_model

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio

path: str = "/api/v1/users/"


@pytest.fixture(autouse=True)
async def seed_users(bind):
    await seed_model(Model, 30)


class TestEndpoint:
    async def test_create_user(self, client):
        response = await client.post(
            path,
            json={
                "first_name": rand_str(),
                "last_name": rand_str(),
                "email": rand_email(),
            },
        )
        assert response.status_code == codes.HTTP_200_OK
        data = response.json()
        assert data["id"] == 31

    async def test_list_users(self, client):
        expected_record_count = 25
        response = await client.get(path)
        assert response.status_code == codes.HTTP_200_OK
        data = response.json()
        assert len(data) == expected_record_count
        assert response.links["next"] is not None

    async def test_get_user(self, client):
        id = 20
        response = await client.get(f"{path}{id}")
        assert response.status_code == codes.HTTP_200_OK
        data = response.json()
        assert data["id"] == 20

    async def test_update_exising_user(self, client):
        id = 10
        name = rand_str(length=25)
        response = await client.put(
            f"{path}{id}",
            json={"first_name": name, "last_name": rand_str(), "email": rand_email()},
        )
        assert response.status_code == codes.HTTP_200_OK
        data = response.json()
        assert data["id"] == id
        assert data["first_name"] == name

    async def test_partial_update_exising_user(self, client):
        id = 10
        name = rand_str(length=25)
        response = await client.patch(
            f"{path}{id}",
            json={"first_name": name, "last_name": rand_str(), "email": rand_email()},
        )
        assert response.status_code == codes.HTTP_200_OK
        data = response.json()
        assert data["id"] == id
        assert data["first_name"] == name

    async def test_update_user_not_found(self, client):
        id = 99999
        response = await client.put(
            f"{path}{id}",
            json={
                "first_name": rand_str(),
                "last_name": rand_str(),
                "email": rand_email(),
            },
        )
        assert response.status_code == codes.HTTP_404_NOT_FOUND

    async def test_delete_existing_user(self, client):
        id = 20
        response = await client.delete(f"{path}{id}")
        assert response.status_code == codes.HTTP_200_OK
        data = response.json()
        assert data["id"] == id

    async def test_delete_user_not_found(self, client):
        id = 99999
        response = await client.delete(f"{path}{id}")
        assert response.status_code == codes.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == ERROR_404["detail"]
