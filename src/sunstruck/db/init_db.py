import logging

import config as conf
from db.models import User
from schemas import UserCreateIn

logger = logging.getLogger(__name__)


async def create_master_user():

    try:
        user = await User.get_by_email(conf.MASTER_USERNAME)

        if not user:

            user_data = UserCreateIn(
                username=conf.MASTER_USERNAME,
                email=conf.MASTER_EMAIL,
                password=conf.MASTER_PASSWORD,
                is_superuser=True,
            )
            user = await User.create(**user_data.dict(exclude_unset=True))
            logger.warning(
                f"Created master user: {conf.MASTER_USERNAME}/{conf.MASTER_EMAIL}"
            )
        else:
            logger.debug("Master user already exists")

    except Exception as e:
        logger.error(f"Failed creating master user: {e}")


async def init_db():
    from db import db

    await db.startup()
    await create_master_user()
    await db.shutdown()
