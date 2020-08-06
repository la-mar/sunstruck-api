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
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    expire = utcnow() + (
        expires_delta or timedelta(minutes=conf.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, conf.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Union[str, int]]:
    return jwt.decode(token, conf.SECRET_KEY, algorithms=[ALGORITHM])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=conf.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email}, conf.SECRET_KEY, algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = decode_token(token)
        return str(decoded_token["sub"])  # email
    except jwt.JWTError:
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
    #         "valid_hours": conf.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
    #         "link": link,
    #     },
    # )
