import logging
from datetime import timedelta
from typing import Optional

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
    """ OAuth2 compatible token login, get an access token for future requests """

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
async def user_signup(
    username: str = Body(...),
    password: str = Body(...),
    email: EmailStr = Body(...),
    first_name: str = Body(None),
    last_name: str = Body(None),
):
    """ Create new user without the need to be logged in. """

    if not conf.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Signup is disabled",
        )
    user = await ORMUser.get_by_email(email)

    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username taken",
        )

    user_data = UserCreateIn(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    user = await ORMUser.create(**user_data.dict(exclude_unset=True))
    return user


@router.post("/recover-password", response_model=Message)
async def recover_password(
    username: Optional[str] = Body(None), email: Optional[str] = Body(None)
):
    """ Password recovery """

    message = "Password recovery email was sent"
    user = await ORMUser.get_by_email(email)

    if not user:
        # NOTE: Avoid indicating if the user actually exists in the response
        logger.info(
            "Password recovery request submitted for non-existent account",
            extra={"username": username, "email": email},
        )
        return {"message": message}

    password_reset_token = security.generate_password_reset_token(
        email=email, secret=user.hashed_password
    )
    security.send_reset_password_email(
        email_to=user.email,
        email=email,
        token=password_reset_token,
        #
    )

    return {"message": message}


@router.post("/reset-password", response_model=Message)
async def reset_password(token: str = Body(...), new_password: str = Body(...)):
    """ Reset password """
    email = security.get_unverified_subject(token)

    log_extras = {"email": email}

    if not email:
        logger.info("Password reset failed: invalid token", extra=log_extras)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = await ORMUser.get_by_email(email)
    if not user:
        logger.info("Password reset failed: user doesn't exist", extra=log_extras)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Password update failed",
        )

    elif not user.is_active:
        logger.info("Password reset failed: user is inactive", extra=log_extras)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Password update failed"
        )

    token_content = security.verify_password_reset_token(
        token, secret=user.hashed_password
    )

    if token_content:
        hashed_password = security.get_password_hash(new_password)
        await user.update(hashed_password=hashed_password).apply()
        logger.info("Password reset succeeded", extra=log_extras)
        return {"message": "Password update successful"}
    else:
        logger.info("Password reset failed: failed to validate token", extra=log_extras)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
