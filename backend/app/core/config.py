import os
import secrets
from typing import List, Union, Dict, Any
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60分钟 * 24小时 * 8天 = 8天
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    # CORS允许的源
    CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # LLM模型设置
    LLM_MODEL_PATH: str = os.getenv("LLM_MODEL_PATH", "/models/llama3")
    SCGPT_MODEL_PATH: str = os.getenv("SCGPT_MODEL_PATH", "/models/scgpt")
    GENEFORMER_MODEL_PATH: str = os.getenv("GENEFORMER_MODEL_PATH", "/models/geneformer")
    
    # ChromaDB设置
    CHROMADB_HOST: str = os.getenv("CHROMADB_HOST", "localhost")
    CHROMADB_PORT: int = int(os.getenv("CHROMADB_PORT", "8000"))
    
    # HPC设置
    HPC_SCHEDULER_URL: str = os.getenv("HPC_SCHEDULER_URL", "http://localhost:9000")
    HPC_USERNAME: str = os.getenv("HPC_USERNAME", "user")
    HPC_PASSWORD: str = os.getenv("HPC_PASSWORD", "password")
    
    # 日志设置
    LOKI_URL: str = os.getenv("LOKI_URL", "http://localhost:3100")
    
    # 添加共享存储路径配置
    DATA_STORAGE_PATH: str = os.getenv("DATA_STORAGE_PATH", "/shared/data")
    RESULT_STORAGE_PATH: str = os.getenv("RESULT_STORAGE_PATH", "/shared/results")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 