import loggers
from api.helpers.middlewares import ORJSONMiddleware
from sunstruck import app

loggers.config()


def configure_routers(app):
    import api.v1 as v1

    app.include_router(v1.api_router, prefix="/api/v1")


def configure_middlewares(app):
    app.add_middleware(ORJSONMiddleware)


configure_routers(app)
configure_middlewares(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
