# flake8: noqa
import logging

import gino
from gino.ext.starlette import Gino

import config as conf

logger = logging.getLogger(__name__)

db: Gino = Gino(
    dsn=conf.DATABASE_CONFIG.url,
    pool_min_size=conf.DATABASE_POOL_SIZE_MIN,
    pool_max_size=conf.DATABASE_POOL_SIZE_MAX,
    echo=conf.DATABASE_ECHO,
    ssl=conf.DATABASE_SSL,
    use_connection_for_request=conf.DATABASE_USE_CONNECTION_FOR_REQUEST,
    retry_limit=conf.DATABASE_RETRY_LIMIT,
    retry_interval=conf.DATABASE_RETRY_INTERVAL,
    naming_convention={  # passed to sqlalchemy.MetaData
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    },
)


async def startup(
    pool_min_size: int = conf.DATABASE_POOL_SIZE_MIN,
    pool_max_size: int = conf.DATABASE_POOL_SIZE_MAX,
):  # nocover
    await db.set_bind(db.url, min_size=pool_min_size, max_size=pool_max_size)
    logger.debug(f"Connected to {db.url.__to_string__(hide_password=True)}")


async def shutdown():  # nocover
    await db.pop_bind().close()
    logger.debug(f"Disconnected from {db.url.__to_string__(hide_password=True)}")


def qsize():
    """ Get current number of connections held by this instance """
    return db.bind.raw_pool._queue.qsize()


async def active_connection_count() -> int:
    """ Get total number of active connections to the database """

    return await db.scalar("SELECT sum(numbackends) FROM pg_stat_database")


# set some properties for convenience
(db.qsize, db.startup, db.shutdown, db.url, db.active_connection_count,) = (
    qsize,
    startup,
    shutdown,
    conf.DATABASE_CONFIG.url,
    active_connection_count,
)
