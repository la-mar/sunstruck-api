""" Bases for sqlalchemy data models """

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from gino.dialects.asyncpg import JSONB
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql.dml import Insert
from sqlalchemy.schema import Constraint, PrimaryKeyConstraint
from sqlalchemy.sql.base import ImmutableColumnCollection
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.sql.functions import Function
from sqlalchemy_utils import ChoiceType, EmailType, URLType

import util
import util.jsontools
from db import db
from db.mixins import BulkIOMixin
from util.deco import classproperty
from util.dt import utcnow

db.JSONB, db.UUID, db.EmailType, db.URLType, db.ChoiceType = (
    JSONB,
    UUID,
    EmailType,
    URLType,
    ChoiceType,
)


class Base(db.Model, BulkIOMixin):
    """ Data model base class """

    __abstract__ = True
    _columns: Optional[ColumnProxy] = None
    _agg: Optional[AggregateProxy] = None
    _pk: Optional[PrimaryKeyProxy] = None

    def __repr__(self):
        return util.jsontools.make_repr(self)

    @classproperty
    def c(cls) -> ColumnProxy:
        return cls.columns

    @classproperty
    def columns(cls) -> ColumnProxy:
        if not cls._columns:
            cls._columns = ColumnProxy(cls)
        return cls._columns

    @classproperty
    def agg(cls) -> AggregateProxy:
        if not cls._agg:
            cls._agg = AggregateProxy(cls)
        return cls._agg

    @classproperty
    def pk(cls) -> PrimaryKeyProxy:
        if not cls._pk:
            cls._pk = PrimaryKeyProxy(cls)
        return cls._pk

    @classproperty
    def __model_name__(cls) -> str:
        return f"{cls.__module__}.{cls.__name__}"

    @classproperty
    def constraints(cls) -> Dict[str, Constraint]:
        return {x.name: x for x in list(cls.__table__.constraints)}

    @classmethod
    async def merge(cls, constraint: Union[str, Constraint] = None, **values) -> Base:
        """ Upsert the given record.

        Keyword Arguments:
            constraint {Union[str, Constraint]} -- the constraint to use
                to identify conflicting records. If not specified, the table's
                primary key is used (default: None)

        Returns:
            Base -- the updated model instance
        """

        if isinstance(constraint, PrimaryKeyProxy) or constraint is None:
            constraint = cls.__table__.primary_key

        if isinstance(constraint, str):
            constraint = cls.constraints[constraint]

        set_cols = [
            c.name
            for c in cls.columns
            if c not in cls.pk and c not in list(constraint.columns)
        ]
        stmt: Insert = Insert(cls).values(values).returning(*cls.columns)

        update_set: Dict = {k: getattr(stmt.excluded, k) for k in set_cols}
        stmt = stmt.on_conflict_do_update(
            constraint=constraint,
            set_=update_set
            #
        )

        results = await stmt.gino.load(cls).all()
        return util.reduce(results)


class BaseTable(Base, BulkIOMixin):
    created_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, server_default=db.func.now(),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        server_default=db.func.now(),
        index=True,
    )


class ColumnProxy:
    """ Proxy object for a data model's columns """

    def __init__(self, model: Base):
        self.model = model

    def __iter__(self):
        for col in self.columns:
            yield col

    def __repr__(self):
        return util.jsontools.make_repr(self.names)

    def __getitem__(self, item):
        try:  # item is int
            return self.columns[item]
        except TypeError:  # item is not int
            pass

        return self.dict()[item]

    def dict(self) -> Dict:
        return dict(self.sa_obj)

    @property
    def sa_obj(self) -> ImmutableColumnCollection:
        """ Reference to the underlying sqlalchemy object """
        return self.model.__table__.c

    @property
    def columns(self) -> List[Column]:
        return list(self.sa_obj)

    @property
    def names(self) -> List[str]:
        return [x.name for x in self.columns]

    @property
    def pytypes(self) -> Dict[str, Any]:
        """ Return a mapping of the model's field names to Python types.

        Example:
        >>> model.columns.pytypes
        >>> {"id": int, "name": str}

        Returns:
            Dict[str, Any]
        """
        dtypes = {}
        for col in self.columns:
            dtypes[col.name] = col.type.python_type

        return dtypes

    @property
    def dtypes(self) -> Dict[str, Any]:
        """ Return a mapping of the model's field names to SQL column types.

        Example:
        >>> model.columns.dtypes
        >>> {'id': BigInteger(), 'first_name': String(length=100)}

        Returns:
            Dict[str, Any]
        """
        dtypes = {}
        for col in self.columns:
            dtypes[col.name] = col.type

        return dtypes


class PrimaryKeyProxy(ColumnProxy):
    """ Proxy object for a data model's primary key attributes """

    def dict(self) -> Dict:
        return dict(self.sa_obj.columns)

    @property
    def sa_obj(self) -> PrimaryKeyConstraint:
        """ Reference to the underlying sqlalchemy object """
        return self.model.__table__.primary_key

    @property
    def columns(self) -> List[Column]:
        return list(self.sa_obj.columns)

    @property
    async def values(self) -> Union[List[Any]]:
        values = await self.model.select(*self.names).gino.all()
        if len(values) > 0:
            if len(values[0]) == 1:
                values = [v[0] for v in values]
        return values


class AggregateProxy:
    """ Proxy object for invoking aggregate queries against a model's underlying data """

    def __init__(self, model: Base):
        self.model: Base = model

    def __repr__(self):
        return f"AggregateProxy: {self.model.__module__}"

    @property
    def _pk(self) -> PrimaryKeyProxy:
        return self.model.pk

    @property
    def _c(self) -> ColumnProxy:
        return self.model.c

    @property
    def default_column(self) -> Column:
        return self._pk[0] if len(list(self._pk)) > 0 else self._c[0]

    def ensure_column(self, column: Union[str, Column] = None) -> Column:
        if isinstance(column, str):
            column = self._c[column]
        elif column is None:
            column = self.default_column
        return column

    # TODO: test with and without filter
    async def agg(
        self,
        funcs: Union[Function, List[Function]],
        filter: Union[str, TextClause] = None,
    ) -> Dict[str, Union[int, float]]:
        func_map: Dict[str, Function] = {f.name: f for f in util.ensure_list(funcs)}

        q = db.select(func_map.values())

        if filter is not None:
            if not isinstance(filter, TextClause):
                filter = db.text(filter)
            q = q.where(filter)

        results: List = await q.gino.one()

        return dict(zip(func_map, results))

    async def count(self, filter: Union[str, TextClause] = None) -> int:
        """ Get the model's rowcount """

        result = await self.agg(db.func.count(self.default_column), filter=filter)
        return util.reduce(result.values())

    async def max(
        self, column: Union[str, Column] = None, filter: Union[str, TextClause] = None
    ) -> int:
        """ Get the maximum value of the given column.  If no column is specified,
            the max value of the first primary key column is returned.
        """

        func: Function = db.func.max(self.ensure_column(column))
        result = await self.agg(func, filter=filter)
        return util.reduce(result.values())

    async def min(
        self, column: Union[str, Column] = None, filter: Union[str, TextClause] = None
    ) -> int:
        """ Get the minimum value of the given column.  If no column is specified,
            the min value of the first primary key column is returned.
        """

        func: Function = db.func.min(self.ensure_column(column))
        result = await self.agg(func, filter=filter)
        return util.reduce(result.values())
