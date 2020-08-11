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


class PaginationMeta(type):
    """ Pagination dependency metaclass to enable easy extension of default
        (class level) parameters.


    Example:

    >>> class CustomPagination(Pagination):
            default_limit = 3  # override default_limit

    >>> app = FastAPI()

    >>> @app.get("/")
        async def pager(pagination: CustomPagination = Depends()):
            response = await pagination.paginate(Model, serializer=ModelSchema)
            return response


    ### References:
    - https://stackoverflow.com/questions/34781840/using-new-to-override-init-in-subclass
    - https://github.com/identixone/fastapi_contrib/blob/master/fastapi_contrib/pagination.py

    """

    def __new__(meta, name, bases, namespace, *args, **kwargs):
        cls = super(PaginationMeta, meta).__new__(meta, name, bases, namespace)
        init_ref = cls.__init__

        def __init__(
            self,
            request: Request,
            offset: int = Query(
                default=cls.default_offset,
                ge=0,
                description="Offset the results returned by this number.",
                example="offset=45",
            ),
            limit: int = Query(
                default=cls.default_limit,
                ge=-1,
                le=cls.max_limit,
                description="Limit the number of results returned to this number.",
                example="limit=50",
            ),
            filter: str = Query(
                default=cls.default_filter,
                description="Provide a SQL-type predicate to filter the results",
                example="field_name<=10",
            ),
            sort: str = Query(
                default=cls.default_sort,
                description="Field to sort the results by.",
                example="sort=id",
            ),
            desc: bool = Query(
                default=cls.default_desc,
                description="Results should be sorted in descending order.",
                example="desc=false",
            ),
        ):
            init_ref(self, request, offset, limit, filter, sort, desc)

        cls.__init__ = __init__
        return cls


class Pagination(metaclass=PaginationMeta):
    """ Paging dependency for endpoints """

    default_offset = 0
    default_limit = 25
    max_limit: int = 1000
    default_filter: Optional[str] = None
    default_sort: str = ""
    default_desc: bool = True

    def __init__(
        self,
        request: Request,
        offset: int = 0,
        limit: int = 0,
        filter: str = "",
        sort: str = "",
        desc: bool = True,
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
        """ Generate a URI to the next page of the queried resource, if it exists.

        Returns:
            Optional[str] -- string URL or None (e.g. http://example.com/?limit=10&offset=30)
        """

        if self.offset + self.limit >= count or self.limit <= 0:
            #  Currently on last page of results, or no limit is in effect.
            return None

        #  ADD the current offset to limit to build the url for the next page
        return str(
            self.request.url.include_query_params(
                limit=self.limit, offset=self.offset + self.limit
            )
        )

    def get_previous_url(self) -> Optional[str]:
        """ Generate a URI to the previous page of the queried resource, if it exists.

        Returns:
            Optional[str] -- string URL or None (e.g. http://example.com/?limit=10&offset=10)
        """

        if self.offset <= 0:
            #  No offset is in effect
            return None

        if self.offset - self.limit <= 0:
            #  Currently on first page of results
            return str(self.request.url.remove_query_params(keys=["offset"]))

        #  SUBTRACT the current offset from limit to build the url for the previous page
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
        """ Create a paginated response body with prev/next links and total count
            added to body's root.  The records fulfilling the paginated query are
            placed under the "data" key.

            Example:
            {
                "count": 50,
                "next": "http://example.com/?limit=10&offset=30",
                "prev": "http://example.com/?limit=10&offset=10",
                "data": {...},
            }


        Arguments:
            model {Model} -- SQLAlchemy data model or equivalent

        Keyword Arguments:
            serializer {Optional[PydanticModel]} -- Pydantic model to use when
                serializing the resulting records. (default: None)
            filter {Optional[str]} -- filter to apply to the SQL query
                (e.g. id<15 and created_at=2020-01-01).  (default: {None})

        Returns:
            dict -- response body with embedded pagination parameters
        """
        self.model = model
        filter = filter if filter is not None else self.filter

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

        Example:
        (
            [
                {"id": 20, "name": "bob", "created_at": "1975-08-11T20:16:11.337408+00:00"},
                ...
                {"id": 29, "name": "steve", "created_at": "1932-05-18T05:03:55.094191+00:00"},
            ],
            {
                "x-total-count": 50,
                "link": [
                    '<http://example.com/?limit=10&offset=10>; rel="prev"',
                    '<http://example.com/?limit=10&offset=30>; rel="next"'
                ]
            }
        )


        Arguments:
            model {Model} -- SQLAlchemy data model or equivalent

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
            #  Add previous URL to link header
            headers["link"].append(LINK_TEMPLATE.format(url=p["prev"], rel="prev"))

        if p["next"] is not None:
            #  Add next URL to link header
            headers["link"].append(LINK_TEMPLATE.format(url=p["next"], rel="next"))

        return p["data"], headers

    def set_headers(self, response: Response, headers: Dict):
        response.headers["x-total-count"] = str(headers["x-total-count"])
        response.headers["link"] = ",".join(
            [x for x in headers["link"] if x is not None]
        )
        return response
