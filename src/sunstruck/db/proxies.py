""" Bases for sqlalchemy data models """

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import Column
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.sql.base import ImmutableColumnCollection

import util
import util.jsontools
from db import db

if TYPE_CHECKING:
    from db.models.bases import Model


class ProxyBase:
    def __init__(self, model: Model):
        self.model: Model = model


class QueryProxy(ProxyBase):
    pass


class ColumnProxy(ProxyBase):
    """ Proxy object for a data model's columns """

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

    def dict(self) -> Dict[str, Column]:
        return dict(self.sa_obj)  # type: ignore

    @property
    def sa_obj(self) -> ImmutableColumnCollection:
        """ Reference to the underlying sqlalchemy object """
        return self.model.__table__.columns

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
        return dict(self.sa_obj.columns)  # type: ignore

    @property
    def sa_obj(self) -> PrimaryKeyConstraint:  # type: ignore
        """ Reference to the underlying sqlalchemy object """
        return self.model.__table__.primary_key

    @property
    def columns(self) -> List[Column]:
        return list(self.sa_obj.columns)

    @property
    async def values(self) -> List[Any]:

        values: List
        async with db.Session() as session:
            async with session.begin():
                values = (await session.execute(self.model.select(*self.columns))).all()

        return [util.reduce(v) for v in values]


# class AggregateProxy(ProxyBase):
#     """ Proxy object for invoking aggregate queries against a model's underlying data """

#     def __init__(self, model: Model):
#         self.model: Model = model

#     def __repr__(self):
#         return f"AggregateProxy: {self.model.__module__}"

#     @property
#     def _pk(self) -> PrimaryKeyProxy:
#         return self.model.pk

#     @property
#     def _c(self) -> ColumnProxy:
#         return self.model.c

#     @property
#     def default_column(self) -> Column:
#         return self._pk[0] if len(list(self._pk)) > 0 else self._c[0]

#     def ensure_column(self, column: Union[str, Column] = None) -> Column:
#         if isinstance(column, str):
#             column = self._c[column]
#         elif column is None:
#             column = self.default_column
#         return column

#     # TODO: test with and without filter
#     async def agg(
#         self,
#         funcs: Union[Function, List[Function]],
#         filter: Union[str, TextClause] = None,
#     ) -> Dict[str, Union[int, float]]:
#         func_map: Dict[str, Function] = {f.name: f for f in util.ensure_list(funcs)}

#         q = db.select(func_map.values())

#         if filter is not None:
#             if not isinstance(filter, TextClause):
#                 filter = db.text(filter)
#             q = q.where(filter)

#         results: List = await q.gino.one()

#         return dict(zip(func_map, results))

#     async def count(self, filter: Union[str, TextClause] = None) -> int:
#         """ Get the model's rowcount """

#         result = await self.agg(db.func.count(self.default_column), filter=filter)
#         return util.reduce(result.values())

#     async def max(
#         self, column: Union[str, Column] = None, filter: Union[str, TextClause] = None
#     ) -> int:
#         """ Get the maximum value of the given column.  If no column is specified,
#             the max value of the first primary key column is returned.
#         """

#         func: Function = db.func.max(self.ensure_column(column))
#         result = await self.agg(func, filter=filter)
#         return util.reduce(result.values())

#     async def min(
#         self, column: Union[str, Column] = None, filter: Union[str, TextClause] = None
#     ) -> int:
#         """ Get the minimum value of the given column.  If no column is specified,
#             the min value of the first primary key column is returned.
#         """

#         func: Function = db.func.min(self.ensure_column(column))
#         result = await self.agg(func, filter=filter)
#         return util.reduce(result.values())
