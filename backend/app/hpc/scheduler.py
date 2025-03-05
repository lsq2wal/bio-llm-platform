import os
import json
import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

class HPCScheduler:
    """多瑙调度器客户端"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = settings.HPC_SCHEDULER_URL
        self.username = settings.HPC_USERNAME
        self.password = settings.HPC_PASSWORD
        self.token = None
        self.token_expires = 0
    
    async def _get_auth_token(self):
        """获取身份验证令牌"""
        if self.token and self.token_expires > asyncio.get_event_loop().time():
            return self.token
        
        async with aiohttp.ClientSession() as session:
            try:
                auth_url = f"{self.base_url}/api/auth/login"
                payload = {
                    "username": self.username,
                    "password": self.password
                }
                
                async with session.post(auth_url, json=payload) as response:
                    if response.status != 200:
                        self.logger.error(f"HPC身份验证失败: {await response.text()}")
                        raise Exception("HPC身份验证失败")
                    
                    data = await response.json()
                    self.token = data["token"]
                    # 令牌24小时过期
                    self.token_expires = asyncio.get_event_loop().time() + 86400
                    return self.token
            except Exception as e:
                self.logger.error(f"获取身份验证令牌失败: {str(e)}")
                raise e
    
    async def submit_job(self, user: str, task_id: str, analysis_plan: Dict[str, Any], data_id: str) -> str:
        """
        向HPC提交分析作业
        
        Args:
            user: 用户名
            task_id: 任务ID
            analysis_plan: 分析计划
            data_id: 数据ID
            
        Returns:
            HPC作业ID
        """
        try:
            token = await self._get_auth_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # 根据分析计划生成作业脚本
            job_script = self._generate_job_script(user, task_id, analysis_plan, data_id)
            
            # 向多瑙调度器提交作业
            async with aiohttp.ClientSession(headers=headers) as session:
                submit_url = f"{self.base_url}/api/jobs"
                payload = {
                    "name": f"bio_analysis_{task_id}",
                    "script": job_script,
                    "queue": "gpu",  # 使用GPU队列
                    "resource_request": {
                        "nodes": 1,
                        "gpus_per_node": 1,  # 请求1个GPU
                        "memory": "64GB"
                    }
                }
                
                async with session.post(submit_url, json=payload) as response:
                    if response.status != 200:
                        self.logger.error(f"提交HPC作业失败: {await response.text()}")
                        raise Exception("提交HPC作业失败")
                    
                    data = await response.json()
                    hpc_job_id = data["job_id"]
                    
                    # 保存任务映射关系到本地(实际应该保存到数据库)
                    self._save_task_mapping(task_id, hpc_job_id)
                    
                    return hpc_job_id
                    
        except Exception as e:
            self.logger.error(f"提交作业失败: {str(e)}")
            raise e
    
    def _generate_job_script(self, user: str, task_id: str, analysis_plan: Dict[str, Any], data_id: str) -> str:
        """生成HPC作业脚本"""
        # 这里根据分析计划生成实际的执行脚本
        # 简化版本，实际应根据分析类型生成不同的脚本
        
        script = f"""#!/bin/bash
#SBATCH --job-name=bio_{task_id}
#SBATCH --output=logs/bio_{task_id}.out
#SBATCH --error=logs/bio_{task_id}.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --mem=64G

# 激活环境
source /opt/conda/bin/activate bio-llm

# 设置数据路径
DATA_PATH="/data/{user}/{data_id}"
OUTPUT_PATH="/results/{user}/{task_id}"
mkdir -p $OUTPUT_PATH

# 保存分析计划
cat > $OUTPUT_PATH/analysis_plan.json << 'EOF'
{json.dumps(analysis_plan, indent=2)}
EOF

# 执行分析
python /app/analysis/run_analysis.py \\
    --task_id {task_id} \\
    --data_path $DATA_PATH \\
    --output_path $OUTPUT_PATH \\
    --config $OUTPUT_PATH/analysis_plan.json

echo "分析完成，结果保存在 $OUTPUT_PATH"
"""
        return script
    
    def _save_task_mapping(self, task_id: str, hpc_job_id: str):
        """保存任务ID与HPC作业ID的映射关系"""
        mapping_file = "task_mappings.json"
        mappings = {}
        
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                mappings = json.load(f)
        
        mappings[task_id] = hpc_job_id
        
        with open(mapping_file, 'w') as f:
            json.dump(mappings, f, indent=2)
    
    async def get_job_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取HPC作业状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            作业状态字典
        """
        try:
            # 获取HPC作业ID
            mapping_file = "task_mappings.json"
            if not os.path.exists(mapping_file):
                return {"status": "unknown", "progress": 0, "error": "任务映射文件不存在"}
            
            with open(mapping_file, 'r') as f:
                mappings = json.load(f)
            
            if task_id not in mappings:
                return {"status": "unknown", "progress": 0, "error": "任务ID不存在"}
            
            hpc_job_id = mappings[task_id]
            
            # 查询HPC作业状态
            token = await self._get_auth_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            async with aiohttp.ClientSession(headers=headers) as session:
                status_url = f"{self.base_url}/api/jobs/{hpc_job_id}"
                
                async with session.get(status_url) as response:
                    if response.status != 200:
                        self.logger.error(f"获取HPC作业状态失败: {await response.text()}")
                        return {"status": "error", "progress": 0, "error": "获取作业状态失败"}
                    
                    data = await response.json()
                    
                    # 解析状态
                    status_map = {
                        "PENDING": "pending",
                        "RUNNING": "running",
                        "COMPLETED": "completed",
                        "FAILED": "failed",
                        "CANCELLED": "cancelled"
                    }
                    
                    hpc_status = data.get("status", "UNKNOWN")
                    status = status_map.get(hpc_status, "unknown")
                    
                    # 计算进度(简化版本)
                    progress = 0
                    if status == "completed":
                        progress = 1.0
                    elif status == "running":
                        # 从输出日志中解析进度(简化逻辑)
                        progress = 0.5
                    
                    result = None
                    if status == "completed":
                        # 读取结果(简化逻辑)
                        # 实际应该读取结果文件，或提供下载链接
                        result = {"result_url": f"/api/v1/analysis/result/{task_id}"}
                    
                    return {
                        "status": status,
                        "progress": progress,
                        "result": result,
                        "error": data.get("error")
                    }
        except Exception as e:
            self.logger.error(f"获取作业状态失败: {str(e)}")
            return {"status": "error", "progress": 0, "error": str(e)} 