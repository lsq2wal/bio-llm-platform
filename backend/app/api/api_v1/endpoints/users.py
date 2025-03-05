from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user, get_db

router = APIRouter()

@router.get("/me", response_model=dict)
async def read_users_me(
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    获取当前用户信息
    """
    return current_user

@router.get("/", response_model=List[dict])
async def read_users(
    db = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    获取用户列表（仅管理员）
    """
    # 简化版：实际应验证用户是否有管理员权限
    users = [
        {"id": 1, "username": "testuser", "email": "test@example.com", "is_active": True},
        {"id": 2, "username": "testuser2", "email": "test2@example.com", "is_active": True}
    ]
    return users[skip : skip + limit] 