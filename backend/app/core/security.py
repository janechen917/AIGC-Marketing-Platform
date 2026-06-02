"""JWT 鉴权 + 密码哈希工具。

对外暴露：
- hash_password / verify_password   — bcrypt
- create_access_token               — 生成 JWT
- decode_access_token               — 解码/校验 JWT
- get_current_user                  — FastAPI Depends，返回当前登录 User
- require_admin                     — FastAPI Depends，要求 admin 角色
"""
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db

if TYPE_CHECKING:
    from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------- 密码 ----------

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------- JWT ----------

def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """解码 JWT，失败抛出 InvalidTokenError。"""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])


# ---------- 依赖项 ----------

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> "User":
    from app.models.user import User  # 避免循环导入

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="凭证无效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise credentials_exc

    user: User | None = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exc
    return user


def require_admin(
    current_user: Annotated["User", Depends(get_current_user)],
) -> "User":
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user
