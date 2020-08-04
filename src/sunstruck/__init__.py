import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

import config as conf
from db import db

logger = logging.getLogger(__name__)


app: FastAPI = FastAPI(
    title=conf.project,
    version=conf.version,
    openapi_url="/api/v1/openapi.json",
    docs_url="/swagger",
    redoc_url="/docs",
    default_response_class=ORJSONResponse,
    debug=conf.DEBUG,
)


db.init_app(app)


# @app.on_event("startup")
# async def startup():  # nocover (implicitly tested with test client)
#     """ Event hook to run on web process startup """

#     await db.startup()


# @app.on_event("shutdown")
# async def shutdown():  # nocover (implicitly tested with test client)
#     """ Event hook to run on web process shutdown """

#     await db.shutdown()


if __name__ == "__main__":

    async def wrapper():
        #
        #
        from db.models import ReadingByMinute
        from db import db

        await db.startup()
        await ReadingByMinute.query.gino.all()
