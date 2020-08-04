from typing import Callable, Dict

import orjson
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


async def parse_request_body(self) -> Dict:  # nocover
    if not hasattr(self, "_json"):
        body = await self.body()
        self._json = orjson.loads(body)
    return self._json


class ORJSONMiddleware(BaseHTTPMiddleware):
    """ Starlette compatable response and middleware using orjson serializer """

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        response.json = parse_request_body
        return response
