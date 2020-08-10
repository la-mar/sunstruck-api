import logging
from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic.networks import EmailStr

import config as conf
import util.security as security
from api.helpers.auth import OAuth2RequestForm, get_current_active_user
from db.models import OAuth2Client, User
from schemas import (
    ClientCredentialsCreateIn,
    ClientCredentialsOut,
    Message,
    Token,
    UserCreateIn,
    UserOut,
)

logger = logging.getLogger(__name__)

# TODO: thorough logging on all endpoints

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
async def login_access_token(form_data: OAuth2RequestForm = Depends()):
    """ OAuth2 compatible token login, get an access token for future requests """

    if form_data.grant_type == "password":
        user = await User.authenticate(
            email_or_username=form_data.username, password=form_data.password
        )
    elif form_data.grant_type == "client_credentials":
        user = await OAuth2Client.authenticate(
            client_id=form_data.client_id, client_secret=form_data.client_secret
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="missing grant_type"
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


@router.get(
    "/credentials",
    response_model=List[ClientCredentialsOut],
    response_model_exclude_none=True,
)
async def list_client_credentials(
    current_user: User = Depends(get_current_active_user),
):
    """ Create a new set of client credentials """

    return await OAuth2Client.get_by_owner(current_user.id)


@router.post(
    "/credentials",
    response_model=ClientCredentialsOut,
    response_model_exclude_none=True,
)
async def create_client_credentials(
    current_user: User = Depends(get_current_active_user),
):
    """ Create a new set of client credentials """

    credentials = ClientCredentialsCreateIn()
    new = (
        await OAuth2Client.create(**credentials.dict(), owner_id=current_user.id)
    ).to_dict()
    new["client_secret"] = credentials.client_secret
    return new


@router.delete("/credentials", response_model=Message)
async def delete_client_credentials(
    client_id: str, current_user: User = Depends(get_current_active_user),
):
    """ Create a new set of client credentials """

    credentials = await OAuth2Client.get_by_client_id(client_id)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="credentials not found"
        )

    await credentials.delete()
    return {"message": "client_id successfully deleted"}


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
    user = await User.get_by_email(email)

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
    user = await User.create(**user_data.dict(exclude_unset=True))
    return user


@router.post("/recover-password", response_model=Message)
async def recover_password(
    username: Optional[str] = Body(None), email: Optional[str] = Body(None)
):
    """ Password recovery """

    message = "Password recovery email was sent"
    user = await User.get_by_email(email)

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

    user = await User.get_by_email(email)
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
