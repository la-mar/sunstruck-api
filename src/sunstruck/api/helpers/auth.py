from typing import Optional

from fastapi import Depends, Form, HTTPException, Request, status
from fastapi.security import oauth2
from jose import jwt
from pydantic import ValidationError

import config as conf
import util.security as security
from config import API_V1
from db.models import User
from schemas import TokenPayload


class OAuth2PasswordClientCredentials(oauth2.OAuth2):
    """ Authenticate with OAuth2 Password flow (username/password) OR Client Credentials
        (client_id/client_secret).

    fastapi ref: https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py
     """

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):

        flows = oauth2.OAuthFlowsModel(
            password={"tokenUrl": tokenUrl, "scopes": scopes or {}},
            clientCredentials={"tokenUrl": tokenUrl, "scopes": scopes or {}},
        )
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = oauth2.get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


oauth2_authorizer = OAuth2PasswordClientCredentials(
    tokenUrl=f"{API_V1}/login/access-token"
)


async def get_current_user(token: str = Depends(oauth2_authorizer)) -> User:
    try:
        payload = jwt.decode(
            token, str(conf.SECRET_KEY), algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await User.get(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


class OAuth2RequestForm:
    """
    Dependency copied from fastapi.security.OAuth2RequestForm and modified to
    accomodate the OAuth2 password and client_credentials flows. Thus, it will
    accept username/password and client_id/client_secret for authentication; however,
    the grant_type must be specified.

    fastapi ref: https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py

    The dependency creates the following Form request parameters in your endpoint:

    grant_type {str} -- OAuth2 flow: "password" or "client_credentials"
        (default: Form(..., regex="password|client_credentials"))
    username {str} -- username for authentication (default: Form(None))
    password {str} -- password for authentication (default: Form(None))
    scope {str} -- space delimited OAuth2 scopes
        e.g. "profile openid users:read settings:write" (default: Form(""))
    client_id {Optional[str]} -- client id for authentication (default: Form(None))
    client_secret {Optional[str]} -- client secret for authentication (default: Form(None))


    """

    def __init__(
        self,
        grant_type: str = Form(..., regex="password|client_credentials"),
        username: str = Form(None),
        password: str = Form(None),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):

        self.grant_type = grant_type
        self.username = username
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


class OAuth2ClientRequestForm:
    # ref: https://github.com/tiangolo/fastapi/blob/da9b5201c4a021b04bb3a59247c5b9a57a8c3144/fastapi/security/oauth2.py#L13  # noqa

    """ Dependency to inject OAuth2 Client Credentials fields into an endpoint.

    Keyword Arguments:
        grant_type {str} -- OAuth2 grant_type (default: Form(None, regex="client_credentials"))
        scope {str} -- space separated scope identifier.
            e.g. "resource:read resource2:write profile" (default: Form(""))
        client_id {Optional[str]} -- OAuth2 client_id (default: Form(...))
        client_secret {Optional[str]} -- OAuth2 client_secret (default: Form(...))
    """

    def __init__(
        self,
        grant_type: str = Form(None, regex="client_credentials"),
        scope: str = Form(""),
        client_id: Optional[str] = Form(...),
        client_secret: Optional[str] = Form(...),
    ):

        self.grant_type = grant_type
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret
