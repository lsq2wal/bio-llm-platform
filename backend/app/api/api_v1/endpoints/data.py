from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db

router = APIRouter()

class DataItem(BaseModel):
    id: str
    filename: str
    data_type: str
    description: Optional[str] = None
    upload_time: str
    size: int
    user: str

@router.get("/", response_model=List[DataItem])
async def list_data(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    data_type: Optional[str] = Query(None, description="按数据类型筛选")
) -> Any:
    """
    获取用户上传的数据列表
    """
    # 简化版：实际应从数据库中查询
    data_items = [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "sample1.h5ad",
            "data_type": "sc_rnaseq",
            "description": "肺癌患者的单细胞RNA测序数据",
            "upload_time": "2023-07-15T10:30:00",
            "size": 256000000,
            "user": current_user["username"]
        },
        {
            "id": "223e4567-e89b-12d3-a456-426614174001",
            "filename": "sample2.h5ad",
            "data_type": "sc_rnaseq",
            "description": "健康对照组的单细胞RNA测序数据",
            "upload_time": "2023-07-16T14:20:00",
            "size": 245000000,
            "user": current_user["username"]
        }
    ]
    
    # 按数据类型筛选
    if data_type:
        data_items = [item for item in data_items if item["data_type"] == data_type]
    
    return data_items[skip : skip + limit]

@router.get("/{data_id}", response_model=DataItem)
async def get_data(
    data_id: str,
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    获取指定数据项的详情
    """
    # 简化版：实际应从数据库查询
    data_item = {
        "id": data_id,
        "filename": "sample1.h5ad",
        "data_type": "sc_rnaseq",
        "description": "肺癌患者的单细胞RNA测序数据",
        "upload_time": "2023-07-15T10:30:00",
        "size": 256000000,
        "user": current_user["username"]
    }
    return data_item

@router.delete("/{data_id}", response_model=dict)
async def delete_data(
    data_id: str,
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    删除指定数据项
    """
    # 简化版：实际应从数据库和文件系统中删除
    return {"status": "success", "message": f"数据 {data_id} 已成功删除"} 