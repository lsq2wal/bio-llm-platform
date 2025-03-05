from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
import os

from app.llm.pipeline import LLMAnalysisPipeline
from app.hpc.scheduler import HPCScheduler
from app.api.deps import get_current_user

router = APIRouter()

class AnalysisRequest(BaseModel):
    task_type: str  # 任务类型: "cell_annotation", "gene_perturbation", "pathway_analysis"等
    description: str  # 用户描述的任务需求
    parameters: dict  # 任务特定参数
    data_id: str  # 已上传数据的ID

class AnalysisResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float
    result: Optional[dict] = None
    error: Optional[str] = None

# LLM分析流水线实例
llm_pipeline = LLMAnalysisPipeline()
# HPC调度器实例
hpc_scheduler = HPCScheduler()

@router.post("/submit", response_model=AnalysisResponse)
async def submit_analysis(
    request: AnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    提交分析任务
    """
    try:
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        
        # 使用LLM解析用户需求
        analysis_plan = await llm_pipeline.parse_request(
            request.task_type,
            request.description,
            request.parameters
        )
        
        # 将任务提交到HPC调度系统
        hpc_job_id = await hpc_scheduler.submit_job(
            user=current_user["username"],
            task_id=task_id,
            analysis_plan=analysis_plan,
            data_id=request.data_id
        )
        
        # 保存任务信息到数据库(简化版本)
        # TODO: 实际应保存到数据库
        
        return AnalysisResponse(
            task_id=task_id,
            status="submitted",
            message="分析任务已提交成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交分析任务失败: {str(e)}")

@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取任务状态
    """
    try:
        # 从HPC系统获取作业状态
        job_status = await hpc_scheduler.get_job_status(task_id)
        
        # 构造响应
        return TaskStatus(
            task_id=task_id,
            status=job_status["status"],
            progress=job_status["progress"],
            result=job_status.get("result"),
            error=job_status.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

@router.post("/upload_data", response_model=dict)
async def upload_data(
    file: UploadFile = File(...),
    data_type: str = Form(...),
    description: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    上传生物数据文件
    """
    try:
        # 生成唯一数据ID
        data_id = str(uuid.uuid4())
        
        # 创建保存目录
        os.makedirs(f"data/{current_user['username']}/{data_id}", exist_ok=True)
        
        # 保存上传的文件
        file_path = f"data/{current_user['username']}/{data_id}/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # TODO: 添加到数据库记录
        
        return {
            "data_id": data_id,
            "filename": file.filename,
            "data_type": data_type,
            "status": "uploaded"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传数据失败: {str(e)}") 