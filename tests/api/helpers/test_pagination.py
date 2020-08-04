import logging

import pytest
from async_asgi_testclient import TestClient
from asyncpg.exceptions import UndefinedColumnError
from fastapi import Depends, FastAPI
from httpx import URL
from starlette.requests import Request
from starlette.responses import Response

from api.helpers import Pagination
from db.models import User as Model
from schemas.user import UserOut as ModelSchema
from tests.utils import seed_model

logger = logging.getLogger(__name__)


pytestmark = pytest.mark.asyncio


app = FastAPI()


@app.get("/test/pagination/")
async def pager(pagination: Pagination = Depends(Pagination), id: int = None):
    response = await pagination.paginate(Model, serializer=ModelSchema)
    return response


@app.get("/test/pagination/links/")
async def link_pager(
    response: Response, pagination: Pagination = Depends(Pagination), id: int = None,
):
    data, headers = await pagination.paginate_links(Model, serializer=ModelSchema)

    response.headers["x-total-count"] = str(headers["x-total-count"])
    response.headers["link"] = ",".join([x for x in headers["link"] if x is not None])
    return data


@pytest.fixture
def request_obj():
    yield Request(
        {
            "type": "http",
            "path": "/api/v1/user",
            "query_string": "",
            "headers": {},
            "method": "GET",
            "server": "localhost:8000".split(":"),
            "scheme": "http",
        }
    )


@pytest.fixture(autouse=True)
async def seed_users(bind):
    await seed_model(Model, 30)


class TestPaginationResponse:
    @pytest.mark.parametrize(
        "path,expected_record_count",
        [
            ("/test/pagination/", 25),
            ("/test/pagination/?limit=0", 30),
            ("/test/pagination/?limit=-1", 30),
            ("/test/pagination/?limit=10", 10),
            ("/test/pagination/?limit=10&arbitrary_param=450", 10),
        ],
    )
    async def test_pagination_limits(self, path, expected_record_count):
        async with TestClient(app) as client:
            response = await client.get(path)
            assert response.status_code == 200
            response = response.json()
            assert len(response["data"]) == expected_record_count

    async def test_filtered_paginator(self):
        async with TestClient(app) as client:
            response = await client.get("/test/pagination/?filter=id<16")
            assert response.status_code == 200
            response = response.json()

            assert response["count"] == 15
            assert len(response["data"]) == 15

    async def test_follow_next_link_until_exausted(self):
        async with TestClient(app) as client:
            response = await client.get("/test/pagination/links/?limit=10")
            assert response.status_code == 200

            responses = []
            while response.links.get("next", {}).get("url"):
                assert int(response.headers["x-total-count"]) == 30
                assert len(response.json()) == 10

                url = URL(response.links["next"]["url"])
                next = f"{url.path}?{url.query}"
                logger.debug(next)
                response = await client.get(next)
                responses.append(response)
                assert response.status_code == 200

            # get last one
            assert int(response.headers["x-total-count"]) == 30
            assert len(response.json()) == 10
            responses.append(response)

            assert len(responses) == 3

    async def test_follow_prev_link_until_exausted(self):
        async with TestClient(app) as client:
            response = await client.get("/test/pagination/links/?offset=20&limit=10")
            assert response.status_code == 200
            responses = []
            while response.links.get("prev", {}).get("url"):
                assert int(response.headers["x-total-count"]) == 30
                assert len(response.json()) == 10

                url = URL(response.links["prev"]["url"])
                prev = f"{url.path}?{url.query}"
                logger.debug(prev)
                response = await client.get(prev)
                responses.append(response)
                assert response.status_code == 200

            # get last one
            assert int(response.headers["x-total-count"]) == 30
            assert len(response.json()) == 10
            responses.append(response)

            assert len(responses) == 3


class TestPaginationCore:
    async def test_no_prev_link_on_first_page(self, bind, request_obj):
        limit = 10

        result = await Pagination(
            request_obj, offset=0, limit=limit, sort="created_at", desc=True, filter="",
        ).paginate(Model, serializer=ModelSchema)

        assert result["count"] == 30
        assert result["next"] is not None
        assert result["prev"] is None
        assert len(result["data"]) == limit

    async def test_no_last_link_on_last_page(self, bind, request_obj):
        limit = 10

        result = await Pagination(
            request_obj,
            offset=20,
            limit=limit,
            sort="created_at",
            desc=True,
            filter="",
        ).paginate(Model, serializer=ModelSchema)

        assert result["count"] == 30
        assert result["next"] is None
        assert result["prev"] is not None
        assert len(result["data"]) == limit

    async def test_both_links_exist_on_middling_page(self, bind, request_obj):
        limit = 10

        result = await Pagination(
            request_obj,
            offset=10,
            limit=limit,
            sort="created_at",
            desc=True,
            filter="",
        ).paginate(Model, serializer=ModelSchema)

        assert result["count"] == 30
        assert result["next"] is not None
        assert result["prev"] is not None
        assert len(result["data"]) == limit

    async def test_no_links_on_single_page(self, bind, request_obj):
        limit = 10

        result = await Pagination(
            request_obj,
            offset=0,
            limit=limit,
            sort="created_at",
            desc=True,
            filter="id < 11",
        ).paginate(Model, serializer=ModelSchema)

        assert result["count"] == 10
        assert result["next"] is None
        assert result["prev"] is None
        assert len(result["data"]) == limit

    async def test_filter_filters_results(self, bind, request_obj):
        limit = 3

        result = await Pagination(
            request_obj,
            offset=5,
            limit=limit,
            sort="created_at",
            desc=True,
            filter="id < 16",
        ).paginate(Model, serializer=ModelSchema)

        assert result["count"] == 15
        assert result["next"] is not None
        assert result["prev"] is not None
        assert len(result["data"]) == 3

    async def test_no_serializer(self, bind, request_obj):
        limit = 3

        result = await Pagination(
            request_obj,
            offset=5,
            limit=limit,
            sort="created_at",
            desc=True,
            filter="id <= 15",
        ).paginate(Model, serializer=None)

        assert result["count"] == 15
        assert result["next"] is not None
        assert result["prev"] is not None
        assert len(result["data"]) == 3

    async def test_raise_undefined_column(self, bind, request_obj):
        with pytest.raises(UndefinedColumnError):
            limit = 3

            result = await Pagination(
                request_obj,
                offset=5,
                limit=limit,
                sort="created_at",
                desc=True,
                filter="fake_column <= 15",
            ).paginate(Model, serializer=None)

            assert result["count"] == 15
            assert result["next"] is not None
            assert result["prev"] is not None
            assert len(result["data"]) == 3


class TestPaginationWithLinks:
    async def test_no_prev_link_on_first_page(self, bind, request_obj):
        limit = 10

        result, headers = await Pagination(
            request_obj, offset=0, limit=limit, sort="created_at", desc=True, filter="",
        ).paginate_links(Model, serializer=ModelSchema)

        links = headers["link"]
        next = [x for x in links if 'rel="next"' in x][0]
        prev = [x for x in links if 'rel="prev"' in x]

        assert headers["x-total-count"] == 30
        assert next is not None
        with pytest.raises(IndexError):
            prev[0]

    async def test_no_last_link_on_last_page(self, bind, request_obj):
        limit = 10

        result, headers = await Pagination(
            request_obj,
            offset=20,
            limit=limit,
            sort="created_at",
            desc=True,
            filter="",
        ).paginate_links(Model, serializer=ModelSchema)

        links = headers["link"]
        next = [x for x in links if 'rel="next"' in x]
        prev = [x for x in links if 'rel="prev"' in x][0]

        assert headers["x-total-count"] == 30
        assert prev is not None
        with pytest.raises(IndexError):
            next[0]

    async def test_both_links_exist_on_middling_page(self, bind, request_obj):
        limit = 10

        result, headers = await Pagination(
            request_obj,
            offset=10,
            limit=limit,
            sort="created_at",
            desc=True,
            filter="",
        ).paginate_links(Model, serializer=ModelSchema)

        links = headers["link"]
        next = [x for x in links if 'rel="next"' in x][0]
        prev = [x for x in links if 'rel="prev"' in x][0]

        assert headers["x-total-count"] == 30
        assert prev is not None
        assert next is not None

    async def test_no_links_on_single_page(self, bind, request_obj):
        limit = 10

        result, headers = await Pagination(
            request_obj,
            offset=0,
            limit=limit,
            sort="created_at",
            desc=True,
            filter=f"id <= {limit}",
        ).paginate_links(Model, serializer=ModelSchema)

        links = headers["link"]
        next = [x for x in links if 'rel="next"' in x]
        prev = [x for x in links if 'rel="prev"' in x]

        assert headers["x-total-count"] == limit
        with pytest.raises(IndexError):
            prev[0]
        with pytest.raises(IndexError):
            next[0]

    async def test_filter_filters_results(self, bind, request_obj):
        limit = 3

        result, headers = await Pagination(
            request_obj,
            offset=5,
            limit=limit,
            sort="created_at",
            desc=True,
            filter="id <= 15",
        ).paginate_links(Model, serializer=ModelSchema)

        links = headers["link"]
        next = [x for x in links if 'rel="next"' in x][0]
        prev = [x for x in links if 'rel="prev"' in x][0]

        assert headers["x-total-count"] == 15
        assert prev is not None
        assert next is not None
