# from pathlib import Path


import asyncio

import loggers
from db import db
from db.models import User
from tests.utils import seed_model

loggers.config(30)


async def seed_models():

    await db.startup()

    await seed_model(User)


def run():
    asyncio.run(seed_models())


if __name__ == "__main__":

    run()
