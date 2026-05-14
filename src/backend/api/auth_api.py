from fastapi import APIRouter, HTTPException

from src.backend.core.db import get_user_by_username
from src.backend.core.security import create_access_token, verify_password
from src.backend.schemas.auth import LoginRequest

router = APIRouter()


@router.post('/login')
def login(req: LoginRequest) -> dict:
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user['password_hash']):
        raise HTTPException(status_code=401, detail='用户名或密码错误')

    token = create_access_token(user['username'], user['role'])
    return {
        'code': 0,
        'message': 'ok',
        'data': {'token': token, 'role': user['role']},
    }
