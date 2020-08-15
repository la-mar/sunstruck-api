import logging
import re
from typing import Any, Callable, Dict, List, Optional

from pydantic import parse_obj_as
from sqlalchemy import and_
from sqlalchemy.sql.elements import BinaryExpression, ClauseList
from sqlalchemy.sql.schema import Column

from db.models import Model
from schemas.query_filter import FilterParam, FilterParams

logger = logging.getLogger(__name__)

regex = r"""
        # (?:\?filter=)?
        (?P<conjunctive>[:|]?)
        (?P<field_name>[:|]?\w+[^:|'\"])?
        (?P<sep>[:|])
        (?P<inverter>~)?
        (?P<operator>eq|gte|gt|lte|lt|in|between|regex|like|is})
        (?=:(?P<value>
        (?P<quoted>['\"][^'\"\\]*(?:\\.[^'\\]*)*['\"])
        |
        (?:(?P<unquoted>[^:|\s]*[^'\":|\s]))
        ))
        """

PATTERN = re.compile(regex, re.VERBOSE)

OPERATIONS: Dict[str, Callable[[Column, Any], BinaryExpression]] = {
    "is": lambda column, value: column.is_(value),
    "eq": lambda column, value: column == value,
    "gt": lambda column, value: column > value,
    "gte": lambda column, value: column >= value,
    "lt": lambda column, value: column < value,
    "lte": lambda column, value: column <= value,
    "like": lambda column, value: column.like(value),
    "in": lambda column, value: column.in_(value),
    "between": lambda column, value: column.between(*value),
    "~is": lambda column, value: column.isnot_(value),
    "~eq": lambda column, value: column != value,
    "~like": lambda column, value: column.notlike(value),
    "~in": lambda column, value: column.notin_(value),
}


class Filter:
    # Dependency for injection

    def __init__(self, model: Model):
        self.model = model
        self.column_map = self.model.c.dict()

    def __call__(self, filter: str) -> ClauseList:
        return self.translate(self.parse(filter))

    @staticmethod
    def parse(s: str) -> List[FilterParam]:
        records = [dict(zip(PATTERN.groupindex, m)) for m in PATTERN.findall(s)]
        return FilterParams(params=records).params

    def translate(self, filters: List[FilterParam]) -> ClauseList:
        """ Translate the given list of filters to a sqlalchemy predicate.

        Parameters
        ----------
        filters : List[FilterParam]
            list of filter parameter objects

        Returns
        -------
        sqlalchemy.elements.ClauseList
            completed predicate, ready to be passed to
            sqlalchemy (e.g. .filter(predicate)) or
            gino (e.g. .where(predicate))
        """

        group_conjunctive = and_
        expressions = []
        field_name: Optional[str] = None
        expression_group: List[BinaryExpression] = []
        for filt in filters:
            if filt.field_name is not None:

                # start of new filter
                if filt.field_name != field_name:

                    # progressed to another field's filter
                    if len(expression_group) > 0:
                        expressions.append(group_conjunctive(*expression_group))

                    expression_group = []

                # field_name changed. update it's ref
                field_name = filt.field_name

            else:  # field_name is None
                # filter is a chained filter on the same field, so
                # carry the previous field name forward
                pass

            if filt.conjunctive is not None:
                if filt.conjunctive != group_conjunctive:
                    if len(expression_group) > 0:
                        expressions.append(group_conjunctive(*expression_group))
                    expression_group = []

                group_conjunctive = filt.conjunctive
                logger.debug(f"group={group_conjunctive.__name__}")

            sep = filt.conjunctive or filt.sep
            if filt.sep is not None:
                # if sep != conjunctive:
                #     if len(expression_group) > 0:
                #         expressions.append(conjunctive(*expression_group))
                #     expression_group = []

                # conjunctive changed. update it's ref
                group_conjunctive = sep
                logger.debug(f"{group_conjunctive.__name__}")

            column = self.column_map[field_name]

            if filt.operator in ["in", "like", "between"]:
                # parse as list of items
                value = [
                    parse_obj_as(column.type.python_type, v)
                    for v in filt.value.strip('"').split(",")
                ]
            else:
                # parse as scalar item
                value = parse_obj_as(column.type.python_type, filt.value)

            op = f"{filt.inverter or ''}{filt.operator}"
            expression: BinaryExpression = OPERATIONS[op](column, value)
            expression_group.append(filt.sep(expression))
            logger.debug([str(x) for x in expression_group])

        # capture remainder
        if len(expression_group) > 0:
            expressions.append(group_conjunctive(*expression_group))

        # completed predicate, ready to be passed to
        # sqlalchemy (e.g. .filter(predicate)) or
        # gino (e.g. .where(predicate))
        predicate = and_(*expressions)
        logger.debug(f"translated filter to sql predicate: {predicate.compile()}")
        return predicate


if __name__ == "__main__":
    s = 'id:lte:5:gte:4|lt:6|is_superuser:~in:false,false|is:true:updated_at:between:"1929-01-01T17:22:20.937752,2020-01-31T17:22:20.937752"'  # noqa

    from db import db
    from db.models import User

    async def wrapper():

        await db.startup()

        filter = Filter(User)
        # self = filter

        filters = filter.parse(s)
        predicate = filter.translate(filters)

        # dir(db)
        # dir(User.id)
        # predicate = db.and_(User.id.in_([1, 2, 3]))

        await User.query.where(predicate).gino.all()
