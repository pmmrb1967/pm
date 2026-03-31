import secrets
import time
from typing import Annotated

from fastapi import Header, HTTPException

# token -> (username, issued_at)
_tokens: dict[str, tuple[str, float]] = {}

_USERNAME = "user"
_PASSWORD = "password"
_TOKEN_TTL = 8 * 3600  # 8 hours


def create_token(username: str) -> str:
    token = secrets.token_hex(32)
    _tokens[token] = (username, time.monotonic())
    return token


def validate_credentials(username: str, password: str) -> bool:
    return username == _USERNAME and password == _PASSWORD


def get_username(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.removeprefix("Bearer ")
    entry = _tokens.get(token)
    if not entry:
        raise HTTPException(status_code=401, detail="Invalid token")
    username, issued_at = entry
    if time.monotonic() - issued_at > _TOKEN_TTL:
        del _tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")
    return username
