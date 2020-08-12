# flake8: noqa


from __future__ import annotations

import logging

import gino.api
import sqlalchemy as sa
from gino.ext.starlette import Gino
from sqlalchemy.engine.url import URL

import config as conf

logger = logging.getLogger(__name__)


class GinoExtended(Gino, gino.api.Gino):  # add gino.api.Gino to mro to help mypy
    """ Extend Gino to add some convenience properties. """

    _url: URL

    def __init__(self, *args, **kwargs):
        self._url = kwargs.get("dsn", None)
        super().__init__(*args, **kwargs)

        # explicitly add sqlalchemy attributes implicitly provided on Gino object
        # to improve static analysis.
        self.inspect = sa.inspect
        self.BLANK_SCHEMA = sa.BLANK_SCHEMA
        self.CheckConstraint = sa.CheckConstraint
        self.Column = sa.Column
        self.ColumnDefault = sa.ColumnDefault
        self.Computed = sa.Computed
        self.Constraint = sa.Constraint
        self.DDL = sa.DDL
        self.DefaultClause = sa.DefaultClause
        self.FetchedValue = sa.FetchedValue
        self.ForeignKey = sa.ForeignKey
        self.ForeignKeyConstraint = sa.ForeignKeyConstraint
        self.IdentityOptions = sa.IdentityOptions
        self.Index = sa.Index
        self.MetaData = sa.MetaData
        self.PassiveDefault = sa.PassiveDefault
        self.PrimaryKeyConstraint = sa.PrimaryKeyConstraint
        self.Sequence = sa.Sequence
        self.Table = sa.Table
        self.ThreadLocalMetaData = sa.ThreadLocalMetaData
        self.UniqueConstraint = sa.UniqueConstraint
        self.alias = sa.alias
        self.all_ = sa.all_
        self.and_ = sa.and_
        self.any_ = sa.any_
        self.asc = sa.asc
        self.between = sa.between
        self.bindparam = sa.bindparam
        self.case = sa.case
        self.cast = sa.cast
        self.collate = sa.collate
        self.column = sa.column
        self.delete = sa.delete
        self.desc = sa.desc
        self.distinct = sa.distinct
        self.except_ = sa.except_
        self.except_all = sa.except_all
        self.exists = sa.exists
        self.extract = sa.extract
        self.false = sa.false
        self.func = sa.func
        self.funcfilter = sa.funcfilter
        self.insert = sa.insert
        self.intersect = sa.intersect
        self.intersect_all = sa.intersect_all
        self.join = sa.join
        self.lateral = sa.lateral
        self.literal = sa.literal
        self.literal_column = sa.literal_column
        self.modifier = sa.modifier
        self.not_ = sa.not_
        self.null = sa.null
        self.nullsfirst = sa.nullsfirst
        self.nullslast = sa.nullslast
        self.or_ = sa.or_
        self.outerjoin = sa.outerjoin
        self.outparam = sa.outparam
        self.over = sa.over
        self.select = sa.select
        self.subquery = sa.subquery
        self.table = sa.table
        self.tablesample = sa.tablesample
        self.text = sa.text
        self.true = sa.true
        self.tuple_ = sa.tuple_
        self.type_coerce = sa.type_coerce
        self.union = sa.union
        self.union_all = sa.union_all
        self.update = sa.update
        self.within_group = sa.within_group
        self.ARRAY = sa.ARRAY
        self.BIGINT = sa.BIGINT
        self.BigInteger = sa.BigInteger
        self.BINARY = sa.BINARY
        self.Binary = sa.Binary
        self.BLOB = sa.BLOB
        self.BOOLEAN = sa.BOOLEAN
        self.Boolean = sa.Boolean
        self.CHAR = sa.CHAR
        self.CLOB = sa.CLOB
        self.DATE = sa.DATE
        self.Date = sa.Date
        self.DATETIME = sa.DATETIME
        self.DateTime = sa.DateTime
        self.DECIMAL = sa.DECIMAL
        self.Enum = sa.Enum
        self.FLOAT = sa.FLOAT
        self.Float = sa.Float
        self.INT = sa.INT
        self.INTEGER = sa.INTEGER
        self.Integer = sa.Integer
        self.Interval = sa.Interval
        self.JSON = sa.JSON
        self.LargeBinary = sa.LargeBinary
        self.NCHAR = sa.NCHAR
        self.NUMERIC = sa.NUMERIC
        self.Numeric = sa.Numeric
        self.NVARCHAR = sa.NVARCHAR
        self.PickleType = sa.PickleType
        self.REAL = sa.REAL
        self.SMALLINT = sa.SMALLINT
        self.SmallInteger = sa.SmallInteger
        self.String = sa.String
        self.TEXT = sa.TEXT
        self.Text = sa.Text
        self.TIME = sa.TIME
        self.Time = sa.Time
        self.TIMESTAMP = sa.TIMESTAMP
        self.TypeDecorator = sa.TypeDecorator
        self.Unicode = sa.Unicode
        self.UnicodeText = sa.UnicodeText
        self.VARBINARY = sa.VARBINARY
        self.VARCHAR = sa.VARCHAR

    @property
    def url(self) -> URL:
        return self._url

    async def startup(
        self,
        pool_min_size: int = conf.DATABASE_POOL_SIZE_MIN,
        pool_max_size: int = conf.DATABASE_POOL_SIZE_MAX,
    ) -> GinoExtended:
        """ Bind gino engine to the configured database.

        Keyword Arguments:
            pool_min_size {int} -- minimum number of connections held by the connection pool
                (default: conf.DATABASE_POOL_SIZE_MIN)
            pool_max_size {int} -- maximum number of connection consumed by the connection pool
                (default: conf.DATABASE_POOL_SIZE_MAX)

        """
        await self.set_bind(self.url, min_size=pool_min_size, max_size=pool_max_size)
        logger.debug(f"Connected to {self.url.__to_string__(hide_password=True)}")
        return self

    async def shutdown(self) -> GinoExtended:
        """ Close the connection to the database. """

        await self.pop_bind().close()
        logger.debug(f"Disconnected from {self.url.__to_string__(hide_password=True)}")
        return self

    async def active_connection_count(self) -> int:
        """ Get total number of active connections to the database """

        return await self.scalar("SELECT sum(numbackends) FROM pg_stat_database")

    def qsize(self):
        """ Get current number of connections held by this instance's connection pool """
        return self.bind.raw_pool._queue.qsize()


db: GinoExtended = GinoExtended(
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
