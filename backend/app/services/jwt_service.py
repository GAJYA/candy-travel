from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.config import settings

ALGORITHM = "HS256"


class JwtError(Exception):
    """JWT 解码 / 校验失败的统一异常"""


def issue_token(user_id: UUID) -> tuple[str, int]:
    """签发 access token，返回 (token, expires_in_seconds)"""
    now = datetime.now(UTC)
    expire_seconds = settings.jwt_expire_days * 24 * 3600
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expire_seconds)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return token, expire_seconds


def decode_token(token: str) -> UUID:
    """解码 token 并返回 user_id；任何失败都抛 JwtError"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as e:
        raise JwtError("token expired") from e
    except jwt.InvalidTokenError as e:
        raise JwtError(f"invalid token: {e}") from e

    sub = payload.get("sub")
    if not sub:
        raise JwtError("token missing sub")
    try:
        return UUID(sub)
    except ValueError as e:
        raise JwtError("token sub not a valid uuid") from e
