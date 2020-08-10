import logging

import pytest
from fastapi import status
from httpx import AsyncClient
from jose import jwt

import config as conf
from db.models import User
from sunstruck.main import app
from tests.utils import rand_email, rand_str, unpack_fixture
from util import security

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio

v1: str = "/api/v1"


@pytest.fixture
def user_data():
    yield {
        "username": rand_str(length=7),
        "email": rand_email(min=5, max=5),
        "password": rand_str(length=10),
        #
    }


class TestAccessToken:
    async def test_password_flow(self, client):

        user_data = {
            "grant_type": "password",
            "username": conf.MASTER_USERNAME,
            "password": conf.MASTER_PASSWORD,
            #
        }
        response = await client.post(f"{v1}/login/access-token", data=user_data)
        assert response.status_code == status.HTTP_200_OK

        token_data = response.json()
        assert "access_token" in token_data.keys()
        assert token_data["access_token"]

    async def test_client_credentials_flow(self, authorized_client):

        # Generate a set of client credentials
        credentials = (await authorized_client.post(f"{v1}/credentials")).json()

        # Create a separate client and attempt to authenticate using the generated credentials
        async with AsyncClient(app=app, base_url="http://testserver") as client2:

            form_data = {
                "grant_type": "client_credentials",
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"],
            }

            response = await client2.post(f"{v1}/login/access-token", data=form_data)
            assert response.status_code == status.HTTP_200_OK

            token_data = response.json()
            assert "access_token" in token_data.keys()
            assert token_data["access_token"]


class TestClientCredentials:
    async def test_create(self, authorized_client):
        response = await authorized_client.get(f"{v1}/credentials")
        assert response.json() == []

        response = await authorized_client.post(f"{v1}/credentials")
        assert response.status_code == status.HTTP_200_OK
        credentials = response.json()

        assert credentials["client_id"]
        assert credentials["client_secret"]
        with pytest.raises(KeyError):
            credentials["id"]

    async def test_delete(self, authorized_client):
        response = await authorized_client.get(f"{v1}/credentials")
        assert len(response.json()) == 0

        credentials = (await authorized_client.post(f"{v1}/credentials")).json()

        response = await authorized_client.get(f"{v1}/credentials")
        assert len(response.json()) == 1

        data = {"client_id": credentials["client_id"]}
        response = await authorized_client.delete(f"{v1}/credentials", params=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"]

    async def test_delete_not_found(self, authorized_client):

        data = {"client_id": "pretendkey-nothingtoseehere"}
        response = await authorized_client.delete(f"{v1}/credentials", params=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]

    async def test_list(self, authorized_client):
        response = await authorized_client.get(f"{v1}/credentials")
        assert len(response.json()) == 0

        for x in range(0, 5):
            await authorized_client.post(f"{v1}/credentials")

        response = await authorized_client.get(f"{v1}/credentials")
        credentials: list = response.json()
        assert len(credentials) == 5

        for creds in credentials:
            with pytest.raises(KeyError):
                creds["id"]


class TestUserSignup:
    async def test_registration_enabled(self, client, user_data, monkeypatch):
        monkeypatch.setattr(conf, "USERS_OPEN_REGISTRATION", True, raising=True)
        response = await client.post(f"{v1}/signup", json=user_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == user_data["username"]

    async def test_registration_disabled(self, client, user_data, monkeypatch):
        monkeypatch.setattr(conf, "USERS_OPEN_REGISTRATION", False, raising=True)
        response = await client.post(f"{v1}/signup", json=user_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "Signup is disabled"

    @pytest.mark.parametrize("enabled", [True, False])
    async def test_registration_no_data(self, client, enabled, monkeypatch):
        monkeypatch.setattr(conf, "USERS_OPEN_REGISTRATION", enabled, raising=True)
        response = await client.post(f"{v1}/signup")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_registration_duplicate(self, client, user_data, monkeypatch):
        monkeypatch.setattr(conf, "USERS_OPEN_REGISTRATION", True, raising=True)
        response = await client.post(f"{v1}/signup", json=user_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == user_data["username"]

        response = await client.post(f"{v1}/signup", json=user_data)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == "Username taken"


class TestRecoverPassword:
    async def test_user_exists(self, client, user_data, monkeypatch):
        monkeypatch.setattr(conf, "USERS_OPEN_REGISTRATION", True, raising=True)
        response = await client.post(f"{v1}/signup", json=user_data)
        assert response.status_code == status.HTTP_200_OK

        response = await client.post(f"{v1}/recover-password", json=user_data)
        assert response.status_code == status.HTTP_200_OK

    async def test_user_no_exists(self, client, user_data, monkeypatch):
        response = await client.post(f"{v1}/recover-password", json=user_data)
        assert response.status_code == status.HTTP_200_OK


class TestResetPassword:
    async def test_valid(self, client, user_data, monkeypatch, bind):
        monkeypatch.setattr(conf, "USERS_OPEN_REGISTRATION", True, raising=True)
        response = await client.post(f"{v1}/signup", json=user_data)
        assert response.status_code == status.HTTP_200_OK

        # fetch current hashed_password from database
        db_user = await User.get_by_email(user_data["email"])

        # create reset token
        token = security.generate_password_reset_token(
            user_data["email"], secret=db_user.hashed_password
        )

        # submit reset request
        body = {"token": token, "new_password": "new_password"}
        response = await client.post(f"{v1}/reset-password", json=body)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Password update successful"

    async def test_invalid_token(self, client, user_data, monkeypatch):
        monkeypatch.setattr(conf, "USERS_OPEN_REGISTRATION", True, raising=True)
        response = await client.post(f"{v1}/signup", json=user_data)
        assert response.status_code == status.HTTP_200_OK

        # create reset token - exclude hashed_password to simulate bad token
        token = security.generate_password_reset_token(user_data["email"])

        # submit reset request
        body = {"token": token, "new_password": "new_password"}
        response = await client.post(f"{v1}/reset-password", json=body)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid token"

    async def test_malformed_token(self, client):

        body = {"token": "", "new_password": "new_password"}
        response = await client.post(f"{v1}/reset-password", json=body)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid token"

    async def test_missing_subject(self, client):

        token = jwt.encode(
            {"aud": "intentionally missing subject"},
            "secret",
            algorithm=security.ALGORITHM,
        )

        # submit reset request
        body = {"token": token, "new_password": "new_password"}
        response = await client.post(f"{v1}/reset-password", json=body)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid token"

    async def test_missing_user(self, client, user_data):

        # create reset token
        token = security.generate_password_reset_token(user_data["email"])

        # submit reset request
        body = {"token": token, "new_password": "new_password"}
        response = await client.post(f"{v1}/reset-password", json=body)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Password update failed"

    async def test_inactive_user(self, client, user_data):
        user_data["is_active"] = False
        response = await client.post(f"{v1}/users", json=user_data)
        assert response.status_code == status.HTTP_200_OK

        # create reset token
        token = security.generate_password_reset_token(user_data["email"])

        # submit reset request
        body = {"token": token, "new_password": "new_password"}
        response = await client.post(f"{v1}/reset-password", json=body)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Password update failed"


if __name__ == "__main__":
    user_data = unpack_fixture(user_data)
