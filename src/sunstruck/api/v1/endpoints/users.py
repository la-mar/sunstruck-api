import logging
from typing import Dict, List

import starlette.status as codes
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse

from api.helpers import Pagination
from db.models import User as ORMUser
from schemas.user import UserCreateIn, UserOut, UserUpdateIn

logger = logging.getLogger(__name__)

router = APIRouter()

ERROR_404: Dict = dict(status_code=codes.HTTP_404_NOT_FOUND, detail="user not found")


@router.post("/", response_model=UserOut)
async def create_user(user: UserCreateIn):
    """
    Create a new user.
    """

    return await ORMUser.create(**user.dict(exclude_unset=True))


@router.get("/", response_model=List[UserOut])
async def list_users(response: ORJSONResponse, pagination: Pagination = Depends()):
    """
    Get a list of users.
    """

    data, headers = await pagination.paginate_links(ORMUser, serializer=None)

    response = pagination.set_headers(response, headers)

    return data


@router.get("/{id}", response_model=UserOut)
async def retrieve_user(id: int):
    """
    Get a single user.
    """
    user: UserOut = await ORMUser.get(id)
    if not user:
        raise HTTPException(**ERROR_404)

    return user


@router.put("/{id}", response_model=UserOut, status_code=codes.HTTP_200_OK)
async def update_user_full(id: int, body: UserUpdateIn):
    """
    Overwrite a user record.
    """
    user: ORMUser = await ORMUser.get(id)
    if not user:
        raise HTTPException(**ERROR_404)

    await user.update(**body.dict()).apply()
    return user


@router.patch("/{id}", response_model=UserOut, status_code=codes.HTTP_200_OK)
async def update_user_partial(id: int, body: UserUpdateIn):
    """
    Update specific attributes of a user.
    """
    user: ORMUser = await ORMUser.get(id)
    if not user:
        raise HTTPException(**ERROR_404)

    await user.update(**body.dict(exclude_unset=True)).apply()
    return user


@router.delete("/{id}", response_model=UserOut)
async def delete_user(id: int):
    """
    Delete a user
    """
    user: ORMUser = await ORMUser.get(id)
    if not user:
        raise HTTPException(**ERROR_404)

    await user.delete()
    return user
