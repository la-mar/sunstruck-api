from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import oauth2
from jose import jwt
from pydantic import ValidationError

import config as conf
import util.security as security
from config import API_V1
from db.models import User
from schemas import TokenPayload

oauth2_password = oauth2.OAuth2PasswordBearer(tokenUrl=f"{API_V1}/login/access-token")


async def get_current_user(token: str = Depends(oauth2_password)) -> User:
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


class Oauth2ClientCredentials(oauth2.OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):

        flows = oauth2.OAuthFlowsModel(
            clientCredentials={"tokenUrl": tokenUrl, "scopes": scopes or {}}
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


oauth2_client_credentials = Oauth2ClientCredentials(tokenUrl=f"{API_V1}/login/???????")
