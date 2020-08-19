# flake8: noqa


from __future__ import annotations

import logging
from typing import Optional, Type, Union

import sqlalchemy as sa
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.schema import MetaData

import config as conf

logger = logging.getLogger(__name__)


# TODO: request-local sessions
#   - https://docs.sqlalchemy.org/en/14/orm/contextual.html#unitofwork-contextual
#   - https://github.com/encode/starlette/issues/420


class Database:
    """ API between SQLAlchemy and the calling application """

    _url: URL

    def __init__(
        self,
        metadata: MetaData = None,
        model_base: DeclarativeMeta = None,
        app=None,
        #
    ):
        self.engine = create_async_engine(conf.DATABASE_CONFIG.url, echo=True)
        self.session_factory = sessionmaker(
            bind=self.engine, class_=AsyncSession, future=True
        )
        self.Session = scoped_session(self.session_factory, scopefunc=None)

    # async def startup(
    #     self,
    #     pool_min_size: int = conf.DATABASE_POOL_SIZE_MIN,
    #     pool_max_size: int = conf.DATABASE_POOL_SIZE_MAX,
    # ) -> Database:
    #     """ Bind gino engine to the configured database.

    #     Keyword Arguments:
    #         pool_min_size {int} -- minimum number of connections held by the connection pool
    #             (default: conf.DATABASE_POOL_SIZE_MIN)
    #         pool_max_size {int} -- maximum number of connection consumed by the connection pool
    #             (default: conf.DATABASE_POOL_SIZE_MAX)

    #     """
    #     await self.set_bind(self.url, min_size=pool_min_size, max_size=pool_max_size)
    #     logger.debug(f"Connected to {self.url.__to_string__(hide_password=True)}")
    #     return self

    # async def shutdown(self) -> Database:
    #     """ Close the connection to the database. """

    #     await self.pop_bind().close()
    #     logger.debug(f"Disconnected from {self.url.__to_string__(hide_password=True)}")
    #     return self

    # async def active_connection_count(self) -> int:
    #     """ Get total number of active connections to the database """

    #     return await self.scalar("SELECT sum(numbackends) FROM pg_stat_database")

    # def qsize(self):
    #     """ Get current number of connections held by this instance's connection pool """
    #     return self.bind.raw_pool._queue.qsize()


db: Database = Database(
    # bind=conf.DATABASE_CONFIG.url,
    # pool_min_size=conf.DATABASE_POOL_SIZE_MIN,
    # pool_max_size=conf.DATABASE_POOL_SIZE_MAX,
    # echo=conf.DATABASE_ECHO,
    # ssl=conf.DATABASE_SSL,
    # use_connection_for_request=conf.DATABASE_USE_CONNECTION_FOR_REQUEST,
    # retry_limit=conf.DATABASE_RETRY_LIMIT,
    # retry_interval=conf.DATABASE_RETRY_INTERVAL,
    # naming_convention={  # passed to sqlalchemy.MetaData
    #     "ix": "ix_%(column_0_label)s",
    #     "uq": "uq_%(table_name)s_%(column_0_name)s",
    #     "ck": "ck_%(table_name)s_%(constraint_name)s",
    #     "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    #     "pk": "pk_%(table_name)s",
    # },
)

if __name__ == "__main__":

    db.Session()
    self = db
