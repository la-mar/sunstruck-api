import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse

from api.helpers import Pagination
from api.helpers.auth import get_current_active_user
from db.models import User as User
from schemas.user import UserCreateIn, UserOut, UserUpdateIn

logger = logging.getLogger(__name__)

router = APIRouter()

ERROR_404: Dict = dict(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """ Get info about the currrently signed in user. """
    return current_user


@router.post("/", response_model=UserOut)
async def create_user(user: UserCreateIn):
    """ Create a new user. """

    return await User.create(**user.dict())


@router.get("/", response_model=List[UserOut])
async def list_users(response: ORJSONResponse, pagination: Pagination = Depends()):
    """ Get a list of users. """

    data, headers = await pagination.paginate_links(User, serializer=None)

    response = pagination.set_headers(response, headers)

    return data


@router.get("/{id}", response_model=UserOut)
async def retrieve_user(id: int):
    """ Get a single user. """
    user: UserOut = await User.get(id)
    if not user:
        raise HTTPException(**ERROR_404)

    return user


@router.put("/{id}", response_model=UserOut)
async def update_user_full(id: int, body: UserUpdateIn):
    """ Overwrite a user record. """
    user: User = await User.get(id)
    if not user:
        raise HTTPException(**ERROR_404)

    await user.update(**body.dict()).apply()
    return user


@router.patch("/{id}", response_model=UserOut)
async def update_user_partial(id: int, body: UserUpdateIn):
    """ Update specific attributes of a user. """
    user: User = await User.get(id)
    if not user:
        raise HTTPException(**ERROR_404)

    await user.update(**body.dict(exclude_unset=True)).apply()
    return user


@router.delete("/{id}", response_model=UserOut)
async def delete_user(id: int):
    """ Delete a user """
    user: User = await User.get(id)
    if not user:
        raise HTTPException(**ERROR_404)

    await user.delete()
    return user
