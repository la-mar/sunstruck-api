# flake8: noqa


from __future__ import annotations

import logging
from typing import Optional, Type, Union

import sqlalchemy as sa
from sqlalchemy.engine import Row  # type: ignore
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


class SQLAlchemyProps:
    """ Make frequently needed SQLAlchemy imports available on an API or Model instance
        without negatively impacting static analysis (e.g. typing, code completion).
    """

    def __init__(self):
        self.Row = Row
        self.alias = sa.alias
        self.all_ = sa.all_
        self.and_ = sa.and_
        self.any_ = sa.any_
        self.asc = sa.asc
        self.between = sa.between
        self.BigInteger = sa.BigInteger
        self.bindparam = sa.bindparam
        self.BLANK_SCHEMA = sa.BLANK_SCHEMA
        self.Boolean = sa.Boolean
        self.case = sa.case
        self.cast = sa.cast
        self.CheckConstraint = sa.CheckConstraint
        self.collate = sa.collate
        self.column = sa.column
        self.Column = sa.Column
        self.ColumnDefault = sa.ColumnDefault
        self.Constraint = sa.Constraint
        self.Date = sa.Date
        self.DateTime = sa.DateTime
        self.DDL = sa.DDL
        self.DefaultClause = sa.DefaultClause
        self.delete = sa.delete
        self.desc = sa.desc
        self.distinct = sa.distinct
        self.Enum = sa.Enum
        self.except_ = sa.except_
        self.except_all = sa.except_all
        self.exists = sa.exists
        self.extract = sa.extract
        self.false = sa.false
        self.FetchedValue = sa.FetchedValue
        self.Float = sa.Float
        self.ForeignKey = sa.ForeignKey
        self.ForeignKeyConstraint = sa.ForeignKeyConstraint
        self.func = sa.func
        self.funcfilter = sa.funcfilter
        self.Index = sa.Index
        self.insert = sa.insert
        self.inspect = sa.inspect
        self.Integer = sa.Integer
        self.intersect = sa.intersect
        self.intersect_all = sa.intersect_all
        self.Interval = sa.Interval
        self.join = sa.join
        self.JSON = sa.JSON
        self.LargeBinary = sa.LargeBinary
        self.lateral = sa.lateral
        self.literal = sa.literal
        self.literal_column = sa.literal_column
        self.MetaData = sa.MetaData
        self.modifier = sa.modifier
        self.not_ = sa.not_
        self.null = sa.null
        self.Numeric = sa.Numeric
        self.or_ = sa.or_
        self.outerjoin = sa.outerjoin
        self.outparam = sa.outparam
        self.over = sa.over
        self.PickleType = sa.PickleType
        self.PrimaryKeyConstraint = sa.PrimaryKeyConstraint
        self.select = sa.select
        self.Sequence = sa.Sequence
        self.SmallInteger = sa.SmallInteger
        self.String = sa.String
        self.subquery = sa.subquery
        self.table = sa.table
        self.Table = sa.Table
        self.tablesample = sa.tablesample
        self.text = sa.text
        self.Text = sa.Text
        self.ThreadLocalMetaData = sa.ThreadLocalMetaData
        self.Time = sa.Time
        self.true = sa.true
        self.tuple_ = sa.tuple_
        self.type_coerce = sa.type_coerce
        self.TypeDecorator = sa.TypeDecorator
        self.Unicode = sa.Unicode
        self.UnicodeText = sa.UnicodeText
        self.union = sa.union
        self.union_all = sa.union_all
        self.UniqueConstraint = sa.UniqueConstraint
        self.update = sa.update
        self.within_group = sa.within_group


class Database(SQLAlchemyProps):
    """ Global API between SQLAlchemy and the calling application """

    _url: URL

    def __init__(
        self,
        metadata: MetaData = None,
        model_base: DeclarativeMeta = None,
        app=None,
        #
    ):
        super().__init__()
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
