""" Global App Configuration

    All configuration items are 12 Factor compliant in that their values are inherited
    via a waterfall of definition locations. The value for a configuration item will be
    determined in the following order:
        1) environment variables exposed through a .env file in the project root
        2) system environment variables
        3) default value, if present
    If a value isn't found in one of the three locations, the configuration item will
    raise an error.
 """

from typing import Dict

import uvloop
from starlette.config import Config
from starlette.datastructures import Secret

from schemas.database_url import DatabaseURL
from util.toml import project, version  # noqa

# --- uvloop ----------------------------------------------------------------- #

uvloop.install()  # configure asyncio to use uvloop as the default event loop


# --- general ---------------------------------------------------------------- #

conf: Config = Config(env_file=".env")  # initialize from .env file, if present

ENV: str = conf("ENV", cast=str, default="development")
DEBUG: bool = conf("DEBUG", cast=bool, default=False)


# --- backends --------------------------------------------------------------- #

DATABASE_DRIVER: str = conf("DATABASE_DRIVER", cast=str, default="postgresql+asyncpg")
DATABASE_USERNAME: str = conf("DATABASE_USERNAME", cast=str)
DATABASE_PASSWORD: Secret = conf("DATABASE_PASSWORD", cast=Secret)
DATABASE_HOST: str = conf("DATABASE_HOST", cast=str, default="localhost")
DATABASE_PORT: int = conf("DATABASE_PORT", cast=int, default=5432)
DATABASE_NAME: str = conf("DATABASE_NAME", cast=str, default=project)
DATABASE_POOL_SIZE_MIN: int = conf("DATABASE_POOL_SIZE_MIN", cast=int, default=1)
DATABASE_POOL_SIZE_MAX: int = conf("DATABASE_POOL_SIZE_MIN", cast=int, default=15)
DATABASE_ECHO: bool = conf("DATABASE_ECHO", cast=bool, default=False)
DATABASE_SSL = conf("DATABASE_SSL", default=None)
DATABASE_USE_CONNECTION_FOR_REQUEST = conf(
    "DATABASE_USE_CONNECTION_FOR_REQUEST", cast=bool, default=True
)
DATABASE_RETRY_LIMIT = conf("DATABASE_RETRY_LIMIT", cast=int, default=1)
DATABASE_RETRY_INTERVAL = conf("DATABASE_RETRY_INTERVAL", cast=int, default=1)

DATABASE_CONFIG: DatabaseURL = DatabaseURL(
    drivername=DATABASE_DRIVER,
    username=DATABASE_USERNAME,
    password=DATABASE_PASSWORD,
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    database=DATABASE_NAME,
)

# --- alembic --- #

ALEMBIC_CONFIG: DatabaseURL = DatabaseURL(
    drivername="postgresql+psycopg2",  # alembic requires sync driver
    username=DATABASE_USERNAME,
    password=DATABASE_PASSWORD,
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    database=DATABASE_NAME,
)


# --- logging ---------------------------------------------------------------- #
LOG_LEVEL: str = conf("LOG_LEVEL", cast=str, default="20")
LOG_FORMAT: str = conf("LOG_FORMAT", cast=str, default="json")

# --- other ------------------------------------------------------------------ #

# FIRST_SUPERUSER: EmailStr
# FIRST_SUPERUSER_PASSWORD: str
USERS_OPEN_REGISTRATION: bool = conf(
    "USERS_OPEN_REGISTRATION", cast=bool, default=False
)
EMAILS_ENABLED: bool = False

# --- security --------------------------------------------------------------- #

SECRET_KEY: Secret = conf("SECRET_KEY", cast=Secret)

ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 * 7  # 7 days
EMAIL_RESET_TOKEN_EXPIRE_MINUTES: int = 15

MASTER_USERNAME: str = conf("MASTER_USERNAME", cast=str, default="sunstuck")
MASTER_PASSWORD: str = conf("MASTER_PASSWORD", cast=str)
MASTER_EMAIL: str = conf("MASTER_EMAIL", cast=str)

API_V1: str = "/api/v1"


def items() -> Dict:
    """ Return all configuration items as a dictionary. Only items that are fully
        uppercased and do not begin with an underscore are included."""
    return {
        x: globals()[x]
        for x in globals().keys()
        if not x.startswith("_") and x.isupper()
    }
