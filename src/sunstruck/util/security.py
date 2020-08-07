import logging
from datetime import timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext

import config as conf
from util.dt import utcnow

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None, secret: str = None
) -> str:
    """ Generate a JWT access token.

    Arguments:
        subject {Union[str, Any]} -- the subject of the key's purpose.

    Keyword Arguments:
        expires_delta {timedelta} -- duration the key should remain active (default: {None})
        secret {str} -- an extra secret to augment the system-wide secret key.
            For example, a user's email address or hashed_password. (default: {None})


    Returns:
        str -- [description]
    """
    expire = utcnow() + (
        expires_delta or timedelta(minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject)}
    secret = conf.SECRET_KEY + (secret or "")
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str, secret: str = None) -> Dict[str, Union[str, int]]:
    return jwt.decode(token, conf.SECRET_KEY + (secret or ""), algorithms=[ALGORITHM])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_password_reset_token(
    email: str, expires_delta: timedelta = None, secret: str = None
) -> str:
    """ Generate a one-time use token for password reset. The generated token
        is comprised of three keys:
            - exp (expiration): the point in time that the token expires.
            - nbf (not before): the point in time that this token becomes active.
            - sub (subject): the subject of the token.

        The value of each key is calculated as follows:

            - exp = utcnow + offset of a few minutes into the future
                - the value of offset is determined by the EMAIL_RESET_TOKEN_EXPIRE_MINUTES
                  configuration setting.
            - nbf = utcnow
            - sub = the email parameter, which is the user's email address.

        Example of the token's structure, once decoded:
            {
                'exp': 1596733678,
                'nbf': 1596732778,
                'sub': 'user@example.com'
            }

    Arguments:
        email {str} -- the user's email address

    Keyword Arguments:
        secret {str} -- an extra secret to augment the system-wide secret key.
            For example, a user's email address or hashed_password. (default: {None})

    Returns:
        str -- a signed JWT token
    """

    # nbf: https://tools.ietf.org/html/rfc7519#section-4.1.5

    now = utcnow()
    expire = now + (
        expires_delta or timedelta(minutes=conf.EMAIL_RESET_TOKEN_EXPIRE_MINUTES)
    )
    content = {"exp": expire, "nbf": now, "sub": email}
    secret = conf.SECRET_KEY + (secret or "")

    return jwt.encode(content, secret, algorithm=ALGORITHM)


def verify_password_reset_token(token: str, secret: str = None) -> Optional[Dict]:
    """ Verify the authenticity of a password reset token.

    Arguments:
        token {str} -- encoded JWT token. The decoded token should have all of the
            following keys: exp, nbf, and sub.

    Keyword Arguments:
        secret {str} -- an extra secret to augment the system-wide secret key.
            For example, a user's email address or hashed_password. (default: {None})

    Returns:
        Optional[str] -- the requesting user's email address, if verification
            was successful.
    """
    try:
        content = decode_token(token, secret=secret)
        return content
    except jwt.JWTError as e:
        using_extra_secret = secret is not None
        logger.info(f"{e.__class__.__name__}: {e} ({using_extra_secret=})")
        return None


def get_unverified_subject(token: str) -> Optional[str]:
    try:
        return jwt.get_unverified_claims(token).get("sub")
    except jwt.JWTError as e:
        logger.info(f"{e.__class__.__name__}: {e}")
        return None


def send_email(
    email_to: str,
    subject_template: str = "",
    html_template: str = "",
    environment: Dict[str, Any] = {},
) -> None:
    assert conf.EMAILS_ENABLED, "no provided configuration for email variables"
    # message = emails.Message(
    #     subject=JinjaTemplate(subject_template),
    #     html=JinjaTemplate(html_template),
    #     mail_from=(conf.EMAILS_FROM_NAME, conf.EMAILS_FROM_EMAIL),
    # )
    # smtp_options = {"host": conf.SMTP_HOST, "port": conf.SMTP_PORT}
    # if conf.SMTP_TLS:
    #     smtp_options["tls"] = True
    # if conf.SMTP_USER:
    #     smtp_options["user"] = conf.SMTP_USER
    # if conf.SMTP_PASSWORD:
    #     smtp_options["password"] = conf.SMTP_PASSWORD
    # response = message.send(to=email_to, render=environment, smtp=smtp_options)
    # logging.info(f"send email result: {response}")


def send_test_email(email_to: str) -> None:
    project_name = conf.project
    subject = f"{project_name} - Test email"
    logger.warning(f"{subject=}")
    # with open(Path(conf.EMAIL_TEMPLATES_DIR) / "test_email.html") as f:
    #     template_str = f.read()
    # send_email(
    #     email_to=email_to,
    #     subject_template=subject,
    #     html_template=template_str,
    #     environment={"project_name": conf.project, "email": email_to},
    # )


def send_reset_password_email(email_to: str, email: str, token: str) -> None:
    project_name = conf.project
    subject = f"{project_name} - Password recovery for user {email}"
    logger.warning(f"{subject=}")
    # with open(Path(conf.EMAIL_TEMPLATES_DIR) / "reset_password.html") as f:
    #     template_str = f.read()
    # server_host = conf.SERVER_HOST
    # link = f"{server_host}/reset-password?token={token}"
    # send_email(
    #     email_to=email_to,
    #     subject_template=subject,
    #     html_template=template_str,
    #     environment={
    #         "project_name": conf.project,
    #         "username": email,
    #         "email": email_to,
    #         "valid_hours": conf.EMAIL_RESET_TOKEN_EXPIRE_MINUTES,
    #         "link": link,
    #     },
    # )
