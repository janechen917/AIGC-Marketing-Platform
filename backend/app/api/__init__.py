"""认证 API：注册 / 登录 / 查看当前用户。

端点：
  POST /api/auth/register  — 注册新用户（返回 UserInfo）
  POST /api/auth/login     — 登录（OAuth2 表单，返回 JWT）
  GET  /api/auth/me        — 查看当前登录用户信息
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas import LoginResponse, RegisterRequest, UserInfo

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = User(email=req.email, hashed_password=hash_password(req.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已注册")
    return user


@router.post("/login", response_model=LoginResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    user: User | None = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")
    token = create_access_token(user.id, user.role)
    return LoginResponse(access_token=token, role=user.role)


@router.get("/me", response_model=UserInfo)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user
