# flake8: noqa isort:skip_file
import asyncio
from starlette.config import environ

# inject environment variables prior to first import
environ["TESTING"] = "true"
environ["DATABASE_NAME"] = "testing"
environ["DATABASE_ECHO"] = "false"

import os

import gino
import pytest
import sqlalchemy
from sqlalchemy_utils import create_database, database_exists, drop_database

import config
from db.init_db import create_master_user
from db import db
from sunstruck.main import app
from util.jsontools import load_json
import tests.utils as testutils
from httpx import AsyncClient

# Import testing-only database models
from tests.fixtures.models import TestModel  # noqa


def pytest_configure(config):
    # register custom markers
    config.addinivalue_line("markers", "cionly: run on CI only")


def pytest_runtest_setup(item):

    # test selection logic using custom markers
    is_ci_env = testutils.to_bool(os.getenv("CI"))
    has_ci_only_marker = [mark for mark in item.iter_markers(name="cionly")]
    if not is_ci_env and has_ci_only_marker:
        pytest.skip("run on CI only")


url = config.ALEMBIC_CONFIG.url

if not database_exists(url):
    create_database(url)


@pytest.fixture(scope="session")
def sa_engine():
    url = config.ALEMBIC_CONFIG.url

    if database_exists(url):
        drop_database(url)
    create_database(url)

    rv = sqlalchemy.create_engine(url, echo=config.DATABASE_ECHO)
    db.create_all(rv)  # create tables
    yield rv
    db.drop_all(rv)  # undo all that hard work you did
    rv.dispose()


@pytest.fixture
async def engine(sa_engine):
    db.create_all(sa_engine)
    e = await gino.create_engine(config.DATABASE_CONFIG.url, echo=config.DATABASE_ECHO)
    yield e
    await e.close()
    db.drop_all(sa_engine)


@pytest.fixture
async def bind(sa_engine):
    db.create_all(sa_engine)
    async with db.with_bind(config.DATABASE_CONFIG.url, echo=config.DATABASE_ECHO) as e:
        await create_master_user()
        yield e
    db.drop_all(sa_engine)


@pytest.fixture
def conf():
    yield config


@pytest.fixture(scope="session")
def event_loop():
    """ Event loop scope must be equivalent (or higher) in scope than any async fixture scope."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client(bind):
    """ Create a test client connected to the main app instance. """

    # http://testserver is an httpx "magic" url that tells the client to query the
    # given app instance.
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def superuser_token_headers(client: AsyncClient, bind):
    """ Authenticate with the client's app instance and return an Authorization
        header with a populated Bearer token. """

    user_data = {
        "grant_type": "password",
        "username": config.MASTER_USERNAME,
        "password": config.MASTER_PASSWORD,
    }

    response = await client.post(f"{config.API_V1}/login/access-token", data=user_data)

    token_data = response.json()
    access_token = token_data["access_token"]

    yield {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def authorized_client(bind, superuser_token_headers):
    """ Create a test client that is authenticated using the master username/password"""

    async with AsyncClient(
        app=app, base_url="http://testserver", headers=superuser_token_headers
    ) as client:
        yield client


@pytest.fixture
async def client_credentials(authorized_client):
    """ Create a new set of client credentials for the master account """
    yield await client.post(f"{config.API_V1}/credentials")


# --- json fixtures ---------------------------------------------------------- #


@pytest.fixture(scope="session")
def json_fixture():
    yield lambda x: load_json(f"tests/fixtures/{x}")
