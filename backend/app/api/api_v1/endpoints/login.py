from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.api.deps import get_db

router = APIRouter()

@router.post("/login/access-token")
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db)
) -> Any:
    """
    获取JWT访问令牌
    """
    # 简化版本：这里应该查询数据库验证用户
    # 使用固定的测试用户
    username = "testuser"
    hashed_password = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "password"
    
    if form_data.username != username or not verify_password(form_data.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/login/test-token")
async def test_token(current_user = Depends(get_db)) -> Any:
    """
    测试访问令牌
    """
    return current_user 