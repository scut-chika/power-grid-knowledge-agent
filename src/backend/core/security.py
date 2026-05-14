import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.backend.core.config import settings

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password


def create_access_token(username: str, role: str, expires_minutes: int = 120) -> str:
    payload = {
        'sub': username,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm='HS256')


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=['HS256'])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='无效token') from exc


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='缺少认证信息')
    from src.backend.core.db import get_user_by_username

    payload = decode_token(credentials.credentials)
    user = get_user_by_username(payload['sub'])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='用户不存在')
    return user


def require_admin(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if user['role'] != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='需要管理员权限')
    return user
