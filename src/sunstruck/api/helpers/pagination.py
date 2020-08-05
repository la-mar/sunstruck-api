import logging
from typing import Dict, List, Optional, Tuple, Union

from fastapi import Query
from pydantic import BaseModel as PydanticModel
from sqlalchemy.sql.elements import TextClause
from starlette.requests import Request
from starlette.responses import Response

from db import db
from db.models import Model

logger = logging.getLogger(__name__)

LINK_TEMPLATE = '<{url}>; rel="{rel}"'


class Pagination:
    """ Paging dependency for endpoints """

    default_offset = 0
    default_limit = 25
    max_offset = None
    max_limit = 1000

    def __init__(
        self,
        request: Request,
        offset: int = Query(default=default_offset, ge=0, le=max_offset),
        limit: int = Query(default=default_limit, ge=-1, le=max_limit),
        filter: str = Query(default=None, description=""),
        sort: str = Query(default=""),
        desc: bool = Query(default=True),
    ):

        self.request = request
        self.offset = offset
        self.limit = limit
        self.filter = filter
        self.sort = sort
        self.desc = desc
        self.sort_direction = "desc" if desc else "asc"
        self.model: Model = None

    def get_next_url(self, count: int) -> Optional[str]:
        if self.offset + self.limit >= count or self.limit <= 0:
            return None
        return str(
            self.request.url.include_query_params(
                limit=self.limit, offset=self.offset + self.limit
            )
        )

    def get_previous_url(self) -> Optional[str]:
        if self.offset <= 0:
            return None

        if self.offset - self.limit <= 0:
            return str(self.request.url.remove_query_params(keys=["offset"]))

        return str(
            self.request.url.include_query_params(
                limit=self.limit, offset=self.offset - self.limit
            )
        )

    async def get(
        self,
        filter: Optional[Union[str, TextClause]] = None,
        serializer: Optional[PydanticModel] = None,
    ) -> list:
        """ Build and execute the paged sql query, returning the results as a list of Pydantic
            model instances (if serializer is specified) or dicts (if serializer is NOT specified)
        """
        q = self.model.query
        filter = filter if filter is not None else self.filter

        if filter is not None:
            if not isinstance(filter, TextClause):
                filter = db.text(filter)
            q = q.where(filter)
        if self.limit > 0:
            q = q.limit(self.limit)
        if self.sort:
            q = q.order_by(db.text(f"{self.sort} {self.sort_direction}"))
        result = await q.offset(self.offset).gino.all()

        if serializer:
            return [serializer.from_orm(x) for x in result]
        else:
            return result

    async def paginate(
        self,
        model: Model,
        serializer: Optional[PydanticModel] = None,
        filter: Optional[str] = None,
    ) -> dict:
        self.model = model
        count = await self.model.agg.count(filter)

        return {
            "count": count,
            "next": self.get_next_url(count),
            "prev": self.get_previous_url(),
            "data": await self.get(filter, serializer=serializer),
        }

    async def paginate_links(
        self,
        model: Model,
        serializer: Optional[PydanticModel] = None,
        filter: Optional[str] = None,
    ) -> Tuple[List[Union[Dict, PydanticModel]], Dict[str, Union[int, List]]]:
        """ Paginate using link headers

        Arguments:
            model {Model} -- SQLAlchemy data model

        Keyword Arguments:
            serializer {Optional[PydanticModel]} -- [description] (default: {None})
            filter {Optional[str]} -- textual filter expression
                (e.g. "timestamp > 2020-01-01 and timestamp <= 2020-12-31") (default: {None})

        Returns:
            Tuple[List[Union[Dict, PydanticModel]], Dict[str, Union[int, List]]] --
                Tuple of data and headers
        """
        p = await self.paginate(model=model, serializer=serializer, filter=filter)
        headers = {
            "x-total-count": p["count"],
            "link": [],
        }

        if p["prev"] is not None:
            headers["link"].append(LINK_TEMPLATE.format(url=p["prev"], rel="prev"))

        if p["next"] is not None:
            headers["link"].append(LINK_TEMPLATE.format(url=p["next"], rel="next"))

        return p["data"], headers

    def set_headers(self, response: Response, headers: Dict):
        response.headers["x-total-count"] = str(headers["x-total-count"])
        response.headers["link"] = ",".join(
            [x for x in headers["link"] if x is not None]
        )
        return response
