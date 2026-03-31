import secrets
from typing import Annotated

from fastapi import Header, HTTPException

_tokens: dict[str, str] = {}

_USERNAME = "user"
_PASSWORD = "password"


def create_token(username: str) -> str:
    token = secrets.token_hex(32)
    _tokens[token] = username
    return token


def validate_credentials(username: str, password: str) -> bool:
    return username == _USERNAME and password == _PASSWORD


def get_username(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.removeprefix("Bearer ")
    username = _tokens.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username
