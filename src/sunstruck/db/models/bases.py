""" Bases for sqlalchemy data models

    ref: SQLAlchemy 1.4+ migration (https://docs.sqlalchemy.org/en/14/changelog/migration_14.html#behavioral-changes-orm)

"""  # noqa

from __future__ import annotations

from typing import Any, Dict, Generator, List, Optional, Tuple

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.schema import Constraint
from sqlalchemy.sql.schema import MetaData, Table

import util
import util.jsontools
from db.mixins import BulkIOMixin, CrudMixin
from db.proxies import ColumnProxy, PrimaryKeyProxy, QueryProxy
from util.deco import classproperty

# from sqlalchemy_utils import ChoiceType, EmailType, URLType


# db.JSONB, db.UUID, db.EmailType, db.URLType, db.ChoiceType = (
#     JSONB,
#     UUID,
#     EmailType,
#     URLType,
#     ChoiceType,
# )


@as_declarative()
class Model(CrudMixin, BulkIOMixin):
    """ Data model base class """

    # __abstract__ = True
    __table__: Table
    metadata: MetaData

    _columns: Optional[ColumnProxy] = None
    # _agg: Optional[AggregateProxy] = None
    _pk: Optional[PrimaryKeyProxy] = None
    _query: Optional[QueryProxy] = None

    def __repr__(self):
        return util.jsontools.make_repr(self)

    def __iter__(self) -> Generator:
        for item in self.dict().items():
            yield item

    @classproperty
    def __model_name__(cls) -> str:
        return f"{cls.__module__}.{cls.__name__}"

    @classproperty
    def constraints(cls) -> Dict[str, Constraint]:
        return {str(x.name): x for x in list(cls.__table__.constraints)}

    @classproperty
    def c(cls) -> ColumnProxy:
        return cls.columns

    @classproperty
    def columns(cls) -> ColumnProxy:
        if not cls._columns:
            cls._columns = ColumnProxy(cls)
        return cls._columns

    def dict(self) -> Dict[str, Any]:
        # sqlalchemy 1.4+ returns named tuples instead of mappings by default
        # ref: https://docs.sqlalchemy.org/en/14/changelog/migration_14.html#behavioral-changes-orm
        return {col: getattr(self, col) for col in self.c.names}

    # @classproperty
    # def agg(cls) -> AggregateProxy:
    #     if not cls._agg:
    #         cls._agg = AggregateProxy(cls)
    #     return cls._agg

    @classproperty
    def pk(cls) -> PrimaryKeyProxy:
        if not cls._pk:
            cls._pk = PrimaryKeyProxy(cls)
        return cls._pk

    # @classproperty
    # def query(cls) -> QueryProxy:
    #     if not cls._query:
    #         cls._query = QueryProxy(cls)
    #     return cls._query

    # @classmethod
    # async def merge(cls, constraint: Union[str, Constraint] = None, **values) -> Base:
    #     """ Upsert the given record.

    #     Keyword Arguments:
    #         constraint {Union[str, Constraint]} -- the constraint to use
    #             to identify conflicting records. If not specified, the table's
    #             primary key is used (default: None)

    #     Returns:
    #         Base -- the updated model instance
    #     """

    #     if isinstance(constraint, PrimaryKeyProxy) or constraint is None:
    #         constraint = cls.__table__.primary_key

    #     if isinstance(constraint, str):
    #         constraint = cls.constraints[constraint]

    #     set_cols = [
    #         c.name
    #         for c in cls.columns
    #         if c not in cls.pk and c not in list(constraint.columns)
    #     ]
    #     stmt: Insert = Insert(cls).values(values).returning(*cls.columns)

    #     update_set: Dict = {k: getattr(stmt.excluded, k) for k in set_cols}
    #     stmt = stmt.on_conflict_do_update(
    #         constraint=constraint,
    #         set_=update_set
    #         #
    #     )

    #     results = await stmt.gino.load(cls).all()
    #     return util.reduce(results)


if __name__ == "__main__":
    import config as conf
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, and_
    from db import db  # noqa

    class User(Model):
        __tablename__ = "users2"
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(String(50), primary_key=True)

    dir(User)

    dir(User.__table__)

    engine = create_async_engine(conf.DATABASE_CONFIG.url, echo=True)
    session = AsyncSession(engine, future=True)

    async def wrapper():

        async with engine.begin() as conn:
            await conn.run_sync(Model.metadata.drop_all)
            await conn.run_sync(Model.metadata.create_all)

        async with db.Session() as session:
            async with session.begin():
                for x in range(1, 6):
                    user = User(username=f"test-{x}")
                    session.add(user)

        # selecting columns returns tuples
        stmt = select(*User.pk)
        result = await session.execute(stmt)
        rows: List[Tuple[int, str]] = result.all()
        row: Tuple[int, str] = rows[0]
        rows
        row

        # selecting the model returns model objects
        stmt = select(User)
        result = await session.execute(stmt)
        rows: List[User] = result.scalars().all()
        row: User = rows[0]
        rows
        dir(row)
        row

        import pandas as pd

        pd.DataFrame(rows, columns=User.pk.names)

        # await User.pk.values

        # returns tuple
        stmt = User.select().where(User.id == 1)
        user: Tuple = (await session.execute(stmt)).one()

        # returns model instance
        stmt = select(User).where(User.id == 1)
        user: User = (await session.execute(stmt)).scalar()

        # returns model instance
        stmt = User.select()
        user: User = (await session.execute(stmt)).scalar()

        predicate = and_(*[col == getattr(user, col.name) for col in user.pk])

        # stmt = User.select().where(predicate)
        stmt = User.__table__.update().where(predicate).values(username="autoupdate")
        await session.execute(stmt)
        await session.commit()

        user.username = "updated"
        await session.commit()

        user: User = await User.get(id=6, username="test")

        user

        self = user

        import sqlalchemy as sa

        kwargs = dict(username="test-10")

        result = None
        async with db.Session() as session:
            async with session.begin():
                stmt = sa.insert(self.__class__).returning(*self.c).values(**kwargs)
                result = (await session.execute(stmt)).one()
        result

        user = await User.create(**kwargs)

        User(**user._mapping)
