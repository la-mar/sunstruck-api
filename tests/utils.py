import contextlib
import logging
import os
import random
import socket
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

from httpx import AsyncClient

import config as conf
from db.models import Model

logger = logging.getLogger(__name__)


def unpack_fixture(fixture: Any, *args, **kwargs) -> Any:
    """ Unpack a fixture for use in interactive debugging """

    if hasattr(fixture, "_pytestfixturefunction"):
        return next(fixture.__wrapped__(*args, **kwargs))  # type: ignore
    else:
        return fixture


def get_open_port():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


async def get_superuser_token_headers(client: AsyncClient) -> Dict[str, str]:
    user_data = {
        "username": conf.MASTER_USERNAME,
        "password": conf.MASTER_PASSWORD,
        #
    }
    response = await client.post("/api/v1/login/access-token", data=user_data)

    token_data = response.json()
    access_token = token_data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


def rand(length: int = None, min: int = None, max: int = None, choices=None):
    n = 8

    if length:
        n = length
    else:
        if not length and min and max:
            n = random.choice(range(min, max + 1))

    return "".join(random.choice(choices) for _ in range(n))


def rand_str(
    length: int = None, min: int = None, max: int = None, choices=string.ascii_letters
):
    return rand(length, min, max, choices)


def rand_int(
    length: int = None, min: int = None, max: int = None, choices=string.digits
):
    return int(rand(length, min, max, choices))


def rand_float(min: float = 0, max: float = 100):
    return random.uniform(min, max)


def rand_lon(min: float = -98.7, max: float = -95):
    return rand_float(min, max)


def rand_lat(min: float = 31.9, max: float = 33.6):
    return rand_float(min, max)


def rand_email(min: int = 5, max: int = 25):
    return f"{rand_str(min=min, max=max)}@hoaxmail.com"


def rand_datetime(min_year=1900, max_year=datetime.now().year):
    start = datetime(min_year, 1, 1, 00, 00, 00)
    years = max_year - min_year + 1
    end = start + timedelta(days=365 * years)
    return start + (end - start) * random.random()


def rand_bool():
    return random.choice([True, False])


def generator_map():
    return {
        datetime: rand_datetime(),
        int: rand_int(min=1, max=9),
        str: rand_str(min=4, max=10),
        float: rand_float(),
        bool: rand_bool(),
        bytes: rand_str(min=300, max=10000).encode(),
        dict: {rand_str(length=4): rand_str(length=4) for x in range(0, 5)},
        list: [rand_str(length=4) for x in range(0, 5)],
    }


def to_bool(value: Optional[str]) -> bool:
    valid = {
        "true": True,
        "t": True,
        "1": True,
        "yes": True,
        "no": False,
        "false": False,
        "f": False,
        "0": False,
    }

    if value is None:
        return False

    if isinstance(value, bool):
        return value

    if not isinstance(value, str):
        raise ValueError("invalid literal for boolean. Not a string.")

    lower_value = value.lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError('invalid literal for boolean: "%s"' % value)


async def seed_model(model: Model, n: int = 10):
    items = []
    pytypes = model.columns.pytypes
    dtypes = model.columns.dtypes
    for i in range(0, n):
        item = {}
        for col_name, col_type in pytypes.items():
            dtype = dtypes[col_name]
            dtype_name = dtype.__class__.__name__
            value = None
            if dtype_name == "ChoiceType":  # handle enums
                value = random.choice(dtype.choices.values())
            elif dtype_name == "EmailType":  # handle enums
                value = rand_email(min=5, max=20)
            elif col_name == "lon":
                value = rand_lon()
            elif col_name == "lat":
                value = rand_lat()
            else:
                value = generator_map()[col_type]

            if col_name not in ["id"]:
                item[col_name] = value
        items.append(item)

    # from util.jsontools import to_string

    # print(to_string(items))
    await model.bulk_insert(items)
    print(f"Created {len(items)} {model.__tablename__}")


@contextlib.contextmanager
def working_directory(p: Union[Path, str]):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(p)
    try:
        yield
    finally:
        os.chdir(prev_cwd)
