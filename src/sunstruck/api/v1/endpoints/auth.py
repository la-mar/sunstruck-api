import logging
from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic.networks import EmailStr

import config as conf
import util.security as security
from db.models import User as ORMUser
from schemas import Message, Token, UserCreateIn, UserOut

logger = logging.getLogger(__name__)

# TODO: thorough logging on all endpoints

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
async def login_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """

    user = await ORMUser.authenticate(
        email_or_username=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )
    access_token_expires = timedelta(minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/signup", response_model=UserOut)
async def create_user_open(
    password: str = Body(...),
    email: EmailStr = Body(...),
    first_name: str = Body(None),
    last_name: str = Body(None),
):
    """
    Create new user without the need to be logged in.
    """
    if not conf.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Open signup is disabled",
        )
    user = await ORMUser.get_by_email(email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists",
        )
    user_in = UserCreateIn(
        password=password, email=email, first_name=first_name, last_name=last_name
    )
    user = await ORMUser.create(**user_in.dict(exclude_unset=True))
    return user


@router.post("/recover-password", response_model=Message)
def recover_password(email: str):
    """
    Password Recovery
    """
    user = ORMUser.get_by_email(email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = security.generate_password_reset_token(email=email)
    security.send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Password recovery email sent"}


@router.post("/reset-password", response_model=Message)
async def reset_password(token: str = Body(...), new_password: str = Body(...)):
    """
    Reset password
    """
    email = security.get_unverified_subject(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = await ORMUser.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )

    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    token_content = security.verify_password_reset_token(
        token, secret=user.hashed_password
    )

    if token_content:
        hashed_password = security.get_password_hash(new_password)
        await user.update(hashed_password=hashed_password).apply()
        return {"msg": "Password updated successfully"}
    else:
        return {"msg": "Password update failed"}
