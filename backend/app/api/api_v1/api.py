from fastapi import APIRouter
from app.api.api_v1.endpoints import login, users, analysis, data

api_router = APIRouter()
api_router.include_router(login.router, tags=["登录"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(data.router, prefix="/data", tags=["数据"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["分析任务"]) 